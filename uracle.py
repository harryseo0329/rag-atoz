import streamlit as st
from dotenv import load_dotenv
from llm import generate_bot_response  # 챗봇 응답 생성 함수
from PIL import Image
from database import process_and_store_document  # 문서 처리 함수
import webbrowser

# 환경 변수 로드
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(page_title="유라클 시스템", page_icon="📄")

# 사이드바에서 페이지 선택
page = st.sidebar.selectbox("페이지를 선택하세요", ["챗봇 페이지", "어드민 페이지"])

# 챗봇 페이지
if page == "챗봇 페이지":
    st.title("🤖 유라클 챗봇")
    st.caption("유라클에 관련된 모든 것을 답해드립니다!")

    # 세션 상태에 메시지 리스트 초기화
    if 'message_list' not in st.session_state:
        st.session_state.message_list = []

    # 이전 대화 내용 표시
    for message in st.session_state.message_list:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # 응답에 이미지가 있을 경우 이미지를 표시
            if "images" in message:
                for img_path in message["images"]:
                    st.image(img_path, use_column_width=True)

    # 사용자 입력을 받음
    if user_question := st.chat_input(placeholder="유라클에 관련된 궁금한 내용을 말씀해주세요!"):
        with st.chat_message("user"):
            st.write(user_question)
        st.session_state.message_list.append({"role": "user", "content": user_question})

        # 답변 생성 중 스피너 표시
        with st.spinner("답변을 생성하는 중입니다..."):
            # 챗봇 응답 생성 함수 호출
            response_text, response_images = generate_bot_response(user_question)

        # 챗봇 응답을 Streamlit에 표시
        with st.chat_message("assistant"):
            st.write(response_text)
            # 이미지가 있는 경우 표시
            if response_images:
                for img_path in response_images:
                    st.image(img_path, use_column_width=True)

        # 챗봇 응답을 세션 상태에 저장
        st.session_state.message_list.append({
            "role": "assistant",
            "content": response_text,
            "images": response_images if response_images else []
        })

# 어드민 페이지
elif page == "어드민 페이지":
    st.title("사내 문서 관리 어드민 페이지")
    st.write("사내 문서를 업로드하고 AI 모델을 학습시킬 수 있습니다.")

    # 파일 업로드 기능
    uploaded_file = st.file_uploader("문서를 업로드하세요", type=["txt", "pdf", "docx", "doc", "xlsx", "png", "jpg", "jpeg", "pptx"])

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()

        # 스피너를 사용해 로딩 표시
        with st.spinner('문서를 처리하고 저장 중입니다...'):
            result = process_and_store_document(uploaded_file, file_extension)

        # 처리 결과 출력
        st.write(result)  # process_and_store_document 함수의 결과가 문자열 또는 텍스트일 경우

        # 완료 메시지 표시
        st.success("문서가 성공적으로 저장 및 학습되었습니다!")
