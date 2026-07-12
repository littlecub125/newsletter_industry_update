# CLAUDE.md

이 파일은 Claude Code가 이 프로젝트의 맥락을 이해하기 위한 문서입니다.

## 작업공간 구조

이 폴더(`newsletter_claude/`)는 **dev 전용 작업공간**이다 — 코드/파이프라인/웹사이트/
배포만 다루고, 마케팅·사업 전략 자료는 형제 폴더인 `../marketing_claude/`,
`../business_claude/`에 있다. 세 작업공간이 어떻게 협업하는지는 프로젝트 루트의
[`../CLAUDE.md`](../CLAUDE.md)를 참고할 것. 이 폴더만 git 저장소(공개 GitHub 저장소,
`master`+`gh-pages`)이고 나머지 두 작업공간은 버전 관리 대상이 아니다.

## 프로젝트 개요

산업별 뉴스 큐레이션 뉴스레터 서비스. 구독자가 관심 산업을 선택하면
매주 그 산업의 주요 뉴스를 요약해 이메일로 받아본다.

**타겟**: 특정 산업의 취업준비생 + 바쁜 현직자
**핵심 가치**: "매번 직접 뉴스를 찾아볼 필요 없이, 정기적으로 도착하는 산업 동향"
**운영 주체**: 1인 (본업 병행), 초기 자본 거의 없음

작업 단위로 정리된 프롬프트 모음이 `PROMPTS.md`에 있다. 우선순위(A: 첫 호 발행 →
B: 배포 → C: 파이프라인 개선 → D: 나중에)별로 정리돼 있으니, 사용자가 다음에
뭘 할지 막막해하면 이 파일을 먼저 참고할 것.

티어(요금제) 비즈니스 로직과 그걸 구현하는 파이프라인 아키텍처의 설계 근거는
`SERVICE_DESIGN.md`에 있다. "왜 이렇게 만들었는가"가 궁금하면 이 파일을 참고할 것.

지금 뭐가 막혀 있고 다음에 뭘 해야 하는지는 `TODO.md`에 있다. 새 세션을 시작하면
대화 기록을 다시 읽는 대신 이 파일부터 확인할 것 — 최신 상태 스냅샷이라 갱신된다.

웹사이트(`web/`)의 비주얼 디자인 토큰(색상/타이포그래피/레이아웃)은 `DESIGN_GUIDE.md`에,
카피 톤은 `../marketing_claude/STYLE_GUIDE.md`에, 검색 노출(SEO) 구현 체크리스트는
`SEO_CHECKLIST.md`(전략은 `../business_claude/SEO_STRATEGY.md`)에 있다.

## 현재 상태

- 뉴스 수집·태깅 파이프라인 구현 완료 (실제 운영 실행은 아직 안 함)
- 웹사이트 5개 페이지 구현 완료 (스티비 구독 폼 미연결)
- 스티비 계정 생성 완료, 주소록/구독 폼 세팅 진행 중
- **구독자 0명, 발행 0호** — 아직 실제 검증 전 단계

## 폴더 구조

```
newsletter-project/
├── web/                 # 정적 웹사이트 (그대로 호스팅 가능)
│   ├── index.html       # 홈 (구독 랜딩)
│   ├── news.html        # 뉴스 (산업 필터 + 최신/아카이브 탭)
│   ├── pricing.html     # 요금 (4개 티어)
│   ├── about.html       # 소개
│   ├── privacy.html     # 개인정보처리방침
│   └── news.json        # 뉴스 데이터 (build_news.py가 갱신)
├── pipeline/            # 뉴스 수집·태깅 파이프라인 (Python)
│   ├── config_loader.py    # 경로 상수 + config/*.json, tagged_articles.jsonl 로더 (공용)
│   ├── ranking.py          # 산업별 랭킹, 티어별 슬라이싱, 회사명 필터 (공용)
│   ├── scrape_rss.py       # RSS 수집 (표준 라이브러리만 사용)
│   ├── tag_articles.py     # LLM 태깅 (Anthropic API)
│   ├── run_pipeline.py     # 수집 → 태깅 실행
│   ├── build_news.py       # 태깅 결과 → news.json 변환 (free/premium만, 웹 노출용)
│   ├── build_newsletter.py # 태깅 결과 → 이메일 초안 HTML (4개 티어 + 회사 섹션, 발송용)
│   └── lookup_company.py   # 회사명으로 태깅 기사 검색 CLI (VIP 수동 조립 보조)
├── config/              # 설정 파일 (여기만 고치면 확장됨)
│   ├── industries.json  # 산업 대분류 10개 + 중분류
│   ├── event_types.json # 이벤트 유형, 감성, scope 고정 리스트
│   ├── sources.json     # 산업별 RSS 소스 매핑
│   ├── tiers.json       # 티어별 한도 (산업 수/회사 수/뉴스 개수/광고/웹 노출 방식)
│   └── company_aliases.json  # 회사명 별칭 사전 (표기 불일치 보완, lookup_company.py가 사용)
└── data/                # 실행 시 자동 생성 (gitignore 대상)
    ├── processed_urls.json      # 중복 방지용 처리 완료 URL
    ├── tagged_articles.jsonl    # 태깅 결과 누적
    └── newsletter_drafts/       # build_newsletter.py가 생성하는 이메일 초안
```

## 데이터 흐름

```
RSS 소스 (config/sources.json)
  ↓ scrape_rss.py         (수집 + 링크 기준 중복 제거)
  ↓ tag_articles.py       (Claude API로 JSON 태깅)
  → data/tagged_articles.jsonl
  ↓ build_news.py         (산업별 impact_score 상위 추출)
  → web/news.json         (웹사이트 자동 반영)
```

## 기사 태깅 스키마

`tag_articles.py`가 각 기사를 아래 JSON으로 변환한다:

| 필드 | 설명 |
|---|---|
| industries | 산업 id 배열 (config/industries.json의 id만 사용) |
| subcategories | 하위 분류 배열 |
| companies | 언급된 회사명 배열 |
| event_type | 투자/M&A/제품출시/규제/인사/실적/논란/파트너십/채용동향/R&D/기타 |
| sentiment | 긍정 / 부정 / 중립 / 혼조 |
| controversy_flag | 논란 여부 (sentiment와 **별개 축**) |
| scope | 특정기업 / 산업전반 / 정책·규제 |
| tech_keywords | 기술 키워드 배열 |
| region | 국내 / 해외 국가명 |
| impact_score | 1~5 (뉴스레터 노출 순위 결정에 사용) |
| summary | 1~2문장 자체 요약 (**원문 인용 금지, 반드시 재서술**) |
| reasoning | 태깅 근거 한 줄 (사람이 검수할 때 사용) |

### 아직 구현되지 않은 태그
- `cluster_id`: 같은 사건을 다룬 여러 매체 기사를 하나로 묶기 (중복 게재 방지)
- `source_reliability`: 1차 소스 / 취재 기사 / 루머성 구분
- `company_stage`: 스타트업 / 중견 / 대기업

## news.json 스키마

`build_news.py`가 산출하는 `web/news.json`은 `industries`(id/label 목록)와
`weeks` 배열로 구성된다. 각 week는 아래 형태이며, 배열 맨 앞(0번 인덱스)이
최신 주차다:

```json
{
  "week_label": "2026년 7월 2주",
  "published_at": "2026-07-13",
  "items": [
    { "industry": "robot", "tier": "free|premium", "title": "...",
      "summary": "...", "source": "...", "link": "...",
      "event_type": "...", "sentiment": "..." }
  ]
}
```

한 기사가 여러 산업에 걸치면 `items`에 산업별로 중복 등록된다 (기사 단위가
아니라 "산업×기사" 단위로 존재). `news.html`은 이 파일을 fetch로 읽어 필터링·
최신/아카이브 탭을 렌더링한다.

## 요금 티어 (pricing.html)

| 티어 | 산업 개수 | 회사 지정 | 산업당 뉴스 | 광고 | 상태 |
|---|---|---|---|---|---|
| 무료 | 1개 | - | 3개 | 있음 | 지금 오픈 |
| 프리미엄 | 최대 5개 | - | 10개+ | 없음 | 곧 오픈 |
| VIP 개인 | 최대 5개 | 최대 3개 | 10개+ | 없음 | 준비 중 |
| VIP 기업 | 최대 10개 | 최대 10개 | 10개+ | 없음 | 준비 중 |

- 티어별 한도의 단일 진실 공급원은 `config/tiers.json`이다. 코드에 숫자를 하드코딩하지 않는다.
- VIP 두 티어는 산업뿐 아니라 **특정 회사 지정** → 그 회사 관련 뉴스를 맞춤 발송한다는 게 핵심 차이.
  VIP 기업은 "구독자 1명"이 아니라 "고객사 1곳" 단위 개인화(팀 발송)다.
- `max_industries`/`max_companies`는 아직 강제 검증이 아니라 참고값이다 (구독 폼에 선택 UI가
  없어서 — 아래 TODO #1 참고). 왜 이렇게 설계했는지는 `SERVICE_DESIGN.md` 참고.

## 코딩 규칙

- **파이프라인은 표준 라이브러리 우선.** `scrape_rss.py`는 의존성 없이 동작해야 함 (feedparser 등 사용 금지)
- **설정은 config/의 JSON으로.** 산업이나 이벤트 유형을 코드에 하드코딩하지 말 것.
  프롬프트도 실행 시점에 JSON을 읽어 동적으로 삽입한다.
- **웹사이트는 정적 HTML.** 빌드 도구, 프레임워크 없음. 5개 페이지가 같은 CSS 변수·내비게이션 구조를 공유한다.
- **디자인은 임시.** 지금은 범용 톤이고, 나중에 갈아끼울 예정.

## 중요한 제약 / 주의사항

### 저작권
- 기사 원문을 그대로 옮기면 안 된다. `summary`는 **반드시 자체 재서술**.
- RSS 콘텐츠 재배포는 언론사별 정책 확인이 필요할 수 있다 (config/sources.json의 legal_note_ko 참고).

### 개인정보
- 이메일 수집 시 개인정보처리방침 필수 (privacy.html에 작성됨, 운영자 이름·문의 이메일 미기입 상태).
- 실제 발송은 스티비가 담당 (수신거부·반송 처리 등을 대행).

### 태깅 품질
- LLM 태깅은 초기 정확도가 낮다. 특히 `sentiment`의 "중립 vs 혼조", `controversy_flag` 판단.
- **완전 자동 발행 금지.** 사람이 최종 선별·검수하는 단계를 반드시 유지한다.
  이것이 범용 AI 뉴스 요약 툴(Feedly, News Minimalist 등)과의 유일한 차별점이다.

## 미완성 / TODO

1. ~~스티비 구독 폼 연결~~ — 완료 (2026-07-12), `web/index.html`에 이메일 + 산업 선택 필드 연결
2. ~~privacy.html 빈칸~~ — 완료 (2026-07-12), 책임자 김유빈 / 문의 yubi2023@gmail.com
3. **로봇신문 등 RSS 없는 소스** — `config/sources.json`에 `type: "site_crawl"`로 표시됨, 크롤러 미구현
4. **cluster_id** — 같은 사건 중복 기사 묶기 미구현
5. ~~호스팅~~ — 완료 (2026-07-12), `web/` 폴더가 GitHub Pages로 배포됨 (아래 "배포" 섹션 참고)
6. **스케줄러** — 주기 실행 미구현 (수동 실행만 검증됨)
7. **VIP용 회사 선택 UI 미구현** — 구독 폼의 산업 선택은 완료(위 1번)했지만, 회사 지정(VIP
   개인/기업)과 다중 산업 선택(프리미엄)은 아직 없음. `build_newsletter.py`는 그때까지 운영자가
   `--industries`/`--companies`를 직접 지정하는 방식으로 운영한다. `SERVICE_DESIGN.md` 5번
   항목 참고.

## 실행 방법

```bash
pip install anthropic python-dotenv
# ANTHROPIC_API_KEY=... 를 프로젝트 루트 .env 파일에 저장 (config_loader.py가 자동 로드함)

# 1. 수집 + 태깅
python pipeline/run_pipeline.py

# 2. 태깅 결과 → 웹사이트 데이터 변환
python pipeline/build_news.py --week "2026년 7월 2주"

# 3. 태깅 결과 → 이메일 초안 (티어별로 별도 실행)
python pipeline/build_newsletter.py --tier free --week "2026년 7월 2주"

# 4. 웹사이트 확인 (정적 파일이라 그냥 열면 됨)
#    단, news.html은 fetch로 news.json을 읽으므로 로컬 서버 필요
cd web && python -m http.server 8000
```

개별 모듈만 따로 확인하고 싶을 때 (전체 파이프라인 대비 API 비용/리스크가 작음):

```bash
# RSS 수집만 (태깅 없이, 처음 5건만 출력)
python pipeline/scrape_rss.py

# 태깅 프롬프트 하나만 시험 (하드코딩된 샘플 기사 1건에 Claude API 1회 호출)
python pipeline/tag_articles.py

# 회사명으로 태깅된 기사 검색 (VIP 다이제스트 수동 조립 보조, API 호출 없음)
python pipeline/lookup_company.py "레인보우로보틱스"
```

## 배포

- **저장소**: `https://github.com/littlecub125/newsletter_industry_update` (public)
- **사이트**: `https://littlecub125.github.io/newsletter_industry_update/`
- GitHub Pages는 저장소 루트나 `/docs` 폴더만 배포 소스로 잡을 수 있어서, `web/` 하위 폴더를
  그대로 서비스하기 위해 `git subtree`로 `web/` 내용만 별도 `gh-pages` 브랜치에 분리해뒀다.
  즉 저장소에는 브랜치가 두 개다: `master`(전체 소스, 파이프라인 포함)와 `gh-pages`(웹사이트만).
- **`web/` 파일을 고친 뒤 실제 배포에 반영하려면** 아래 두 단계가 모두 필요하다:
  ```bash
  git add -A && git commit -m "..."   # master에 커밋 (평소처럼)
  git subtree push --prefix web origin gh-pages   # web/ 변경분만 gh-pages로 재배포
  ```
  `master`에 커밋만 하고 subtree push를 빠뜨리면 실제 배포된 사이트는 안 바뀐다.

## 이 프로젝트의 우선순위

기술적 완성도보다 **첫 호 발행과 구독자 확보**가 우선이다.
자동화·SaaS·모니터링 등은 실제로 몇 호를 수동 발행해본 뒤,
어디가 진짜 반복 노동인지 확인하고 붙인다.
