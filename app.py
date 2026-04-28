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
    st.image('character.