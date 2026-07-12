---
name: deploy
description: web/ 변경사항을 실제 GitHub Pages 사이트(https://littlecub125.github.io/newsletter_industry_update/)에 반영한다. master 커밋 + git subtree push 2단계를 빠뜨리지 않게 하고, 배포 후 실제 사이트를 스크린샷/fetch로 확인한다. "배포해줘", "사이트에 반영해줘", "gh-pages에 올려줘", "웹사이트 업데이트해줘" 같은 요청에 사용.
---

# 배포 (web/ → GitHub Pages)

이 프로젝트는 `web/` 폴더만 `git subtree`로 별도 `gh-pages` 브랜치에 분리 배포한다
(`CLAUDE.md` "배포" 섹션 참고). **`master`에 커밋만 하고 subtree push를 빠뜨리는 게
가장 흔한 실수**이므로, 이 스킬은 항상 두 단계를 순서대로 확인하며 진행한다.

## 1. 배포 전 확인

1. `git status`로 `web/` 하위에 반영 안 된 변경이 있는지 확인한다. 커밋 안 된 변경이
   있으면 무엇이 바뀌었는지 사용자에게 요약해서 보여준다.
2. `web/`가 아닌 다른 변경(파이프라인 코드, config 등)이 같이 섞여 있으면, 이번 배포와
   무관한 변경까지 같이 커밋하는 게 맞는지 확인한다 — 배포 요청은 보통 `web/` 반영이
   목적이므로, 무관한 변경은 별도 커밋으로 분리하는 게 나을 수 있다.

## 2. master에 커밋

이 저장소는 **public GitHub 저장소**다. 커밋하기 전에 `.env`, API 키 등 비밀 정보가
섞여 들어가지 않는지 `git status`/`git diff`로 다시 확인한다 (`.gitignore`가 `.env`를
막고 있지만, 실수로 다른 파일에 키를 하드코딩했을 가능성까지 체크).

```bash
git add -A
git commit -m "..."
```

커밋 메시지는 이번에 `web/`에서 뭐가 바뀌었는지 한 줄로 요약한다.

## 3. gh-pages로 subtree push

```bash
git subtree push --prefix web origin gh-pages
```

- 이 명령은 **원격(GitHub)에 실제로 push**하는 동작이다 — 실행 전에 사용자에게 진행해도
  되는지 확인한다 (사용자가 "배포해줘"라고 명시적으로 요청한 경우 이 확인은 생략해도
  된다).
- 실패하면(예: 히스토리 충돌) 강제 push(`git push -f`)로 바로 넘어가지 않는다. 에러
  메시지를 사용자에게 보여주고, 원인(예: `gh-pages` 브랜치가 로컬에 없어서 첫 push인
  경우 vs 이미 있는 브랜치와 충돌하는 경우)을 확인한 뒤 사용자와 상의해서 진행한다.

## 4. 배포 확인

- 배포는 GitHub Pages 반영까지 수 분 걸릴 수 있다. 바로 확인이 안 되면 잠시 후 다시
  확인한다고 안내한다.
- 실제 배포된 사이트(`https://littlecub125.github.io/newsletter_industry_update/`)에서
  바뀐 부분이 반영됐는지 확인한다. 방법:
  - 간단히는 `curl`/`WebFetch`로 해당 페이지를 가져와 바뀐 텍스트가 보이는지 확인.
  - 시각적 확인이 필요하면 `.claude/skills/instagram-post`(marketing_claude 소유)가
    쓰는 것과 같은 방식으로 PowerShell + Edge 헤드리스 스크린샷을 찍어 Read 도구로
    직접 열어본다 (`--window-size=480,<세로값> --virtual-time-budget=8000`).
- `news.html`처럼 `fetch("news.json")`으로 비동기 로딩하는 페이지는 `--virtual-time-budget`을
  충분히 주지 않으면 빈 화면으로 찍힌다 — 확인 시 이 점을 감안한다.

## 5. 마무리

배포가 끝나면 사용자에게 실제 반영된 URL과 확인한 내용을 요약해서 보여준다. `TODO.md`
갱신이 필요하면(예: 새로운 완료 항목) 사용자에게 갱신할지 물어본다.
