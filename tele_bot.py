import telepot
import logging
import tele_mode
import set_dic
import os
from dotenv import load_dotenv
from llm import get_ai_response
import streamlit as st
import re
import threading
import time
from datetime import datetime
import uuid
logger = logging.getLogger(__name__)

load_dotenv()

# MarkdownV2에서 이스케이프 처리가 필요한 문자
escape_chars = r'\_*[]()~`>#+-=|{}.!'

# 이스케이프 함수 정의
def escape_markdown(text, version=2):
    if version == 2:
        # 필요한 문자들을 모두 이스케이프 처리
        pattern = r'([{}])'.format(re.escape(escape_chars))
        return re.sub(pattern, r'\\\1', text)
    return text

def get_session_id():
    return str(uuid.uuid4())  # 고유 ID 생성

alarms = {}

def send_alarm_message(chat_id, message):
    """알람 메시지 전송"""
    bot.sendMessage(chat_id, f"🔔 알람: {message}")

def alarm_scheduler():
    """알람 스케줄러 - 매 분마다 알람 체크"""
    while True:
        now = datetime.now().strftime("%H:%M")  # 현재 시간 (HH:MM)
        for chat_id, alarm_list in alarms.items():
            for alarm_time in alarm_list:
                if alarm_time == now:  # 알람 시간 도달
                    send_alarm_message(chat_id, f"지정된 시간 {alarm_time}입니다!")
                    alarms[chat_id].remove(alarm_time)  # 알람을 제거
        time.sleep(30)  # 1분 간격으로 실행

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
                w = " ".join("삼성역")   
                if args: 
                    w = " ".join(args)
                else:
                    bot.sendMessage(chat_id, "기본 날씨는 삼성역 입니다.")
                weather = tele_mode.get_weather(w)
                bot.sendMessage(chat_id, weather)
            elif command[0:4] == "/get" or command == "/파일":
                filepath = " ".join(args)
                logger.log_custom("filepath:\n%s", filepath)
                if os.path.exists("./files/" +filepath):
                    try:
                        if command == "/getfile":
                            bot.sendDocument(chat_id, open("./files/" + filepath, "rb"))
                        elif command == "/getimage":
                            bot.sendPhoto(chat_id, open("./files/" +filepath, "rb"))
                        elif command == "/getaudio":
                            bot.sendAudio(chat_id, open("./files/" +filepath, "rb"))
                        elif command == "/getvideo":
                            bot.sendVideo(chat_id, open("./files/" +filepath, "rb"))
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
            elif command == "/setalarm" or command == "/알람":  # 알람 설정 명령어
                try:
                    _, time_str = str_message.split()  # /setalarm HH:MM
                    datetime.strptime(time_str, "%H:%M")  # HH:MM 형식 확인
                    if chat_id not in alarms:
                        alarms[chat_id] = []
                    alarms[chat_id].append(time_str)
                    bot.sendMessage(chat_id, f"✅ 알람이 {time_str}으로 설정되었습니다.")
                except ValueError:
                    bot.sendMessage(chat_id, "❌ 시간 형식이 잘못되었습니다. /알람 HH:MM 형식으로 입력해주세요.")
            
            elif command == "/listalarm" or command == "/알람목록":  # 알람 목록 확인 명령어
                if chat_id in alarms and alarms[chat_id]:
                    alarm_list = "\n".join(alarms[chat_id])
                    bot.sendMessage(chat_id, f"🔔 설정된 알람 목록:\n{alarm_list}")
                else:
                    bot.sendMessage(chat_id, "🔕 설정된 알람이 없습니다.")
            
            elif command == "/removealarm" or command == "/알람제거":  # 알람 제거 명령어
                try:
                    _, time_str = str_message.split()  # /removealarm HH:MM
                    if chat_id in alarms and time_str in alarms[chat_id]:
                        alarms[chat_id].remove(time_str)
                        bot.sendMessage(chat_id, f"🗑️ 알람 {time_str}이 삭제되었습니다.")
                    else:
                        bot.sendMessage(chat_id, f"❌ {time_str} 알람이 존재하지 않습니다.")
                except ValueError:
                    bot.sendMessage(chat_id, "❌ 시간 형식이 잘못되었습니다. /알람제거 HH:MM 형식으로 입력해주세요.")
        else :
            print(str_message)
            args = str_message.split("날씨")
            bot.sendMessage(chat_id, "대화 생성중입니다....")
            if str_message.strip().find("날씨") >= 0 :
                if args: 
                    w = " ".join(args[0])
                else:
                    w = " ".join("삼성역")    
                    bot.sendMessage(chat_id, "기본 날씨는 삼성역 입니다.")
                weather = tele_mode.get_weather(w)
                bot.sendMessage(chat_id, weather)
            elif str_message.strip().find("파일") >= 0 :
                bot.sendMessage(chat_id, "저장된 파일 정보를 알고 싶으면 '/목록' 이라고 입력 해주세요. \r\n 파일을 다운 받고 싶으면 '/getfile 파일명'라고 입력해주세요.")    
            elif str_message.strip().find("알람") >= 0 :
                bot.sendMessage(chat_id, "알람을 맞추고 싶으면 '/알람 HH:MM'라고 입력 해주세요. \r\n 설정된 알람 목록을 알고 싶으면 '/알람목록' 이라고 입력해주세요. \r\n 알람을 제거하고 싶으면 '/알람제거 HH:MM'라고 입력해주세요.")    
            else:    
                ai_response = get_ai_response(str_message, get_session_id()) 
                result_str2 = st.write_stream(ai_response)
                # 데이터 이스케이프 처리
                escaped_data = escape_markdown(result_str2)
                bot.sendMessage(chat_id, str(escaped_data), parse_mode='MarkdownV2')

bot = telepot.Bot(os.getenv("TELEGRAM_TOKEN"))
bot.message_loop(handler, run_forever=True)

try:
    scheduler_thread = threading.Thread(target=alarm_scheduler, daemon=True)
    scheduler_thread.start()

    print("텔레그램 봇이 실행 중입니다. Ctrl+C로 종료하세요.")
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("\n❗ 프로그램이 종료되었습니다.")
