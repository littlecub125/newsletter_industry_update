"""
규칙 기반 자동승인(예외 기반 검수, review-by-exception).

"완전 자동 발행 금지" 원칙을 없애는 게 아니라 사람이 봐야 할 대상을 줄이는 필터다.
config/auto_approve_rules.json의 조건을 전부 통과한 레코드만 approved=true로 자동
전환된다. approved=true가 되는 경로는 정확히 둘뿐이다:

    1. 이 모듈의 규칙을 전부 통과 -- approval_source="auto_rule"로 기록
    2. 사람이 admin 페이지에서 개별/일괄로 명시적으로 승인 -- approval_source="manual"로 기록

apply_to_record()는 approval_source가 "manual"인 레코드는 절대 건드리지 않는다 --
사람이 이미 내린 판단(승인이든 반려든)을 규칙 재실행이 뒤집지 않는다는 뜻이다.
"""

from config_loader import load_auto_approve_rules, load_industries


def valid_industry_ids() -> set:
    return {ind["id"] for ind in load_industries()["industries"]}


def evaluate(tagged: dict, valid_ids: set, rules: dict):
    """tagged 딕셔너리 하나를 규칙에 대조해서 (통과여부, 실패사유 목록)을 반환한다.
    reasons는 사람이 admin 페이지에서 바로 읽을 수 있는 한국어 문장으로 구성한다."""
    reasons = []
    tagged = tagged or {}

    if rules.get("require_valid_industries", True):
        industries = tagged.get("industries") or []
        if not industries:
            reasons.append("industries 없음")
        else:
            invalid = [i for i in industries if i not in valid_ids]
            if invalid:
                reasons.append(f"유효하지 않은 industries: {invalid}")

    threshold = rules.get("min_impact_score")
    if threshold is not None:
        score = tagged.get("impact_score")
        if score is None:
            reasons.append("impact_score 없음")
        elif score < threshold:
            reasons.append(f"impact_score {score} < 임계값 {threshold}")

    if rules.get("disallow_controversy", True):
        if tagged.get("controversy_flag") is True:
            reasons.append("controversy_flag=true (논쟁 소지, 사람 검토 필요)")

    if rules.get("require_sentiment", True):
        if not tagged.get("sentiment"):
            reasons.append("sentiment 없음")

    if rules.get("require_summary", True):
        if not (tagged.get("summary") or "").strip():
            reasons.append("summary 없음")

    if rules.get("require_why_it_matters", True):
        if not (tagged.get("why_it_matters") or "").strip():
            reasons.append("why_it_matters 없음")

    return (len(reasons) == 0, reasons)


def apply_to_record(record: dict, valid_ids: set, rules: dict) -> dict:
    """레코드 하나에 규칙을 적용한다. record["auto_approve"]에 항상 최신 판정 결과를
    남기고(사람이 왜 자동승인되지 않았는지 볼 수 있도록), approval_source가 "manual"이
    아닌 경우에만 approved/approval_source를 규칙 결과로 (재)설정한다. in-place 수정."""
    tagged = record.get("tagged", {}) or {}
    passed, reasons = evaluate(tagged, valid_ids, rules)
    record["auto_approve"] = {"passed": passed, "reasons": reasons}

    if record.get("approval_source") == "manual":
        return record

    if passed:
        record["approved"] = True
        record["approval_source"] = "auto_rule"
    else:
        record["approved"] = False
        record["approval_source"] = None

    return record


def apply_to_records(records: list) -> dict:
    """레코드 리스트 전체에 규칙을 재실행한다. (records를 in-place로 수정하고) 통계를 반환한다."""
    valid_ids = valid_industry_ids()
    rules = load_auto_approve_rules()

    total = len(records)
    passed_count = 0
    changed = 0
    for rec in records:
        before = rec.get("approved")
        apply_to_record(rec, valid_ids, rules)
        if rec.get("approved") != before:
            changed += 1
        if rec.get("auto_approve", {}).get("passed"):
            passed_count += 1

    return {
        "total": total,
        "auto_passed": passed_count,
        "needs_review": total - passed_count,
        "changed": changed,
    }
