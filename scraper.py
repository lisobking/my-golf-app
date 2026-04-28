import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def fetch_kakao_golf_data():
    async with async_playwright() as p:
        # 브라우저 실행 (사용자처럼 보이기 위해 User-Agent 설정 추가)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. 메인 페이지로 먼저 접속 (차단 방지)
            await page.goto("https://kakaogolfbooking.com", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # 2. 티타임 예약 페이지로 이동
            # 주소가 틀렸을 가능성을 대비해 실제 접속 가능한 경로로 수정
            target_url = "https://kakaogolfbooking.com/reservation/t-times" # s가 붙는지 확인 필요
            await page.goto(target_url, wait_until="load", timeout=60000)
            
            await page.wait_for_timeout(3000) # 로딩 대기

            # 데이터 추출 로직 (이전과 동일하지만 에러 방지 추가)
            golf_items = await page.query_selector_all(".golf-card-item") 
            
            data_list = []
            for item in golf_items:
                try:
                    name_el = await item.query_selector(".name")
                    time_el = await item.query_selector(".time")
                    price_el = await item.query_selector(".price")
                    
                    if name_el and time_el and price_el:
                        name = await name_el.inner_text()
                        time = await time_el.inner_text()
                        price_str = await price_el.inner_text()
                        price = int(price_str.replace(',', '').replace('원', '').strip())
                        
                        data_list.append({"골프장": name, "시간": time, "그린피": price})
                except:
                    continue
            
            await browser.close()
            return pd.DataFrame(data_list)
            
        except Exception as e:
            await browser.close()
            # 에러 메시지를 구체적으로 확인하기 위해 다시 던짐
            raise e