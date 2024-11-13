import streamlit as st
from dotenv import load_dotenv
from llm import generate_bot_response  # 챗봇 응답 생성 함수
from PIL import Image

# 환경 변수 로드
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(page_title="유라클 챗봇", page_icon="🤖")

# 페이지 제목과 설명
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
