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

from config import answer_examples
from logger import logger
from dic import dictionary

from utils import (
    stopwords,
    get_sparse_encoder_path
)

import os
import time

global_question = ""
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Retriever
def get_retriever():
    start_time = time.time()

    # 임베딩 생성
    embedding = UpstageEmbeddings(model='solar-embedding-1-large')
    
    # 파인콘 인덱스
    index_name = os.getenv('INDEX_NAME')
    database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)
    
    # 의미 중심 리트리버
    dense_retriever = database.as_retriever(search_kwargs={'k': 10})  # 결과 개수 증가
    
    elapsed_time = time.time() - start_time
    logger.log_custom("Retriever 생성 소요시간 : %s", elapsed_time)
    return dense_retriever

def get_history_retriever():
    llm = get_llm()
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
    return history_aware_retriever

# LLM
def get_llm():
    return ChatUpstage()

# Dictionary Chain
def get_dictionary_chain():
    myDictionary = dictionary
    
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(f"""
        사용자의 질문을 보고, 사전의 내용을 참고해 질문을 변경하세요.
        변경이 필요 없으면 원래 질문을 그대로 반환하세요.
        사전: {myDictionary}
        질문: {{question}}
    """)

    dictionary_chain = prompt | llm | StrOutputParser()
    return dictionary_chain

# RAG Chain
def get_rag_chain():
    llm = get_llm()
    
    example_prompt = ChatPromptTemplate.from_messages(
        [('human', '{input}'), ('ai', '{answer}')]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        examples=answer_examples,
        example_prompt=example_prompt,
    )

    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the provided retrieved context to answer the question concisely. "
        "If no context is sufficient, state that you don't know. "
        "Limit your answer to three sentences. "
        "For responses with `image_path` in metadata, include the image as a markdown image."
        "\n\n{context}"
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
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ).pick('answer')
    
    return conversational_rag_chain

# 수정된 get_ai_response
def get_ai_response(user_message):
    global global_question 
    global_question = user_message
    
    dictionary_chain = get_dictionary_chain()

    # 사전 체인 로깅 추가
    def dictionary_chain_with_logging(input_data):
        logger.log_custom("Dictionary Chain Input:\n%s", input_data)
        output = dictionary_chain.invoke(input_data)
        logger.log_custom("Dictionary Chain Output:\n%s", output)
        return output

    rag_chain = get_rag_chain()
    atoz_chain = {"input": dictionary_chain_with_logging} | rag_chain

    ai_response = atoz_chain.stream(
        {"question": global_question},
        config={"configurable": {"session_id": "abc1d111234"}}
    )
    print(ai_response)
    # 문맥이 부족하거나 학습되지 않은 내용에 대한 처리
    if ai_response is None or "학습되지 않은 내용" in ai_response:
        return "죄송합니다. 이 질문에 대해 학습된 정보가 없습니다."

    return ai_response
