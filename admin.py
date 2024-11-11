import streamlit as st
from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader
import tempfile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from langchain_upstage import UpstageEmbeddings
from langchain.callbacks.base import BaseCallbackHandler

load_dotenv()

embedding = UpstageEmbeddings(model="solar-embedding-1-large")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
)

st.set_page_config(page_title="유라클 A to Z 챗봇 관리자", page_icon="./files/uracle_favicon.png")
st.title("유라클 A to Z 챗봇 관리자")
st.caption("파일 업로드 및 설정으로 챗봇 데이터를 업데이트 할 수 있습니다.")

st.divider()

col1, col2 = st.columns([9,1])
with col1:
	multi = '''1.**첨부파일 업로드**
	(허용 확장자 : docx, txt, md, pdf)
	'''
	st.markdown(multi)

	
with col2:
	st.button("적용", key=0)


uploaded_files = st.file_uploader(
	label="파일 선택",
	type=["docx", "pdf", "md", "txt", "pptx"],
	accept_multiple_files=True,
	help="워드, 텍스트, 마크다운 파일을 선택해 주세요.",
)




class MyCallbackHandler(BaseCallbackHandler):
	def on_text(self, text: str, **kwargs):
		print(f"Progress: {text}")
		st.write(text)

	def on_document(self, document, **kwargs):
		print(f"Processing document: {document.page_content[:30]}...")
		st.write()

uploadCallBack = MyCallbackHandler()

if uploaded_files is not None:
	for uploaded_file in uploaded_files:
		file_extension = Path(uploaded_file.name).suffix.lower()
		st.write(file_extension)
		if file_extension == ".pdf":
			# 임시 파일에 저장
			with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
				temp_file.write(uploaded_file.read())
				temp_file_path = temp_file.name
    
			# PyMuPDFLoader에 임시 파일 경로 전달
			pdf_loader = PyMuPDFLoader(temp_file_path)
			documents = pdf_loader.load()

			document_list = pdf_loader.load_and_split(text_splitter=text_splitter)
			st.write(document_list)

			index_name = 'uracle-atoz-chelsea'
			# database = PineconeVectorStore.from_documents(document_list, embedding, index_name=index_name, callbacks=uploadCallBack)

			# Streamlit에서 진행률 바 생성
			progress_bar = st.progress(0)
			total_docs = len(document_list)

			def update_progress(document_index):
				progress = (document_index + 1) / total_docs
				progress_bar.progress(progress)

			# 벡터 스토어 생성 및 진행률 업데이트 콜백 추가
			for i, doc in enumerate(documents):
				update_progress(i)  # 진행률 업데이트
				vector_store = PineconeVectorStore.from_documents(document_list, embedding, index_name=index_name)

    		# 결과 출력
			# for doc in documents:
			# 	st.write(doc.page_content)  # 문서 내용 출력
		# 	st.write(f"파일 확장자: {file_extension}")

		# bytes_data = uploaded_file.read()
		
		# # 저장할 파일 경로와 이름 지정
		# save_path = f"./{uploaded_file.name}"
    
		# # 파일을 바이너리로 열어서 저장
		# with open(save_path, "wb") as f:
		# 	f.write(uploaded_file.getbuffer())
			
		# st.success(f"File saved successfully at {save_path}")

st.divider()

col1, col2 = st.columns([9,1])

with col1:
	st.markdown("2.**텍스트 등록**")

with col2:
	st.button("적용", key=1)


st.text_area("글 입력")

st.divider()

col1, col2 = st.columns([9,1])

with col1:
	multi = '''3.**유사성 등록**
	(대리 => 수석)
	'''
	st.markdown(multi)

with col2:
	st.button("적용", key=2)
	
col1, col2 = st.columns(2)
with col1:
	title = st.text_input("변경 전 텍스트")

with col2:
	title = st.text_input("변경 후 텍스트")


st.divider()