# SEO_CHECKLIST.md (검색 노출 구현 체크리스트 · dev 작업공간 소유)

이 문서는 뉴스레터 웹사이트(`web/`)의 검색 노출 **구현** 체크리스트다. `newsletter_claude`
(dev 작업공간)가 소유한다. 왜 이 순서로 하는지, 어떤 키워드를 노릴지 같은 전략은 이 문서가
아니라 `../business_claude/SEO_STRATEGY.md`(business 작업공간 소유)에 있다 — 방향이
바뀌면 그 문서가 먼저 갱신되고, 이 체크리스트는 그에 따라 실행한다.

지금 상태(2026-07-12 기준): 5개 페이지 모두 `<meta charset>`, `<meta viewport>`,
`<title>`만 있고 **meta description, Open Graph, canonical, robots.txt, sitemap.xml이
전부 없다.** 아래 순서대로 채운다.

## A. 기본 메타 태그 (5개 페이지 전부, 최우선)

각 페이지 `<head>`에 추가:

```html
<meta name="description" content="{페이지별 1~2문장, 155자 내외}" />
<link rel="canonical" href="https://littlecub125.github.io/newsletter_industry_update/{파일명}" />
<meta property="og:title" content="{title과 동일하거나 축약}" />
<meta property="og:description" content="{meta description과 동일}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://littlecub125.github.io/newsletter_industry_update/{파일명}" />
<meta property="og:locale" content="ko_KR" />
<meta name="twitter:card" content="summary" />
```

페이지별 description 초안 (실제 반영 시 `../marketing_claude/STYLE_GUIDE.md` 톤 기준으로
다듬을 것 — 문구 검토는 marketing-agent에게 확인받는다):

| 페이지 | description 방향 |
|---|---|
| `index.html` | 핵심 가치 제안 그대로 — "관심 산업 뉴스를 매주 한 통으로 받아보는 뉴스레터" |
| `news.html` | "산업별 주요 뉴스를 매주 정리해 무료로 공개합니다" (공개 아카이브라는 점 강조) |
| `pricing.html` | 티어 구조 요약 — "무료부터 VIP까지, 필요한 만큼 산업·회사 뉴스를 받아보세요" |
| `about.html` | 서비스 소개/운영 철학 요약 |
| `privacy.html` | "개인정보 수집·이용 안내" (검색 노출 우선순위 낮음, 형식만 갖춰도 충분) |

**og:image는 지금 만들지 않는다** — 대표 이미지가 아직 없고(`DESIGN_GUIDE.md`가 정식
디자인이 아니라고 명시한 것과 같은 이유), 없는 이미지 경로를 넣으면 오히려 깨진 링크
미리보기가 생긴다. 정식 디자인/로고가 나오면 그때 추가한다.

## B. `robots.txt` / `sitemap.xml` (`web/` 루트에 신규 생성)

`robots.txt` 예시:
```
User-agent: *
Allow: /

Sitemap: https://littlecub125.github.io/newsletter_industry_update/sitemap.xml
```

`sitemap.xml`은 5개 정적 페이지를 등록한다. `news.html`은 매주 내용이 바뀌므로
`changefreq: weekly`로 표시:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://littlecub125.github.io/newsletter_industry_update/index.html</loc></url>
  <url><loc>https://littlecub125.github.io/newsletter_industry_update/news.html</loc><changefreq>weekly</changefreq></url>
  <url><loc>https://littlecub125.github.io/newsletter_industry_update/pricing.html</loc></url>
  <url><loc>https://littlecub125.github.io/newsletter_industry_update/about.html</loc></url>
</urlset>
```
(`privacy.html`은 굳이 sitemap에 안 넣어도 된다 — 검색 노출 필요 없는 페이지.)

이 두 파일도 `git subtree push --prefix web origin gh-pages`로 같이 배포해야 실제
반영된다 (`CLAUDE.md` "배포" 섹션과 동일한 함정).

## C. `news.html`의 클라이언트 렌더링 이슈 (중요, 구현 난이도 있음)

`news.html`은 뉴스 목록을 `fetch("news.json")`으로 **클라이언트 사이드에서** 그린다
(`web/news.html:165`). 구글은 JS를 렌더링하긴 하지만 크롤 예산이 제한적이고 렌더링이
지연될 수 있어, 이 페이지의 실질적인 콘텐츠(기사 제목·요약)가 색인에 늦게 잡히거나
누락될 위험이 있다. 이 서비스의 SEO 가치 대부분이 이 페이지(주기적으로 새로워지는
산업별 뉴스)에서 나온다는 점을 감안하면 우선순위가 높은 문제다.

- **당장은 A/B(메타 태그·sitemap)만으로 충분** — 지금 콘텐츠 볼륨(주 1회 발행, 티어당
  소수 기사)에서는 과한 엔지니어링이다.
- 구독자/트래픽이 늘어 이 문제가 실제 병목으로 확인되면, `build_news.py`가 `news.json`과
  함께 **정적 HTML(또는 각 주차별 정적 스니펫)도 같이 생성**하는 방향을 검토한다 (완전한
  SSR 프레임워크 도입 대신, 지금의 "빌드 도구 없는 정적 사이트" 원칙과 맞는 최소 확장).
  이 판단은 business-agent와 먼저 우선순위를 맞춘 뒤 진행한다.

## D. 기타 (우선순위 낮음, 나중에)

- `<html lang="ko">`는 이미 전 페이지 적용돼 있음 — 유지만 하면 됨.
- Google Search Console 등록은 **첫 호 발행 이후**, 실제 콘텐츠가 쌓인 뒤에 진행한다
  (빈 사이트를 먼저 등록해도 이득이 적음).
- 구조화 데이터(JSON-LD, `NewsArticle`/`Organization` 스키마)는 콘텐츠·트래픽이 어느
  정도 쌓인 뒤 고려한다. 지금 단계에서는 A/B 항목이 훨씬 비용 대비 효과가 크다.
