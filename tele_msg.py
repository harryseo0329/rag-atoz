import telepot
import tele_bot
from llm import get_ai_response
import set_dic
import tele_mode  # 필요한 모듈 임포트
import streamlit as st
import re
import sys
import os
# MarkdownV2에서 이스케이프 처리가 필요한 문자
escape_chars = r'\_*[]()~`>#+-=|{}.!'

# 이스케이프 함수 정의
def escape_markdown(text, version=2):
    if version == 2:
        return re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)
    return text


# 핸들러 함수 정의
def message_handler(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)


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
                    tele_bot.sendMessage(chat_id, filelist)
                else:
                    filelist = tele_mode.get_dir_list(filepath)
                    tele_bot.sendMessage(chat_id, filelist)
            elif command == "/weather" or command == "/날씨":
                if args: 
                    w = " ".join(args)
                else:
                    w = "삼성역"    
                    tele_bot.sendMessage(chat_id, "기본 날씨는 삼성역 입니다.")
                weather = tele_mode.get_weather(w)
                tele_bot.sendMessage(chat_id, weather)
            elif command[0:4] == "/get" or command == "/파일":
                filepath = " ".join(args)
                if os.path.exists("./files/" + filepath):
                    try:
                        if command == "/getfile":
                            tele_bot.sendDocument(chat_id, open("./files/" + filepath, "rb"))
                        elif command == "/getimage":
                            tele_bot.sendPhoto(chat_id, open("./files/" + filepath, "rb"))
                        elif command == "/getaudio":
                            tele_bot.sendAudio(chat_id, open("./files/" + filepath, "rb"))
                        elif command == "/getvideo":
                            tele_bot.sendVideo(chat_id, open("./files/" + filepath, "rb"))
                    except Exception as e:
                        tele_bot.sendMessage(chat_id, "파일 전송 실패 {}".format(e))
                else:
                    tele_bot.sendMessage(chat_id, "파일이 존재하지 않습니다.")
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
                    tele_bot.sendMessage(chat_id, "/dic keyword, keyword2")
                else:
                    output = set_dic.add_entry_to_file(ws[0], ws[1])
                    tele_bot.sendMessage(chat_id, output)       
        else:
            print(str_message)
            if str_message.strip().find("날씨") > 0 :
                w = "삼성역" 
                tele_mode.get_weather(w)
            else:    
                tele_bot.sendMessage(chat_id, "대화 생성중입니다....")
                ai_response = get_ai_response(str_message) 
                result_str2 = st.write_stream(ai_response)
                # 데이터 이스케이프 처리
                escaped_data = escape_markdown(result_str2)
                tele_bot.sendMessage(chat_id, str(escaped_data), parse_mode='MarkdownV2')        

# 핸들러 실행
tele_bot.handle_message(message_handler)
