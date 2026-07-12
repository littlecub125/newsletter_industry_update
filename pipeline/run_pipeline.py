"""
전체 파이프라인: RSS 수집 -> 중복 제거 -> LLM 태깅 -> 결과 저장

실행 방법:
    python run_pipeline.py

사전 준비:
    1. pip install anthropic --break-system-packages
    2. 환경변수 ANTHROPIC_API_KEY 설정
    3. industries.json, event_types.json, sources.json 같은 폴더에 위치

결과:
    tagged_articles.jsonl 에 한 줄당 기사 하나씩 JSON으로 누적 저장
"""

import json
import os
import time
from datetime import datetime

from scrape_rss import collect_all
from tag_articles import tag_article

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, "tagged_articles.jsonl")


def append_result(original: dict, tagged: dict):
    record = {
        "title": original["title"],
        "link": original["link"],
        "source": original["source"],
        "published_at": original.get("published_at"),
        "collected_at": datetime.now().isoformat(),
        "tagged": tagged
    }
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run():
    print("=== 1단계: RSS 수집 ===")
    new_articles = collect_all()

    if not new_articles:
        print("신규 기사가 없습니다. 종료합니다.")
        return

    print(f"\n=== 2단계: 태깅 시작 ({len(new_articles)}건) ===")
    success, failed = 0, 0

    for i, article in enumerate(new_articles, 1):
        print(f"[{i}/{len(new_articles)}] 태깅 중: {article['title'][:40]}...")
        try:
            tagged = tag_article(article)
            append_result(article, tagged)
            success += 1
        except Exception as e:
            print(f"  [ERROR] 태깅 실패: {e}")
            failed += 1

        time.sleep(1)  # API 요청 간 최소 딜레이

    print(f"\n=== 완료 ===")
    print(f"성공: {success}건 / 실패: {failed}건")
    print(f"결과 파일: {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
