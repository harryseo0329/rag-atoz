import streamlit as st
from dotenv import load_dotenv
from llm import get_ai_response, get_direct_ai_response, save_question, ai_recommand_questions
import base64
import importlib

from utils import get_image
from logger import logger

import random
import string

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

import os
import time
from datetime import datetime
import asyncio
import threading
from streamlit.components.v1 import html

load_dotenv()
SENDER_EMAIL_ADDRESS = os.getenv('SENDER_EMAIL_ADDRESS') 
SENDER_EMAIL_PASSWORD = os.getenv('SENDER_EMAIL_PASSWORD') 
RECIEVER_EMAIL_ADDRESS = os.getenv('RECIEVER_EMAIL_ADDRESS') 

# 이메일 보내는 함수
def send_email(sender_email, receiver_email, subject, body, smtp_server, smtp_port, sender_password):
    try:
        # MIME 구조로 이메일 작성
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        
        # SMTP 서버에 연결하여 이메일 전송
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        
        return "메일이 성공적으로 전송되었습니다!"
    
    except Exception as e:
        return f"메일 전송 중 오류가 발생했습니다: {str(e)}"

def generate_random_key(length=16):
        # 영문 대소문자 + 숫자 포함 랜덤 문자열 생성
        characters = string.ascii_letters + string.digits
        random_key = ''.join(random.choice(characters) for _ in range(length))
        return random_key

def getNextNextMonth():
    # 현재 날짜
    current_date = datetime.now()

    # 현재 월과 연도 구하기
    current_year = current_date.year
    current_month = current_date.month

    # 두 달 뒤 계산
    if current_month + 2 > 12:
        next_next_month = (current_year + 1, (current_month + 2) - 12)
    else:
        next_next_month = (current_year, current_month + 2)
    return f"{next_next_month[0]}년 {next_next_month[1]}월"

def save_logs_in_thread(arr):
    """로그 저장을 별도의 스레드에서 실행"""
    asyncio.run(save_question(arr))

st.set_page_config(page_title="A to Z Uracle", page_icon="./images/common/uracle_favicon.png", initial_sidebar_state="collapsed")

# # 메뉴 선택
# menu = st.sidebar.selectbox("메뉴를 선택해 주세요.", ["Home", "Admin"])

# 각 섹션을 조건에 따라 보여주기
if menu == "Home":
    st.markdown(
        """
        <div style="display: flex; align-items: center;">
            <img src="data:image/png;base64,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" alt="logo" style="margin-right: 20px;width:48px;height:48px;">
            <h1>A to Z Uracle</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.caption("Uracle에 대한 모든것!")

    if 'recommad_displayed' not in st.session_state:
        st.session_state.recommad_displayed = False

    if 'selected_question' not in st.session_state:
        st.session_state.selected_question = ""

    #질문 추천을 위한 사전정보
    if 'prior_info_fm' not in st.session_state:
        st.session_state.prior_info_fm = ""
    
    if 'prior_info_dept' not in st.session_state:
        st.session_state.prior_info_dept = ""
    
    if 'prior_info_pos' not in st.session_state:
        st.session_state.prior_info_pos = ""

    #메시지 히스토리
    if 'message_list' not in st.session_state:
        st.session_state.message_list = []

    #추천 사용자 질문
    if 'recommand_question_list' not in st.session_state:
        st.session_state.recommand_question_list = []    

    #질문 메일버튼,폼 hide/show
    if 'ebutton_displayed' not in st.session_state:
        st.session_state.ebutton_displayed = False

    if 'eform_displayed' not in st.session_state:
        st.session_state.eform_displayed = False

    #휴양소 신청 메일버튼,폼 hide/show
    if 'rbutton_displayed' not in st.session_state:
        st.session_state.rbutton_displayed = False

    if 'rform_displayed' not in st.session_state:
        st.session_state.rform_displayed = False    


    if st.session_state.recommad_displayed == True:
        selected_question = st.selectbox("📚 AI기반으로 성별, 부서, 직책 맞는 질문을 추천해드립니다.", st.session_state.recommand_question_list, index=0)
        if selected_question != "질문을 선택해 주세요" and selected_question != st.session_state.selected_question:
            st.session_state.selected_question = selected_question
            message_placeholder = st.empty()
            with message_placeholder.container():
                with st.chat_message("user"):
                    st.write(selected_question)

            with st.spinner("..."):
                st.session_state.message_list.append({"role":"user", "content":selected_question})
                st.session_state.message_list.append({"role": "ai", "content": get_direct_ai_response(selected_question)})
                message_placeholder.empty()
                st.session_state.eform_displayed = False
                st.session_state.rform_displayed = False

    if st.session_state.prior_info_fm == "" or st.session_state.prior_info_dept == "" or st.session_state.prior_info_pos == "":
        with st.form("prior_info_form"):
            prior_info_fm = st.radio("성별", ["남성", "여성"])
            prior_info_dept = st.text_input("부서", value="", placeholder="컨버전스개발실")
            prior_info_pos = st.text_input("직급", value="", placeholder="과장(선임)")

            # 제출 버튼
            submit_button = st.form_submit_button("저장")

            if submit_button:
                # 입력값이 모두 채워졌는지 확인
                all_fields_filled = all([prior_info_fm, prior_info_dept, prior_info_pos]) 

                if not all_fields_filled:
                    st.error("양식을 모두 채워서 작성해주세요.")
                else:
                    st.session_state.prior_info_fm = prior_info_fm
                    st.session_state.prior_info_dept = prior_info_dept
                    st.session_state.prior_info_pos = prior_info_pos
                    st.success("저장되었습니다.")
                    st.session_state.recommand_question_list = ai_recommand_questions(st.session_state.prior_info_fm, st.session_state.prior_info_dept, st.session_state.prior_info_pos)
                    st.session_state.recommad_displayed = True
                    time.sleep(1.5)  # 1.5초 대기
                    st.rerun()


    for message in st.session_state.message_list:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    st.components.v1.html("""
        <script>
            window.scrollTo(0, document.documentElement.scrollHeight);
        </script>
        """, height=0)

    logger.log_custom("st.session_state.eform_displayed:%s",str(st.session_state.eform_displayed))
    if user_question := st.chat_input(placeholder="유라클에 대한 궁금한 내용들을 말씀해주세요!"):
        with st.chat_message("user"):
            st.write(user_question)
        st.session_state.message_list.append({"role":"user", "content":user_question})
        st.session_state.eform_displayed = False
        st.session_state.rform_displayed = False

        with st.spinner("..."):
            all_meta_fields_filled = all([st.session_state.prior_info_fm, st.session_state.prior_info_dept, st.session_state.prior_info_pos]) 

            if all_meta_fields_filled:
                #save_question([user_question, st.session_state.prior_info_fm, st.session_state.prior_info_dept, st.session_state.prior_info_pos])
                threading.Thread(target=save_logs_in_thread, args=([user_question, st.session_state.get("prior_info_fm"), st.session_state.get("prior_info_dept"), st.session_state.get("prior_info_pos")],)).start()
            
            ai_response = get_ai_response(user_question) 
            with st.chat_message("ai"):
                ai_message = st.write_stream(ai_response)
            st.session_state.message_list.append({"role":"ai", "content":ai_message})
            st.session_state.ebutton_displayed = True
            if "휴양소" in user_question :
                st.session_state.rbutton_displayed = True
            else :
                st.session_state.rbutton_displayed = False

    # "이메일 보내기" 버튼 클릭
    if st.session_state.ebutton_displayed or st.session_state.rbutton_displayed :
        col1, col2 = st.columns([1, 6])  # 왼쪽 열(col1)과 오른쪽 열(col2)을 배치
        with col2:
            st.markdown("""
                <style>
                    .stColumn {
                        text-align: right;
                    }   
                    .stColumn div {
                        display: inline;
                    }
                    .stButton {
                        margin-left: 8px;
                    }
                </style>
            """, unsafe_allow_html=True)
            if st.session_state.rbutton_displayed and st.button("✉️ 휴양소 신청 메일 보내기"):
                st.session_state.rform_displayed = True
                st.rerun()
            if st.session_state.ebutton_displayed and st.button("❔ 답변요청 메일 보내기"):
                st.session_state.eform_displayed = True
                st.rerun()
            
    #이메일 발송 디스플레이
    if st.session_state.eform_displayed:
        # 이메일 발송 폼
        with st.form("email_form"):
            receiver_email = st.text_input("수신자 이메일 주소", value=RECIEVER_EMAIL_ADDRESS, disabled=True)
            subject = st.text_input("이메일 제목", value="AtoZ 챗봇의 답변 내용이 부족하여 더 상세한 답변 요청드립니다.")
            last_user_message = st.session_state.message_list[-2]["content"] if len(st.session_state.message_list) > 1 else "질문이 없습니다."
            last_ai_response = st.session_state.message_list[-1]["content"] if len(st.session_state.message_list) > 0 else "답변이 없습니다."
            body = st.text_area("이메일 내용", value=f"""
 안녕하세요 AtoZ 챗봇에게 아래의 질문을 했었는데

챗봇의 답변 내용이 부족하여 추가적인 답변 및 설명을 요청드리려 합니다.

내용 확인 후 회신부탁드립니다.

감사합니다.     
                                               
----------------------------------------------------------------------

질문 : {last_user_message}

답변 : {last_ai_response}
            """)
             
            # 제출 버튼
            submit_button = st.form_submit_button("메일 전송")

            if submit_button:
                # 이메일 발송 함수 호출
                result = send_email(SENDER_EMAIL_ADDRESS, receiver_email, subject, body, "smtp.gmail.com", 465, SENDER_EMAIL_PASSWORD)
                st.success(result)
                time.sleep(1.5)  # 1.5초 대기
                st.session_state.ebutton_displayed = False
                st.session_state.eform_displayed = False
                st.rerun()
        
    #휴양소 이메일 발송 디스플레이
    if st.session_state.rform_displayed:
        # 이메일 발송 폼
        with st.form("resort_email_form"):
            month = getNextNextMonth()
            receiver_email = st.text_input("수신자 이메일 주소", value=RECIEVER_EMAIL_ADDRESS, disabled=True)
            subject = st.text_input("이메일 제목", value=f"속초 및 제주 휴양소 {month} 예약신청합니다.")
            pos = st.radio("휴양소", ["제주", "속초"])
            dept = st.text_input("부서", value="", placeholder="컨버전스개발실")
            name = st.text_input("신청자명", value="", placeholder="홍길동")
            p_date = st.text_input("희망날짜", value="", placeholder="10/3~10/5")
            period = st.text_input("기간", value="", placeholder="2박3일")
            cnt = st.text_input("인원", value="", placeholder="2명")
            body = f"""
 안녕하세요. {dept} {name}입니다. 
{month} {pos} 휴양소 예약 신청합니다.
희망날짜는 {p_date}({period})이며, 인원은 {cnt} 입니다.
감사합니다.

*신청정보
 - 휴양소지역 : {pos}
 - 부서 : {dept}
 - 신청자 : {name}
 - 희망날짜 : {p_date}({period})
 - 인원 : {cnt}
"""     
            

            # 제출 버튼
            submit_button = st.form_submit_button("메일 전송")

            if submit_button:
                # 입력값이 모두 채워졌는지 확인
                all_fields_filled = all([subject, dept, name, p_date, period, cnt]) 

                if not all_fields_filled:
                    st.error("양식을 모두 채워서 작성해주세요.")
                else:
                    # 이메일 발송 함수 호출
                    result = send_email(SENDER_EMAIL_ADDRESS, receiver_email, subject, body, "smtp.gmail.com", 465, SENDER_EMAIL_PASSWORD)
                    st.success(result)
                    time.sleep(1.5)  # 1.5초 대기
                    st.session_state.rbutton_displayed = False
                    st.session_state.rform_displayed = False
                    st.rerun()

        #image 불러오기 예시
        #st.image(get_image("seo","townhall_ai_20241030103001222.jpg"), caption="참고이미지", use_column_width=True)    
        #st.image("https://uracle.notion.site/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F7e05b6b0-caa6-40af-bb5c-bf5e0c6fb756%2FUntitled.png?table=block&id=94d25cf8-79f7-4a90-a71e-aabfcc3172df&spaceId=d549a58f-3f07-47fc-94e9-076887e1bf1f&width=1420&userId=&cache=v2")
        #st.image(base64.b64decode("data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==".split(",")[1]), caption='참고이미지', use_column_width=True)
elif menu == "Admin":       

#             # AI 메시지 출력
#             with st.chat_message("ai"):
#                 if isinstance(ai_response, str):  # 응답이 문자열일 경우
#                     st.write(ai_response)
#                 else:
#                     for chunk in ai_response:  # 만약 응답이 스트리밍이라면 한 번에 출력
#                         st.write(chunk)
#             st.session_state.message_list.append({"role": "ai", "content": ai_response})
    
#         #image 불러오기 예시
#         #st.image(get_image("seo","townhall_ai_20241030103001222.jpg"), caption="참고이미지", use_column_width=True)    
#         #st.image("https://uracle.notion.site/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F7e05b6b0-caa6-40af-bb5c-bf5e0c6fb756%2FUntitled.png?table=block&id=94d25cf8-79f7-4a90-a71e-aabfcc3172df&spaceId=d549a58f-3f07-47fc-94e9-076887e1bf1f&width=1420&userId=&cache=v2")
#         #st.image(base64.b64decode("data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==".split(",")[1]), caption='참고이미지', use_column_width=True)
# elif menu == "Admin":       

#     password_placeholder = st.empty() 
#     result_placeholder = st.empty() 
  
#     # 비밀번호 입력 받기
#     password = password_placeholder.text_input("비밀번호를 입력하세요", type="password")
 
#     if password:
#         if password == "0302":
#             result_placeholder.success("비밀번호가 맞습니다. 관리 페이지로 이동합니다.")
#             password_placeholder.empty()
#             result_placeholder.empty()
#             admin_page = importlib.import_module("admin")
#             admin_page.show_page()  # page1.py에서 show_page() 함수를 실행
#         else:
#             result_placeholder.error("비밀번호가 틀렸습니다. 다시 시도하세요.")

    


