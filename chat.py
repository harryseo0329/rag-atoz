import streamlit as st
from dotenv import load_dotenv
from llm import get_ai_response
import base64
import importlib

from utils import get_image
from logger import logger

load_dotenv()

st.set_page_config(page_title="A to Z Uracle", page_icon="./files/uracle_favicon.png", initial_sidebar_state="collapsed")

# 메뉴 선택
menu = st.sidebar.selectbox("메뉴를 선택해 주세요.", ["Home", "Admin"])

# 각 섹션을 조건에 따라 보여주기
if menu == "Home":

    st.title("🤖 A to Z Uracle")
    st.caption("Uracle에 대한 모든것!")

    if 'message_list' not in st.session_state:
        st.session_state.message_list = []

    for message in st.session_state.message_list:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if user_question := st.chat_input(placeholder="유라클에 대한 궁금한 내용들을 말씀해주세요!"):
        with st.chat_message("user"):
            st.write(user_question)
        st.session_state.message_list.append({"role":"user", "content":user_question})

        with st.spinner("..."):
            ai_response = get_ai_response(user_question) 
            with st.chat_message("ai"):
                ai_message = st.write_stream(ai_response)
            st.session_state.message_list.append({"role":"ai", "content":ai_message})
        
        #image 불러오기 예시
        #st.image(get_image("seo","townhall_ai_20241030103001222.jpg"), caption="참고이미지", use_column_width=True)    
        #st.image("https://uracle.notion.site/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F7e05b6b0-caa6-40af-bb5c-bf5e0c6fb756%2FUntitled.png?table=block&id=94d25cf8-79f7-4a90-a71e-aabfcc3172df&spaceId=d549a58f-3f07-47fc-94e9-076887e1bf1f&width=1420&userId=&cache=v2")
        #st.image(base64.b64decode("data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==".split(",")[1]), caption='참고이미지', use_column_width=True)
elif menu == "Admin":       

    password_placeholder = st.empty() 
    result_placeholder = st.empty() 
 
    # 비밀번호 입력 받기
    password = password_placeholder.text_input("비밀번호를 입력하세요", type="password")
 
    if password:
        if password == "0302":
            result_placeholder.success("비밀번호가 맞습니다. 관리 페이지로 이동합니다.")
            password_placeholder.empty()
            result_placeholder.empty()
            admin_page = importlib.import_module("admin")
            admin_page.show_page()  # page1.py에서 show_page() 함수를 실행
        else:
            result_placeholder.error("비밀번호가 틀렸습니다. 다시 시도하세요.")

    


