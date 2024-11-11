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

from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.text_splitter import TokenTextSplitter

from config import answer_examples
from logger import logger


global_question = ""
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

#retriever
def get_retriever():
    #임베딩
    embedding = UpstageEmbeddings(model='solar-embedding-1-large')

    #파인콘 인덱스명
    index_name = "atoz-index"

    database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)
    
    #의미중심 리트리버
    dense_retriever = database.as_retriever(search_kwargs={'k': 4})
    
    #키워드중심 리트리버
    filter_criteria = {'source': {'$in': ['../dept-user-markdown-table.json', '../atoz-crawling.txt']}}
    #target_documents = dense_retriever.invoke(global_question, filters=filter_criteria)
    target_documents = database.similarity_search(query=global_question, filter=filter_criteria, k=4)
    
    bm25_retriever = BM25Retriever.from_documents(target_documents, tokenizer=TokenTextSplitter())
    
    # 앙상블 방식으로 retriever들을 결합 
    ensemble_retriever = EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever], weights=[0.5, 0.5]
    )
    
    return ensemble_retriever

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
    llm=ChatUpstage()
    return llm

#dictionary 
def get_dictionary_chain():
    
    dictionary = [
        "*님의 * 알려줘 -> 이름이 *인 사람의 * 알려줘",
        "직급 중 주임 -> 주임(대리)",
        "직급 중 선임 -> 선임(과장)",
        "직급 중 수석 -> 수석(부장)",
        "직급 중 이사 -> 이사(임원)",
        "직급 중 상무 -> 상무(임원)"
    ]
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(f"""
        사용자의 질문을 먼저 보고, 우리의 사전을 참고해서 사용자의 질문을 변경해주세요.
        만약 변경할 필요가 없다고 판단된다면, 사용자의 질문을 변경하지 않아도 됩니다.  
        그런 경우에는 질문만 리턴해주세요.
        사전: {dictionary}                        
                                            
        질문: {{question}}
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
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
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
    """
    # Add invoke logging
    def question_answer_chain_with_logging(input_data):
        logger.log_custom("Invoking question_answer_chain with input:\n%s", input_data)
        output = question_answer_chain.invoke(input_data)
        logger.log_custom("Output from question_answer_chain:\n%s", output)
        logger.log_custom("--------------------------------------------------------------------")
        return output
    """

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
    ai_response = atoz_chain.stream({"question":global_question},config={"configurable":{"session_id":"abcd1234"}})

    return ai_response 
