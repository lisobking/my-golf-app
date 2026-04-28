import streamlit as st
import asyncio
import pandas as pd
from scraper import fetch_kakao_golf_data

# 웹 페이지 설정
st.set_page_config(page_title="야간 골프 최저가 검색기", layout="wide")

# 제목 및 설명
st.title("⛳️ 효섭님의 실시간 야간 라운드 검색기")
st.markdown("---")

# 지역 매칭 정보 (효섭님이 알려주신 정보 반영!)
area_map = {
    "서울/경기": "1",
    "강원": "2",
    "충청": "3",
    "전라": "4",
    "경상": "5",
    "제주": "6"
}

# 1. 사용자 입력 섹션
with st.sidebar:
    st.header("🔍 검색 조건 설정")
    
    # 여러 지역 선택 가능 (Multi-select)
    selected_areas = st.multiselect(
        "지역을 선택하세요",
        options=list(area_map.keys()),
        default=["서울/경기"]
    )
    
    # 날짜 선택
    selected_date = st.date_input("날짜를 선택하세요", value=pd.to_datetime("today"))
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # 검색 버튼
    search_button = st.button("🚀 최저가 검색 시작")

# 2. 결과 출력 섹션
if search_button:
    if not selected_areas:
        st.warning("조회할 지역을 하나 이상 선택해 주세요.")
    else:
        # 선택된 이름들을 코드로 변환 (예: "1,2,3")
        codes = [area_map[name] for name in selected_areas]
        area_codes_str = ",".join(codes)
        
        with st.spinner(f"{', '.join(selected_areas)} 지역의 데이터를 불러오는 중..."):
            try:
                # scraper.py 실행
                df = asyncio.run(fetch_kakao_golf_data(date=date_str, area_codes=area_codes_str))
                
                if not df.empty:
                    # 그린피 낮은 순 정렬
                    df_sorted = df.sort_values(by='그린피')
                    
                    # 상단 요약 지표
                    st.success(f"총 {len(df_sorted)}개의 티타임을 찾았습니다!")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("최저가", f"{df_sorted['그린피'].min():,}원")
                    m2.metric("평균가", f"{int(df_sorted['그린피'].mean()):,}원")
                    m3.metric("검색 건수", f"{len(df_sorted)}건")
                    
                    # 데이터 표 출력 (디자인 가미)
                    st.dataframe(
                        df_sorted, 
                        use_container_width=True,
                        column_config={
                            "그린피": st.column_config.NumberColumn("그린피 (원)", format="%d"),
                            "시간": "티타임 ⏰",
                            "골프장": "골프장 이름 ⛳️"
                        }
                    )
                    
                    st.balloons() # 성공 축하!
                else:
                    st.info("조회된 티타임이 없습니다. 날짜를 변경해 보세요.")
            
            except Exception as e:
                st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")