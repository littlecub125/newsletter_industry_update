"""
로컬 전용 관리자 페이지 서버 (표준 라이브러리 http.server만 사용, 새 의존성 없음)

tagged_articles.jsonl을 브라우저에서 보고/고치고 approved(승인) 플래그를 매기게 해준다.
"완전 자동 발행 금지" 원칙의 실제 집행 지점 -- build_news.py/build_newsletter.py는
approved=true인 기사만 최종 산출물에 포함시킨다 (config_loader.load_tagged_articles의
`only_approved` 인자, 이 파일 참고).

129건을 한 건씩 클릭하며 검수하는 게 비현실적이라(2026-07-21), 두 기능을 추가했다:
- 필터(산업/impact_score 범위/승인상태/industries 오류 여부) + 체크박스 다중선택 +
  일괄 승인/미승인 (PUT /api/articles/bulk)
- 규칙 기반 자동승인(auto_approve.py, config/auto_approve_rules.json) + 재실행 버튼
  (POST /api/auto-approve/rerun). 검수를 없애는 게 아니라 "규칙 통과 = 사람 승인과
  동등한 근거"로 인정해 사람이 볼 대상을 줄이는 방식 -- approved=true가 되는 경로는
  자동 규칙 통과 아니면 사람의 명시적 승인(approval_source 필드로 구분), 이 둘뿐이다.

**로컬 전용이다.** 인터넷에 올리지 않는다 (`web/`가 아니라 `admin/`에 프론트를 둔 이유 --
`git subtree push --prefix web`로 배포되는 대상에서 완전히 분리해 실수로도 공개되지 않게
함). 1인 운영자 전제라 인증도 없음 -- 절대 0.0.0.0으로 바인딩하거나 외부에 노출하지 말 것.

실행:
    python pipeline/admin_server.py
    브라우저에서 http://127.0.0.1:8787 접속 (Ctrl+C로 종료)
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from auto_approve import apply_to_records, evaluate
from config_loader import BASE_DIR, DATA_DIR, load_auto_approve_rules, load_industries

ADMIN_DIR = os.path.join(BASE_DIR, "admin")
TAGGED_FILE = os.path.join(DATA_DIR, "tagged_articles.jsonl")
HOST = "127.0.0.1"
PORT = 8787

# 프론트에서 고칠 수 있는 tagged.* 필드 (industries의 오분류 버그를 사람이 손으로
# 바로잡을 수 있어야 하고, summary/why_it_matters도 검수 중 다듬을 수 있어야 함)
EDITABLE_TAGGED_FIELDS = {"summary", "why_it_matters", "industries"}

STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/admin.js": ("admin.js", "application/javascript; charset=utf-8"),
    "/admin.css": ("admin.css", "text/css; charset=utf-8"),
}


def load_records() -> list:
    records = []
    if not os.path.exists(TAGGED_FILE):
        return records
    with open(TAGGED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_records(records: list):
    """원자적 저장 -- 임시 파일에 먼저 쓰고 os.replace로 교체해서, 저장 중 죽어도
    tagged_articles.jsonl 자체가 반쯤 써진 채로 깨지지 않게 한다."""
    tmp_path = TAGGED_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    os.replace(tmp_path, TAGGED_FILE)


def valid_industry_ids() -> set:
    return {ind["id"] for ind in load_industries()["industries"]}


class AdminHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filename: str, content_type: str):
        path = os.path.join(ADMIN_DIR, filename)
        if not os.path.exists(path):
            self.send_error(404)
            return
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path in STATIC_FILES:
            filename, content_type = STATIC_FILES[path]
            self._send_file(filename, content_type)
            return

        if path == "/api/articles":
            records = load_records()
            valid_ids = valid_industry_ids()
            rules = load_auto_approve_rules()
            out = []
            for i, rec in enumerate(records):
                tagged = rec.get("tagged", {}) or {}
                industries = tagged.get("industries") or []
                invalid = [ind for ind in industries if ind not in valid_ids]
                # 저장된 auto_approve 판정이 있으면 그대로 쓰고(재실행 이후 상태),
                # 없으면(구버전 레코드, 아직 규칙 재실행 전) 조회 시점에 즉석으로 계산해서
                # 보여준다 -- 파일에 즉시 쓰지는 않는다(그건 rerun 엔드포인트의 역할).
                auto = rec.get("auto_approve")
                if auto is None:
                    passed, reasons = evaluate(tagged, valid_ids, rules)
                    auto = {"passed": passed, "reasons": reasons}
                out.append({
                    "index": i,
                    "title": rec.get("title", ""),
                    "link": rec.get("link", ""),
                    "source": rec.get("source", ""),
                    "published_at": rec.get("published_at"),
                    "collected_at": rec.get("collected_at"),
                    "tagged": tagged,
                    "approved": bool(rec.get("approved")),
                    "approval_source": rec.get("approval_source"),
                    "invalid_industries": invalid,
                    "auto_approve": auto,
                })
            self._send_json(200, {
                "articles": out,
                "valid_industries": sorted(valid_ids),
                "auto_approve_rules": rules,
            })
            return

        self.send_error(404)

    def do_PUT(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) < 3 or parts[0] != "api" or parts[1] != "articles":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid json body"})
            return

        if len(parts) == 3 and parts[2] == "bulk":
            self._handle_bulk_approve(payload)
            return

        if len(parts) != 3:
            self.send_error(404)
            return

        try:
            index = int(parts[2])
        except ValueError:
            self._send_json(400, {"error": "invalid index"})
            return

        records = load_records()
        if index < 0 or index >= len(records):
            self._send_json(404, {"error": "article not found"})
            return

        rec = records[index]
        tagged = rec.setdefault("tagged", {})
        for field in EDITABLE_TAGGED_FIELDS:
            if field in payload:
                tagged[field] = payload[field]
        if "approved" in payload:
            # 사람이 admin 페이지에서 명시적으로 승인/반려한 것이므로 manual로 기록.
            # 이후 자동승인 규칙 재실행이 이 판단을 절대 덮어쓰지 않는다.
            rec["approved"] = bool(payload["approved"])
            rec["approval_source"] = "manual"

        save_records(records)

        valid_ids = valid_industry_ids()
        invalid = [ind for ind in (tagged.get("industries") or []) if ind not in valid_ids]
        self._send_json(200, {"ok": True, "invalid_industries": invalid})

    def _handle_bulk_approve(self, payload: dict):
        """필터로 골라낸 여러 기사를 한 번에 승인/미승인 처리한다 (일괄 승인 UI).
        여기서도 approval_source="manual"로 기록 -- 필터링 후 일괄 클릭도 사람의
        명시적 판단이라는 점에서 개별 승인과 동일하게 취급한다."""
        indices = payload.get("indices")
        approved = payload.get("approved")
        if not isinstance(indices, list) or not isinstance(approved, bool):
            self._send_json(400, {"error": "indices(list)와 approved(bool)가 필요합니다"})
            return

        records = load_records()
        updated = 0
        for idx in indices:
            if isinstance(idx, int) and 0 <= idx < len(records):
                records[idx]["approved"] = approved
                records[idx]["approval_source"] = "manual"
                updated += 1

        save_records(records)
        self._send_json(200, {"ok": True, "updated": updated, "total_requested": len(indices)})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/auto-approve/rerun":
            records = load_records()
            stats = apply_to_records(records)
            save_records(records)
            self._send_json(200, {"ok": True, **stats})
            return
        self.send_error(404)

    def log_message(self, format, *args):
        print("[admin] " + (format % args))


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), AdminHandler)
    print(f"관리자 페이지: http://{HOST}:{PORT}  (Ctrl+C로 종료)")
    print(f"편집 대상 파일: {TAGGED_FILE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")


if __name__ == "__main__":
    main()
