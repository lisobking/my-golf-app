import streamlit as st
import asyncio
import pandas as pd
from scraper import fetch_kakao_golf_data
from datetime import datetime

# 1. 페이지 및 테마 설정
st.set_page_config(
    page_title="골프 가성비 비서", 
    page_icon="⛳️", 
    layout="centered"
)

# [핵심] 모바일 앱 감성을 위한 커스텀 CSS
st.markdown("""
    <style>
    /* 기본 배경 및 폰트 설정 */
    .main { background-color: #f8f9fa; }
    
    /* 카드 디자인 */
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 15px !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px !important;
    }
    
    /* 카드 제목(골프장명) 스타일 */
    .st-emotion-cache-p5msec { 
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        color: #2c3e50;
    }

    /* 하단 버튼 스타일 */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5rem;
        background: linear-gradient(135deg, #1dcc70 0%, #13a35a 100%);
        color: white;
        font-size: 1.1rem;
        border: none;
        transition: all 0.3s;
    }
    
    /* 상단 지표(Metric) 카드 */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #edf2f7;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 섹션
st.title("⛳️ 골프 가성비 비서")
st.markdown("<p style='color: gray; margin-top: -15px;'>효섭님의 스마트한 라운드 파트너</p>", unsafe_allow_html=True)

# 2. 검색 조건 설정
area_map = {
    "서울/경기": "1", "강원": "2", "충청": "3", 
    "전라": "4", "경상": "5", "제주": "6"
}

with st.container():
    selected_areas = st.multiselect(
        "📍 조회 지역",
        options=list(area_map.keys()),
        default=["서울/경기"]
    )
    
    selected_date = st.date_input(
        "📅 라운드 날짜", 
        value=datetime.now(),
        min_value=datetime.now()
    )
    date_str = selected_date.strftime("%Y-%m-%d")

search_btn = st.button("🚀 실시간 최저가 검색")

# 3. 데이터 표시 및 상세 정보 로직
if search_btn:
    if not selected_areas:
        st.warning("지역을 선택해 주세요.")
    else:
        codes = [area_map[name] for name in selected_areas]
        area_codes_str = ",".join(codes)
        
        with st.spinner("⛳️ 최적의 티타임을 찾는 중..."):
            try:
                # 데이터 수집 (기존 scraper.py 활용)
                df = asyncio.run(fetch_kakao_golf_data(date=date_str, area_codes=area_codes_str))
                
                if not df.empty:
                    df_sorted = df.sort_values(by='그린피')
                    
                    # 요약 지표 리포트
                    col1, col2 = st.columns(2)
                    col1.metric("오늘의 최저가", f"{df_sorted['그린피'].min():,}원")
                    col2.metric("예약가능 골프장", f"{len(df_sorted)}곳")
                    
                    st.divider()
                    
                    # [핵심 UX] 카드형 리스트 (클릭 시 상세 정보 확장)
                    for _, row in df_sorted.iterrows():
                        # 카드 제목 구성 (골프장 이름 | 최저가)
                        label = f"{row['골프장']}  |  {row['그린피']:,}원~"
                        
                        with st.expander(label):
                            st.markdown(f"""
                                <div style='padding: 10px; border-left: 4px solid #1dcc70;'>
                                    <p style='margin-bottom: 5px;'>⏰ <b>잔여 티타임 정보</b>: {row['잔여팀']}</p>
                                    <p style='margin-bottom: 5px;'>💰 <b>그린피</b>: {row['그린피']:,}원 부터</p>
                                    <p style='font-size: 0.9rem; color: #666;'>※ 정확한 시간대별 가격은 카카오골프 앱에서 확인해 주세요.</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # 바로 예약하기 버튼 (실제 카카오 주소 연결 가능하도록 구성)
                            st.link_button(f"🔗 {row['골프장']} 예약하러 가기", 
                                          f"https://www.kakao.golf/tee-time?date={date_str.replace('-','')}&area={area_codes_str}")

                    st.success("최신 정보를 모두 가져왔습니다!")
                    st.balloons()
                else:
                    st.info("현재 예약 가능한 티타임이 없습니다. 😂")
            except Exception:
                st.error("카카오 서버 접속이 원활하지 않습니다. 잠시 후 다시 시도해 주세요.")

st.markdown("<br><p style='text-align: center; color: #bdc3c7; font-size: 0.8rem;'>© 2026 효섭's AI Golf Assistant</p>", unsafe_allow_html=True)