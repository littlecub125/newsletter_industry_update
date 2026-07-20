"""
RSS 수집 모듈
- sources.json에 정의된 산업별 RSS를 순회하며 기사 목록을 가져옴
- 표준 라이브러리(urllib, xml.etree)만 사용 -> 별도 설치 불필요
- 이미 처리한 기사(링크 기준)는 state 파일로 걸러서 중복 태깅 방지
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

from config_loader import DATA_DIR, load_sources

STATE_FILE = os.path.join(DATA_DIR, "processed_urls.json")
DAILY_CAP_STATE_FILE = os.path.join(DATA_DIR, "newswire_daily_counts.json")

CONTENT_NS = {"content": "http://purl.org/rss/1.0/modules/content/"}
MIN_CONTENT_LENGTH = 30   # 이보다 짧은 본문은 태깅 API 비용 절약을 위해 스킵
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1  # 재시도 간격: 1초 -> 2초 -> 4초

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text).strip()


def _normalize_pubdate(raw: str) -> str:
    """RFC 2822 형식(pubDate)을 ISO 8601로 정규화. 파싱 실패 시 원문을 그대로 유지."""
    if not raw:
        return raw
    try:
        return parsedate_to_datetime(raw).isoformat()
    except (TypeError, ValueError):
        print(f"[WARN] pubDate 정규화 실패, 원문 유지: {raw}")
        return raw


def load_processed_urls() -> set:
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_processed_urls(urls: set):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(urls), f, ensure_ascii=False)


def load_daily_counts() -> dict:
    """소스별 오늘 수집 건수를 읽는다. 날짜가 바뀌었으면 자동으로 초기화한다.

    저장 형식: {"date": "YYYY-MM-DD", "counts": {"<source url>": <int>}}
    processed_urls.json과 같은 패턴(data/ 아래, .gitignore 대상)을 따른다.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(DAILY_CAP_STATE_FILE):
        return {"date": today, "counts": {}}
    with open(DAILY_CAP_STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
    if state.get("date") != today:
        return {"date": today, "counts": {}}
    return state


def save_daily_counts(state: dict):
    with open(DAILY_CAP_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def fetch_rss(url: str, timeout: int = 10, max_retries: int = MAX_RETRIES) -> str:
    """RSS XML을 가져온다. 네트워크 실패 시 지수 백오프로 재시도한다."""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except (urllib.error.URLError, OSError) as e:
            last_error = e
            if attempt < max_retries:
                wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                print(f"[WARN] {url} 요청 실패 ({attempt}/{max_retries}), {wait}초 후 재시도: {e}")
                time.sleep(wait)
    raise last_error


def parse_rss(xml_text: str) -> list:
    """표준 RSS 2.0 <item> 구조를 파싱. 사이트마다 태그가 조금씩 다를 수 있어 예외 처리 포함.

    content:encoded 네임스페이스 태그가 있으면 description보다 우선 사용하고,
    본문이 너무 짧은(MIN_CONTENT_LENGTH 미만) 기사는 태깅 API 비용 절약을 위해 스킵한다.
    """
    articles = []
    skipped_short = 0
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"[WARN] XML 파싱 실패: {e}")
        return articles

    for item in root.findall(".//item"):
        title = item.findtext("title", default="").strip()
        link = item.findtext("link", default="").strip()
        description = item.findtext("description", default="").strip()
        content_encoded = item.findtext("content:encoded", default="", namespaces=CONTENT_NS).strip()
        content = _strip_html(content_encoded) if content_encoded else _strip_html(description)
        pub_date = _normalize_pubdate(item.findtext("pubDate", default="").strip())

        if not title or not link:
            continue
        if len(content) < MIN_CONTENT_LENGTH:
            skipped_short += 1
            continue

        articles.append({
            "title": title,
            "link": link,
            "content": content,
            "published_at": pub_date
        })

    if skipped_short:
        print(f"[SKIP] 본문이 너무 짧아 스킵된 기사: {skipped_short}건")
    return articles


def collect_articles_for_industry(industry_id: str, sources_config: dict, daily_counts: dict = None) -> list:
    """특정 산업 id에 매핑된 모든 RSS 소스를 순회하며 기사 수집

    daily_counts가 주어지면 소스별 `daily_cap`(예: 뉴스와이어 "하루 5건" 한도, 별도 허락
    미획득 상태 - TODO.md "법적/저작권 확인 필요" 참고)을 강제한다. 같은 소스(url 기준)가
    여러 산업에 매핑된 경우(예: "뉴스와이어 - 소프트웨어"가 embedded_iot/ai_software 둘 다에
    쓰임)에도 누적 건수가 합산되도록 url을 키로 쓴다. daily_counts는 호출자가 이어서 쓸 수
    있도록 그 자리에서 갱신한다(in-place).
    """
    all_articles = []
    industry_sources = sources_config["sources"].get(industry_id, [])
    if daily_counts is None:
        daily_counts = {}

    for source in industry_sources:
        if source.get("type") != "rss":
            print(f"[SKIP] {source['name']}: RSS 아님 (type={source.get('type')}), 별도 크롤러 필요")
            continue
        if not source.get("redistribution_allowed"):
            print(f"[SKIP] {source['name']}: 재배포 허가 미확인 (redistribution_allowed=false), 수집 제외")
            continue

        daily_cap = source.get("daily_cap")
        source_key = source["url"]
        used_today = daily_counts.get(source_key, 0)
        if daily_cap is not None and used_today >= daily_cap:
            print(f"[SKIP] {source['name']}: 오늘 일일 한도({daily_cap}건) 도달, 추가 수집 건너뜀 "
                  f"(뉴스와이어 대량 이용 별도 허락 미획득 - TODO.md 참고)")
            continue

        try:
            xml_text = fetch_rss(source["url"])
            articles = parse_rss(xml_text)

            if daily_cap is not None:
                remaining = daily_cap - used_today
                if len(articles) > remaining:
                    print(f"[CAP] {source['name']}: 수집분 {len(articles)}건이 일일 잔여 한도"
                          f"({remaining}건)를 초과해 {remaining}건만 사용, 나머지 건너뜀")
                    articles = articles[:remaining]
                daily_counts[source_key] = used_today + len(articles)

            for a in articles:
                a["source"] = source["name"]
                a["industry_hint"] = industry_id  # 어느 산업 소스에서 왔는지 힌트로 저장 (최종 판단은 태깅 단계에서)
            all_articles.extend(articles)
            print(f"[OK] {source['name']}: {len(articles)}건 수집")
        except Exception as e:
            print(f"[ERROR] {source['name']} 수집 실패: {e}")

        time.sleep(1)  # 서버 부담 줄이기 위한 최소 딜레이

    return all_articles


def collect_all(sources_path: str = None, max_new_articles: int = None) -> list:
    """max_new_articles를 주면 이번 실행에서 반환(=태깅 대상)할 신규 기사 수를 그 값으로
    제한한다 (config/pipeline_limits.json의 max_articles_tagged_per_run, API 비용 상한
    가드 - TODO.md "장기 구상" 참고). 상한을 넘는 나머지는 processed_urls.json에 아예
    기록하지 않아서, 다음 실행 때 다시 수집·태깅 후보로 남는다 (이번 회차에서 조용히
    유실되지 않음)."""
    if sources_path is None:
        sources_config = load_sources()
    else:
        with open(sources_path, "r", encoding="utf-8") as f:
            sources_config = json.load(f)

    processed = load_processed_urls()
    daily_state = load_daily_counts()
    new_articles = []

    for industry_id in sources_config["sources"].keys():
        articles = collect_articles_for_industry(industry_id, sources_config, daily_state["counts"])
        for a in articles:
            if a["link"] not in processed:
                new_articles.append(a)

    if max_new_articles is not None and len(new_articles) > max_new_articles:
        skipped = len(new_articles) - max_new_articles
        print(f"[CAP] 신규 기사 {len(new_articles)}건이 회차 상한({max_new_articles}건)을 "
              f"초과해 {max_new_articles}건만 태깅 대상으로 사용합니다. 나머지 {skipped}건은 "
              f"processed 표시하지 않으므로 다음 실행에서 다시 수집됩니다.")
        new_articles = new_articles[:max_new_articles]

    for a in new_articles:
        processed.add(a["link"])

    save_processed_urls(processed)
    save_daily_counts(daily_state)
    print(f"\n총 신규 기사: {len(new_articles)}건 (중복 제외)")
    return new_articles


if __name__ == "__main__":
    articles = collect_all()
    for a in articles[:5]:
        print(json.dumps(a, ensure_ascii=False, indent=2))
