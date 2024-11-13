import os
import subprocess
import tempfile
from pdf2image import convert_from_path
from pptx import Presentation
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pinecone
from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_upstage import UpstageEmbeddings
from dotenv import load_dotenv
import pandas as pd
from docx import Document as DocxDocument
import fitz  # PyMuPDF
import platform

# 환경 변수 로드
load_dotenv()

# Pinecone 클라이언트 생성
pc = pinecone.Pinecone(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENV'))

# Tesseract OCR 경로 설정
tesseract_base_path = os.path.join("libs", "tesseract")
pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_base_path, "tesseract.exe")
os.environ["TESSDATA_PREFIX"] = os.path.join(tesseract_base_path, "tessdata")

poppler_path = 'libs/poppler/Library/bin'  # poppler 경로 설정

# OS에 따른 LibreOffice 경로 설정
if platform.system() == "Windows":
    LIBREOFFICE_PATH = "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
else:
    LIBREOFFICE_PATH = "/Applications/LibreOffice.app/Contents/MacOS/soffice"  # Mac용 경로

# 파일 형식별 처리 함수 정의

def process_text_file(file_path):
    """TXT 파일의 내용을 읽어 문자열로 반환합니다."""
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
    print(f"TXT 파일 내용:\n{text}\n{'-'*50}")
    return text

def process_docx_file(file_path):
    """DOCX 파일의 각 단락을 읽어 문자열로 결합하여 반환하며, 파일명을 metadata에 추가합니다."""
    doc = DocxDocument(file_path)
    document_text = "\n".join([para.text for para in doc.paragraphs])
    return document_text  # 파일명은 반환하지 않고 호출 함수에서 전달

def process_doc_file(file_path):
    """DOC 파일을 LibreOffice를 사용하여 DOCX로 변환한 후, 텍스트를 추출하여 반환합니다."""
    # DOC 파일을 DOCX로 변환
    docx_path = file_path.replace(".doc", ".docx")
    result = subprocess.run(
        [LIBREOFFICE_PATH, "--headless", "--convert-to", "docx", file_path, "--outdir", os.path.dirname(file_path)],
        capture_output=True, text=True
    )
    
    # 변환 실패 시 예외 발생
    if result.returncode != 0:
        print("LibreOffice DOC to DOCX 변환 실패:", result.stderr)
        raise Exception("DOC to DOCX 변환 실패")
    
    # 변환된 DOCX 파일에서 텍스트 추출
    document_text = process_docx_file(docx_path)
    print(f"DOC 파일 내용:\n{document_text}\n{'-'*50}")
    
    # 변환된 DOCX 파일 삭제
    os.remove(docx_path)
    
    return document_text

def process_xlsx_file(file_path):
    """엑셀 파일의 각 시트를 개별 Document로 생성하여 반환하고, 긴 텍스트는 분할하여 저장합니다."""
    sheet_documents = []
    xls = pd.ExcelFile(file_path)

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        sheet_text = " ".join(df.astype(str).values.flatten())
        
        # 텍스트 분할: 1000 토큰으로 청크를 분할, 200 토큰 중첩
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_texts = text_splitter.split_text(sheet_text)
        
        # 각 분할된 텍스트를 Document로 생성
        for text in split_texts:
            sheet_documents.append(Document(page_content=text, metadata={"sheet_name": sheet_name}))

    return sheet_documents

def process_pdf_file(file_path):
    """PDF 파일의 모든 페이지에서 텍스트를 추출하여 하나의 문자열로 반환합니다."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    print(f"PDF 파일 내용:\n{text}\n{'-'*50}")
    return text

def process_image_file(file_path):
    """이미지 파일에서 OCR을 사용해 텍스트를 추출하여 문자열로 반환합니다."""
    image = Image.open(file_path)
    image = image.convert("L")  # 흑백 변환
    image = ImageEnhance.Contrast(image).enhance(2)  # 대비 증가
    image = image.filter(ImageFilter.SHARPEN)  # 샤프닝 필터 적용
    text = pytesseract.image_to_string(image, lang="kor").strip()
    print(f"이미지 파일 OCR 내용:\n{text}\n{'-'*50}")
    return text

def preprocess_image_for_ocr(image_path):
    """이미지 전처리: 대비 증가, 흑백 변환, 샤프닝 적용"""
    image = Image.open(image_path)
    image = image.convert("L")  # 흑백 변환
    image = ImageEnhance.Contrast(image).enhance(2)  # 대비 증가
    image = image.filter(ImageFilter.SHARPEN)  # 샤프닝 필터 적용
    return image

def convert_pptx_to_pdf_images(pptx_path, save_dir="images/poppler"):
    """PPTX 파일을 PDF로 변환 후, PDF의 각 페이지를 이미지로 변환하여 상대 경로로 이미지 파일 경로를 반환합니다."""
    os.makedirs(save_dir, exist_ok=True)
    
    # PDF 파일 경로 설정 (temp 폴더에 임시로 저장)
    pdf_path = os.path.join("temp", f"{os.path.splitext(os.path.basename(pptx_path))[0]}.pdf")
    
    # LibreOffice를 사용하여 PPTX를 PDF로 변환
    result = subprocess.run(
        [LIBREOFFICE_PATH, "--headless", "--convert-to", "pdf", pptx_path, "--outdir", os.path.dirname(pdf_path)],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print("LibreOffice 변환 실패:", result.stderr)
        raise Exception("PPTX to PDF 변환 실패")

    if not os.path.exists(pdf_path):
        raise Exception("PDF 파일이 생성되지 않았습니다.")
    
    images = convert_from_path(pdf_path, poppler_path=poppler_path)
    image_paths = []

    for i, img in enumerate(images):
        # 상대 경로로 이미지 저장
        image_name = f"{os.path.splitext(os.path.basename(pptx_path))[0]}_page_{i + 1}.png"
        image_path = os.path.join(save_dir, image_name)
        img.save(image_path, "PNG")
        
        # 이미지 상대 경로로 리스트에 추가
        image_paths.append(image_path.replace("\\", "/"))  # 경로에 슬래시(`/`) 사용

    os.remove(pdf_path)  # 임시 PDF 파일 삭제
    return image_paths

def process_and_store_document(uploaded_file, file_type):
    """파일을 읽어 Pinecone에 저장합니다. 파일 형식에 따라 적절한 처리 함수를 호출합니다."""
    try:
        
        # 원본 파일명을 저장
        file_name = uploaded_file.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        # Document 객체를 저장할 리스트
        documents = []

        if file_type == "pptx":
            # PPTX 파일의 슬라이드를 PDF로 변환 후 각 페이지를 이미지로 변환
            image_files = convert_pptx_to_pdf_images(temp_file_path)  # PDF -> 이미지 변환
            ppt = Presentation(temp_file_path)

            for i, slide in enumerate(ppt.slides):
                slide_text = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        slide_text.append(shape.text)
                
                # OCR 수행
                ocr_text_content = ""
                if i < len(image_files):
                    preprocessed_image = preprocess_image_for_ocr(image_files[i])
                    ocr_text_content = pytesseract.image_to_string(preprocessed_image, lang="kor").strip()

                # 슬라이드 텍스트와 OCR 텍스트 결합하여 Document 객체 생성
                combined_content = f"{' '.join(slide_text)}\n{ocr_text_content}"
                print(f"PPTX 파일 슬라이드 {i+1} 내용:\n{combined_content}\n{'-'*50}")
                documents.append(Document(
                    page_content=combined_content,
                    metadata={
                        "slide_index": i + 1,
                        "image_path": image_files[i],
                        "source": file_name
                    }
                ))

        elif file_type == "xlsx":
            # 엑셀 파일 각 시트를 Document로 생성하고, 파일명 metadata에 추가
            sheet_documents = process_xlsx_file(temp_file_path)
            documents = [Document(page_content=sheet.page_content, metadata={"source": file_name, "sheet_name": sheet.metadata["sheet_name"]}) for sheet in sheet_documents]
        
        elif file_type == "docx":
            document_text = process_docx_file(temp_file_path)
            print(f"DOCX 파일 내용:\n{document_text}\n{'-'*50}")
            
            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            split_texts = text_splitter.split_text(document_text)
             # 분할된 텍스트 각각에 Document 생성 및 metadata에 원본 파일명을 포함한 source 추가
            documents = [
                Document(
                    page_content=text,
                    metadata={
                        "source": file_name
                    }
                ) for index, text in enumerate(split_texts)
            ]

        elif file_type == "doc":
            document_text = process_doc_file(temp_file_path)
            print(f"DOC 파일 내용:\n{document_text}\n{'-'*50}")
            
            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            split_texts = text_splitter.split_text(document_text)
            documents = [Document(page_content=text, metadata={"source": file_name}) for text in split_texts]

        elif file_type == "pdf":
            document_text = process_pdf_file(temp_file_path)
            print(f"PDF 파일 내용:\n{document_text}\n{'-'*50}")
            
            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            split_texts = text_splitter.split_text(document_text)
            documents = [Document(page_content=text, metadata={"source": file_name}) for text in split_texts]

        elif file_type in ["png", "jpg", "jpeg"]:
            document_text = process_image_file(temp_file_path)
            print(f"이미지 파일 OCR 내용:\n{document_text}\n{'-'*50}")
            
            # 이미지 OCR 결과를 Document 객체로 생성
            documents = [Document(page_content=document_text, metadata={"source": file_name})]

        # Pinecone에 저장
        embeddings = UpstageEmbeddings(model="solar-embedding-1-large")
        index_name = os.getenv('INDEX_NAME')
        
        # 인덱스가 존재하는지 확인
        if index_name not in pc.list_indexes().names():
            pc.create_index(index_name, dimension=embeddings.dimension)
        
        database = PineconeVectorStore.from_documents(documents, embeddings, index_name=index_name)
        
        print("임베딩이 성공적으로 저장되었습니다!")
        return True

    except Exception as e:
        print(f"임베딩 저장 실패: {e}")
        return False



