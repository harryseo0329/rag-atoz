import streamlit as st
from dotenv import load_dotenv
from llm import get_ai_response, get_direct_ai_response, save_question, ai_recommand_questions, init_session_history
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

import uuid

load_dotenv()
SENDER_EMAIL_ADDRESS = os.getenv('SENDER_EMAIL_ADDRESS') 
SENDER_EMAIL_PASSWORD = os.getenv('SENDER_EMAIL_PASSWORD') 
RECIEVER_EMAIL_ADDRESS = os.getenv('RECIEVER_EMAIL_ADDRESS') 

def get_session_id():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())  # 고유 ID 생성
    return st.session_state.session_id

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

def scroll_to_bottom():
        st.components.v1.html(f"""
            <script>
                console.log("go to bottom");
                var ifr = window.parent.document.querySelectorAll('[data-testid="stIFrame"]');
                for(var i=0; i<ifr.length; i++){{
                    ifr[i].parentElement.style.display = "none";
                }}
                setTimeout(function(){{
                    window.parent.document.querySelectorAll('[data-testid="stAppScrollToBottomContainer"]')[0].scrollTo(0, window.parent.document.querySelectorAll('[data-testid="stAppScrollToBottomContainer"]')[0].scrollHeight)
                }}, 300);
            </script>
        """, 0, 0, False)

st.set_page_config(page_title="A to Z Uracle", page_icon="./images/common/uracle_favicon.png", initial_sidebar_state="collapsed")

# 메뉴 선택
menu = st.sidebar.selectbox("메뉴를 선택해 주세요.", ["Home", "Admin"])

# 각 섹션을 조건에 따라 보여주기
if menu == "Home":
    st.markdown(
        """
        <div style="display: flex; align-items: center;">
            <!--img src="data:image/png;base64,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" alt="logo" style="margin-right: 20px;width:48px;height:48px;"-->
            <!--h1>A to Z Uracle</h1-->
            <img src="data:image/jpeg;base64,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" alt="logo" style="width:180px;height:70px;">
            
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.caption("Uracle에 대한 모든것!")

    get_session_id()

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
            st.session_state.message_list.append({"role":"user", "content":selected_question})
            st.session_state.message_list.append({"role": "ai", "content": "", "response_yn" : "n", "select_question": selected_question})
            st.session_state.eform_displayed = False
            st.session_state.rform_displayed = False

    if st.session_state.prior_info_fm == "" or st.session_state.prior_info_dept == "" or st.session_state.prior_info_pos == "":
        with st.form("prior_info_form"):
            prior_info_fm = st.radio("성별", ["남성", "여성"])
            prior_info_dept = st.text_input("부서", value="", placeholder="컨버전스개발실")
            prior_info_pos = st.radio("직급", ["사원(연구원)", "대리(주임)", "과장(선임)", "차장(책임)", "부장(수석)", "임원"])#st.text_input("직급", value="", placeholder="과장(선임)")

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
        if message["role"] == "ai" and message["response_yn"] == "n":
            with st.spinner("..."):
                scroll_to_bottom()
                message["content"] = get_direct_ai_response(message["select_question"], get_session_id())
                message["response_yn"] = "y"
                with st.chat_message("ai"):
                    st.write(message["content"])
                    scroll_to_bottom()
        else:
            with st.chat_message(message["role"]):
                st.write(message["content"])

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
            
            ai_response = get_ai_response(user_question, get_session_id()) 
            with st.chat_message("ai"):
                ai_message = st.write_stream(ai_response)
            st.session_state.message_list.append({"role":"ai", "content":ai_message, "response_yn":"y"})
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

    


