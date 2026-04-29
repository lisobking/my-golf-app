import streamlit as st
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="5/2 리베라 CC 라운딩 안내", layout="wide")

# HTML 파일 읽기
with open("index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# 화면에 표시
components.html(html_content, height=1000, scrolling=True)