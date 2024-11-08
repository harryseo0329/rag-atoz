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
    
    
    #-------- 추가 
import telepot
import logging
import tele_mode
import set_dic
import os
from dotenv import load_dotenv
from llm import get_ai_response
import streamlit as st
import re
logger = logging.getLogger(__name__)

load_dotenv()

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
                    w = " ".join("삼성역")    
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
        else :
            print(str_message)
            bot.sendMessage(chat_id, "대화 생성중입니다....")
            ai_response = get_ai_response(str_message) 
            result_str2 = st.write_stream(ai_response)
            # 데이터 이스케이프 처리
            escaped_data = escape_markdown(result_str2)
            bot.sendMessage(chat_id, str(escaped_data), parse_mode='MarkdownV2')

bot = telepot.Bot(os.getenv("TELEGRAM_TOKEN"))
bot.message_loop(handler, run_forever=True)



