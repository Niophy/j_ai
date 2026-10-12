"""JADE HTTP API (v2): the examiner as a local web service, standard library only.

Endpoints (JSON in, JSON out):
    GET  /health                      liveness, name, version, judge model
    GET  /cases                       case ids, types and questions (never the marking scheme)
    POST /evaluate                    {"case_id": "...", "answer": "...", "student": "..."?} -> graded result
    GET  /history?limit=20&student=x  recent gradings from the evaluation history (no answer text)
    GET  /kpis?student=x              KPIs computed from the history

Run:  python -m jai.api.server            (listens on 127.0.0.1:8765)
      JAI_API_PORT=9000 python -m jai.api.server

Security: binds to the loopback address by default, so only this machine can reach it.
JAI_API_HOST can widen that; put an authenticating proxy in front before doing so.
Gradings run one at a time (one GPU), each saved as a run file and recorded in the history.
"""

import json
import os
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

import jai
from jai import history
from jai.eval.runner import load_cases, provider_label, run_single_case, save_run

MAX_BODY = 64 * 1024
PUBLIC_CASE_KEYS = ("id", "type", "tags")


def _public_case(case):
    out = {k: case[k] for k in PUBLIC_CASE_KEYS if k in case}
    out["question"] = case["input"].get("scenario") or case["input"].get("question")
    return out


def make_handler(judge):
    lock = threading.Lock()
    cases = {c["id"]: c for c in load_cases().get("cases", [])}
    judge_name = provider_label(judge)

    class Handler(BaseHTTPRequestHandler):
        server_version = f"JADE/{jai.__version__}"

        def log_message(self, fmt, *args):  # quiet by default; JAI_API_LOG=1 to see requests
            if os.getenv("JAI_API_LOG") == "1":
                sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def _send(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _error(self, status, message):
            self._send(status, {"error": message})

        def do_GET(self):
            url = urlparse(self.path)
            qs = {k: v[-1] for k, v in parse_qs(url.query).items()}
            if url.path == "/health":
                return self._send(HTTPStatus.OK, {"status": "ok", "name": "JADE", "version": jai.__version__, "judge": judge_name})
            if url.path == "/cases":
                return self._send(HTTPStatus.OK, {"cases": [_public_case(c) for c in cases.values()]})
            if url.path == "/history":
                try:
                    limit = max(1, min(500, int(qs.get("limit", 20))))
                except ValueError:
                    return self._error(HTTPStatus.BAD_REQUEST, "limit must be a number")
                rows = history.recent(limit=limit, student=qs.get("student"))
                for r in rows:
                    r.pop("answer", None)  # personal data stays out of the API
                return self._send(HTTPStatus.OK, {"gradings": rows})
            if url.path == "/kpis":
                return self._send(HTTPStatus.OK, history.kpis(student=qs.get("student")))
            return self._error(HTTPStatus.NOT_FOUND, f"no such endpoint: {url.path}")

        def do_POST(self):
            if urlparse(self.path).path != "/evaluate":
                return self._error(HTTPStatus.NOT_FOUND, "POST only on /evaluate")
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "bad Content-Length")
            if length <= 0:
                return self._error(HTTPStatus.BAD_REQUEST, "empty body")
            if length > MAX_BODY:
                return self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, f"body over {MAX_BODY} bytes")
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return self._error(HTTPStatus.BAD_REQUEST, "body must be JSON")
            if not isinstance(data, dict):
                return self._error(HTTPStatus.BAD_REQUEST, "body must be a JSON object")
            case = cases.get(str(data.get("case_id", "")))
            if case is None:
                return self._error(HTTPStatus.NOT_FOUND, f"unknown case_id: {data.get('case_id')!r}")
            answer = data.get("answer")
            if not isinstance(answer, str):
                return self._error(HTTPStatus.BAD_REQUEST, "answer must be a string")
            student = data.get("student") if isinstance(data.get("student"), str) else None
            with lock:  # one grading at a time: one GPU
                outcome = run_single_case(case, judge, answer)
                run_file = save_run([outcome], course="api", version=jai.__version__,
                                    provider=judge_name, student=student, source="api")
            outcome["run_id"] = run_file.stem
            return self._send(HTTPStatus.OK, outcome)

    return Handler


def make_server(judge, host="127.0.0.1", port=8765):
    return ThreadingHTTPServer((host, port), make_handler(judge))


def main():
    load_dotenv()
    from src.core.provider_factory import get_provider
    host = os.getenv("JAI_API_HOST", "127.0.0.1")
    port = int(os.getenv("JAI_API_PORT", "8765"))
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(f"WARNING: listening on {host}; anyone who can reach it can submit gradings.", file=sys.stderr)
    server = make_server(get_provider(role="judge"), host, port)
    print(f"JADE API {jai.__version__} on http://{host}:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
