# DESIGN_GUIDE.md (비주얼 디자인 토큰 · dev 작업공간 소유)

이 문서는 웹사이트(`web/`)의 **비주얼 디자인 토큰** 기준이다. `dev_claude`(dev
작업공간)가 소유하며, 새 페이지/컴포넌트를 추가할 때 먼저 확인한다.

- 카피 톤/말투 기준은 이 문서가 아니라 `../marketing_claude/STYLE_GUIDE.md`(marketing
  작업공간 소유)에 있다 — 이 문서는 색상·타이포그래피 등 시각 요소만 다룬다.
- `CLAUDE.md`: 프로젝트 전반 오리엔테이션
- `SERVICE_DESIGN.md`: 티어 구조 설계 근거
- `SEO_CHECKLIST.md`: 검색 노출 구현 체크리스트

> **주의**: `CLAUDE.md`에 "디자인은 임시, 나중에 갈아끼울 예정"이라고 명시돼 있다. 이
> 문서는 **지금 웹사이트에 실제로 쓰이고 있는 값**을 그대로 기록한 것이지, "이렇게 가야
> 한다"고 새로 정한 디자인 시스템이 아니다. 목적은 5개 페이지 간 비주얼 일관성을 지금
> 수준에서라도 깨지지 않게 하는 것이다. 디자인을 정식으로 갈아엎는 라운드가 오면 이
> 문서를 그때 다시 쓴다.

## 색상

`web/index.html`, `news.html`, `pricing.html`, `about.html`, `privacy.html`은 동일한
CSS 변수와 내비게이션 구조를 공유한다. 새 색상을 임의로 추가하지 말고 아래 팔레트 안에서
해결한다.

```css
--bg: #ffffff;          /* 배경 */
--text: #1a1a1a;        /* 본문/제목 텍스트 */
--text-muted: #666666;  /* 보조 텍스트 */
--accent: #2563eb;      /* 브랜드 강조색 (CTA, 링크, 체크 아이콘) */
--accent-hover: #1d4ed8;/* accent hover 상태 */
--border: #e5e7eb;      /* 카드/구분선 테두리 */
--surface: #f9fafb;     /* 카드 배경, 비활성 배지 배경 */
```

배지(badge) 색상 (`pricing.html`의 상태 표시):
```css
.badge-open  { background: #dcfce7; color: #166534; } /* 지금 오픈 (초록) */
.badge-soon  { background: #fef9c3; color: #854d0e; } /* 곧 오픈 (노랑) */
.badge-prep  { background: var(--surface); color: var(--text-muted); } /* 준비 중 (회색) */
```

정말 새 색이 필요하면(예: 배지 상태 추가) 기존 배지 패턴(연한 배경 + 진한 텍스트)을
따른다.

## 타이포그래피

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  "Helvetica Neue", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
line-height: 1.6;
```

웹폰트를 새로 불러오지 않는다 (시스템 폰트 스택 유지 — 로딩 속도, 의존성 없음 원칙과
일치, `CLAUDE.md`의 "빌드 도구 없음" 규칙 참고).

| 용도 | 크기 | 굵기 | letter-spacing |
|---|---|---|---|
| 페이지 H1 | 34~40px | 800 | -0.03em |
| 섹션 H2 | 24px | 700 | -0.02em |
| 카드 제목(H3) | 16~20px | 700 | - |
| 본문 | 14~18px | 400 | - |
| 보조 텍스트 | 13~15px | 400, `--text-muted` | - |
| 로고/내비 | 20px / 15px | 700 / 400 | -0.02em |

모바일(`max-width: 640px`)에서는 H1을 30px로 줄이고, 3열 그리드는 1열로 전환한다.

## 레이아웃

- 컨테이너 최대 너비: 본문 위주 페이지(`index.html`, `about.html`, `privacy.html`)는
  `720px`, 그리드가 있는 페이지(`pricing.html`, `news.html`)는 `960px`.
- 카드/버튼 radius: 큰 카드(구독 박스, 요금제 카드) `12~14px`, 버튼/뱃지는 `8px`, 필터
  칩·뱃지는 `999px`(완전 원형).
- 카드: `border: 1px solid var(--border)` + 필요 시 `background: var(--surface)`.
  강조 카드(추천 요금제 등)는 `border-color: var(--accent); border-width: 2px`.
- 레이아웃 구조(컨테이너 너비, 헤더 구조)는 정식 리디자인 전까지 임의로 바꾸지 않는다.

## 내비게이션 (공통 구조)

모든 페이지가 동일한 헤더를 쓴다: 좌측 로고(`뉴스레터`) + 우측 `뉴스 / 요금 / 소개 /
구독하기(CTA 버튼)`. 현재 페이지는 `.nav-links a.active`로 굵게 표시. 새 페이지를
추가하면 5개 페이지 전부의 내비게이션에 링크를 동시에 추가해야 한다 (하나만 고치고
나머지를 빠뜨리지 않도록 주의 — `CLAUDE.md` 코딩 규칙과 동일한 함정).
