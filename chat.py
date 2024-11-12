import streamlit as st
from dotenv import load_dotenv
from llm import get_ai_response
import base64

from utils import get_image

load_dotenv()

st.set_page_config(page_title="A to Z Uracle", page_icon="🤖")
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
    
 




