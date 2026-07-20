# SERVICE_DESIGN.md

이 문서는 티어(요금제) 비즈니스 로직과 파이프라인 아키텍처를 잇는 **설계 근거** 문서다.
"왜 이렇게 만들었는가"에 집중한다.

- `CLAUDE.md`: 프로젝트 전반 오리엔테이션 (폴더 구조, 데이터 흐름, 코딩 규칙)
- `PROMPTS.md`: 작업 단위 프롬프트 모음 (우선순위별)
- **`SERVICE_DESIGN.md` (이 문서)**: 티어 구조가 왜 이렇게 정해졌고, 파이프라인이 그걸 어떻게
  구현하는지, 그리고 아직 결정 못 한 부분은 무엇인지

세 문서는 역할이 겹치지 않는다. CLAUDE.md/PROMPTS.md를 고칠 필요가 생기면 이 문서를 고치는
대신 그쪽을 고친다.

## 1. 티어 구조

| 티어 | 산업 개수 | 회사 지정 | 산업당 뉴스 | 광고 | 웹 노출 |
|---|---|---|---|---|---|
| 무료 (`free`) | 1개 | - | 3개 | 있음 | 공개(누구나 열람) |
| 프리미엄 (`premium`) | 최대 5개 | - | 10개+ | 없음 | 잠금 미리보기 |
| VIP 개인 (`vip_individual`) | 최대 5개 | 최대 3개 | 10개+ | 없음 | 웹 미노출 |
| VIP 기업 (`vip_business`) | 최대 10개 | 최대 10개 | 10개+ | 없음 | 웹 미노출 |

한도 값의 단일 진실 공급원(source of truth)은 `config/tiers.json`이다. 코드에 숫자를 하드코딩하지
않는다 (CLAUDE.md 코딩 규칙과 동일한 원칙).

VIP 기업은 "구독자 1명"이 아니라 **"고객사 1곳"** 단위의 개인화다. 여러 수신자가 같은 초안을
받는 팀 발송 구조라는 점이 VIP 개인과 다르다.

## 2. 산출물 두 갈래의 구분 (가장 중요한 개념)

같은 `tagged_articles.jsonl`에서 출발하지만, 목적이 다른 두 파이프라인으로 갈라진다.

```
                         data/tagged_articles.jsonl
                                    │
                ┌───────────────────┴───────────────────┐
                ▼                                        ▼
        pipeline/build_news.py                pipeline/build_newsletter.py
        (불특정 다수 방문자용)                    (실제 발송 대상 이메일 본문)
                │                                        │
                ▼                                        ▼
         web/news.json                     data/newsletter_drafts/*.html
     free/premium 2단만 존재                 4개 티어 전부 대응, 회사 섹션 포함
     (VIP는 웹에 안 올림)                     사람 검수 후 스티비에 수동 붙여넣기
```

- **`web/news.json`**: "구독하면 이런 걸 받는다"를 보여주는 마케팅용 미리보기. 구독 여부와
  무관하게 누구나 볼 수 있고, free는 그대로 노출, premium은 잠금 표시만 한다. VIP 두 티어는
  회사 단위로 개인화되기 때문에 이 불특정 다수용 페이지에 노출할 방법이 없다 — 그래서 아예
  다루지 않는다 (`config/tiers.json`의 `web_visibility: "none"`).
- **`build_newsletter.py` 초안**: 실제로 발송될 이메일 본문. 산업뿐 아니라 회사 지정까지 지원하고,
  운영자가 검수·코멘트 추가한 뒤 스티비 에디터에 붙여넣는 걸 전제로 한다.

이 둘의 숫자(산업당 몇 개 뽑는지)가 서로 다른 곳에서 따로 관리되면 언젠가 어긋난다. 그래서
`pipeline/ranking.py`의 랭킹 함수를 두 스크립트가 공유한다.

## 3. 파일 구조

```
dev_claude/
├── SERVICE_DESIGN.md          # 이 문서
├── pipeline/
│   ├── config_loader.py       # BASE_DIR/CONFIG_DIR/DATA_DIR + config/*.json, tagged_articles.jsonl 로더
│   ├── ranking.py             # 산업별 랭킹, 티어별 슬라이싱, 회사명 필터 — build_news/build_newsletter 공유
│   ├── scrape_rss.py          # RSS 수집 (기존, config_loader 사용하도록 수정)
│   ├── tag_articles.py        # LLM 태깅 (기존, config_loader 사용하도록 수정)
│   ├── run_pipeline.py        # 수집 → 태깅 오케스트레이션 (변경 없음)
│   ├── build_news.py          # 태깅 결과 → web/news.json (free/premium만, tiers.json 참조로 변경)
│   ├── build_newsletter.py    # 태깅 결과 → 이메일 초안 (신규, 4개 티어 + 회사 섹션 지원)
│   └── lookup_company.py      # 회사명으로 태깅 기사 검색 CLI (신규, VIP 수동 조립 보조)
├── config/
│   └── tiers.json             # 티어별 한도 정의 (신규)
└── web/pricing.html           # 티어 설명 문구만 최신화 (디자인은 별도 라운드)
```

기존 4개 스크립트는 리네임하지 않았다. `pipeline/`을 더 깊은 하위 폴더로 쪼개는 안도 검토했지만
현재 코드량(스크립트 몇 개, 수백 줄)에는 과설계라 flat 구조를 유지했다.

## 4. `config/tiers.json` 스키마

```json
{
  "tiers": [
    { "id": "free", "label_ko": "무료", "max_industries": 1, "max_companies": 0,
      "news_count_per_industry": 3, "has_ads": true, "status": "open",
      "web_visibility": "public" },
    { "id": "premium", "max_industries": 5, "news_count_per_industry": 10,
      "has_ads": false, "web_visibility": "locked_preview", "...": "..." },
    { "id": "vip_individual", "max_industries": 5, "max_companies": 3,
      "company_digest": true, "web_visibility": "none", "...": "..." },
    { "id": "vip_business", "max_industries": 10, "max_companies": 10,
      "company_digest": true, "web_visibility": "none", "...": "..." }
  ]
}
```

- `max_industries`/`max_companies`는 **지금은 강제 검증이 아니라 참고값**이다. `build_newsletter.py`는
  이 값을 초과하는 `--industries`/`--companies` 인자가 들어오면 경고만 출력하고 그대로 진행한다.
  이유는 아래 5번 항목 참고.
- `company_digest: true`가 없는 티어(free/premium)에 `--companies`를 주면 무시되고 경고가 뜬다.
- `web_visibility`: `build_news.py`가 이 필드로 웹 노출 방식을 판단한다 (`public`/`locked_preview`는
  다루고, `none`인 VIP 두 티어는 애초에 대상에서 제외).

## 5. 구독자 선호 저장 — 스티비 커스텀필드 채택

~~지금 스티비 구독 폼은 이메일만 받는다~~ **✅ 결정 완료 (2026-07-12)**: 옵션 1(스티비
커스텀필드)을 채택했다. `web/index.html`의 스티비 폼에 "구독 산업" 드롭다운 필드(키:
`industry_interest`, 필수 입력)를 추가해 구독 시점에 산업 1개를 고르도록 했다. 별도 백엔드
없이 스티비 주소록에 구독자별로 저장되고, 필요하면 스티비의 세그먼트 기능으로 발송 대상을
나눌 수 있다.

당시 검토했던 두 옵션과 채택 이유:

1. **스티비 커스텀필드/태그만 사용** *(채택)*: 별도 백엔드 없이 스티비 구독 폼에 필드를 추가하는
   것만으로 해결됨. 지금 열려 있는 티어가 무료(산업 1개)뿐이라 단일 선택 드롭다운으로 충분해서,
   구현 난이도 대비 얻는 게 커서 바로 적용했다.
2. **자체 경량 저장소** *(보류)*: 회사 단위 조합처럼 복잡한 로직(VIP 티어)이 필요해지면 다시 검토.
   지금은 프리미엄/VIP가 아직 안 열려 있어 필요 없다.

**남은 제약**: 스티비 폼의 드롭다운은 "1개만" 강제할 수 있어서 무료 티어엔 딱 맞지만, 프리미엄
(최대 5개)·VIP(산업+회사 조합)가 열릴 때는 이 필드로는 부족하다 — 그때 다중 선택 필드 추가 또는
옵션 2 재검토가 필요하다 (11번 TODO 인덱스에 기록).

## 6. VIP 개인화 워크플로우 (수동 조립)

VIP 개인/기업의 회사별 맞춤 뉴스는 초기엔 자동 매칭 파이프라인 없이 **운영자가 직접 조립**한다.
"완전 자동 발행 금지, 사람이 최종 검수" 원칙(CLAUDE.md)과 같은 맥락이고, 구독자가 적은 지금
자동화 비용을 들일 이유가 없다.

순서:

1. 구독자가 지정한 회사 목록 확인 (현재는 저장소가 없으므로 운영자가 별도로 파악·기록)
2. `python pipeline/lookup_company.py "<회사명>"`으로 그 주 태깅된 관련 기사 검색
3. 결과를 보고 수기로 큐레이션 (어떤 기사를 포함할지, 코멘트는 뭐라 쓸지)
4. `python pipeline/build_newsletter.py --tier vip_individual --industries <산업들> --companies <회사들> --week "<주차>"`로 초안 생성
5. 초안 검수 (코멘트 채우기, 배너에 있는 자리표시 제거)
6. 스티비 에디터에 붙여넣어 발송

## 7. `lookup_company.py` 사용법과 한계

```bash
python pipeline/lookup_company.py "레인보우로보틱스"
python pipeline/lookup_company.py "삼성" --limit 5
```

`tagged.companies[]` 필드를 부분일치(대소문자 무시)로 검색한다. **한계**: LLM이 같은 회사를
"삼성전자"와 "삼성전자(Samsung Electronics)"처럼 다르게 태깅할 수 있어 부분일치로도 놓칠 수 있다.

**✅ 완료 (2026-07-12)** — `config/company_aliases.json`에 정식명/별칭 그룹을 등록해두면
`ranking.py`의 `filter_by_company()`가 양방향으로 매칭한다("삼성전자"로 검색해도 "Samsung
Electronics"로 태깅된 기사가 나오고, 그 반대도 동일). `lookup_company.py`와
`build_newsletter.py --companies` 둘 다 이 사전을 자동으로 사용한다. 지금은 잘 알려진 대기업
몇 곳만 예시로 채워둔 상태라, 운영하면서 놓치는 회사가 나오면 그때그때 사전에 추가하면 된다.
이 사전은 "지금 RSS로 수집된 기사 안에서 표기만 다른 걸 찾는" 용도이지, RSS 수집 범위 밖 회사를
찾아주진 못한다 — 그건 8번 항목의 별개 리스크다.

## 8. API 사용/비용 모델과 회사 커버리지 한계

이 프로젝트가 쓰는 유일한 외부 API는 **Anthropic Claude API**다 (`tag_articles.py`, 기사 1건당
1회 호출). 이 섹션 이전까지는 티어 설계가 이 API와 어떤 관계인지 다루지 않았다 — 명시적으로
정리한다.

**티어와 API 비용은 서로 독립적이다.** 태깅은 `config/sources.json`에 정의된 산업별 RSS 소스에서
수집되는 기사 **전체**에 대해, 구독자의 티어·산업 선택과 무관하게 한 번씩 이뤄진다
(`run_pipeline.py` → `tag_articles.py`). 무료 구독자만 있든 VIP 기업 구독자가 생기든, 그 주
태깅 API 호출 수는 똑같다. 티어(`build_news.py`/`build_newsletter.py`)는 이미 태깅된 데이터에서
"얼마나 많이 보여줄지"를 **사후에** 필터링할 뿐이다. 실제 API 비용을 늘리는 변수는 구독자 수나
티어 구성이 아니라 `config/sources.json`에 등록된 소스 개수와 수집 주기다.

**VIP 회사 지정 기능은 새 API 호출을 만들지 않는다 — 그리고 이게 한계다.** `lookup_company.py`와
`build_newsletter.py --companies`는 **이미 태깅된 데이터 안에서만** 회사명을 검색한다. 즉 구독자가
지정한 회사가 현재 산업별 RSS 수집 범위 밖이면(그 언론사가 그 회사를 다루지 않았거나, 애초에
`config/sources.json`에 해당 업종 소스가 없으면) 관련 기사를 전혀 못 찾는다. 이건 VIP의 핵심
가치 제안("내가 지정한 회사 소식")과 직접 부딪힐 수 있는 리스크다.

"회사 전용 검색 API 추가"(아래 2번)는 **하지 않고 인지만 한다** (구독자 0명 단계에서 새 API
붙이는 건 이르다는 5번 항목과 같은 판단). 대신 1번(현재 RSS 커버리지로 버티기)을 보완하는
**회사명 별칭 사전**(`config/company_aliases.json`)은 API 추가 없이 가능한 저비용 개선이라
2026-07-12에 구현했다 — 자세한 내용은 7번 항목 참고.

1. **현재 RSS 커버리지로 버틴다** *(채택, 별칭 사전으로 보완)*: 전자신문 등 이미 수집 중인 소스가
   웬만한 회사를 다뤄줄 거라 전제하고 운영, 놓치는 회사는 VIP 큐레이션 과정에서 운영자가 수동으로
   인지 + `config/company_aliases.json`에 새 표기를 추가.
2. **회사 전용 뉴스 검색 API 추가** *(보류)*: VIP 조회 시점에 네이버 뉴스 검색 API, Google News
   등을 별도로 호출해 커버리지를 보강. 새로운 API 의존성·비용·저작권 확인(`legal_note_ko`와 동일한
   이슈)이 따르므로 지금 범위 밖. 별칭 사전으로도 못 잡는(=RSS에 아예 안 올라온) 회사가 실제로
   반복되면 그때 재검토.

## 9. `pricing.html` 텍스트 정합성 체크리스트

| 카드 | 이전 | 이후 |
|---|---|---|
| 무료 | 관심 산업 여러 개 선택 | 관심 산업 1개 선택 |
| 프리미엄 | 관심 산업 여러 개 선택 | 관심 산업 최대 5개 선택 |
| VIP 개인 | 관심 회사 여러 개 등록 | 관심 회사 최대 3개 등록 |
| VIP 기업 | 회사·산업 맞춤 뉴스 모니터링 | 회사 최대 10개 + 산업 최대 10개 맞춤 모니터링 |

문구만 고쳤고 디자인/CSS/레이아웃은 그대로다. 문구가 길어지며 배지·버튼 줄바꿈이 달라질 수
있는데, 그 조정은 다음 "claude design" 라운드(웹 전체 비주얼 개선)에서 다룬다.

## 10. 엣지 케이스 / 트레이드오프

- **산업당 기사 부족**: 그 주 특정 산업 태깅 기사가 티어 요구 개수보다 적으면 있는 만큼만 출력한다.
  억지로 채우지 않는다.
- **회사명 표기 불일치**: 위 7번 항목 참고. `config/company_aliases.json`으로 부분 완화됐지만,
  사전에 없는 새 표기는 여전히 놓칠 수 있다.
- **무료 "산업 1개" 강제는 지금 시행되지 않는다**: 스티비 폼에 산업 선택 UI 자체가 없어서
  (CLAUDE.md TODO #1), `tiers.json`의 한도는 앞으로 폼이 붙었을 때 참조할 스펙일 뿐이다. 지금
  `build_newsletter.py`를 운영자가 직접 실행하는 단계에서는 한도 초과 시 경고만 뜨고 강제되지 않는다.
- **웹/이메일 숫자 불일치 방지**: `ranking.py` 공용화로 해결한다. 나중에 "웹 미리보기는 마케팅용으로
  더 적게, 이메일은 그대로"처럼 의도적으로 다르게 하고 싶어지면 `tiers.json`에
  `web_teaser_count` 같은 필드를 분리해야 한다 — 지금은 동일하다고 가정하고 시작한다.
- **초안 저장 위치**: `data/newsletter_drafts/`는 `data/`가 이미 `.gitignore` 대상이라 별도 조치
  없이 공개 저장소에 올라가지 않는다.

## 11. 열린 TODO 인덱스

이 문서에서 새로 생긴 TODO만 모았다 (CLAUDE.md의 기존 TODO 6개와 별개).

1. ~~구독자의 산업/회사 선호를 저장할 방식 결정~~ — 완료 (2026-07-12, 5번 항목: 스티비
   커스텀필드 채택)
2. ~~스티비 구독 폼에 산업 선택 UI 추가~~ — 완료 (2026-07-12, 무료 티어용 단일 선택 드롭다운).
   **회사 선택 UI는 아직**(VIP 티어가 열릴 때 필요, 프리미엄의 "산업 최대 5개"도 다중 선택으로
   바꿔야 함 — 5번 항목 "남은 제약" 참고)
3. ~~회사명 별칭 사전~~ — 완료 (2026-07-12, 7번 항목). 다만 사전 자체는 계속 채워나가야 함
4. VIP 구독자 수가 늘어나 수동 조립이 감당 안 될 때 자동 매칭 파이프라인 설계 재검토
5. VIP 회사 검색 API 도입 여부 — 별칭 사전으로도 못 잡는(RSS 수집 범위 밖) 회사가 실제로
   반복될 때 재검토 (8번 항목 2번 옵션)
