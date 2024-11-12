
import requests
import os
from PIL import Image

def get_image(file_path, file_nm):
    pre_path = ""
    os_seperator = ""
    
    if os.name == 'nt':
        pre_path = "C:\\Users\\uracle\\Desktop\\python-workspace\\ai\\rag-atoz\\images\\"
        os_seperator = "\\"
    else:
        pre_path = "/ai/rag-atoz/images/"
        os_seperator = "/"

    image = {}
    try:
        image = Image.open(pre_path + file_path + os_seperator + file_nm)
        # 이미지가 성공적으로 열리면 다음 코드 실행
        #print("이미지가 성공적으로 열렸습니다.")
    except FileNotFoundError:
        image = Image.open(pre_path + "common" + os_seperator + "no_image.jpg")
        #print(f"오류: 해당 경로에 이미지 파일이 존재하지 않습니다.")
    except Exception as e:
        image = Image.open(pre_path + "common" + os_seperator + "no_image.jpg")
        #print(f"오류 발생: {e}")
    
    return image

def stopwords():
    f = open('/ai/rag-atoz/korean_stopwords.txt','r',encoding='utf-8')
    contents = f.read()
    f.close()

    # 응답으로부터 텍스트 데이터를 받아옵니다.
    stopwords_data = contents

    # 텍스트 데이터를 줄 단위로 분리합니다.
    stopwords = stopwords_data.splitlines()

    # 각 줄에서 여분의 공백 문자(개행 문자 등)를 제거합니다.
    return [word.strip() for word in stopwords]

def get_sparse_encoder_path():
    sparse_encoder_path = ""
    
    if os.name == 'nt':
        sparse_encoder_path = "C:\\Users\\uracle\\Desktop\\python-workspace\\ai\\sparse_encoder.pkl"
    else:
        sparse_encoder_path = "/ai/rag-atoz/sparse_encoder.pkl"

    return sparse_encoder_path

