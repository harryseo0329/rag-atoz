import os
import pinecone
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_upstage import UpstageEmbeddings
import tempfile
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
import pandas as pd
from PIL import Image
import pytesseract
from pptx import Presentation

# 환경변수를 불러옴
load_dotenv()

def process_and_store_document(uploaded_file, file_type):
    try:
        # 1. 업로드된 파일을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        # 2. 파일 형식에 따른 로더 선택
        if file_type == "txt":
            with open(temp_file_path, "r", encoding="utf-8") as file:
                document = file.read()
        
        elif file_type == "pdf":
            loader = PyPDFLoader(temp_file_path)
            document = loader.load()
        
        elif file_type == "docx":
            loader = Docx2txtLoader(temp_file_path)
            document = loader.load()

        elif file_type == "xlsx":
            # 엑셀 파일 로드
            df = pd.read_excel(temp_file_path)
            document = " ".join(df.astype(str).values.flatten())  # 모든 셀의 텍스트를 문자열로 결합
        
        elif file_type in ["png", "jpg", "jpeg"]:
            # 이미지에서 텍스트 추출
            image = Image.open(temp_file_path)
            document = pytesseract.image_to_string(image)  # 이미지에서 텍스트 추출
        
        elif file_type == "pptx":
            # 파워포인트 파일 로드
            ppt = Presentation(temp_file_path)
            document = []
            for slide in ppt.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        document.append(shape.text)
            document = " ".join(document)  # 슬라이드 텍스트를 결합
            
        else:
            print(f"지원되지 않는 파일 형식입니다: {file_type}")
            return False
        
        # 3. document가 리스트 형태일 경우 문자열로 결합
        if isinstance(document, list):
            document = " ".join([doc.page_content for doc in document])  # 각 Document 객체의 텍스트를 결합
            
        # 3. 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        split_texts = text_splitter.split_text(document)

        # 5. 문자열 분할 결과를 Document 객체로 변환
        documents = [Document(page_content=text) for text in split_texts]
    
        # 6. UpstageEmbeddings와 PineconeVectorStore 초기화 및 저장
        embeddings = UpstageEmbeddings(model="solar-embedding-1-large")  # UpstageEmbeddings를 초기화
        index_name = 'uracle-index'
        database = PineconeVectorStore.from_documents(documents, embeddings, index_name=index_name)

        print("임베딩이 성공적으로 저장되었습니다!")
        return True  # 저장 성공 시 True 리턴

    except Exception as e:
        print(f"임베딩 저장 실패: {e}")
        return False  # 오류 발생 시 False 리턴