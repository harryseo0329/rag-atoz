import os
import shutil
import re
from datetime import datetime

def is_valid_part(part):
    """
    각 입력 부분이 알파벳, 숫자, 한글, 공백 및 () 괄호만 포함하는지 확인하는 함수.
    """
    pattern = r"^[a-zA-Z가-힣0-9()\s]+$"
    return bool(re.match(pattern, part))

def create_backup_directory(backup_dir='backups'):
    """
    백업 파일을 저장할 디렉토리를 생성하는 함수. 이미 존재하면 생략.
    """
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"'{backup_dir}' 디렉토리가 생성되었습니다.")

def backup_file(file_path, backup_dir='backups'):
    """
    파일을 백업하는 함수. 백업 파일은 별도의 디렉토리에 저장되며,
    파일 이름에 타임스탬프를 붙여 덮어쓰기 방지.
    """
    create_backup_directory(backup_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{os.path.basename(file_path)}_{timestamp}.bak"
    backup_path = os.path.join(backup_dir, backup_filename)
    shutil.copy(file_path, backup_path)
    print(f"'{file_path}' 파일이 '{backup_path}'로 백업되었습니다.")

def check_keyword_exists(keyword, dictionary):
    """
    dictionary 내에서 동일한 키워드가 존재하는지 확인하는 함수.
    """
    for entry in dictionary:
        existing_keyword, existing_value = entry.split(" -> ")
        if existing_keyword.strip() == keyword or existing_value.strip() == keyword:
            return True
    return False

def add_entry_to_file(keyword, value, file_path='dic.py', backup_dir='backups'):
    # 각 입력의 유효성 검사
    if not is_valid_part(keyword) or not is_valid_part(value):
        print("잘못된 형식의 입력입니다. 알파벳, 숫자, 괄호 () 및 공백만 허용됩니다.")
        return

    new_entry = f"{keyword} -> {value}"

    # 파일에서 현재 dictionary 가져오기
    from dic import dictionary

    # 키워드와 값의 중복 여부 확인
    keyword_exists = check_keyword_exists(keyword, dictionary)
    value_exists = check_keyword_exists(value, dictionary)

    if keyword_exists or value_exists:
        return(f"키워드 '{keyword}' 또는 값 '{value}'가 이미 존재합니다.")

    # 파일 백업
    if os.path.exists(file_path):
        backup_file(file_path, backup_dir)
    else:
        print(f"'{file_path}' 파일이 존재하지 않습니다.")

    # 파일에 새로운 항목 추가
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        for line in lines:
            file.write(line)
            if line.strip() == 'dictionary = [':
                file.write(f'    "{new_entry}",\n')

    return(f"'{new_entry}'가 파일에 추가되었습니다.")

# 사용자의 키워드와 값을 각각 입력 받기
if __name__ == "__main__":
    keyword = input("키워드를 입력하세요: ")
    value = input("값을 입력하세요: ")
    add_entry_to_file(keyword, value)

    # 새로 파일을 읽어서 dictionary를 출력
    from dic import dictionary

    for item in dictionary:
        print(item)
