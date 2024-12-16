answer_examples = [
#OO의 법인카드 사용금액 한도는 얼마인가요? 
    {
        "input":"팀장의 법인카드 사용금액 한도는 얼마인가요?",
        "answer":"""법인카드관리규정(2020.7.1)에 따르면,
팀장의 법인카드 사용금액 한도는 월 200만원입니다.
또한 직급에 따라 법인카드 사용금액 한도는 아래와 같습니다.\n
| 구분   | 임원  | 실장  | 팀장  | 부장~차장 | 과장~대리 | 사원 |
|------|-----|-----|-----|-------|-------|----|
| 한도금액 | 500 | 300 | 200 | 150   | 100   | 50 |
"""
    },
    {
        "input":"실장의 법인카드 사용금액 한도는 얼마인가요?",
        "answer":"""법인카드관리규정(2020.7.1)에 따르면,
실장의 법인카드 사용금액 한도는 월 300만원입니다.
또한 직급에 따라 법인카드 사용금액 한도는 아래와 같습니다.\n
| 구분   | 임원  | 실장  | 팀장  | 부장~차장 | 과장~대리 | 사원 |
|------|-----|-----|-----|-------|-------|----|
| 한도금액 | 500 | 300 | 200 | 150   | 100   | 50 |
"""
    },
    {
        "input":"사원의 법인카드 사용금액 한도는 얼마인가요?",
        "answer":"""법인카드관리규정(2020.7.1)에 따르면,
사원의 법인카드 사용금액 한도는 월 50만원입니다.
또한 직급에 따라 법인카드 사용금액 한도는 아래와 같습니다.\n
| 구분   | 임원  | 실장  | 팀장  | 부장~차장 | 과장~대리 | 사원 |
|------|-----|-----|-----|-------|-------|----|
| 한도금액 | 500 | 300 | 200 | 150   | 100   | 50 |
"""
    },
#OOO님의 사원정보 알려줘
    {
        "input":"최정동님의 사원정보 알려줘",
        "answer":""" 최정동님의 사원 정보입니다.\n
| 구분 | 내용 |
|------|------|
| 사원번호 | U0001X |
| 이름 | 최정동 |
| 소속  | 주식회사 유라클-대표이사-기술1부문-개발1본부-컨버젼스개발실-SM팀 |
| 부서명  | SM팀 |
| 직위(직급)  | 부장(수석) |
| 직책 | 팀장   |
| 휴대전화 | 010-6306-XXXX   |
| 이메일 | XXd0302@uracle.co.kr |
\n
사원번호, 휴대전화, 이메일 등은 일부 비공개 처리되었습니다.
"""
    },
#이름이 OOO인 사람의 사원정보 알려줘
    {
        "input":"이름이 서해원인 사람의 사원정보 알려줘",
        "answer":""" 서해원님의 사원 정보입니다.\n
| 구분 | 내용 |
|------|------|
| 사원번호 | U0028X |
| 이름 | 서해원 |
| 소속  | 주식회사 유라클-대표이사-기술1부문-개발1본부-컨버젼스개발실-수행팀 |
| 부서명  | 수행팀 |
| 직위(직급)  | 과장(선임) |
| 직책 | 팀원   |
| 휴대전화 | 010-4001-XXXX   |
| 이메일 | XXrryseo0329@uracle.co.kr |
\n
사원번호, 휴대전화, 이메일 등은 일부 비공개 처리되었습니다.
"""
    },
    {
        "input":"강덕득님의 사원정보 알려줘",
        "answer":""" 강덕득님에 대한 사원정보가 없습니다."""
    },
    {
        "input":"이름이 김급수인 사람의 사원정보 알려줘",
        "answer":""" 김급수님에 대한 사원정보가 없습니다."""
    },
    {
        "input":"사장님 성함을 알려줘",
        "answer":""" 사장님 성함은 권태일 입니다."""
    },
#직원의 고희 경조금액에 대해서 알려줘
    {
        "input":"직원의 고희 경조금액에 대해서 알려줘",
        "answer":""" 직원의 고희 경조금액은 20만원입니다.\n
| 대상 | 임원 고희 경조금 | 직원 고희 경조금 | 사우회비 | 경조휴가 | 과일바구니 | 화환 | 제출서류             |
|----|--------|--------|------|------|-------|----|------------------|
| 부모 | 30만원   | 20만원   | 20만원 |      |       |    | 가족관계증명서(주민등록등본)  |
\n
사우회비는 직원이 고희 경조금을 받는 경우, 사우회비 20만원을 포함하여 총 40만원을 받게 됩니다. 경조휴가는 별도로 제공되지 않습니다. 제출서류로는 가족관계증명서(주민등록등본)가 필요합니다.
"""
    },    
#임원 자녀의 결혼 경조금액은 얼마야?
    {
        "input":"임원 자녀의 결혼 경조금액은 얼마야?",
        "answer":""" 임원 자녀의 결혼 경조금액은 100만원입니다.\n
| 대상        | 임원 결혼 경조금  | 사우회비 | 경조휴가 | 과일바구니 | 화환 | 제출서류          |
|-----------|--------|------|------|-------|----|---------------|
| 본인   | 100만원  | 50만원 | 5일   |       | ㅇ  | 청첩장           |
| 자녀        | 100만원  | 50만원 | 1일   |       | ㅇ  | 가족관계증명서, 청첩장  |
| 형제자매      | 30만원   | 20만원 | 1일   |       |    | 가족관계증명서, 청첩장  |
| 배우자의 형제자매 | 30만원   | 20만원 | 1일   |       |    | 가족관계증명서, 청첩장  |
\n
사우회비는 임원이 결혼 경조금을 받는 경우, 사우회비 50만원을 포함하여 총 150만원을 받게 됩니다. 경조휴가는 1일이 제공됩니다. 제출서류로는 가족관계증명서, 청첩장이 필요합니다.
"""
    },  
]