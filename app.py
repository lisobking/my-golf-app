import streamlit as st
import asyncio
import pandas as pd
from scraper import fetch_kakao_golf_data
from datetime import datetime
import os

# 1. 페이지 설정 (모바일 최적화)
st.set_page_config(page_title="골프 가성비 비서", page_icon="⛳️", layout="centered")

# [강력한 UI 커스텀] 카카오 앱 감성 입히기
st.markdown("""
    <style>
    /* 전체 배경색 */
    .stApp { background-color: #F2F2F2; }
    
    /* 헤더 제거 및 여백 조정 */
    header {visibility: hidden;}
    .main .block-container { padding-top: 1rem !important; }

    /* 캐릭터 메인 배너 스타일 */
    .char-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 20px;
    }
    .char-msg {
        background-color: white;
        padding: 12px 20px;
        border-radius: 20px;
        border-bottom-left-radius: 2px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        font-weight: bold;
        color: #1E1E1E;
        position: relative;
    }

    /* 카카오 노란색 버튼 */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 4rem;
        background-color: #FAE100 !important;
        color: #1E1E1E !important;
        font-size: 1.2rem;
        font-weight: 800;
        border: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-top: 10px;
    }

    /* 골프장 카드 스타일 */
    .golf-card {
        background-color: white;
        border-radius: 15px;
        padding: 18px;
        margin-bottom: 12px;
        border: 1px solid #EAEAEA;
    }
    .golf-name { font-size: 1.2rem; font-weight: 900; color: #1E1E1E; }
    .golf-price { color: #FF4D5A; font-size: 1.1rem; font-weight: 700; margin-top: 5px; }
    .golf-info { color: #8E8E8E; font-size: 0.85rem; margin-top: 3px; }
    
    /* 입력 폼 컨테이너 */
    div[data-testid="stForm"] {
        border: none !important;
        background-color: transparent !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 상단 캐릭터 섹션 (말풍선 기능 추가)
st.markdown("<div class='char-container'>", unsafe_allow_html=True)
st.markdown("<div class='char-msg'>효섭님, 오늘 야간 라운드<br>최저가 제가 다 찾아드릴게요! 🏌️‍♂️</div>", unsafe_allow_html=True)
if os.path.exists('character.png'):
    st.image('character.png', width=140)
st.markdown("</div>", unsafe_allow_html=True)

# 3. 검색 조건 섹션
with st.form("search_form"):
    area_map = {"서울/경기": "1", "강원": "2", "충청": "3", "전라": "4", "경상": "5", "제주": "6"}
    
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_areas = st.multiselect("📍 지역", options=list(area_map.keys()), default=["서울/경기"])
    with col2:
        selected_date = st.date_input("📅 날짜", value=datetime.now())
    
    date_str = selected_date.strftime("%Y-%m-%d")
    submitted = st.form_submit_button("최저가 티타임 확인하기")

# 4. 데이터 조회 및 카드형 결과 출력
if submitted:
    if not selected_areas:
        st.warning("지역을 선택해 주세요!")
    else:
        codes = [area_map[name] for name in selected_areas]
        area_codes_str = ",".join(codes)
        
        with st.spinner("⛳️ 곰돌이가 골프장을 뒤지고 있어요..."):
            try:
                df = asyncio.run(fetch_kakao_golf_data(date=date_str, area_codes=area_codes_str))
                
                if not df.empty:
                    df_sorted = df.sort_values(by='그린피')
                    
                    # 상단 요약
                    st.markdown(f"### 🏆 총 {len(df_sorted)}개의 가성비 티타임")
                    
                    for _, row in df_sorted.iterrows():
                        # [핵심 UX] 카드 형태 디자인
                        st.markdown(f"""
                            <div class='golf-card'>
                                <div class='golf-name'>{row['골프장']}</div>
                                <div class='golf-price'>{row['그린피']:,}원 ~</div>
                                <div class='golf-info'>⏰ 잔여 티타임: {row['잔여팀']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 예약 버튼
                        st.link_button(f"👉 {row['골프장']} 예약 사이트 이동", 
                                      f"https://www.kakao.golf/tee-time?date={date_str.replace('-','')}&area={area_codes_str}")
                    
                    st.balloons()
                else:
                    st.info("조건에 맞는 티타임이 없어요. 다른 날짜를 골라보세요!")
            except Exception:
                st.error("카카오 서버와 통신이 원활하지 않습니다.")

st.markdown("<br><p style='text-align: center; color: #bdc3c7; font-size: 0.8rem;'>© 2026 효섭's AI Golf Assistant</p>", unsafe_allow_html=True)