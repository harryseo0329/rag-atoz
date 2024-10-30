
import os
from PIL import Image

def get_image(file_path, file_nm):
    pre_path = ""
    os_seperator = ""

    if os.name == 'nt':
        pre_path = "C:\\Users\\uracle\\Desktop\\python-workspace\\ai\\rag_atoz\\images\\"
        os_seperator = "\\"
    else:
        pre_path = "/ai/rag_atoz/images/"
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