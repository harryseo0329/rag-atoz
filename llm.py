from langchain_upstage import UpstageEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import ChatUpstage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

#from langchain.chat_models import ChatOllama
#from langchain_ollama import ChatOllama
#from langchain_chroma import Chroma

from config import answer_examples
from logger import logger
from dic import dictionary

#from utils import (
#    stopwords,
#    get_sparse_encoder_path
#)
#from harry_pinecone import (
#    init_pinecone_index,
#    PineconeKiwiHybridRetriever
#)
import os

import time

import uuid
import numpy as np
from langchain.schema import Document
from pinecone import Pinecone

global_question = ""
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


#retriever
def get_retriever():
    start_time = time.time()
    #임베딩
    embedding = UpstageEmbeddings(model='solar-embedding-1-large')

    #파인콘 인덱스명
    index_name = os.getenv('INDEX_NAME') 

    database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)
    #database = Chroma(collection_name='chroma-rules-3',persist_directory="./chroma3", embedding_function=embedding)

    #의미중심 리트리버
    dense_retriever = database.as_retriever(search_kwargs={'k': 4}) 
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.log_custom("소요시간 : %s", elapsed_time)
    return dense_retriever 

def get_history_retriever():
    llm = get_llm()
    retriever = get_retriever()

    
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
        "If the question is about employee information, ignore the chat history entirely and provide an answer based solely on the question."
    )
    contextualize_q_system_prompt=""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    return history_aware_retriever

#llm
def get_llm():
    #Upstage LLM
    llm=ChatUpstage()

    #Ollama kullm3
    #llm = ChatOllama(model="bnksys/kullm3-11b")
    return llm


#dictionary 
def get_dictionary_chain():
    
    myDictionary = dictionary
    """
        사용자의 질문을 먼저 보고, 우리의 사전을 참고해서 사용자의 질문을 변경해주세요.
        만약 변경할 필요가 없다고 판단된다면, 사용자의 질문을 변경하지 않아도 됩니다.  
        그런 경우에는 질문만 리턴해주세요
    """
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(f"""
        First, review the user's question and refer to our dictionary to modify the user's question if necessary.
        If no modification is needed, return the original question as it is.
        In such cases, simply return the question without any changes.
        
        dictionary: {myDictionary}                        
                                            
        question: {{question}}
    """)

    dictionary_chain = prompt | llm | StrOutputParser()
    
    return dictionary_chain

def get_rag_chain():
    llm = get_llm()
    
    example_prompt = ChatPromptTemplate.from_messages(
        [('human', '{input}'), ('ai', '{answer}')]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        examples=answer_examples,
        # This is a prompt template used to format each individual example.
        example_prompt=example_prompt,
    )

    system_prompt = (
        "You are an assistant for question-answering tasks for Uracle Corp. "
        "Use the following pieces of retrieved context to answer "
        "the question. Do not use external internet data or search the web. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "And if there is `image_path` in the metadata of retrieved context to answer, convert the URL value to a markdown image and add it to the end of the answer."
        "And if there is markdown table in your answer, please show it as a table."
        "And if there is a markdown-image that can be used as a reference in the answer, please show the Markdown image in your answer."
        "\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            few_shot_prompt,
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    history_aware_retriever = get_history_retriever()
    #history_aware_retriever = get_retriever()
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # Add invoke logging
    '''
    def question_answer_chain_with_logging(input_data):
        logger.log_custom("Invoking question_answer_chain with input:\n%s", input_data)
        output = question_answer_chain.invoke(input_data, streaming=True)

        answer_image = ""
        for doc in input_data["context"]:
            image_path = doc.metadata.get("image_path")
            if image_path:
                logger.log_custom("image_path:%s",image_path)
                answer_image = image_path
                break
        
        output += f"\n\n![Image]({answer_image})"  # 이미지 삽입

        logger.log_custom("Output from question_answer_chain:\n%s", output)
        logger.log_custom("--------------------------------------------------------------------")
        return output 
    '''
    #rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain_with_logging)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    
      
    conversaional_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ).pick('answer')

    return conversaional_rag_chain

def get_ai_response(user_message):
    global global_question 
    global_question = user_message
    dictionary_chain = get_dictionary_chain()

    # Add invoke logging
    def dictionary_chain_with_logging(input_data):
        logger.log_custom("Invoking dictionary_chain with input:\n%s", input_data)
        output = dictionary_chain.invoke(input_data)
        logger.log_custom("Output from dictionary_chain:%s", output)
        logger.log_custom("--------------------------------------------------------------------")
        return output

    rag_chain = get_rag_chain()
    atoz_chain = {"input":dictionary_chain_with_logging} | rag_chain
    ai_response = atoz_chain.stream({"question":global_question},config={"configurable":{"session_id":"abcd12123"}})

    return ai_response 

def get_direct_ai_response(user_message):
    global global_question 
    global_question = user_message
    dictionary_chain = get_dictionary_chain()

    # Add invoke logging
    def dictionary_chain_with_logging(input_data):
        logger.log_custom("Invoking dictionary_chain with input:\n%s", input_data)
        output = dictionary_chain.invoke(input_data)
        logger.log_custom("Output from dictionary_chain:%s", output)
        logger.log_custom("--------------------------------------------------------------------")
        return output

    rag_chain = get_rag_chain()
    atoz_chain = {"input":dictionary_chain_with_logging} | rag_chain
    ai_response = atoz_chain.invoke({"question": global_question}, config={"configurable": {"session_id": "abcd12123"}})

    return ai_response

def save_question(qustion_arr):
    embedding = UpstageEmbeddings(model='solar-embedding-1-large')
    # 질문 벡터화
    question_vector = embedding.embed_query(qustion_arr[0])

    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    pc = Pinecone(api_key=pinecone_api_key)

    index_description = pc.describe_index(os.environ.get("QUESTION_INDEX_NAME"))
    index_host = index_description.host

    index = pc.Index(host=index_host)
    
    # 기존 질문을 찾기 (빈도수 업데이트)
    existing_question = index.query(
        vector=question_vector, top_k=1, filter={
            "fm": qustion_arr[1], "dept": qustion_arr[2], "pos": qustion_arr[3]
        },
        include_metadata=True  # 메타데이터 포함
    )
    question_id = str(uuid.uuid4())
    new_frequency = 0
    # 기존 질문이 있으면 빈도수 증가
    if existing_question and existing_question['matches']:
        existing_metadata = existing_question['matches'][0]['metadata']
        score = existing_question['matches'][0]['score']
        if score >= 0.8:
            question_id = existing_question['matches'][0]['id']
            new_frequency = existing_metadata['frequency'] + 1
        else:
            new_frequency = 1
    else:
        # 새로운 질문은 빈도수 1로 설정
        new_frequency = 1
        
    # 기존 질문의 빈도수만 갱신
    index.upsert(
        vectors=[{
            'id': question_id,  # 기존 ID 사용
            'values': question_vector,
            'metadata': {
                'question': qustion_arr[0],
                'fm': qustion_arr[1],
                'dept': qustion_arr[2],
                'pos': qustion_arr[3],
                'frequency': new_frequency
            }
        }]
    )



def ai_recommand_questions(fm, dept, pos):
    embedding = UpstageEmbeddings(model='solar-embedding-1-large')
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    pc = Pinecone(api_key=pinecone_api_key)
    index_description = pc.describe_index(os.environ.get("QUESTION_INDEX_NAME"))
    index_host = index_description.host

    index = pc.Index(host=index_host)

    # 메타데이터 필터를 사용하여 유사한 질문 검색
    filter_metadata = {
        "fm": fm,
        "dept": dept,
        "pos": pos
    }

    # Pinecone에서 메타데이터 기반으로 유사한 질문을 검색
    results = index.query(
        vector=[0] * 4096,
        top_k=20,  # 최대 5개 질문 검색
        filter=filter_metadata,  # 메타데이터 필터를 사용
        include_metadata=True  # 메타데이터 포함
    )
    
    # 검색된 질문을 빈도수 기준으로 정렬
    sorted_questions = sorted(
        results['matches'], 
        key=lambda x: x['metadata']['frequency'],  # 빈도수 기준으로 정렬
        reverse=True  # 빈도수가 높은 순으로
    )
    
    # 질문 텍스트만 추출하여 반환
    similar_questions = ["질문을 선택해 주세요"] + [match['metadata']['question'] for match in sorted_questions[:5]]
    
    return similar_questions
