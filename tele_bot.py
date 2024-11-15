import telepot
import logging
import tele_mode
import set_dic
import os
from dotenv import load_dotenv
from llm import get_ai_response
import streamlit as st
import re
import sys

logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

# PID 파일 경로 설정 (임시 파일 경로로 설정)
PID_FILE = '/tmp/telegram_bot.pid'

# 중복 실행 방지 함수
def is_already_running():
    if os.path.isfile(PID_FILE):
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 프로세스가 아직 실행 중인지 확인
        try:
            os.kill(pid, 0)  # 프로세스가 실행 중이면 예외 발생 안 함
        except OSError:
            # 프로세스가 실행 중이 아니면 PID 파일 삭제
            os.remove(PID_FILE)
        else:
            print("Bot is already running. Exiting...")
            sys.exit(1)

    # 현재 프로세스 ID를 PID 파일에 기록
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

def cleanup():
    # 종료 시 PID 파일 삭제
    if os.path.isfile(PID_FILE):
        os.remove(PID_FILE)

import atexit
atexit.register(cleanup)

# 중복 실행 체크
is_already_running()

# MarkdownV2에서 이스케이프 처리가 필요한 문자
escape_chars = r'\_*[]()~`>#+-=|{}.!'

# 이스케이프 함수 정의
def escape_markdown(text, version=2):
    if version == 2:
        return re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)
    return text

def handler(msg):
    content_type, chat_Type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)

    if content_type == "text":
        str_message = msg["text"]
        if str_message[0:1] == "/":
            args = str_message.split(" ")
            command = args[0]
            del args[0]

            if command == "/dir" or command == "/목록":
                filepath = " ".join(args)
                if filepath.strip() == "":
                    filelist = tele_mode.get_dir_list("./files")
                    bot.sendMessage(chat_id, filelist)
                else:
                    filelist = tele_mode.get_dir_list(filepath)
                    bot.sendMessage(chat_id, filelist)
            elif command == "/weather" or command == "/날씨":
                if args: 
                    w = " ".join(args)
                else:
                    w = "삼성역"    
                    bot.sendMessage(chat_id, "기본 날씨는 삼성역 입니다.")
                weather = tele_mode.get_weather(w)
                bot.sendMessage(chat_id, weather)
            elif command[0:4] == "/get" or command == "/파일":
                filepath = " ".join(args)
                logger.log_custom("filepath:\n%s", filepath)
                if os.path.exists("./files/" + filepath):
                    try:
                        if command == "/getfile":
                            bot.sendDocument(chat_id, open("./files/" + filepath, "rb"))
                        elif command == "/getimage":
                            bot.sendPhoto(chat_id, open("./files/" + filepath, "rb"))
                        elif command == "/getaudio":
                            bot.sendAudio(chat_id, open("./files/" + filepath, "rb"))
                        elif command == "/getvideo":
                            bot.sendVideo(chat_id, open("./files/" + filepath, "rb"))
                    except Exception as e:
                        bot.sendMessage(chat_id, "파일 전송 실패 {}".format(e))
                else:
                    bot.sendMessage(chat_id, "파일이 존재하지 않습니다.")
            elif command == "/dic":
                print(args)
                if isinstance(args[0], str):
                    args = args[0].strip()
                else:
                    args = ""
                print(args)
                # args가 빈 문자열인지 확인하여 처리
                ws = args.split(",") if args != "" else []

                print(args.split(","))
                # ws 리스트의 길이와 요소들을 확인하여 메시지를 전송
                if len(ws) < 2 or ws[0] == "" or ws[1] == "":
                    bot.sendMessage(chat_id, "/dic keyword, keyword2")
                else:
                    output = set_dic.add_entry_to_file(ws[0], ws[1])
                    bot.sendMessage(chat_id, output)       
        else:
            print(str_message)
            bot.sendMessage(chat_id, "대화 생성중입니다....")
            ai_response = get_ai_response(str_message) 
            result_str2 = st.write_stream(ai_response)
            # 데이터 이스케이프 처리
            escaped_data = escape_markdown(result_str2)
            bot.sendMessage(chat_id, str(escaped_data), parse_mode='MarkdownV2')

# 텔레그램 봇 실행
bot = telepot.Bot(os.getenv("TELEGRAM_TOKEN"))
bot.message_loop(handler, run_forever=True)