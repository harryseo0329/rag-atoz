
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

    #이미 생성된 파인콘 인덱스로 database구성
    database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)
    
    

    retriever = database.as_retriever(search_kwargs={'k': 4})
    
    return retriever

def get_history_retriever():
    llm = get_llm()
    retriever = get_retriever()
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
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

#llm
def get_llm():
    llm=ChatUpstage()
    return llm

#dictionary 
def get_dictionary_chain():
    
    dictionary = [
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
        "And if there is markdown in your answer, please show it as a table."
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
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    conversaional_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ).pick('answer')

    #print(conversaional_rag_chain)

    return conversaional_rag_chain

def get_ai_response(user_message):
    dictionary_chain = get_dictionary_chain()
    rag_chain = get_rag_chain()
    atoz_chain = {"input":dictionary_chain} | rag_chain
    ai_response = atoz_chain.stream({"question":user_message},config={"configurable":{"session_id":"abc123"}})

    return ai_response
