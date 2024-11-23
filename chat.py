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

import time
from datetime import datetime
import asyncio
import threading

load_dotenv()

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

st.set_page_config(page_title="A to Z Uracle", page_icon="./files/uracle_favicon.png", initial_sidebar_state="collapsed")

# 메뉴 선택
menu = st.sidebar.selectbox("메뉴를 선택해 주세요.", ["Home", "Admin"])

# 각 섹션을 조건에 따라 보여주기
if menu == "Home":
    st.title("🤖 A to Z Uracle")
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
            st.session_state.message_list.append({"role":"user", "content":selected_question})
            st.session_state.message_list.append({"role": "ai", "content": get_direct_ai_response(selected_question)})
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
                    time.sleep(3)  # 3초 대기
                    st.rerun()


    for message in st.session_state.message_list:
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
                save_question([user_question, st.session_state.prior_info_fm, st.session_state.prior_info_dept, st.session_state.prior_info_pos])
            
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
            receiver_email = st.text_input("수신자 이메일 주소", value="harryseo0329@uracle.co.kr", disabled=True)
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
                # SMTP 서버 설정 (예: Gmail)
                smtp_server = "smtp.gmail.com"
                smtp_port = 465  # SSL 포트
                # 이메일 발송 함수 호출
                result = send_email("harry0329.developer@gmail.com", receiver_email, subject, body, smtp_server, smtp_port, "deegbyaaffqfsrjz")
                st.success(result)
                time.sleep(3)  # 3초 대기
                st.session_state.ebutton_displayed = False
                st.session_state.eform_displayed = False
                st.rerun()
        
    #휴양소 이메일 발송 디스플레이
    if st.session_state.rform_displayed:
        # 이메일 발송 폼
        with st.form("resort_email_form"):
            month = getNextNextMonth()
            receiver_email = st.text_input("수신자 이메일 주소", value="harryseo0329@uracle.co.kr", disabled=True)
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
                    # SMTP 서버 설정 (예: Gmail)
                    smtp_server = "smtp.gmail.com"
                    smtp_port = 465  # SSL 포트
                    # 이메일 발송 함수 호출
                    result = send_email("harry0329.developer@gmail.com", receiver_email, subject, body, smtp_server, smtp_port, "deegbyaaffqfsrjz")
                    st.success(result)
                    time.sleep(3)  # 3초 대기
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

    


