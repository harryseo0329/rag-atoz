import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_upstage import ChatUpstage, UpstageEmbeddings  
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Pinecone
from langchain_pinecone import PineconeVectorStore
from PIL import Image
import json

# 환경 변수 로드
load_dotenv()

# ChatUpstage 모델을 초기화하는 함수
def get_llm():
    return ChatUpstage()

# Pinecone에서 검색을 수행하는 함수
def get_retriever():
    embeddings = UpstageEmbeddings(model="solar-embedding-1-large")
    index_name = os.getenv('INDEX_NAME')
    database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)
    return database.as_retriever(search_kwargs={"k": 4})

def generate_bot_response(user_question):
    retriever = get_retriever()
    llm = get_llm()

    # QA 체인 설정 (유사도 기반 검색)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    # 유사한 문서 검색
    response = qa_chain.invoke({"query": user_question})
    answer_text = response["result"]
    source_documents = response["source_documents"]

    # 텍스트 및 이미지 기반 검색 결과 구성
    answer_images = []
    has_relevant_text = bool(answer_text.strip())

    for doc in source_documents:
        image_path = doc.metadata.get("image_path")
        if image_path:
            answer_images.append(image_path)

    # 이미지가 없는 경우와 텍스트가 없는 경우를 모두 고려하여 응답 수정
    if not has_relevant_text and not answer_images:
        answer_text = "해당 질문에 대한 관련 정보를 찾을 수 없습니다."
    elif not answer_images:
        answer_text += "\n(관련된 슬라이드 이미지는 찾을 수 없습니다.)"
    elif not has_relevant_text:
        answer_text = "해당 질문에 대한 텍스트 정보는 없습니다만, 관련 슬라이드 이미지를 제공합니다."

    return answer_text.strip(), answer_images

# 사용자와 상호작용 예시
def main():
    user_question = input("질문을 입력하세요: ")
    response_text, response_images = generate_bot_response(user_question)

    print("AI 응답:", response_text)
    
    if response_images:
        print("관련 슬라이드 이미지:")
        for image_path in response_images:
            print(f"이미지 경로: {image_path}")
            try:
                img = Image.open(image_path)
                img.show()
            except Exception as e:
                print(f"이미지를 열 수 없습니다: {e}")
    else:
        print("해당 질문에 대한 관련 슬라이드는 없습니다.")

if __name__ == "__main__":
    main()