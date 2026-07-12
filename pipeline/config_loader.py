"""
경로 상수 + config/*.json 로더 통합
- 파이프라인 스크립트들에 각자 중복돼 있던 BASE_DIR 계산과 JSON 로딩을 한곳으로 모음
"""

import json
import os

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


def load_tagged_articles() -> list:
    """data/tagged_articles.jsonl을 줄 단위 JSON으로 읽는다. 파일이 없으면 빈 리스트."""
    path = os.path.join(DATA_DIR, "tagged_articles.jsonl")
    records = []
    if not os.path.exists(path):
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
