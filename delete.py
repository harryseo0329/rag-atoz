import os
from pinecone import Pinecone
from dotenv import load_dotenv
import streamlit as st

# 환경 변수 로드
load_dotenv()

# Pinecone API 초기화
api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=api_key)
index_name = os.getenv('INDEX_NAME')
index = pc.Index(index_name)

# 특정 source에 맞는 벡터 삭제 함수
def delete_vectors_by_source(source_value):
    # 빈 벡터로 유사도 검색을 수행하면서 필터 조건을 추가하여 검색 (4096차원으로 설정)
    results = index.query(
        vector=[0.0] * 4096,  # 4096차원 빈 벡터
        top_k=1000,  # 가져올 최대 벡터 개수 (필요에 따라 조정 가능)
        filter={"source": source_value},
        include_metadata=True
    )

    # 삭제할 벡터의 ID 목록을 추출
    ids_to_delete = [match['id'] for match in results['matches']]
    
    # 삭제 수행
    if ids_to_delete:
        index.delete(ids=ids_to_delete)
        return f"{len(ids_to_delete)}개의 벡터가 삭제되었습니다."
    else:
        return "해당 source을 가진 벡터가 없습니다."

# Streamlit 애플리케이션
st.title("Pinecone Vector Deletion Tool")
st.write("삭제할 벡터의 `source` 값을 입력하세요.")

# 사용자 입력
source_input = st.text_input("삭제할 `source` 값:", "")

# 삭제 버튼
if st.button("벡터 삭제 실행"):
    if source_input.strip():  # 입력 값이 비어있지 않으면 실행
        with st.spinner("벡터를 삭제하는 중..."):
            result = delete_vectors_by_source(source_input.strip())
        st.success("작업 완료!")
        st.write(result)
    else:
        st.warning("삭제할 `source` 값을 입력해주세요.")
