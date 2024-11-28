from dotenv import load_dotenv
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

import os

import os
import time

import uuid
import numpy as np
#from langchain.schema import Document
from pinecone import Pinecone
import re
from langchain_upstage import UpstageGroundednessCheck

load_dotenv()

#Upstage LLM
llm = ChatUpstage()

#Ustage Embedding
embedding = UpstageEmbeddings(model='solar-embedding-1-large')

#atoz-index
index_name = os.getenv('INDEX_NAME') 
database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)

#question-index
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
question_index_description = pc.describe_index(os.environ.get("QUESTION_INDEX_NAME"))
question_index_host = question_index_description.host
question_index = pc.Index(host=question_index_host)

store = {}

def stream_response(response: str):
    # 정규식을 사용해 단어, 공백, 특수문자, 줄바꿈을 분리
    tokens = re.findall(r'\S+|\n', response)

    for token in tokens:
        if token == "\n":  # 줄바꿈 처리
            yield "\n"
        else:
            yield token + " "  # 단어 또는 특수문자 처리
        time.sleep(0.015)  # 딜레이 추가

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Retriever
def get_retriever():
    start_time = time.time()
    #임베딩
    #embedding = UpstageEmbeddings(model='solar-embedding-1-large')

    #파인콘 인덱스명
    #index_name = os.getenv('INDEX_NAME') 

    #database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)
    #database = Chroma(collection_name='chroma-rules-3',persist_directory="./chroma3", embedding_function=embedding)

    #의미중심 리트리버
    dense_retriever = database.as_retriever(search_kwargs={'k': 3}) 
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.log_custom("get_retriever() 소요시간 : %s", elapsed_time)
    return dense_retriever 

def get_history_retriever():
    start_time = time.time()
    retriever = get_retriever()
    
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question, "
        "reformulate the question to make it standalone. "
        "Preserve the original intent but include missing details if referenced in the chat history."
        "For employee-related queries, disregard chat history and answer solely based on the question."
    )
    
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

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.log_custom("get_history_retriever() 소요시간 : %s", elapsed_time)
    return history_aware_retriever

#llm
'''
def get_llm():
    start_time = time.time()
    #Upstage LLM
    llm=ChatUpstage()

    #Ollama kullm3
    #llm = ChatOllama(model="bnksys/kullm3-11b")
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.log_custom("get_llm() 소요시간 : %s", elapsed_time)
    return llm
'''

# Dictionary Chain
def get_dictionary_chain():
    start_time = time.time()
    myDictionary = dictionary
    """
        사용자의 질문을 먼저 보고, 우리의 사전을 참고해서 사용자의 질문을 변경해주세요.
        만약 변경할 필요가 없다고 판단된다면, 사용자의 질문을 변경하지 않아도 됩니다.  
        그런 경우에는 질문만 리턴해주세요
    """
    #llm = get_llm()
    prompt = ChatPromptTemplate.from_template(f"""
        First, review the user's question and refer to our dictionary to modify the user's question if necessary.
        If no modification is needed, return the original question as it is.
        In such cases, simply return the question without any changes.
        
        dictionary: {myDictionary}                        
                                            
        question: {{question}}
    """)

    dictionary_chain = prompt | llm | StrOutputParser()
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.log_custom("get_dictionary_chain() 소요시간 : %s", elapsed_time)
    return dictionary_chain

# RAG Chain
def get_rag_chain():
    start_time = time.time()
    #llm = get_llm()
    
    example_prompt = ChatPromptTemplate.from_messages(
        [('human', '{input}'), ('ai', '{answer}')]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        examples=answer_examples,
        example_prompt=example_prompt,
    )

    system_prompt = (
        "You are an assistant for question-answering tasks for Uracle Corp. "
        "Use the following pieces of retrieved context to answer the question. "
        "Do not use external internet data, do not search the web, and do not access any external databases or external sources. "
        "If the provided context does not contain enough information, explicitly say \"I don’t know.\" "
        "Use three sentences maximum and keep the answer concise. "
        "And if there is \"image_path\" in the metadata of retrieved context to answer, convert the URL value to a markdown image and add it to the end of the answer."
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
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # Add invoke logging
    
    def question_answer_chain_with_logging(input_data):
        logger.log_custom("=================================================================================================")
        logger.log_custom("[ BASE_DATA( chat_history ) ] Invoking question_answer_chain with input:\n%s", input_data["chat_history"])
        logger.log_custom("=================================================================================================")
        logger.log_custom("[ BASE_DATA( context ) ] Invoking question_answer_chain with input:\n%s", input_data["context"])
        logger.log_custom("=================================================================================================")
        retrieved_content = ""   
        answer_image = ""
        
        for doc in input_data["context"]:
            retrieved_content += doc.page_content+"\n"
            image_path = doc.metadata.get("image_path")
            if image_path:
                logger.log_custom("image_path:%s",image_path)
                if answer_image != "":
                    answer_image = image_path
            
        start_time1 = time.time()
        output = question_answer_chain.invoke(input_data, streaming=True)
        end_time1 = time.time()
        elapsed_time1 = end_time1 - start_time1
        logger.log_custom("question_answer_chain.invoke() 소요시간 : %s", elapsed_time1)

        if answer_image != "":
            output += f"\n\n![Image]({answer_image})"  # 이미지 삽입

        logger.log_custom("[ ANSWER ] Output from question_answer_chain(검사전):\n%s", output)
        logger.log_custom("--------------------------------------------------------------------")

        
        #groundedness 체크
        groundedness_check = UpstageGroundednessCheck()
        request_input = {
            "context": retrieved_content,
            "answer": output,
        }
        start_time2 = time.time()
        response = groundedness_check.invoke(request_input)
        end_time2 = time.time()
        elapsed_time2 = end_time2 - start_time2
        logger.log_custom("groundedness_check.invoke() 소요시간 : %s", elapsed_time2)

        logger.log_custom("-----------groundedness_check-----------")
        logger.log_custom(response)

        if response == "notGrounded" :
            output = "죄송합니다. 검색된 문맥에서 해당 내용을 찾을 수 없어서 답변드릴 수 없습니다."
            logger.log_custom("[ ANSWER ] Output from question_answer_chain(검사후):\n%s", output)
            logger.log_custom("--------------------------------------------------------------------")
            
        return output 
    
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain_with_logging)

    #rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversaional_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ).pick('answer')
    
    return conversational_rag_chain

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.log_custom("get_rag_chain() 소요시간 : %s", elapsed_time)    
    return conversaional_rag_chain

def get_ai_response(user_message):
    dictionary_chain = get_dictionary_chain()

    # Add invoke logging
    def dictionary_chain_with_logging(input_data):
        logger.log_custom("Invoking dictionary_chain with input:\n%s", input_data)
        start_time = time.time()
        output = dictionary_chain.invoke(input_data)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.log_custom("dictionary_chain.invoke() 소요시간 : %s", elapsed_time) 
        logger.log_custom("Output from dictionary_chain:%s", output)
        logger.log_custom("--------------------------------------------------------------------")
        return output

    rag_chain = get_rag_chain()
    atoz_chain = {"input":dictionary_chain_with_logging} | rag_chain
    #ai_response = atoz_chain.stream({"question":global_question},config={"configurable":{"session_id":"abcd1123"}})
    ai_response = atoz_chain.invoke({"question":user_message},config={"configurable":{"session_id":"abcd123"}})
    
    return stream_response(ai_response) #ai_response

def get_direct_ai_response(user_message):
    dictionary_chain = get_dictionary_chain()

    # 사전 체인 로깅 추가
    def dictionary_chain_with_logging(input_data):
        logger.log_custom("Dictionary Chain Input:\n%s", input_data)
        output = dictionary_chain.invoke(input_data)
        logger.log_custom("Dictionary Chain Output:\n%s", output)
        return output

    rag_chain = get_rag_chain()
    atoz_chain = {"input":dictionary_chain_with_logging} | rag_chain
    ai_response = atoz_chain.invoke({"question": user_message}, config={"configurable": {"session_id": "abcd123"}})

    return ai_response

async def save_question(qustion_arr):
    start_time = time.time()
    
    # 질문 벡터화
    question_vector = embedding.embed_query(qustion_arr[0])

    # 기존 질문을 찾기 (빈도수 업데이트)
    existing_question = question_index.query(
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

    logger.log_custom("async def save_question() 질문 저장( ID: %s )", question_id)    
    # 기존 질문의 빈도수만 갱신
    question_index.upsert(
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
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.log_custom("save_question() 소요시간 : %s", elapsed_time)


def ai_recommand_questions(fm, dept, pos):
    start_time = time.time()

    # 메타데이터 필터를 사용하여 유사한 질문 검색
    filter_metadata = {
        "fm": fm,
        "dept": dept,
        "pos": pos
    }

    # Pinecone에서 메타데이터 기반으로 유사한 질문을 검색
    results = question_index.query(
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

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.log_custom("ai_recommand_questions() 소요시간 : %s", elapsed_time)
    
    return similar_questions 
