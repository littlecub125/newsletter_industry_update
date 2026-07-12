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


def collect_articles_for_industry(industry_id: str, sources_config: dict) -> list:
    """특정 산업 id에 매핑된 모든 RSS 소스를 순회하며 기사 수집"""
    all_articles = []
    industry_sources = sources_config["sources"].get(industry_id, [])

    for source in industry_sources:
        if source.get("type") != "rss":
            print(f"[SKIP] {source['name']}: RSS 아님 (type={source.get('type')}), 별도 크롤러 필요")
            continue

        try:
            xml_text = fetch_rss(source["url"])
            articles = parse_rss(xml_text)
            for a in articles:
                a["source"] = source["name"]
                a["industry_hint"] = industry_id  # 어느 산업 소스에서 왔는지 힌트로 저장 (최종 판단은 태깅 단계에서)
            all_articles.extend(articles)
            print(f"[OK] {source['name']}: {len(articles)}건 수집")
        except Exception as e:
            print(f"[ERROR] {source['name']} 수집 실패: {e}")

        time.sleep(1)  # 서버 부담 줄이기 위한 최소 딜레이

    return all_articles


def collect_all(sources_path: str = None) -> list:
    if sources_path is None:
        sources_config = load_sources()
    else:
        with open(sources_path, "r", encoding="utf-8") as f:
            sources_config = json.load(f)

    processed = load_processed_urls()
    new_articles = []

    for industry_id in sources_config["sources"].keys():
        articles = collect_articles_for_industry(industry_id, sources_config)
        for a in articles:
            if a["link"] not in processed:
                new_articles.append(a)
                processed.add(a["link"])

    save_processed_urls(processed)
    print(f"\n총 신규 기사: {len(new_articles)}건 (중복 제외)")
    return new_articles


if __name__ == "__main__":
    articles = collect_all()
    for a in articles[:5]:
        print(json.dumps(a, ensure_ascii=False, indent=2))
