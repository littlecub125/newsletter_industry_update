"""
뉴스 기사 태깅 파이프라인
- industries.json, event_types.json을 읽어서 프롬프트에 동적으로 삽입
- 산업/이벤트 리스트를 추가/수정할 땐 이 두 json 파일만 고치면 됨
"""

import json
import anthropic

from config_loader import load_event_types, load_industries

client = anthropic.Anthropic()  # API 키는 환경변수 ANTHROPIC_API_KEY 사용

def load_config():
    return load_industries(), load_event_types()


def build_system_prompt(industries: dict, event_types: dict) -> str:
    """모든 기사 호출에서 동일한 부분(지침/목록/스키마/규칙). 프롬프트 캐싱 대상이므로
    기사마다 바뀌는 내용을 여기 섞지 말 것 — 캐싱은 "매번 똑같은 부분이 먼저"일 때만 적용된다.
    """
    industry_lines = []
    for ind in industries["industries"]:
        subs = ", ".join(ind["subcategories"])
        industry_lines.append(f'- {ind["label_ko"]} ({ind["id"]}): {subs}')
    industry_block = "\n".join(industry_lines)

    event_type_list = ", ".join([e["label_ko"] for e in event_types["event_types"]])
    sentiment_list = ", ".join(event_types["sentiment_values"])
    scope_list = ", ".join(event_types["scope_values"])

    return f"""당신은 산업 뉴스 분석 전문가입니다. 사용자가 주는 기사를 분석해서
반드시 아래 JSON 스키마 형식으로만 답변하세요.
다른 설명, 서론, 마크다운 코드블록 표시 없이 JSON 객체 하나만 출력하세요.

[선택 가능한 산업 및 하위분류 목록 - 반드시 이 안에서만 선택]
{industry_block}

[선택 가능한 이벤트 유형 - 반드시 이 안에서만 선택]
{event_type_list}

[감성 값 - 반드시 이 안에서만 선택]
{sentiment_list}

[범위 값 - 반드시 이 안에서만 선택]
{scope_list}

[출력 스키마]
{{
  "industries": ["산업id1", "산업id2"],
  "subcategories": ["하위분류1", "하위분류2"],
  "companies": ["회사명1", "회사명2"],
  "event_type": "이벤트유형 중 하나",
  "sentiment": "감성값 중 하나",
  "controversy_flag": true 또는 false,
  "scope": "범위값 중 하나",
  "tech_keywords": ["키워드1", "키워드2"],
  "region": "국내 또는 해외 국가명",
  "impact_score": 1부터 5 사이 정수,
  "summary": "1~2문장 자체 요약 (원문 문장을 그대로 베끼지 말고 반드시 자신의 말로 재작성)",
  "why_it_matters": "이 산업의 취업준비생/현직자 입장에서 이 소식이 왜 중요한지 1~2문장",
  "reasoning": "이렇게 태깅한 근거를 한 줄로"
}}

[규칙]
- industries, event_type, sentiment, scope는 위에 제시된 목록에 없는 값을 만들어내지 마세요.
- 확실하지 않은 필드는 null로 표기하세요.
- summary는 절대 원문을 그대로 인용하지 말고 완전히 재서술하세요.
- why_it_matters는 반드시 이 기사 하나에 나온 사실에만 근거하세요. 다른 기사나 배경지식을
  끌어와 종합·추론하지 말고, 이 기사가 취업준비생의 취업 준비 방향이나 현직자의 업무에
  어떤 의미가 있는지만 짧게 짚으세요. 확실하지 않으면 무리해서 만들어내지 말고 null로
  표기하세요.
"""


def build_article_message(article: dict) -> str:
    """기사마다 바뀌는 부분만. system 프롬프트 뒤에 붙는 user 메시지로 들어간다."""
    return f"""[기사 원문]
제목: {article['title']}
본문: {article['content']}
출처: {article['source']}
발행일: {article['published_at']}"""


def tag_article(article: dict) -> dict:
    industries, event_types = load_config()
    system_prompt = build_system_prompt(industries, event_types)
    user_message = build_article_message(article)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{"role": "user", "content": user_message}]
    )

    raw_text = response.content[0].text.strip()
    # 혹시 모델이 코드블록으로 감싸는 경우 대비한 정리
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        tagged = json.loads(raw_text)
    except json.JSONDecodeError:
        raise ValueError(f"JSON 파싱 실패, 원본 응답: {raw_text}")

    return tagged


if __name__ == "__main__":
    sample_article = {
        "title": "레인보우로보틱스, 산업용 협동로봇 신제품 출시",
        "content": "레인보우로보틱스가 새로운 협동로봇 라인업을 공개했다...",
        "source": "로봇신문",
        "published_at": "2026-07-01"
    }

    result = tag_article(sample_article)
    print(json.dumps(result, ensure_ascii=False, indent=2))
