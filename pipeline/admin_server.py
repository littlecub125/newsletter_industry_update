"""
로컬 전용 관리자 페이지 서버 (표준 라이브러리 http.server만 사용, 새 의존성 없음)

tagged_articles.jsonl을 브라우저에서 보고/고치고 approved(승인) 플래그를 매기게 해준다.
"완전 자동 발행 금지" 원칙의 실제 집행 지점 -- build_news.py/build_newsletter.py는
approved=true인 기사만 최종 산출물에 포함시킨다 (config_loader.load_tagged_articles의
`only_approved` 인자, 이 파일 참고).

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

from config_loader import BASE_DIR, DATA_DIR, load_industries

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
            out = []
            for i, rec in enumerate(records):
                tagged = rec.get("tagged", {}) or {}
                industries = tagged.get("industries") or []
                invalid = [ind for ind in industries if ind not in valid_ids]
                out.append({
                    "index": i,
                    "title": rec.get("title", ""),
                    "link": rec.get("link", ""),
                    "source": rec.get("source", ""),
                    "published_at": rec.get("published_at"),
                    "collected_at": rec.get("collected_at"),
                    "tagged": tagged,
                    "approved": bool(rec.get("approved")),
                    "invalid_industries": invalid,
                })
            self._send_json(200, {"articles": out, "valid_industries": sorted(valid_ids)})
            return

        self.send_error(404)

    def do_PUT(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[0] != "api" or parts[1] != "articles":
            self.send_error(404)
            return

        try:
            index = int(parts[2])
        except ValueError:
            self._send_json(400, {"error": "invalid index"})
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid json body"})
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
            rec["approved"] = bool(payload["approved"])

        save_records(records)

        valid_ids = valid_industry_ids()
        invalid = [ind for ind in (tagged.get("industries") or []) if ind not in valid_ids]
        self._send_json(200, {"ok": True, "invalid_industries": invalid})

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
