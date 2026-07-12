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

- [ ] **Anthropic API 크레딧 미충전.** `.env`에 `ANTHROPIC_API_KEY` 설정 완료, 인증도 확인됐지만
  console.anthropic.com 계정에 크레딧이 없어 `anthropic.BadRequestError`(잔액 부족)로 실패한다.
  사용자가 "나중에 충전하겠다"고 함 (2026-07-12). **Plans & Billing에서 충전 전까지 실제 태깅
  API 호출이 필요한 모든 작업(A-2 이후)은 대기.**

## 다음 액션 (순서대로)

0. [x] ~~(사용자) 스티비 구독 폼 실제 제출 테스트~~ (2026-07-12 완료, 정상 동작 확인)
1. [ ] (사용자) console.anthropic.com에서 API 크레딧 충전
2. [ ] A-2 마무리 — 테스트 모드(RSS 1~2개 소스)로 수집+태깅 실행, 결과 5건 검수
      (RSS 구조가 scrape_rss.py 파싱 로직과 일치함은 이미 실 fetch로 확인 완료, 태깅만 남음)
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
