---
name: instagram-post
description: 뉴스레터 프로젝트에 새로 추가된 작업 내용을 정리해서 인스타그램 포스팅용 사진(모바일 세로 비율 스크린샷)과 캡션+해시태그를 준비한다. 실제 업로드는 하지 않는다. "인스타 포스팅 준비해줘", "인스타에 올릴 거 만들어줘", "빌드로그 포스팅 만들어줘" 같은 요청에 사용.
---

# 인스타그램 포스팅 준비

이 스킬은 최근 작업 내용을 요약해 인스타그램에 올릴 **사진(스크린샷)**과 **캡션 텍스트(해시태그
포함)**를 준비한다. Instagram API 연동은 하지 않는다 — 사용자가 결과물을 보고 직접 앱에서
올리는 것을 전제로 한다.

## 1. 무엇이 새로 추가됐는지 파악

1. `TODO.md`의 "최근 완료" 섹션에서 가장 최근 날짜 블록을 읽는다. 이 프로젝트는 작업할 때마다
   이 섹션에 완료 항목을 기록해두므로, 여기서 "이번에 뭘 했는지"를 바로 파악할 수 있다.
2. `instagram_posts/.last_post_commit` 파일이 있으면 그 안의 커밋 해시 이후 `git log --oneline`을
   같이 참고해서, 이미 포스팅했던 내용과 겹치지 않게 한다. 파일이 없으면(첫 실행) TODO.md의
   최신 완료 블록 전체를 대상으로 삼는다.
3. 범위가 애매하면(예: "최근"이 어디부터인지 불분명하면) 사용자에게 짧게 확인한다.

## 2. 스크린샷 준비 (모바일 세로 비율, 카드/섹션 단위로 분할)

**한 장짜리 풀페이지 스크린샷을 그대로 쓰지 말 것.** 인스타 피드는 세로 비율이 4:5 정도까지만
잘 보이는데, 페이지 전체를 한 장으로 찍으면 훨씬 더 길어서 피드에서 위아래가 잘려 보인다.
그렇다고 고정 픽셀 간격(예: 600px마다)으로 기계적으로 잘라도 안 된다 — 카드나 문장 중간이
잘려서 이미지 한 장만 보면 무슨 내용인지 이해가 안 되는 문제가 있었다 (2026-07-12에 실제로
겪음). **반드시 카드/섹션 경계에서만 잘라야 한다.**

### 2-1. 전체 페이지 스크린샷 먼저 확보

- 배포된 사이트(`https://littlecub125.github.io/newsletter_industry_update/`)를 대상으로,
  이번 작업과 관련 있는 페이지 위주로 스크린샷을 찍는다. 배포가 최신 상태인지 확실하지 않으면
  먼저 `git log`로 마지막 커밋과 `gh-pages` 배포 시점을 확인하거나, 로컬 서버(`python -m
  http.server`, `web/` 폴더)를 대신 써도 된다.
- PowerShell + Edge 헤드리스로 캡처한다. **`--window-size`의 너비는 480을 쓸 것** — 430처럼
  실제 모바일 뷰포트 값을 그대로 넣으면 헤드리스 캡처 특성상 우측이 잘리는 문제가 있었다.
  480이면 잘림 없이 깔끔하게 나온다.
  ```powershell
  $edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
  & $edge --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 `
    --window-size=480,<세로값> --virtual-time-budget=8000 --screenshot="<출력경로>.png" "<URL>"
  ```
  - `<세로값>`은 페이지 실제 콘텐츠보다 넉넉하게 크게 잡는다 (예: 2400~2800). 모바일에서는
    카드/그리드가 세로로 쌓여서 데스크톱보다 훨씬 길어진다 — 너무 작게 잡으면 뒷부분(하단 카드,
    푸터)이 통째로 안 찍힌다. 일단 크게 찍고, 아래쪽 여백이 많으면 자를 때 버리면 된다.
  - `--virtual-time-budget=8000`은 `fetch("news.json")` 같은 비동기 로딩이 끝날 시간을 준다.
    이걸 빼먹으면 뉴스 목록이 빈 채로 찍힌다.
  - 풀페이지 스크린샷은 `instagram_posts/<날짜>/full_page/`에 저장한다 (최종 포스팅용이
    아니라 자르기 위한 원본이므로 별도 폴더로 구분).

### 2-2. 흰 여백을 스캔해서 카드/섹션 경계 찾기

고정 간격으로 자르지 말고, 이미지에서 "완전히 흰 줄(카드 사이 여백)"이 넓게 이어지는 지점을
찾아서 그 지점을 자르는 기준으로 삼는다. PowerShell + System.Drawing으로 스캔한다:

```powershell
Add-Type -AssemblyName System.Drawing
function Find-Gaps($path, $minGapHeight) {
  $img = New-Object System.Drawing.Bitmap $path
  $w = $img.Width; $h = $img.Height
  $isWhiteRow = New-Object bool[] $h
  for ($y = 0; $y -lt $h; $y++) {
    $white = $true
    for ($x = 0; $x -lt $w; $x += 8) {
      $p = $img.GetPixel($x, $y)
      if ($p.R -lt 250 -or $p.G -lt 250 -or $p.B -lt 250) { $white = $false; break }
    }
    $isWhiteRow[$y] = $white
  }
  $gaps = @(); $start = -1
  for ($y = 0; $y -lt $h; $y++) {
    if ($isWhiteRow[$y]) { if ($start -eq -1) { $start = $y } }
    else { if ($start -ne -1) { $len = $y-$start; if ($len -ge $minGapHeight) { $gaps += [PSCustomObject]@{Start=$start;End=$y;Mid=[int](($start+$y)/2);Len=$len} }; $start=-1 } }
  }
  $img.Dispose(); return $gaps
}
Find-Gaps "<풀페이지.png경로>" 40 | Format-Table
```

- `minGapHeight`(마지막 인자)를 40~45 정도로 시작한다. 이러면 섹션 사이의 큰 여백(60px+)은
  잡히지만, 문단 안 줄바꿈이나 리스트 항목 사이의 자잘한 간격(보통 20px 이하)은 노이즈로
  걸러진다.
- 이렇게 찾은 경계만으로 카드 개수만큼 안 나뉘면(예: 요금제 카드처럼 카드 사이 간격이
  20px밖에 안 되는 경우), 자를 지점 후보들의 `Mid` 값을 하나씩 살펴보고 실제로 카드/섹션이
  바뀌는 지점인지 판단한다. 애매하면 일단 잘라서 Read 도구로 직접 열어 확인하고, 텍스트가
  잘렸으면 경계를 30~50px 정도 옮겨서 다시 자른다 — **이 확인 단계를 생략하지 말 것.**

### 2-3. 자르기

```powershell
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("<풀페이지.png>")
$w = $img.Width
$y0 = <시작Y>; $y1 = <끝Y>; $th = $y1 - $y0
$tile = New-Object System.Drawing.Bitmap $w, $th
$g = [System.Drawing.Graphics]::FromImage($tile)
$g.DrawImage($img, (New-Object System.Drawing.Rectangle 0,0,$w,$th), (New-Object System.Drawing.Rectangle 0,$y0,$w,$th), [System.Drawing.GraphicsUnit]::Pixel)
$g.Dispose()
$tile.Save("<출력경로>.png", [System.Drawing.Imaging.ImageFormat]::Png)
$tile.Dispose(); $img.Dispose()
```

- 조각 이미지는 `instagram_posts/<날짜>/` 최상위에 `01_`, `02_` 순번을 붙여 저장한다
  (풀페이지 원본은 `full_page/` 하위에 남겨두되 이건 포스팅용이 아니라 참고용).
- 완전히 빈(흰색뿐인) 조각이 나오면 삭제한다.
- 카드 1개가 한 장에 다 안 들어가면 억지로 줄이지 말고 조각을 늘린다 — 장수보다 "잘림 없이
  읽히는 것"이 우선이다.

## 3. 캡션 + 해시태그 작성

- **톤**: `CLAUDE.md`/`SERVICE_DESIGN.md`에 드러나는 이 프로젝트의 목소리를 따른다 — 담백하고
  솔직한 "빌드 인 퍼블릭" 톤. 과장된 광고 문구보다 "이번에 이런 걸 만들었다 / 이런 문제를
  풀었다"는 식의 진행 로그에 가깝게 쓴다.
- **구조**:
  1. 첫 줄: 이번에 뭘 했는지 한 문장 훅
  2. 2~3줄: 왜 이걸 만들었는지 / 어떤 문제를 풀었는지 (필요하면 `SERVICE_DESIGN.md`의 동기·
     배경 참고)
  3. 마지막 줄: 다음에 뭘 할지, 또는 가벼운 구독 유도 (실제 URL을 캡션 본문에 박을 필요는 없음 —
     "프로필 링크 확인" 정도로 충분)
- **해시태그**: 한국어+영어 섞어서 10~15개. 카테고리별로 고른다:
  - 프로젝트 성격: #빌드인퍼블릭 #사이드프로젝트 #스타트업 #뉴스레터
  - 타겟 고객: #취준생 #직장인 #이직준비 #커리어
  - 기술/도구: 이번 작업이 개발 관련이면 #클로드코드 #AI개발 등 (마케팅/디자인 작업이면 생략)
  - 산업: 이번에 다룬 산업이 있으면 그것도 추가 (예: #로봇산업 #AI산업)
- `instagram_posts/<날짜>/caption.txt`에 저장한다. 형식: 캡션 본문 → 빈 줄 → 해시태그 한 줄
  나열. 인스타그램 앱에 그대로 복사-붙여넣기 하기 좋게 만든다.

## 4. 마무리

- 완료되면 사용자에게 저장된 이미지 경로와 캡션 미리보기를 보여준다.
- `instagram_posts/.last_post_commit`에 현재 `git rev-parse HEAD` 값을 기록해, 다음 실행 때
  "그 이후 변경사항"만 다루도록 한다.
- `instagram_posts/`는 `.gitignore`에 이미 등록돼 있다 — 마케팅 초안이라 저장소에는 커밋하지
  않는다. 새로 만들 때마다 이 규칙이 유지되는지 확인한다.
