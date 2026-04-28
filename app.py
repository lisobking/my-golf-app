import streamlit as st
import asyncio
import pandas as pd
from scraper import fetch_kakao_golf_data
from datetime import datetime

# 1. 페이지 설정 (제목과 아이콘, 레이아웃)
st.set_page_config(
    page_title="골프 가성비 비서", 
    page_icon="⛳️", 
    layout="centered"  # 모바일은 centered가 훨씬 보기 편합니다.
)

# 모바일 앱 느낌을 주는 CSS 주입
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3rem; font-weight: bold; }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⛳️ 야간 라운드 가성비 봇")
st.caption("카카오골프 실시간 데이터를 기반으로 최저가를 추천합니다.")

# 2. 지역 및 날짜 선택 (모바일에서 터치하기 쉽게 상단 배치)
area_map = {
    "서울/경기": "1",
    "강원": "2",
    "충청": "3",
    "전라": "4",
    "경상": "5",
    "제주": "6"
}

with st.expander("🔍 검색 조건 설정", expanded=True):
    selected_areas = st.multiselect(
        "조회 지역 (복수 선택 가능)",
        options=list(area_map.keys()),
        default=["서울/경기"]
    )
    
    selected_date = st.date_input(
        "라운드 날짜", 
        value=datetime.now(),
        min_value=datetime.now()
    )
    date_str = selected_date.strftime("%Y-%m-%d")

search_btn = st.button("🚀 실시간 최저가 찾기")

# 3. 데이터 표시 로직
if search_btn:
    if not selected_areas:
        st.warning("지역을 선택해 주세요.")
    else:
        codes = [area_map[name] for name in selected_areas]
        area_codes_str = ",".join(codes)
        
        with st.spinner("최신 정보를 수집 중입니다..."):
            try:
                df = asyncio.run(fetch_kakao_golf_data(date=date_str, area_codes=area_codes_str))
                
                if not df.empty:
                    df_sorted = df.sort_values(by='그린피')
                    
                    # 모바일용 요약 지표 (Metric)
                    col1, col2 = st.columns(2)
                    col1.metric("최저가", f"{df_sorted['그린피'].min():,}원")
                    col2.metric("검색결과", f"{len(df_sorted)}건")
                    
                    st.divider()
                    
                    # 모바일 화면에 최적화된 리스트형 데이터프레임
                    # 컬럼 순서를 골프장 -> 가격 -> 잔여팀 순으로 배치
                    display_df = df_sorted[['골프장', '그린피', '잔여팀']]
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "골프장": st.column_config.TextColumn("⛳️ 골프장", width="medium"),
                            "그린피": st.column_config.NumberColumn("💰 그린피", format="%d원"),
                            "잔여팀": st.column_config.TextColumn("⏰ 잔여팀")
                        }
                    )
                    
                    st.success("데이터 업데이트 완료!")
                    st.balloons()
                else:
                    st.info("예약 가능한 티타임이 없습니다. 날짜를 변경해 보세요.")
            except Exception as e:
                st.error("데이터 수집 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

st.markdown("---")
st.caption("© 2026 효섭's AI Golf Assistant")