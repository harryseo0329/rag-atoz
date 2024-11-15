import streamlit as st
import webbrowser
from database import process_and_store_document
from logger import logger
import time

def show_page():
	logger.log_custom("어드민 페이지")
	st.title("사내 문서 관리 어드민 페이지")
	st.write("사내 문서를 업로드하고 AI 모델을 학습시킬 수 있습니다.")

	if 'uploaded_file' not in st.session_state:
		st.session_state.uploaded_file = None
		st.session_state.file_uploader_key = "file_uploader_key_1"  # 초기 key 설정

	
	# 파일 업로드 기능
	st.session_state.uploaded_file = st.file_uploader("문서를 업로드하세요", type=["txt", "pdf", "docx", "doc", "xlsx", "png", "jpg", "jpeg", "pptx"], key=st.session_state.file_uploader_key)
	
	if st.session_state.uploaded_file is not None:
		file_extension = st.session_state.uploaded_file.name.split(".")[-1].lower()
		logger.log_custom("확장자:%s",file_extension)
		# 스피너를 사용해 로딩 표시
		with st.spinner('문서를 처리하고 저장 중입니다...'):
			result = process_and_store_document(st.session_state.uploaded_file, file_extension)

		# 처리 결과 출력 
		st.write(result)  # process_and_store_document 함수의 결과가 문자열 또는 텍스트일 경우

		# 완료 메시지 표시
		st.success("문서가 성공적으로 저장 및 학습되었습니다!")
		st.session_state.uploaded_file = None
		st.session_state.file_uploader_key = f"file_uploader_key_{int(st.session_state.file_uploader_key.split('_')[-1])+1}"  # key 변경
		
		time.sleep(3)  # 3초 대기
		st.rerun()
		
		
		
		