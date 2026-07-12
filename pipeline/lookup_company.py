"""
회사명으로 태깅된 기사를 검색하는 최소 CLI
- VIP 티어(개인/기업)의 회사별 뉴스를 운영자가 수동으로 조립할 때 보조 도구로 사용
- tagged.companies[] 필드를 부분일치(대소문자 무시)로 검색. 저장/구독 로직과는 무관한 순수 조회 도구
- 회사명 표기가 기사마다 다를 수 있어(예: "삼성전자" vs "삼성전자(Samsung Electronics)")
  부분일치로도 못 찾으면 검색어를 바꿔가며 시도해야 한다 (별칭 사전은 아직 없음, SERVICE_DESIGN.md TODO)

사용:
  python lookup_company.py "레인보우로보틱스"
  python lookup_company.py "삼성" --limit 5
"""

import argparse

from config_loader import load_company_aliases, load_tagged_articles
from ranking import filter_by_company


def print_result(rec: dict):
    tagged = rec.get("tagged", {})
    print(f"- [impact {tagged.get('impact_score')}] {rec.get('title')}")
    print(f"  요약: {tagged.get('summary')}")
    print(f"  태깅된 회사: {', '.join(tagged.get('companies') or [])}")
    print(f"  출처: {rec.get('source')} | 링크: {rec.get('link')}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("company", help="검색할 회사명 (부분일치, 대소문자 무시)")
    parser.add_argument("--limit", type=int, default=10, help="최대 출력 개수 (기본 10)")
    args = parser.parse_args()

    records = load_tagged_articles()
    if not records:
        print("data/tagged_articles.jsonl이 비어있거나 없습니다. 먼저 run_pipeline.py를 실행하세요.")
        return

    results = filter_by_company(records, args.company, load_company_aliases())[:args.limit]
    if not results:
        print(f'"{args.company}"와 일치하는 기사를 찾지 못했습니다. (회사명 표기가 다를 수 있으니 다른 검색어도 시도해보세요)')
        return

    print(f'"{args.company}" 검색 결과: {len(results)}건\n')
    for rec in results:
        print_result(rec)


if __name__ == "__main__":
    main()
