"""
태깅 결과(tagged_articles.jsonl) -> 스티비에 붙여넣을 이메일 초안(HTML) 생성

- 티어(--tier)에 따라 산업당 뉴스 개수/광고 유무가 정해진다 (config/tiers.json)
- --industries로 이번 발송에 포함할 산업을 지정한다 (생략 시 전체 산업 대상)
- --companies는 VIP 티어(vip_individual/vip_business) 전용. 지정한 회사명이
  tagged.companies[]에 포함된 기사를 모아 별도 섹션으로 추가한다
- approved=true로 표시된 기사만 포함한다 (admin/ 관리자 페이지에서 사람이 승인) -- 완전
  자동 발행 금지 원칙의 실제 집행 지점
- 완전 자동 발행 금지 원칙(CLAUDE.md)에 따라 상단에 검수 필수 배너를 고정 삽입하고,
  기사 사이에 운영자가 직접 채워 넣을 코멘트 자리표시를 남긴다. 이 스크립트의 출력은
  "초안"이며 그대로 발송하지 않는다.

사용:
  python build_newsletter.py --tier free                          # --week 생략 시 자동 계산
  python build_newsletter.py --tier vip_individual --industries robot,ai_software \
      --companies "레인보우로보틱스,네이버" --week "2026년 7월 2주"  # 수동 지정도 가능

출력:
  data/newsletter_drafts/{week}_{tier}.html 로 저장 + 표준출력에도 그대로 출력
  (스티비 에디터에 바로 복사해 붙여넣기 편하도록)
"""

import argparse
import html
import os
import sys

from config_loader import DATA_DIR, default_week_label, load_company_aliases, load_industries, load_tagged_articles, load_tiers
from ranking import filter_by_company, get_tier, select_items_for_tier

DRAFTS_DIR = os.path.join(DATA_DIR, "newsletter_drafts")


def load_industries_list() -> list:
    return load_industries()["industries"]


def parse_csv_arg(value: str) -> list:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def warn_if_over_limit(label: str, chosen: list, limit):
    if limit is not None and len(chosen) > limit:
        print(f"[경고] {label} {len(chosen)}개가 지정됐지만 이 티어의 한도는 {limit}개입니다. (한도는 참고값이라 그대로 진행합니다)")


def render_article(rec: dict) -> str:
    tagged = rec.get("tagged", {})
    title = html.escape(rec.get("title", ""))
    summary = html.escape(tagged.get("summary", ""))
    source = html.escape(rec.get("source", ""))
    link = html.escape(rec.get("link", ""))
    why_it_matters = tagged.get("why_it_matters")
    why_html = f'\n      <p class="why-it-matters">💡 {html.escape(why_it_matters)}</p>' if why_it_matters else ""
    return f"""    <div class="article">
      <h3><a href="{link}">{title}</a></h3>
      <p class="summary">{summary}</p>{why_html}
      <p class="meta">출처: {source}</p>
      <p class="comment-placeholder">[[ 운영자 코멘트를 여기에 추가하세요 ]]</p>
    </div>"""


def render_section(title: str, items: list, empty_message: str = "이번 주 태깅된 뉴스가 없습니다.") -> str:
    body = "\n".join(render_article(rec) for rec in items) if items else f'    <p class="empty">{html.escape(empty_message)}</p>'
    return f"""  <section>
    <h2>{html.escape(title)}</h2>
{body}
  </section>"""


def build_newsletter_html(tier_id: str, week_label: str, industries: list, companies: list) -> str:
    tiers_config = load_tiers()
    tier = get_tier(tier_id, tiers_config)

    warn_if_over_limit("산업", industries, tier.get("max_industries"))
    warn_if_over_limit("회사", companies, tier.get("max_companies"))

    if companies and not tier.get("company_digest"):
        print(f"[경고] '{tier_id}' 티어는 회사 지정 기능이 없습니다 (VIP 전용). --companies는 무시합니다.")
        companies = []

    # only_approved=True: admin/ 관리자 페이지에서 사람이 승인 체크한 기사만 포함한다
    # (완전 자동 발행 금지 원칙의 실제 집행 지점 -- config_loader.load_tagged_articles 참고)
    records = load_tagged_articles(only_approved=True)
    if not records:
        print("[경고] 승인된(approved=true) 기사가 없습니다. admin/ 관리자 페이지에서 먼저 검수·승인하세요.")

    industries_data = load_industries_list()
    labels = {ind["id"]: ind["label_ko"] for ind in industries_data}
    canonical_order = [ind["id"] for ind in industries_data]

    items_by_industry = select_items_for_tier(records, tier_id, tiers_config, industries or None)
    industry_order = industries if industries else [i for i in canonical_order if i in items_by_industry]

    industry_sections = [
        render_section(labels.get(ind_id, ind_id), items_by_industry.get(ind_id, []))
        for ind_id in industry_order
    ]

    aliases_config = load_company_aliases()
    company_sections = [
        render_section(f"{company} 관련 뉴스", filter_by_company(records, company, aliases_config))
        for company in companies
    ]

    ad_html = ""
    if tier.get("has_ads"):
        ad_html = """  <section class="ad-slot">
    <p>[[ 광고 자리 — 지금은 프리미엄 안내로 채움 ]]</p>
    <p>더 많은 뉴스와 광고 없는 경험을 원하신다면 프리미엄을 확인해보세요.</p>
  </section>"""

    banner = (
        f'  <div class="draft-banner">⚠️ 자동 생성 초안입니다. 발송 전 반드시 사람이 검수하고 '
        f"코멘트를 채운 뒤 스티비에 붙여넣으세요. (티어: {html.escape(tier['label_ko'])} / "
        f"주차: {html.escape(week_label)})</div>"
    )

    body = "\n".join(industry_sections + company_sections + ([ad_html] if ad_html else []))

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>{html.escape(week_label)} 뉴스레터 초안 ({html.escape(tier['label_ko'])})</title>
</head>
<body>
{banner}
  <h1>{html.escape(week_label)}</h1>
{body}
</body>
</html>
"""


def main():
    # Windows 콘솔(cp949)은 이모지(⚠️/💡)를 못 그려서 print()가 UnicodeEncodeError로 죽는다.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", required=True,
                         help="config/tiers.json의 티어 id (free/premium/vip_individual/vip_business)")
    parser.add_argument("--week", default=None,
                         help='주차 라벨 (예: "2026년 7월 2주"). 생략하면 오늘 날짜로 자동 계산')
    parser.add_argument("--industries", default="", help="콤마로 구분한 산업 id 목록 (생략 시 전체 산업)")
    parser.add_argument("--companies", default="", help="콤마로 구분한 회사명 목록 (VIP 티어 전용)")
    args = parser.parse_args()
    if args.week is None:
        args.week = default_week_label()

    industries = parse_csv_arg(args.industries)
    companies = parse_csv_arg(args.companies)

    html_output = build_newsletter_html(args.tier, args.week, industries, companies)

    os.makedirs(DRAFTS_DIR, exist_ok=True)
    filename = f"{args.week.replace(' ', '_')}_{args.tier}.html"
    out_path = os.path.join(DRAFTS_DIR, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(html_output)
    print(f"\n저장: {out_path}")


if __name__ == "__main__":
    main()
