"""
scraper.py  –  카카오골프 티타임 스크레이퍼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
결과 DataFrame 컬럼:
  골프장   str   골프장 이름
  그린피   int   1인 최저 그린피 (원)
  잔여팀   str   잔여 팀수 텍스트
  golf_id  int   카카오골프 골프장 고유 ID

예약 URL 패턴 (실측):
  https://www.kakao.golf/golf/{golf_id}?date=YYYYMMDD&area={area}&reservable=true&timeZone=8

검색 URL 패턴 (실측):
  https://www.kakao.golf/golf?date=YYYYMMDD&area={area}&reservable=true&timeZone=8
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import re
import sys
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


# ────────────────────────────────────────────────────────────────────────────
# 상수 – 실제 사이트 DOM 확인 후 필요시 수정
# ────────────────────────────────────────────────────────────────────────────

# 골프장 카드 셀렉터 후보 (순서대로 시도)
CARD_SELECTORS = [
    ".golf_item",               # 제공 코드에서 확인된 클래스
    "[class*='golf_item']",     # 언더스코어 변형 대응
    "[class*='golfItem']",      # camelCase 변형 대응
    "a[href*='/golf/']",        # golf_id 링크 기반 fallback
]

# 필드별 셀렉터 후보
NAME_SELECTORS  = [".golf_name", "[class*='golf_name']", "h3", "h4", "[class*='name']"]
PRICE_SELECTORS = [".price", "[class*='price']", "[class*='fee']", "[class*='amount']"]
TEAM_SELECTORS  = [".team_count", "[class*='team']", "[class*='remain']", "[class*='count']"]

BASE_URL = "https://www.kakao.golf"


# ────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ────────────────────────────────────────────────────────────────────────────

async def _try_selectors(element, selectors: list) -> str | None:
    """셀렉터 목록을 순서대로 시도, 첫 번째 매칭 텍스트 반환"""
    for sel in selectors:
        try:
            node = await element.query_selector(sel)
            if node:
                text = (await node.inner_text()).strip()
                if text:
                    return text
        except Exception:
            continue
    return None


def _parse_price(raw: str) -> int | None:
    """'170,000원~' 또는 '89000' → 89000, 변환 불가 시 None"""
    if not raw:
        return None
    # 예약 불가 문구 필터
    if any(kw in raw for kw in ["없어요", "마감", "없음", "sold"]):
        return None
    cleaned = re.sub(r"[^\d]", "", raw)
    return int(cleaned) if cleaned else None


def _build_search_url(date_compact: str, area_code: str, time_zone: int) -> str:
    return (
        f"{BASE_URL}/golf"
        f"?date={date_compact}&area={area_code}"
        f"&reservable=true&timeZone={time_zone}"
    )


def _extract_golf_id(href: str) -> int | None:
    """'/golf/430' 또는 '/golf/430?...' → 430"""
    m = re.search(r"/golf/(\d+)", href or "")
    return int(m.group(1)) if m else None


# ────────────────────────────────────────────────────────────────────────────
# 단일 지역 스크레이핑
# ────────────────────────────────────────────────────────────────────────────

async def _scrape_area(page, date_compact: str, area_code: str, time_zone: int) -> list:
    url = _build_search_url(date_compact, area_code, time_zone)
    results = []
    print(f"🚀 접속: {url}")

    # ── 페이지 이동 ──────────────────────────────────────────────────────────
    try:
        # networkidle 대신 load 사용 (SPA에서 networkidle은 타임아웃 잦음)
        await page.goto(url, wait_until="load", timeout=60_000)
    except PlaywrightTimeout:
        print(f"  ❌ 페이지 로드 타임아웃: {url}")
        return results

    # ── 카드 출현 대기 (복수 셀렉터 순서대로 시도) ───────────────────────────
    card_sel = None
    for sel in CARD_SELECTORS:
        try:
            await page.wait_for_selector(sel, timeout=15_000)
            card_sel = sel
            print(f"  ✅ 카드 셀렉터 발견: {sel!r}")
            break
        except PlaywrightTimeout:
            continue

    if card_sel is None:
        # 어떤 셀렉터도 매칭 안 됨 → HTML 덤프 저장
        dump_path = f"debug_area{area_code}.html"
        with open(dump_path, "w", encoding="utf-8") as f:
            f.write(await page.content())
        print(f"  ⚠️  골프장 정보 없음. DOM 덤프 저장: {dump_path}")
        return results

    # ── 무한스크롤 대응 ──────────────────────────────────────────────────────
    for _ in range(10):
        prev = len(await page.query_selector_all(card_sel))
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1_200)
        curr = len(await page.query_selector_all(card_sel))
        if curr == prev:
            break

    cards = await page.query_selector_all(card_sel)
    print(f"  📋 카드 {len(cards)}개 발견 (지역코드 {area_code})")

    # ── 카드별 데이터 추출 ───────────────────────────────────────────────────
    for card in cards:
        try:
            # golf_id: 카드 자체(a 태그) 또는 내부 링크에서 추출
            golf_id = None
            href = await card.get_attribute("href")
            if href:
                golf_id = _extract_golf_id(href)
            if golf_id is None:
                # 카드가 a 태그가 아닌 경우 내부 링크 탐색
                link_el = await card.query_selector("a[href*='/golf/']")
                if link_el:
                    href = await link_el.get_attribute("href")
                    golf_id = _extract_golf_id(href)

            if golf_id is None:
                continue  # golf_id 없으면 예약 링크 생성 불가 → 건너뜀

            name      = await _try_selectors(card, NAME_SELECTORS)
            price_raw = await _try_selectors(card, PRICE_SELECTORS)
            remain    = await _try_selectors(card, TEAM_SELECTORS)

            if not name:
                continue

            price = _parse_price(price_raw or "")
            if price is None:
                continue  # 마감/예약불가 항목 제외

            results.append({
                "골프장":  name,
                "그린피":  price,
                "잔여팀":  remain or "-",
                "golf_id": golf_id,
            })

        except Exception as exc:
            print(f"  [warn] 카드 처리 오류: {exc}")
            continue

    return results


# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────

async def fetch_kakao_golf_data(
    date: str,
    area_codes: str = "1",
    time_zone: int = 8,
    headless: bool = True,
) -> pd.DataFrame:
    """
    Parameters
    ----------
    date        "2026-05-05"  (YYYY-MM-DD)
    area_codes  "1" 또는 "1,2,3"  콤마 구분 지역 코드
                  1=서울/경기, 2=강원, 3=충청, 4=전라, 5=경상, 6=제주
    time_zone   카카오골프 timeZone 파라미터 (기본 8=야간, 0=전체)
    headless    False 로 바꾸면 브라우저 창 보임 (디버깅용)

    Returns
    -------
    pd.DataFrame  컬럼: [골프장, 그린피, 잔여팀, golf_id]
                  그린피 오름차순 정렬, golf_id 기준 중복 제거
    """
    codes = [c.strip() for c in area_codes.split(",") if c.strip()]
    date_compact = date.replace("-", "")   # "2026-05-05" → "20260505"
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
            locale="ko-KR",
        )
        page = await context.new_page()

        try:
            # 세션/쿠키 초기화용 메인 페이지 방문
            await page.goto(BASE_URL, wait_until="load", timeout=30_000)
            await page.wait_for_timeout(1_500)

            for code in codes:
                area_results = await _scrape_area(page, date_compact, code, time_zone)
                all_results.extend(area_results)

        except Exception as exc:
            print(f"❌ 예기치 않은 오류: {exc}")

        finally:
            await browser.close()

    if not all_results:
        print("❌ 데이터를 찾지 못했습니다.")
        return pd.DataFrame(columns=["골프장", "그린피", "잔여팀", "golf_id"])

    df = (
        pd.DataFrame(all_results)
        .drop_duplicates(subset=["golf_id"])
        .sort_values("그린피")
        .reset_index(drop=True)
    )
    print(f"\n✅ 수집 완료: {len(df)}개 골프장")
    return df


# ────────────────────────────────────────────────────────────────────────────
# CLI 테스트
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _date  = sys.argv[1] if len(sys.argv) > 1 else "2026-05-05"
    _areas = sys.argv[2] if len(sys.argv) > 2 else "1,2,3"

    print(f"📅 날짜: {_date}  |  📍 지역코드: {_areas}\n")
    df = asyncio.run(fetch_kakao_golf_data(date=_date, area_codes=_areas))

    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("결과 없음")