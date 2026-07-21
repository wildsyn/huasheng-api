"""Local protocol integration tests for the public Huasheng SDK.

These tests deliberately use a real localhost HTTP server instead of mocking
``HuashengClient`` or reimplementing its request flow.  If the SDK stops
sending the documented payload, CSRF query, polling request, or download
headers, the server rejects the request and the test fails.
"""

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from huasheng import HuashengClient, constants

MEDIA_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x0cmdatmedia"


class HuashengProtocolHandler(BaseHTTPRequestHandler):
    """Minimal deterministic server for the SDK's actual HTTP protocol."""

    server_version = "HuashengProtocolTest/1.0"

    def log_message(self, _format, *_args):
        return

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        size = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(size) or b"{}")

    def do_POST(self):  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        payload = self._read_json()
        self.server.requests.append(("POST", parsed.path, payload, parse_qs(parsed.query)))

        if parsed.path == "/api/huasheng/project/create":
            if parse_qs(parsed.query).get("csrf") != ["test-csrf"]:
                self._send_json({"message": "missing csrf"}, status=403)
                return
            required = {
                "script": "真实 SDK 协议测试文案",
                "voice_id": 5866601,
                "voice_type": 0,
            }
            if any(payload.get(key) != value for key, value in required.items()):
                self._send_json({"message": "invalid create payload"}, status=422)
                return
            self._send_json({"code": 0, "data": {"pid": 321}})
            return

        if parsed.path == "/api/innovideo/project/export/video/task":
            if payload != {"id": 654}:
                self._send_json({"message": "invalid export payload"}, status=422)
                return
            if not self.server.return_task_id:
                self._send_json({"code": 0, "data": {}})
                return
            self._send_json({"task_id": "task-1", "version": "2", "project_hash": "hash-1"})
            return

        self._send_json({"message": "unexpected POST"}, status=404)

    def do_GET(self):  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        self.server.requests.append(("GET", parsed.path, None, query))

        if parsed.path == "/api/innovideo/project/info":
            if query.get("pid") != ["321"]:
                self._send_json({"message": "invalid pid"}, status=422)
                return
            self._send_json(
                {
                    "project": {
                        "pid": 321,
                        "id": "654",
                        "state": "1",
                        "state_message": "项目处理完成",
                        "progress": "100",
                        "project_hash": "hash-1",
                    }
                }
            )
            return

        if parsed.path == "/api/innovideo/project/export/video/info":
            expected = {"id": ["654"], "task_id": ["task-1"], "project_hash": ["hash-1"]}
            if query != expected:
                self._send_json({"message": "invalid export query"}, status=422)
                return
            media_url = "http://{host}:{port}/media/result.mp4".format(
                host=self.server.server_address[0], port=self.server.server_address[1]
            )
            self._send_json({"url": media_url, "progress": "100"})
            return

        if parsed.path == "/media/result.mp4":
            if self.headers.get("Referer") != "https://www.huasheng.cn/":
                self._send_json({"message": "missing referer"}, status=403)
                return
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(MEDIA_BYTES)))
            self.end_headers()
            self.wfile.write(MEDIA_BYTES)
            return

        self._send_json({"message": "unexpected GET"}, status=404)


@pytest.fixture
def protocol_server(monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), HuashengProtocolHandler)
    server.requests = []
    server.return_task_id = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = "http://{host}:{port}".format(
        host=server.server_address[0], port=server.server_address[1]
    )
    monkeypatch.setattr(constants, "PROJECT_CREATE", base_url + "/api/huasheng/project/create")
    monkeypatch.setattr(constants, "PROJECT_INFO", base_url + "/api/innovideo/project/info")
    monkeypatch.setattr(
        constants,
        "EXPORT_TASK",
        base_url + "/api/innovideo/project/export/video/task",
    )
    monkeypatch.setattr(
        constants,
        "EXPORT_INFO",
        base_url + "/api/innovideo/project/export/video/info",
    )

    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def make_client():
    return HuashengClient(
        cookies={"SESSDATA": "test-session", "bili_jct": "test-csrf"},
        poll_interval=0.001,
        poll_timeout=1,
    )


def test_public_sdk_create_export_and_download(protocol_server, tmp_path):
    client = make_client()

    project = client.create_project(script="真实 SDK 协议测试文案")
    output = tmp_path / "result.mp4"
    result_path = client.export_and_download(project.id, str(output), project.project_hash)

    assert project.pid == 321
    assert project.id == "654"
    assert result_path == str(output)
    assert output.read_bytes() == MEDIA_BYTES
    assert (
        hashlib.sha256(output.read_bytes()).hexdigest() == hashlib.sha256(MEDIA_BYTES).hexdigest()
    )

    paths = [(method, path) for method, path, _payload, _query in protocol_server.requests]
    assert paths == [
        ("POST", "/api/huasheng/project/create"),
        ("GET", "/api/innovideo/project/info"),
        ("POST", "/api/innovideo/project/export/video/task"),
        ("GET", "/api/innovideo/project/export/video/info"),
        ("GET", "/media/result.mp4"),
    ]


def test_public_sdk_rejects_export_without_task_id(protocol_server):
    protocol_server.return_task_id = False
    client = make_client()

    with pytest.raises(RuntimeError, match="导出任务创建失败"):
        client.export_video(654)
