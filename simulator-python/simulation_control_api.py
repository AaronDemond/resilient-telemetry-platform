"""Local HTTP service that serves the dashboard and manages simulation lifecycles."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from simulation_manager import SimulationManager


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_UI_PATH = PROJECT_ROOT / "web_ui" / "index.html"


class SimulationControlAPIHandler(BaseHTTPRequestHandler):
    """Serve the browser dashboard and run lifecycle endpoints."""

    server_version = "SimulationControlAPI/1.0"

    @property
    def manager(self) -> SimulationManager:
        return self.server.manager

    def do_OPTIONS(self) -> None:  # pragma: no cover - browser preflight support
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # pragma: no cover - network entry point
        parsed = urlparse(self.path)
        path = parsed.path
        if path in {"/", "/index.html"}:
            self._serve_dashboard()
            return
        if path == "/api/v1/simulations/current":
            run = self.manager.get_current_run()
            if run is None:
                self._send_json(404, {"error": "no active run"})
                return
            self._send_json(200, run)
            return
        if path.startswith("/api/v1/simulations/"):
            run_id = path.rsplit("/", 1)[-1]
            if not run_id or run_id in {"compare", "pause", "stop", "continue"}:
                self._send_json(404, {"error": "run_id required"})
                return
            run = self.manager.get_run(run_id)
            if run is None:
                self._send_json(404, {"error": "unknown run_id"})
                return
            self._send_json(200, run)
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # pragma: no cover - network entry point
        parsed = urlparse(self.path)
        path = parsed.path
        payload = self._read_json_body()

        if path == "/api/v1/simulations":
            try:
                run = self.manager.start_run(
                    seed=int(payload["seed"]),
                    unit_count=int(payload["unit_count"]),
                    interval_ms=int(payload["interval_ms"]),
                    iteration_count=int(payload["iteration_count"]),
                )
            except KeyError as exc:
                self._send_json(400, {"error": f"missing required field: {exc.args[0]}"})
                return
            except (TypeError, ValueError) as exc:
                self._send_json(400, {"error": str(exc)})
                return
            except RuntimeError as exc:
                self._send_json(409, {"error": str(exc)})
                return
            self._send_json(201, run)
            return

        if path == "/api/v1/simulations/pause":
            try:
                run = self.manager.pause_current_run()
            except KeyError:
                self._send_json(404, {"error": "no active run"})
                return
            except RuntimeError as exc:
                self._send_json(409, {"error": str(exc)})
                return
            self._send_json(200, run)
            return

        if path.endswith("/pause"):
            run_id = path.rsplit("/", 2)[-2]
            try:
                run = self.manager.pause_run(run_id)
            except KeyError:
                self._send_json(404, {"error": "unknown run_id"})
                return
            except RuntimeError as exc:
                self._send_json(409, {"error": str(exc)})
                return
            self._send_json(200, run)
            return

        if path == "/api/v1/simulations/stop":
            try:
                run = self.manager.stop_current_run()
            except KeyError:
                self._send_json(404, {"error": "no active run"})
                return
            except RuntimeError as exc:
                self._send_json(409, {"error": str(exc)})
                return
            self._send_json(200, run)
            return

        if path.endswith("/stop"):
            run_id = path.rsplit("/", 2)[-2]
            try:
                run = self.manager.stop_run(run_id)
            except KeyError:
                self._send_json(404, {"error": "unknown run_id"})
                return
            except RuntimeError as exc:
                self._send_json(409, {"error": str(exc)})
                return
            self._send_json(200, run)
            return

        if path.endswith("/continue"):
            run_id = path.rsplit("/", 2)[-2]
            try:
                run = self.manager.continue_run(run_id)
            except KeyError:
                self._send_json(404, {"error": "unknown run_id"})
                return
            except RuntimeError as exc:
                self._send_json(409, {"error": str(exc)})
                return
            self._send_json(200, run)
            return

        if path == "/api/v1/simulations/compare":
            try:
                left_run_id = payload["left_run_id"]
                right_run_id = payload["right_run_id"]
            except KeyError as exc:
                self._send_json(400, {"error": f"missing required field: {exc.args[0]}"})
                return
            try:
                result = self.manager.compare_runs(left_run_id, right_run_id)
            except KeyError:
                self._send_json(404, {"error": "unknown run_id"})
                return
            self._send_json(200, result)
            return

        self._send_json(404, {"error": "not found"})

    def log_message(self, format: str, *args) -> None:  # pragma: no cover - quiet service logs
        return

    def _read_json_body(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw_body = self.rfile.read(content_length)
        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_dashboard(self) -> None:
        if not WEB_UI_PATH.exists():
            self._send_json(404, {"error": "dashboard not found"})
            return
        html = WEB_UI_PATH.read_text(encoding="utf-8")
        body = html.encode("utf-8")
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class SimulationControlAPI(ThreadingHTTPServer):
    """HTTP server that holds the manager for the current session."""

    def __init__(self, server_address: tuple[str, int], manager: SimulationManager) -> None:
        self.manager = manager
        super().__init__(server_address, SimulationControlAPIHandler)


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve the dashboard and lifecycle API from the local control server."""
    manager = SimulationManager()
    server = SimulationControlAPI((host, port), manager)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
