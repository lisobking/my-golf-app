import streamlit as st
import asyncio
import pandas as pd
from scraper import fetch_kakao_golf_data
from datetime import datetime
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="골프 가성비 비서", 
    page_icon="⛳️", 
    layout="centered"
)

# [강력한 커스텀 CSS] 상용 앱 수준의 인터페이스 구현
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    /* 전체 배경 및 폰트 */
    .stApp { background: #F8F9FA; font-family: 'Noto Sans KR', sans-serif; }
    header { visibility: hidden; }
    .main .block-container { padding-top: 0rem !important; max-width: 500px !important; }

    /* 상단 카카오 옐로우 배너 섹션 */
    .brand-header {
        background: linear-gradient(180deg, #FAE100 0%, #FAE100 80%, #F8F9FA 100%);
        margin: -100px -100px 30px -100px;
        padding: 100px 0 50px 0;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    
    .main-title { color: #1E1E1E; font-size: 1.8rem; font-weight: 900; margin-top: 15px; }

    /* 캐릭터 이미지 프레임 (하얀 배경 문제를 디자인으로 승화) */
    .img-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 10px;
    }
    .img-frame {
        background: white;
        border-radius: 40px;
        padding: 10px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.12);
        border: 4px solid white;
        display: inline-block;
    }

    /* 입력창 카드 스타일 */
    div[data-testid="stForm"] {
        background-color: white !important;
        border-radius: 30px !important;
        border: none !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.05) !important;
        padding: 30px !important;
        margin-bottom: 30px;
    }
    
    label p { font-weight: 700 !important; color: #495057 !important; font-size: 1.1rem !important; }

    /* 카카오 블랙 버튼 */
    .stButton>button {
        width: 100%;
        border-radius: 20px !important;
        height: 4.5rem !important;
        background: #1E1E1E !important;
        color: #FAE100 !important;
        font-size: 1.4rem !important;
        font-weight: 900 !important;
        border: none !important;
        margin-top: 20px;
        transition: all 0.2s;
    }
    .stButton>button:active { transform: scale(0.96); opacity: 0.9; }

    /* 결과 카드 디자인 */
    .result-card {
        background: white;
        border-radius: 25px;
        padding: 25px;
        margin-bottom: 15px;
        border: 1px solid #F1F3F5;
        box-shadow: 0 8px 20px rgba(0,0,0,0.02);
    }
    .res-name { font-size: 1.4rem; font-weight: 900; color: #1E1E1E; margin-bottom: 8px; }
    .res-price { font-size: 1.2rem; font-weight: 700; color: #FF4D5A; }
    .res-meta { color: #868E96; font-size: 0.9rem; margin-top: 10px; background: #F8F9FA; padding: 8px 15px; border-radius: 12px; display: inline-block; }
    
    /* 예약 링크 버튼 커스텀 */
    .stLinkButton>a {
        background-color: #FAE100 !important;
        color: #1E1E1E !important;
        border-radius: 15px !important;
        font-weight: 800 !important;
        border: none !important;
        width: 100% !important;
        text-align: center !important;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 상단 브랜드 섹션
st.markdown("<div class='brand-header'>", unsafe_allow_html=True)

# 이미지 표시 (안전한 경로 확인 로직)
if os.path.exists('character.png'):
    st.markdown("<div class='img-container'><div class='img-frame'>", unsafe_allow_html=True)
    st.image('character.png', width=120)
    st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown("<div class='main-title'>골프 가성비 비서</div>", unsafe_allow_html=True)
st.markdown("<div style='color: #555; font-weight:500;'>효섭님의 스마트한 야간 라운드 파트너</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# 3. 검색 폼
with st.form("search_form"):
    area_map = {
        "서울/경기": "1", "강원": "2", "충청": "3", 
        "전라": "4", "경상": "5", "제주": "6"
    }
    
    selected_areas = st.multiselect("📍 어디로 가실까요?", options=list(area_map.keys()), default=["서울/경기"])
    selected_date = st.date_input("📅 언제 가실까요?", value=datetime.now())
    
    date_str = selected_date.strftime("%Y-%m-%d")
    submitted = st.form_submit_button("최저가 티타임 검색")

# 4. 결과 출력
if submitted:
    if not selected_areas:
        st.error("지역을 선택해주세요!")
    else:
        codes = [area_map[name] for name in selected_areas]
        area_codes_str = ",".join(codes)
        
        with st.spinner("⛳️ 곰돌이가 골프장을 뒤지고 있어요..."):
            try:
                # scraper.py 연동
                df = asyncio.run(fetch_kakao_golf_data(date=date_str, area_codes=area_codes_str))
                
                if not df.empty:
                    df_sorted = df.sort_values(by='그린피')
                    st.markdown(f"### 🏆 추천 티타임 {len(df_sorted)}건")
                    
                    for _, row in df_sorted.iterrows():
                        # 카드 디자인 출력
                        st.markdown(f"""
                            <div class='result-card'>
                                <div class='res-name'>{row['골프장']}</div>
                                <div class='res-price'>{row['그린피']:,}원 <span style='font-size:0.8rem; color:#adb5bd;'>부터</span></div>
                                <div class='res-meta'>⏰ {row['잔여팀']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 예약 버튼 (카카오 주소 연동)
                        st.link_button(f"👉 {row['골프장']} 예약하기", 
                                      f"https://www.kakao.golf/tee-time?date={date_str.replace('-','')}&area={area_codes_str}")
                    
                    st.balloons()
                else:
                    st.info("예약 가능한 티타임이 없습니다. 다른 날짜를 선택해 보세요!")
            except Exception as e:
                st.error("카카오 서버와 통신 중 오류가 발생했습니다.")

st.markdown("<br><p style='text-align: center; color: #ced4da; font-size: 0.8rem;'>© 2026 효섭's AI Golf Assistant</p>", unsafe_allow_html=True)