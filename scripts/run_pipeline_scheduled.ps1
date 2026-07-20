# 매일 09:00 Windows 작업 스케줄러가 실행하는 무인 수집+태깅 스크립트.
# run_pipeline.py(RSS 수집 -> tag_articles.py 태깅)만 실행한다.
#
# 이 스크립트가 **하지 않는 것**: build_news.py/build_newsletter.py 실행, 배포(subtree
# push) -- 이건 사람이 admin/ 관리자 페이지에서 검수·승인한 뒤 수동으로 실행한다
# (TODO.md "장기 구상: 에이전트 분리 아키텍처" 5번 -- "승인 상태"가 있는 데이터만
# 배포해야 한다는 원칙). 이 스크립트를 build_news.py/build_newsletter.py 호출로
# 확장하지 말 것.
#
# API 비용 상한: config/pipeline_limits.json의 max_articles_tagged_per_run이 회차당
# 태깅 건수를 제한한다 (run_pipeline.py -> scrape_rss.collect_all이 강제).
#
# 등록(참고, 이미 등록돼 있으면 다시 실행할 필요 없음):
#   schtasks /create /tn "NewsletterProject-PipelineScheduler" /sc daily /st 09:00 ^
#     /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\work\project\dev_claude\scripts\run_pipeline_scheduled.ps1" ^
#     /rl limited

$ErrorActionPreference = "Stop"

$root = "D:\work\project\dev_claude"
$python = Join-Path $root "venv\Scripts\python.exe"
$pipelineScript = Join-Path $root "pipeline\run_pipeline.py"
$logDir = Join-Path $root "scripts\logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir ("{0:yyyy-MM-dd_HHmmss}.log" -f (Get-Date))

Set-Location $root

& $python $pipelineScript *> $logFile

exit $LASTEXITCODE
