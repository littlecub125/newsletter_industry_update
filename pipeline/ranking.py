"""
산업별 impact_score 랭킹 + 티어별 개수 슬라이싱
- build_news.py(웹 노출용)와 build_newsletter.py(이메일 발송용)가 공유하는 랭킹 로직
- 한 곳에서만 "산업별 상위 N개를 어떻게 뽑는지"를 관리해 두 산출물의 숫자가 어긋나지 않게 한다
"""


def group_by_industry(records: list, industries: list = None) -> dict:
    """산업 id -> [(impact_score, record), ...] impact_score 내림차순 정렬.

    industries를 지정하면 해당 산업들만 포함한다. 한 기사가 여러 산업에 걸치면
    각 산업 그룹에 중복으로 들어간다 (기존 build_news.py 동작과 동일).
    """
    by_industry = {}
    for rec in records:
        tagged = rec.get("tagged", {})
        score = tagged.get("impact_score") or 0
        rec_industries = tagged.get("industries") or []
        for ind in rec_industries:
            if industries is not None and ind not in industries:
                continue
            by_industry.setdefault(ind, []).append((score, rec))

    for scored in by_industry.values():
        scored.sort(key=lambda x: x[0], reverse=True)

    return by_industry


def top_n_by_industry(records: list, n: int, industries: list = None) -> dict:
    """산업 id -> impact_score 상위 n개 record 리스트."""
    grouped = group_by_industry(records, industries)
    return {ind: [rec for _, rec in scored[:n]] for ind, scored in grouped.items()}


def get_tier(tier_id: str, tiers_config: dict) -> dict:
    """config/tiers.json에서 티어 id로 티어 정의를 찾는다."""
    tier = next((t for t in tiers_config["tiers"] if t["id"] == tier_id), None)
    if tier is None:
        known = ", ".join(t["id"] for t in tiers_config["tiers"])
        raise ValueError(f"알 수 없는 티어: {tier_id} (사용 가능: {known})")
    return tier


def select_items_for_tier(records: list, tier_id: str, tiers_config: dict, industries: list = None) -> dict:
    """config/tiers.json의 news_count_per_industry만큼 산업별 상위 기사를 뽑는다."""
    tier = get_tier(tier_id, tiers_config)
    return top_n_by_industry(records, tier["news_count_per_industry"], industries)


def _expand_company_names(company: str, aliases_config: dict) -> list:
    """별칭 사전(config/company_aliases.json)에서 company와 같은 회사로 묶인 표기들을 모두 반환.

    검색어가 사전의 정식명/별칭 중 어느 쪽으로 들어와도 같은 그룹을 찾도록 양방향 매칭한다.
    사전에 없는 회사면 검색어 자신만 담긴 리스트를 반환한다 (기존 부분일치 동작과 동일).
    """
    if not aliases_config:
        return [company]
    company_lower = company.lower()
    for canonical, alias_list in aliases_config.get("aliases", {}).items():
        group = [canonical, *alias_list]
        if any(company_lower == g.lower() for g in group):
            return group
    return [company]


def filter_by_company(records: list, company: str, aliases_config: dict = None) -> list:
    """tagged.companies[]에 company(또는 그 별칭)가 부분일치(대소문자 무시)하는 기사를
    impact_score 내림차순으로 반환.

    aliases_config를 주면 config/company_aliases.json 기준으로 같은 회사의 다른 표기도
    같이 검색한다 (예: "삼성전자" 검색 시 "Samsung Electronics" 표기 기사도 포함, SERVICE_DESIGN.md
    8번 항목 — LLM 태깅의 회사명 표기 불일치 보완). VIP 다이제스트(build_newsletter.py)와 회사
    조회 도구(lookup_company.py)가 공유하는 로직이다.
    """
    search_terms = [t.lower() for t in _expand_company_names(company, aliases_config)]
    matched = []
    for rec in records:
        companies = rec.get("tagged", {}).get("companies") or []
        if any(term in c.lower() for c in companies for term in search_terms):
            matched.append(rec)
    matched.sort(key=lambda r: r.get("tagged", {}).get("impact_score") or 0, reverse=True)
    return matched
