"""
경로 상수 + config/*.json 로더 통합
- 파이프라인 스크립트들에 각자 중복돼 있던 BASE_DIR 계산과 JSON 로딩을 한곳으로 모음
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

load_dotenv(os.path.join(BASE_DIR, ".env"))


def _load_json(filename: str) -> dict:
    with open(os.path.join(CONFIG_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def load_industries() -> dict:
    return _load_json("industries.json")


def load_event_types() -> dict:
    return _load_json("event_types.json")


def load_sources() -> dict:
    return _load_json("sources.json")


def load_tiers() -> dict:
    return _load_json("tiers.json")


def load_company_aliases() -> dict:
    return _load_json("company_aliases.json")


def load_pipeline_limits() -> dict:
    """run_pipeline.py 회차당 API 비용 상한 등 실행 가드 설정. config/pipeline_limits.json 참고."""
    return _load_json("pipeline_limits.json")


def default_week_label(date: datetime = None) -> str:
    """오늘(또는 주어진 날짜) 기준 "YYYY년 M월 N주" 라벨을 계산한다. N = ceil(day/7).
    --week를 매번 사람이 손으로 계산해서 넘겨야 했던 게 실수(날짜 지난 라벨 그대로
    씀)로 이어진 적이 있어서(2026-07-20), build_news.py/build_newsletter.py 둘 다
    --week 생략 시 이 함수로 자동 계산하도록 한다."""
    d = date or datetime.now()
    week_no = (d.day - 1) // 7 + 1
    return f"{d.year}년 {d.month}월 {week_no}주"


def load_tagged_articles(only_approved: bool = False) -> list:
    """data/tagged_articles.jsonl을 줄 단위 JSON으로 읽는다. 파일이 없으면 빈 리스트.

    only_approved=True면 관리자 페이지(admin/)에서 사람이 `approved: true`로 표시한
    기사만 반환한다 -- "완전 자동 발행 금지" 원칙의 실제 집행 지점. build_news.py/
    build_newsletter.py는 반드시 only_approved=True로 호출해야 한다. admin_server.py는
    검수 전 기사도 보여줘야 하므로 기본값(False)을 그대로 쓴다."""
    path = os.path.join(DATA_DIR, "tagged_articles.jsonl")
    records = []
    if not os.path.exists(path):
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if only_approved:
        records = [r for r in records if r.get("approved")]
    return records
