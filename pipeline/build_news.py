"""
태깅 결과(tagged_articles.jsonl) -> news.json 주차 데이터 변환

동작:
  1. tagged_articles.jsonl을 읽음
  2. 산업(industry)별로 그룹핑
  3. 각 산업에서 impact_score 상위 N개 추출 (N은 config/tiers.json의 premium.news_count_per_industry)
     - 상위 free.news_count_per_industry개 -> tier: "free"
     - 그 다음(premium 개수까지) -> tier: "premium"
  4. 이번 주차(week) 블록을 만들어 news.json의 weeks 배열 맨 앞에 추가

사용:
  python build_news.py --week "2026년 7월 2주"

주의:
  - 같은 주차 라벨이 이미 있으면 덮어쓸지 물어봅니다(중복 방지).
  - industries 목록은 industries.json, 티어별 개수는 tiers.json에서 읽습니다.
  - VIP 두 티어(vip_individual/vip_business)는 웹에 노출하지 않으므로 이 스크립트는 다루지 않습니다
    (VIP는 build_newsletter.py가 이메일 초안에서만 다룸).
"""

import argparse
import json
import os
from datetime import datetime

from config_loader import BASE_DIR, DATA_DIR, load_industries as load_industries_config
from config_loader import load_tagged_articles, load_tiers
from ranking import group_by_industry

TAGGED_FILE = os.path.join(DATA_DIR, "tagged_articles.jsonl")
NEWS_FILE = os.path.join(BASE_DIR, "web", "news.json")


def load_industries():
    return {ind["id"]: ind["label_ko"] for ind in load_industries_config()["industries"]}


def tier_news_count(tier_id: str) -> int:
    """config/tiers.json에서 티어별 산업당 뉴스 개수를 읽는다 (free=3, premium=10처럼 하드코딩하지 않기 위함)."""
    tier = next(t for t in load_tiers()["tiers"] if t["id"] == tier_id)
    return tier["news_count_per_industry"]


def load_tagged():
    records = load_tagged_articles()
    if not records:
        print(f"[경고] {TAGGED_FILE}이 없습니다. 먼저 run_pipeline.py를 실행하세요.")
    return records


def build_week(week_label: str, published_at: str):
    records = load_tagged()
    if not records:
        return None

    free_count = tier_news_count("free")
    premium_total = tier_news_count("premium")

    # 산업별로 그룹핑 (한 기사가 여러 산업에 걸릴 수 있으므로 각 산업에 중복 등록)
    by_industry = group_by_industry(records)

    items = []
    for ind_id, scored in by_industry.items():
        top = scored[:premium_total]

        for i, (score, rec) in enumerate(top):
            tagged = rec["tagged"]
            tier = "free" if i < free_count else "premium"
            items.append({
                "industry": ind_id,
                "tier": tier,
                "title": rec.get("title", ""),
                "summary": tagged.get("summary", ""),
                "source": rec.get("source", ""),
                "link": rec.get("link", ""),
                "event_type": tagged.get("event_type"),
                "sentiment": tagged.get("sentiment")
            })

    return {
        "week_label": week_label,
        "published_at": published_at,
        "items": items
    }


def load_or_init_news():
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, encoding="utf-8") as f:
            return json.load(f)
    # 없으면 기본 뼈대 생성
    industry_labels = load_industries()
    return {
        "industries": [{"id": k, "label": v} for k, v in industry_labels.items()],
        "weeks": []
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True, help='주차 라벨 (예: "2026년 7월 2주")')
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="발행일 (기본: 오늘)")
    args = parser.parse_args()

    week_block = build_week(args.week, args.date)
    if week_block is None:
        print("변환할 태깅 데이터가 없습니다.")
        return

    news = load_or_init_news()

    # 같은 주차 라벨 중복 확인
    existing = [w for w in news["weeks"] if w["week_label"] == args.week]
    if existing:
        ans = input(f'"{args.week}" 주차가 이미 있습니다. 덮어쓸까요? (y/N): ')
        if ans.lower() != "y":
            print("취소했습니다.")
            return
        news["weeks"] = [w for w in news["weeks"] if w["week_label"] != args.week]

    # 맨 앞에 추가 (최신이 위로)
    news["weeks"].insert(0, week_block)

    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

    free_n = sum(1 for it in week_block["items"] if it["tier"] == "free")
    prem_n = sum(1 for it in week_block["items"] if it["tier"] == "premium")
    print(f'"{args.week}" 주차 추가 완료: 무료 {free_n}개 / 프리미엄 {prem_n}개')
    print(f"저장: {NEWS_FILE}")


if __name__ == "__main__":
    main()
