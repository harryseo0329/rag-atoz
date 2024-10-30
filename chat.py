import streamlit as st
from dotenv import load_dotenv
from llm import get_ai_response

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

    
    


