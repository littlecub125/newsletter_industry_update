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

API 비용 상한:
    config/pipeline_limits.json의 max_articles_tagged_per_run이 회차당(이번 실행 1회당)
    태깅 가능한 최대 기사 수를 정한다. 스케줄러로 무인 실행될 때 버그/소스 물량 급증으로
    비용이 무제한으로 늘어나는 걸 막기 위한 하드 캡 -- 정교한 비용 회계가 아니다.
"""

import json
import os
import time
from datetime import datetime

from auto_approve import apply_to_record, valid_industry_ids
from config_loader import load_auto_approve_rules, load_pipeline_limits
from scrape_rss import collect_all
from tag_articles import tag_article

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, "tagged_articles.jsonl")


def append_result(original: dict, tagged: dict, valid_ids: set, rules: dict):
    """레코드를 만들고 그 자리에서 자동승인 규칙(auto_approve.py)을 적용한 뒤 저장한다 --
    approved는 태깅 직후부터 규칙 판정 결과로 시작하고(기본 false 아님), 규칙을
    통과하지 못한 레코드는 auto_approve.reasons에 사유가 남아 관리자 페이지에서
    바로 보인다. "완전 자동 발행 금지" 원칙은 그대로다 -- 규칙 통과도 사람 승인만큼
    유효한 근거로 취급될 뿐, 검수 자체를 건너뛰는 게 아니다."""
    record = {
        "title": original["title"],
        "link": original["link"],
        "source": original["source"],
        "published_at": original.get("published_at"),
        "collected_at": datetime.now().isoformat(),
        "tagged": tagged
    }
    apply_to_record(record, valid_ids, rules)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def run():
    limits = load_pipeline_limits()
    cap = limits.get("max_articles_tagged_per_run")

    print("=== 1단계: RSS 수집 ===")
    new_articles = collect_all(max_new_articles=cap)

    if not new_articles:
        print("신규 기사가 없습니다. 종료합니다.")
        return

    print(f"\n=== 2단계: 태깅 시작 ({len(new_articles)}건) ===")
    success, failed, auto_approved = 0, 0, 0
    valid_ids = valid_industry_ids()
    rules = load_auto_approve_rules()

    for i, article in enumerate(new_articles, 1):
        print(f"[{i}/{len(new_articles)}] 태깅 중: {article['title'][:40]}...")
        try:
            tagged = tag_article(article)
            record = append_result(article, tagged, valid_ids, rules)
            success += 1
            if record.get("approved"):
                auto_approved += 1
        except Exception as e:
            print(f"  [ERROR] 태깅 실패: {e}")
            failed += 1

        time.sleep(1)  # API 요청 간 최소 딜레이

    print(f"\n=== 완료 ===")
    print(f"성공: {success}건 / 실패: {failed}건 / 자동승인: {auto_approved}건 (나머지는 관리자 페이지에서 검수 필요)")
    print(f"결과 파일: {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
