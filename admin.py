# import streamlit as st
# import webbrowser
# from database import process_and_store_document
# from logger import logger
# import time
# import tele_bot

# chat_id = "123456789"  # 채팅 ID

# def show_page():
#     logger.log_custom("어드민 페이지")
#     st.title("사내 문서 관리 관리자")
#     st.write("사내 문서를 업로드하고 AI 모델을 학습시킬 수 있습니다.")

#     if 'uploaded_file' not in st.session_state:
#         st.session_state.uploaded_file = None
#         st.session_state.file_uploader_key = "file_uploader_key_1"  # 초기 key 설정

#     # 파일 업로드 기능
#     st.session_state.uploaded_file = st.file_uploader(
#         "문서를 업로드하세요",
#         type=["txt", "pdf", "docx", "xlsx", "png", "jpg", "jpeg", "pptx"],
#         key=st.session_state.file_uploader_key
#     )
    
#     # 파일 업로드 후 처리
#     if st.session_state.uploaded_file is not None:
#         file_name = st.session_state.uploaded_file.name
#         file_extension = file_name.split(".")[-1].lower()

#         # 유효성 검사 추가
#         if file_extension not in ["txt", "pdf", "docx", "xlsx", "png", "jpg", "jpeg", "pptx"]:
#             st.error(f"지원하지 않는 파일 형식입니다: {file_extension}")
#             logger.log_custom("지원하지 않는 파일 형식 업로드 시도: %s", file_name)
#             st.session_state.uploaded_file = None
#             return
        
#         logger.log_custom("처리 중인 파일: %s, 확장자: %s", file_name, file_extension)
        
#         # 스피너를 사용해 로딩 표시
#         with st.spinner('문서를 처리하고 저장 중입니다...'):
#             try:
#                 start_time = time.time()
#                 result = process_and_store_document(st.session_state.uploaded_file, file_extension)
#                 elapsed_time = time.time() - start_time
#                 logger.log_custom("문서 처리 시간: %.2f초", elapsed_time)
#                 logger.log_custom("문서 처리 내용: %s", result)
#                 # 처리 결과 출력
#                 if isinstance(result, str):  # 오류 메시지인 경우
#                     logger.log_error("문서 처리 실패: %s", result)
#                     st.error(f"문서 처리 중 오류: {result}")

#                 elif result is True:  # 성공
#                     st.success(f"문서 '{file_name}'가 성공적으로 저장 및 학습되었습니다!")

#                 else:  # 처리 실패
#                     logger.log_error("문서 처리가 실패했습니다.")
#                     st.error(f"문서 '{file_name}' 처리에 실패했습니다.")
#                 # 완료 메시지 표시
#                 st.success(f"문서 '{file_name}'가 성공적으로 저장 및 학습되었습니다!")
                
#                 # 특정 사용자에게 알림 전송
#                 message = f"새로운 문서 '{file_name}'가 성공적으로 저장 및 학습되었습니다."
#                 # tele_bot.send_message(chat_id, message)
#                 # 상태 초기화 및 페이지 새로고침
#                 st.session_state.uploaded_file = None
#                 st.session_state.file_uploader_key = f"file_uploader_key_{int(st.session_state.file_uploader_key.split('_')[-1]) + 1}"  # key 변경
#                 st.rerun()  # rerun() 대신 최신 experimental_rerun() 사용

#             except Exception as e:
#                 logger.log_custom(f"문서 처리 중 오류 발생: {str(e)}")
#                 st.error("문서 처리 중 오류가 발생했습니다. 관리자에게 문의하세요.")
        
import streamlit as st
import webbrowser
from database import process_and_store_document
from logger import logger
import time

def show_page():
    logger.log_custom("어드민 페이지")
    st.title("사내 문서 관리 관리자")
    st.write("사내 문서를 업로드하거나 텍스트를 입력해 AI 모델을 학습시킬 수 있습니다.")

    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
        st.session_state.file_uploader_key = "file_uploader_key_1"  # 초기 key 설정
        st.session_state.text_input = ""  # 텍스트 입력 초기화

    # 업로드 방식 선택
    upload_mode = st.radio(
        "업로드 방법을 선택하세요:",
        ("파일 업로드", "텍스트 입력")
    )

    if upload_mode == "파일 업로드":
        # 파일 업로드 기능
        st.session_state.uploaded_file = st.file_uploader(
            "문서를 업로드하세요", 
            type=["txt", "pdf", "docx", "doc", "xlsx", "png", "jpg", "jpeg", "pptx"], 
            key=st.session_state.file_uploader_key
        )

        if st.session_state.uploaded_file is not None:
            file_extension = st.session_state.uploaded_file.name.split(".")[-1].lower()
            logger.log_custom("확장자:%s", file_extension)
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

    elif upload_mode == "텍스트 입력":
        # 텍스트 입력 기능
        st.session_state.text_input = st.text_area("텍스트를 입력하세요:", height=200)

        if st.button("저장 및 학습"):
            if st.session_state.text_input.strip():
                with st.spinner('텍스트를 처리하고 저장 중입니다...'):
                    result = process_and_store_document(st.session_state.text_input, "text")
                st.write(result)  # 처리 결과 출력
                st.success("텍스트가 성공적으로 저장 및 학습되었습니다!")
                st.session_state.text_input = ""  # 텍스트 입력 초기화
                time.sleep(3)  # 3초 대기
                st.rerun()
            else:
                st.warning("텍스트를 입력하세요.")