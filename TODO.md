# TODO.md

이 파일은 "지금 뭐가 막혀 있고 다음에 뭘 해야 하는지"의 **현재 상태 스냅샷**이다. 새 세션을
시작할 때 전체 대화 기록을 다시 읽는 대신 이 파일부터 확인하면 된다. 작업이 끝나거나 새
블로커가 생기면 이 파일을 그때그때 갱신한다.

- 코드/구조 전반: `CLAUDE.md`
- 작업 단위 프롬프트 모음: `PROMPTS.md`
- 티어 시스템 설계 근거: `SERVICE_DESIGN.md`
- 상세 TODO 백로그(여기선 중복 안 함): `CLAUDE.md`의 "미완성/TODO", `SERVICE_DESIGN.md`의
  "열린 TODO 인덱스"

## 지금 막혀 있는 것

- (없음) ~~재배포 허용 RSS 소스가 하나도 없음~~ — 2026-07-12 해결. 아래 참고.

## 법적/저작권 확인 필요 (첫 호 발행 전, 2026-07-12 추가)

- [x] ~~RSS 재배포 허락 확인~~ — 2026-07-12 완료. 전자신문(etnews) 공식 FAQ에서
  "언론사 허락없이 온라인 뉴스레터를 배포할 수 없다"고 명시적으로 확인함
  (info.etnews.com/sub_2_2.html, 제휴 문의: onbiz@etnews.com / 02-6925-6352). **결정: 지금
  단계에서는 재배포가 허용된 매체만 사용**하기로 함 — `config/sources.json`에
  `redistribution_allowed` 필드를 추가해 강제하도록 코드 반영 완료(위 "지금 막혀 있는 것"
  참고). 전자신문 제휴는 나중에 구독자가 늘어나면 재검토.
- [x] ~~차별화 방안: "취준생/현직자 관점" 필드 추가~~ — 2026-07-12 완료. 다중 소스를 종합
  해석하는 별도 기사 대신(검수 부담이 커짐), 기존 태깅 스키마에 `why_it_matters` 필드를
  추가해 기사 1건의 사실에만 근거한 1~2문장 코멘트를 생성하도록 함(`tag_articles.py`).
  `build_news.py`/`build_newsletter.py`/`web/news.html`에도 반영 완료. 검수 부담은 지금(요약
  정확도 확인)과 동일한 수준으로 유지됨.
- [x] ~~재배포 허용 소스 확보~~ — 2026-07-12 완료. 정부 부처 RSS는 정확한 URL을 검증하지
  못해 보류하고(검색 결과가 부정확했음), 대신 **뉴스와이어(newswire.co.kr)** — 기업이 보도
  자료를 배포하려고 올리는 서비스 — RSS로 전환. 저작권 안내(newswire.co.kr/?od=302)에서
  "보도자료와 사진, 영상을 대중에게 널리 알리기 위한 목적으로 이용할 수 있다"고 명시적으로
  확인함. 조건: (1) 재배포 시 "뉴스와이어" 크레딧 + 보도자료 출처 기업명 표시 필수,
  (2) **하루 5건 이상 대량 이용 시 별도 허락 필요**(02-737-3600, 아직 안 받음 — 발행량이
  이 한도를 넘지 않는지 운영자가 계속 확인할 것). `config/sources.json`의 10개 산업 전부에
  검증된 뉴스와이어 RSS URL 등록 완료(총 15개 피드, 전부 직접 fetch로 유효성 확인).
  `scrape_rss.py`로 실제 수집 테스트 결과 184건 정상 수집됨.
- **결정 (2026-07-12): 지금은 무료 티어만 신경 쓰고 프리미엄/VIP는 무시한다.** 프리미엄
  (`config/tiers.json`의 `pricing.html` 상태도 아직 "곧 오픈"이라 실제 구독자도 없음)은
  나중에 열 때 다시 고려. 이 결정은 뉴스와이어 "하루 5건 이상 대량 이용" 기준과도 맞물림 —
  무료 티어는 산업당 3건(총 10개 산업 × 3 = 30건/주, 하루 평균 4.3건)이라 프리미엄(산업당
  10건, 하루 평균 14건)보다 그 기준에 훨씬 가깝게 유지됨. `build_news.py`/
  `build_newsletter.py`는 코드 변경 없이 그대로 쓰되, `build_newsletter.py`는 당분간
  `--tier free`만 실행할 것.
- [x] ~~뉴스와이어 소스로 A-2 재검증~~ — 2026-07-12 완료. robot 산업 3건 태깅, 전부 성공.
  지난번(전자신문)과 달리 **중복 없이 서로 다른 사건 3건**이 수집됨. `why_it_matters` 필드도
  기사 1건의 사실에만 근거해서 정상 생성되는 것 확인. 이걸로 실제 소스 전환 검증 끝 —
  `data/tagged_articles.jsonl`에는 이제 전자신문 5건(폐기 대상) + 뉴스와이어 3건(사용 가능)이
  섞여 있으니, 다음에 news.json/뉴스레터를 만들 때는 전자신문 5건을 걸러내거나
  `data/tagged_articles.jsonl`을 초기화하고 뉴스와이어로만 다시 전체 수집·태깅할 것.
- [x] ~~전체 파이프라인 1차 실행 + `build_news.py` 검증~~ — 2026-07-12 완료.
  `tagged_articles.jsonl`/`processed_urls.json` 초기화 후 `run_pipeline.py`로 10개 산업 전체
  재수집·재태깅 시작했으나, 테스트 목적이라 76건에서 중단(184건 전부는 안 함). 예상대로
  robot/embedded_iot/semiconductor/automation_factory/ai_software 5개 산업은 자기 소스에서
  직접 수집돼 충실하고, mobility/ecommerce_platform/biotech/fintech/battery_energy 5개는
  자기 소스가 아직 처리 안 돼 부수 태깅만 1~4건. **테스트라 이대로 진행하기로 결정.**
  `build_news.py --week "2026년 7월 2주"` 실행 결과: 무료 25건 / 프리미엄 36건 생성.
  `why_it_matters` null 폴백(모델이 확신 없을 때) 정상 작동 확인.
  **새로 발견한 문제**: 뉴스와이어가 같은 보도자료를 한글판/영문판 둘 다 게시하는 경우가
  있어서, 산업당 3건 한도 안에 같은 사건의 한글판+영문판이 동시에 들어가 자리를 차지하는
  사례 발견(예: [embedded_iot] "마이크로소프트, 시스벨 Wi-Fi..." 한글판 + "Microsoft Takes
  Sisvel..." 영문판). 지난번 발견한 "같은 사건 중복 게재" 문제의 변종 — 실제 발행 전
  `cluster_id`(또는 최소한 "같은 산업 내 유사 요약/한영 중복 필터링") 작업 때 같이 처리할 것.
- [x] ~~`build_newsletter.py` 인코딩 버그 수정~~ — 2026-07-12 완료. `--tier free --week
  "2026년 7월 2주"` 실행 중 배너의 이모지(⚠️)를 Windows 콘솔(cp949)이 출력 못 해서
  `UnicodeEncodeError`로 크래시남 (파일 저장 자체는 성공했지만 스크립트가 트레이스백을
  뿌리며 비정상 종료됐음). `main()` 시작 시 `sys.stdout.reconfigure(encoding="utf-8",
  errors="replace")`로 수정, exit code 0 정상 종료 확인. 무료 티어 이메일 초안 생성 완료
  (`data/newsletter_drafts/2026년_7월_2주_free.html`) — 배너/검수 안내/코멘트 자리표시
  전부 정상. 여기서도 위에서 발견한 한영 중복 문제가 그대로 드러남(임베디드/IoT 섹션에
  Wi-Fi 특허 기사 한글판+영문판이 동시에 들어감).
- [ ] **"(광고)" 표시 여부 확인.** 무료 티어(`config/tiers.json`의 `has_ads: true`)에 광고 섹션이
  포함되는데, 정보통신망법상 영리목적 광고성 정보는 제목에 "(광고)" 표시가 필요할 수 있음.
  구독 동의 기반 뉴스레터 내 광고 섹션이라 회색지대에 가까우나, 스티비 고객센터 또는 간단한
  법률 자문으로 해당 여부를 확인해둘 것. (법률 블로그 다수의 공통된 의견: 타사 광고를 포함한
  뉴스레터는 전체가 광고성 정보로 취급되는 게 원칙 — https://platum.kr/archives/151907 등)

## 다음 액션 (순서대로)

0. [x] ~~(사용자) 스티비 구독 폼 실제 제출 테스트~~ (2026-07-12 완료, 정상 동작 확인)
1. [x] ~~(사용자) console.anthropic.com에서 API 크레딧 충전~~ (2026-07-12 완료)
2. [x] ~~A-2 마무리 — 테스트 모드(RSS 1~2개 소스)로 수집+태깅 실행, 결과 5건 검수~~ (2026-07-12
      완료. robot 산업 1개 RSS(전자신문)로 신규 5건 태깅, 전부 성공. industries/event_type/
      sentiment 분류 타당, summary 자체 재서술 확인(저작권 요건 충족). **발견한 문제**: 태깅한
      5건이 전부 "KETI 물류 휴머노이드 VLA 기술" 관련 동일 사건의 포토 뉴스가 제목만 살짝
      바뀐 채 반복 게재된 것이었음 — 전자신문이 같은 사진 기사를 여러 번 올리는 경우가 실제로
      있다는 뜻. `CLAUDE.md`에 미구현으로 적혀있던 `cluster_id`(같은 사건 중복 기사 묶기)가
      이론상 리스크가 아니라 **실제로 바로 터지는 문제**임을 확인. 지금 당장 고치지는 않고
      기록만 해둠 — 이대로 발행하면 뉴스레터에 같은 내용이 여러 번 나열되고 태깅 비용도
      낭비되니, 실제 정식 발행 파이프라인 돌리기 전(A-2 이후 다음 단계)에 최소한 "같은 배치
      내 제목 유사 기사 필터링" 정도의 간단한 완화책은 넣는 걸 권장.
      **주의(2026-07-12 추가)**: 이 5건은 전자신문 RSS로 수집한 것인데, 같은 세션에서 전자신문
      재배포가 불허임을 확인해 이후 소스를 비활성화했음. `data/tagged_articles.jsonl`에 남아있는
      이 5건은 **테스트용일 뿐 실제 발행(뉴스레터/news.json)에는 쓰면 안 됨** — 재배포 허용
      소스가 확보되면 그걸로 다시 수집·태깅해야 함.
3. [x] ~~A-4 — 스티비 구독 폼 연결~~ (2026-07-12 완료, 아래 참고)
4. [x] ~~B-1 — 로컬에서 5개 페이지 확인~~ (2026-07-12 완료, 아래 참고)
5. [x] ~~B-2 — GitHub Pages 배포~~ (2026-07-12 완료, 아래 참고)
6. [x] ~~C-1 — RSS 파싱 견고화~~ (2026-07-12 완료, 아래 참고)
7. [x] ~~C-5 — 회사명 매칭 품질 개선(별칭 사전)~~ (2026-07-12 부분 완료, 아래 참고)

8. [x] ~~privacy.html 빈칸 채우기~~ (2026-07-12 완료, 아래 참고)

크레딧 충전 전까지는 A-2(태깅 필요)만 대기 상태. 다른 진행 가능한 작업 남은 게 없으면
이제 크레딧 충전이 사실상 유일한 블로커.

## 최근 완료 (2026-07-12)

- [x] 개발환경: Python 3.14.6 설치, `venv/` 생성, `anthropic`/`python-dotenv` 설치
- [x] `.env` + `config_loader.py`가 자동으로 `.env`를 로드하도록 연결 (API 키 인증 확인됨,
  크레딧 부족으로 실제 응답은 못 받음)
- [x] etnews RSS(`rss.etnews.com/04.xml`) 실 fetch로 구조 확인 — `scrape_rss.py` 파싱 로직과
  정확히 일치, 50건 정상 파싱 (인코딩은 정상이며 터미널 출력이 깨져 보였던 것뿐)
- [x] 티어 시스템 설계·구현: `config/tiers.json`, `pipeline/ranking.py`, `pipeline/config_loader.py`,
  `pipeline/build_newsletter.py`(신규), `pipeline/lookup_company.py`(신규), `SERVICE_DESIGN.md`(신규)
- [x] `web/pricing.html` 티어 설명 문구를 새 로직(산업/회사 개수 한도)에 맞게 수정 (디자인은 불변)
- [x] `PROMPTS.md`에 A-1/A-3 완료 표시, `SERVICE_DESIGN.md` TODO를 반영한 C-4/C-5/D-3 프롬프트 추가
- [x] `CLAUDE.md`를 새 파일 구조/티어 표/문서 참조로 갱신
- [x] B-1 — 로컬 서버(`python -m http.server`)로 5개 페이지 headless 스크린샷 확인. 내비게이션·
  `pricing.html`의 새 문구(레이아웃 안 깨짐)·`news.html`의 프리미엄 잠금 뱃지 정상 표시 확인.
  필터 칩/탭 전환은 코드 리뷰로 검증(이번 세션에서 `news.html`은 수정 안 해서 기존 동작 그대로)
- [x] C-1 — `scrape_rss.py`에 `content:encoded` 파싱, pubDate ISO 8601 정규화, 짧은 본문
  스킵, 지수 백오프 재시도, 소스별 로그 반영. 실제 etnews 피드 + 합성 XML로 검증
- [x] C-5(부분) — `config/company_aliases.json` 신설, `ranking.py`의 `filter_by_company()`가
  정식명/별칭 양방향 매칭 지원. `lookup_company.py`/`build_newsletter.py` 둘 다 자동 적용,
  합성 데이터로 양방향 매칭 + 미등록 회사는 기존 부분일치 유지 검증. RSS 수집 범위 밖 회사를
  못 찾는 문제(원래 이유 2번)는 여전히 미해결 — "의도적으로 미룬 것" 참고
- [x] A-4 — 스티비 임베드 코드를 `web/index.html`에 연결 (폼 구조·검증 스크립트는 원본 유지,
  버튼 색상만 사이트 accent로 오버라이드). 로컬 렌더링 + 외부 리소스 응답 확인. **실제 이메일
  제출 테스트는 사용자가 직접 해봐야 함** (아래 "다음 액션" 참고)
- [x] 구독자 선호 저장 방식 결정 — 스티비 커스텀필드 채택. 스티비 폼에 "구독 산업" 단일 선택
  드롭다운 필드(키: `industry_interest`, 필수) 추가 완료. `SERVICE_DESIGN.md` 5번 항목 갱신.
  **주의**: 필드 추가 과정에서 주소록(list) URL이 `tVCuKP...` → `jLnDHB...`로 바뀜 — 처음
  테스트 구독했던 이메일이 있다면 다른 주소록에 들어가 있을 수 있음 (사용자가 확인 필요)
- [x] B-2 — 저장소를 git으로 초기화하고(비밀키 없음 확인 후 커밋)
  `https://github.com/littlecub125/newsletter_industry_update`(public)에 푸시. `web/` 폴더만
  `git subtree push --prefix web origin gh-pages`로 분리 배포, Settings → Pages에서 `gh-pages`
  브랜치 활성화. 실사이트(`https://littlecub125.github.io/newsletter_industry_update/`)에서
  index(스티비 폼)·news(필터/뉴스 목록) 페이지 headless 스크린샷으로 정상 동작 확인
  (`news.json` fetch 포함 — 첫 스크린샷은 fetch 완료 전이라 비어 보였는데, 대기시간을 주니
  정상이었음, 진짜 버그 아니었음)
- [x] `.claude/skills/instagram-post` 스킬 신설 — 작업 내용을 인스타 포스팅용 사진/캡션/
  해시태그로 정리해주는 스킬. 이후 요청으로 릴스용 무음 영상(ffmpeg, 자막 포함) + 녹음 대본
  제작 단계도 추가(TTS 미사용, 사용자 직접 녹음 전제), 콘텐츠 확정 전 사용자에게 항상 확인하는
  단계도 추가. `instagram_posts/`는 마케팅 초안이라 gitignore 처리
- [x] privacy.html 빈칸 채우기 — 책임자 김유빈, 문의 이메일 yubi2023@gmail.com으로 채움.
  이제 없는 플레이스홀더용 안내 문구/CSS도 같이 정리. 로컬 렌더링 확인 후 배포까지 반영
- [x] `redistribution_allowed` 플래그 도입 — `config/sources.json`의 모든 소스에 재배포 허가
  여부 필드 추가(etnews는 전부 false), `scrape_rss.py`가 이 필드를 강제하도록 수정. 위
  "지금 막혀 있는 것" 참고
- [x] `why_it_matters` 필드 추가 — `tag_articles.py` 프롬프트/스키마, `build_news.py`,
  `build_newsletter.py`, `web/news.html`, `CLAUDE.md` 문서까지 전부 반영. 기사 1건의 사실에만
  근거하도록 프롬프트에 명시해 검수 부담 증가를 최소화

## 의도적으로 미룬 것

- **VIP 회사 검색 커버리지 문제**: 현재 RSS 수집 범위 밖 회사는 못 찾음. 회사 전용 뉴스 검색
  API 도입은 TODO로만 남김 (`SERVICE_DESIGN.md` 8번 항목).
- **프리미엄/VIP용 다중 산업·회사 선택 UI**: 지금 스티비 폼은 무료 티어에 맞춘 산업 1개
  단일 선택만 지원. 프리미엄(최대 5개)·VIP(산업+회사 조합)가 열리면 필드를 다시 설계해야 함
  (`SERVICE_DESIGN.md` 5번 항목 "남은 제약").
- **웹 비주얼 디자인 개선("claude design")**: 서비스 로직·첫 호 발행이 끝난 뒤 별도 라운드로
  진행하기로 함. 지금은 문구만 최신화하고 CSS/레이아웃은 그대로 둔다.
- **저장소 분리(소스코드/전략 문서 비공개화)**: 지금 GitHub 저장소는 `master`(전체 소스,
  `pipeline`/`config`/`SERVICE_DESIGN.md` 포함)까지 전부 public이라 코드·전략 문서가 다 보인다
  (비밀키는 `.env`가 `.gitignore`에 있어 안전, 이건 소스코드 노출과는 별개 문제). 비즈니스
  필수는 아니라고 판단해 지금은 미룸 — **구독자가 늘어나면** `web/`만 남긴 public 저장소와
  `pipeline`/`config`/설계 문서용 private 저장소(또는 로컬 전용)로 분리할 것 (2026-07-12 결정).
