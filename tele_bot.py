import telepot
import logging
import os
from dotenv import load_dotenv
from llm import get_ai_response
import streamlit as st

logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

# 텔레그램 봇 초기화
bot = telepot.Bot(os.getenv("TELEGRAM_TOKEN"))

# 메시지 전송 함수
def send_message(chat_id, message):
    """다른 모듈에서 메시지 전송"""
    bot.sendMessage(chat_id, message)

# 메시지 핸들러 정의
def handle_message(handler_function):
    """핸들러 함수를 설정"""
    bot.message_loop(handler_function, run_forever=True)