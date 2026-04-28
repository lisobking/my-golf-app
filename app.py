import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import os

# ── 안정적인 scraper import (없을 경우 더미 데이터로 fallback) ──────────────
try:
    from scraper import fetch_kakao_golf_data
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False
    async def fetch_kakao_golf_data(date: str, area_codes: str):
        """스크레이퍼 미설치 시 더미 데이터 반환"""
        await asyncio.sleep(1)
        return pd.DataFrame([
            {"골프장": "레이크사이드 CC", "그린피": 89000, "잔여팀": "3팀 남음", "url_key": "lakeside"},
            {"골프장": "블루원 용인 CC", "그린피": 72000, "잔여팀": "5팀 남음", "url_key": "blueone"},
            {"골프장": "남서울 골프클럽", "그린피": 95000, "잔여팀": "1팀 남음", "url_key": "namseoul"},
        ])

# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="골프 가성비 비서",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #0D0D0D;
    font-family: 'Noto Sans KR', sans-serif;
    color: #F0F0F0;
}

/* Hide default Streamlit chrome */
header[data-testid="stHeader"],
footer,
#MainMenu { display: none !important; }

.main .block-container {
    padding: 0 !important;
    max-width: 480px !important;
    margin: 0 auto;
}

/* ── Hero Banner ── */
.hero {
    position: relative;
    background: linear-gradient(160deg, #1A1A1A 0%, #0D0D0D 60%);
    padding: 52px 32px 40px;
    overflow: hidden;
    border-bottom: 1px solid #1E1E1E;
}
.hero::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(250,225,0,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.hero::after {
    content: 'GOLF';
    position: absolute;
    bottom: -20px; right: 10px;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 9rem;
    color: rgba(250,225,0,0.04);
    letter-spacing: 8px;
    pointer-events: none;
    line-height: 1;
}
.hero-badge {
    display: inline-block;
    background: #FAE100;
    color: #0D0D0D;
    font-size: 0.65rem;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 100px;
    margin-bottom: 14px;
}
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.4rem;
    color: #FFFFFF;
    line-height: 1.0;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.hero-title span { color: #FAE100; }
.hero-sub {
    font-size: 0.88rem;
    color: #666;
    font-weight: 400;
    letter-spacing: 0.2px;
}

/* ── Form Card ── */
.form-wrap {
    background: #141414;
    border: 1px solid #1E1E1E;
    border-radius: 24px;
    padding: 28px 24px;
    margin: 24px 16px 0;
}
.form-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #555;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: block;
}

/* Streamlit widget overrides */
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* Multiselect */
div[data-baseweb="select"] > div {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 14px !important;
    color: #F0F0F0 !important;
}
div[data-baseweb="tag"] {
    background: #FAE100 !important;
    color: #0D0D0D !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
}

/* Date input */
div[data-testid="stDateInput"] input {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 14px !important;
    color: #F0F0F0 !important;
    padding: 12px 16px !important;
}

/* Labels inside form */
.stForm label p, label p {
    color: #666 !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

/* Submit button */
div[data-testid="stFormSubmitButton"] > button,
.stButton > button {
    width: 100% !important;
    background: #FAE100 !important;
    color: #0D0D0D !important;
    border: none !important;
    border-radius: 16px !important;
    height: 56px !important;
    font-size: 1rem !important;
    font-weight: 900 !important;
    letter-spacing: 0.5px !important;
    margin-top: 18px !important;
    transition: opacity 0.15s, transform 0.1s !important;
    cursor: pointer !important;
}
div[data-testid="stFormSubmitButton"] > button:hover,
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stFormSubmitButton"] > button:active,
.stButton > button:active {
    transform: scale(0.97) !important;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #222, transparent);
    margin: 24px 16px;
}

/* ── Result Header ── */
.result-header {
    padding: 0 16px 16px;
    display: flex;
    align-items: baseline;
    gap: 8px;
}
.result-count {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    color: #FAE100;
    line-height: 1;
}
.result-label {
    font-size: 0.85rem;
    color: #555;
    font-weight: 500;
}

/* ── Golf Card ── */
.golf-card {
    background: #141414;
    border: 1px solid #1E1E1E;
    border-radius: 20px;
    padding: 22px 20px 18px;
    margin: 0 16px 12px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
}
.golf-card:hover {
    border-color: #2E2E2E;
    transform: translateY(-2px);
}
.golf-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: #FAE100;
    border-radius: 4px 0 0 4px;
}
.card-rank {
    position: absolute;
    top: 18px; right: 18px;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    color: #1E1E1E;
    line-height: 1;
}
.card-name {
    font-size: 1.15rem;
    font-weight: 900;
    color: #FFFFFF;
    margin-bottom: 6px;
    padding-right: 40px;
    line-height: 1.3;
}
.card-price {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: #FAE100;
    line-height: 1;
    letter-spacing: 0.5px;
}
.card-price-unit {
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 0.8rem;
    color: #555;
    font-weight: 500;
    margin-left: 4px;
}
.card-meta-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid #1E1E1E;
}
.card-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 0.78rem;
    color: #888;
    font-weight: 500;
}
.badge-hot { border-color: #FF4D5A33; color: #FF6B6B; background: #1A1010; }

/* ── Link button override ── */
.stLinkButton > a {
    display: block !important;
    background: transparent !important;
    border: 1px solid #2A2A2A !important;
    color: #888 !important;
    border-radius: 12px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-align: center !important;
    padding: 10px !important;
    margin: -4px 16px 20px !important;
    transition: border-color 0.2s, color 0.2s !important;
    text-decoration: none !important;
}
.stLinkButton > a:hover {
    border-color: #FAE100 !important;
    color: #FAE100 !important;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 32px;
    color: #333;
}
.empty-icon { font-size: 3rem; margin-bottom: 12px; }
.empty-text { font-size: 0.9rem; line-height: 1.6; color: #444; }

/* ── Footer ── */
.app-footer {
    text-align: center;
    padding: 32px 16px 48px;
    font-size: 0.72rem;
    color: #2A2A2A;
    letter-spacing: 0.5px;
}

/* ── Spinner override ── */
div[data-testid="stSpinner"] > div { color: #FAE100 !important; }

/* ── Error / Info ── */
div[data-testid="stAlert"] {
    border-radius: 14px !important;
    margin: 0 16px !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HERO SECTION
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">⛳ AI Golf Assistant</div>
    <div class="hero-title">최저가<br><span>티타임</span><br>파인더</div>
    <div class="hero-sub">효섭님의 스마트한 야간 라운드 파트너</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SEARCH FORM
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='form-wrap'>", unsafe_allow_html=True)

AREA_MAP = {
    "서울/경기": "1",
    "강원":     "2",
    "충청":     "3",
    "전라":     "4",
    "경상":     "5",
    "제주":     "6",
}

with st.form("search_form", border=False):
    selected_areas = st.multiselect(
        "📍 지역 선택",
        options=list(AREA_MAP.keys()),
        default=["서울/경기"],
        placeholder="지역을 선택하세요",
    )
    selected_date = st.date_input(
        "📅 날짜 선택",
        value=datetime.now().date() + timedelta(days=1),
        min_value=datetime.now().date(),
        format="YYYY.MM.DD",
    )
    submitted = st.form_submit_button("⚡ 최저가 티타임 검색")

st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if submitted:
    if not selected_areas:
        st.error("지역을 하나 이상 선택해주세요.")
    else:
        date_str      = selected_date.strftime("%Y-%m-%d")
        date_display  = selected_date.strftime("%m월 %d일")
        area_codes    = ",".join(AREA_MAP[a] for a in selected_areas)

        with st.spinner("골프장 최저가를 검색하는 중..."):
            try:
                df = asyncio.run(
                    fetch_kakao_golf_data(date=date_str, area_codes=area_codes)
                )
            except Exception as e:
                st.error(f"데이터 수집 중 오류가 발생했습니다.\n\n`{e}`")
                df = pd.DataFrame()

        if df is not None and not df.empty:
            # 정렬 보장
            if "그린피" in df.columns:
                df = df.sort_values("그린피").reset_index(drop=True)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            # 결과 헤더
            st.markdown(f"""
            <div class="result-header">
                <div class="result-count">{len(df)}</div>
                <div class="result-label">개 티타임 발견 · {date_display}</div>
            </div>
            """, unsafe_allow_html=True)

            # 결과 카드 루프
            for i, row in df.iterrows():
                rank    = i + 1
                name    = row.get("골프장", "알 수 없음")
                price   = row.get("그린피", 0)
                remain  = row.get("잔여팀", "-")
                is_best = rank == 1
                badge_class = "card-badge badge-hot" if is_best else "card-badge"
                badge_label = "🔥 최저가" if is_best else f"⏰ {remain}"

                st.markdown(f"""
                <div class="golf-card">
                    <div class="card-rank">#{rank:02d}</div>
                    <div class="card-name">{name}</div>
                    <div style="margin-top:6px;">
                        <span class="card-price">{price:,}</span>
                        <span class="card-price-unit">원 / 1인</span>
                    </div>
                    <div class="card-meta-row">
                        <span class="{badge_class}">{badge_label}</span>
                        <span class="card-badge">📍 {', '.join(selected_areas)}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                url_key  = row.get("url_key", "")
                book_url = (
                    f"https://www.kakao.golf/tee-time"
                    f"?date={date_str.replace('-','')}&area={area_codes}"
                    + (f"&cc={url_key}" if url_key else "")
                )
                st.link_button(f"카카오골프에서 예약하기 →", book_url)

            st.balloons()

        elif df is not None:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🏌️</div>
                <div class="empty-text">
                    해당 날짜/지역에 예약 가능한 티타임이 없습니다.<br>
                    날짜나 지역을 변경해 다시 검색해보세요.
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-footer">
    © 2026 효섭's AI Golf Assistant · Powered by Kakao Golf
</div>
""", unsafe_allow_html=True)