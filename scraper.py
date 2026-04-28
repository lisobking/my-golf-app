import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def fetch_kakao_golf_data():
    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 카카오골프예약 티타임 페이지 접속
        # (실제 운영 시에는 로그인이나 지역 필터링 과정이 추가될 수 있습니다)
        await page.goto("https://kakaogolfbooking.com/reservation/t-time")
        await page.wait_for_timeout(3000) # 로딩 대기

        # 데이터 추출 (카카오 웹사이트 구조에 맞춘 예시 셀렉터입니다)
        # 실제 사이트 업데이트에 따라 셀렉터는 수정될 수 있습니다.
        golf_items = await page.query_selector_all(".golf-card-item") 
        
        data_list = []
        for item in golf_items:
            try:
                name = await (await item.query_selector(".name")).inner_text()
                time = await (await item.query_selector(".time")).inner_text()
                price_str = await (await item.query_selector(".price")).inner_text()
                
                # 가격에서 숫자만 추출 (예: "150,000원" -> 150000)
                price = int(price_str.replace(',', '').replace('원', ''))
                
                data_list.append({
                    "골프장": name,
                    "시간": time,
                    "그린피": price
                })
            except:
                continue
        
        await browser.close()
        return pd.DataFrame(data_list)