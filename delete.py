import os
from pinecone import Pinecone
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
 
# Pinecone API 초기화
api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=api_key)
index_name = "uracle-index"
index = pc.Index(index_name)

# 특정 sheet_name에 맞는 벡터 삭제 함수
def delete_vectors_by_sheet_name(sheet_name_value):
    # 빈 벡터로 유사도 검색을 수행하면서 필터 조건을 추가하여 검색 (4096차원으로 설정)
    results = index.query(
        vector=[0.0] * 4096,  # 4096차원 빈 벡터
        top_k=1000,  # 가져올 최대 벡터 개수 (필요에 따라 조정 가능)
        filter={"sheet_name": sheet_name_value},
        include_metadata=True
    )

    # 삭제할 벡터의 ID 목록을 추출
    ids_to_delete = [match['id'] for match in results['matches']]
    
    # 삭제 수행
    if ids_to_delete:
        index.delete(ids=ids_to_delete)
        print(f"{len(ids_to_delete)}개의 벡터가 삭제되었습니다.")
    else:
        print("해당 sheet_name을 가진 벡터가 없습니다.")

# 사용 예시
delete_vectors_by_sheet_name("전결권한기준표(20200616)")