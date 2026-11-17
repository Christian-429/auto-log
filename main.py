"""Local web dashboard for the TRIO automation tools.

The browser handles the user interface and file management. The existing
Python scripts remain responsible for desktop/browser automation because web
pages cannot safely control other Windows applications.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


PROJECT_DIR = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_DIR / "input.txt"
WEB_APP_FILE = PROJECT_DIR / "web_app.html"
YEAR_PATTERN = re.compile(r"^\d{4}-\d{4}$")


def read_student_ids() -> list[str]:
    """Read the saved IDs, ignoring blank lines."""
    try:
        return [line.strip() for line in INPUT_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError:
        return []


def validate_student_ids(value: str) -> tuple[list[str], list[dict[str, object]]]:
    """Return normalized IDs plus details for lines that require correction."""
    student_ids: list[str] = []
    invalid_lines: list[dict[str, object]] = []
    for line_number, line in enumerate(value.splitlines(), start=1):
        student_id = line.strip()
        if not student_id:
            continue
        if student_id.isdigit():
            student_ids.append(student_id)
        else:
            invalid_lines.append({"line": line_number, "value": student_id})
    return student_ids, invalid_lines


def launch_automation(command: list[str]) -> None:
    """Start one of the established desktop automation scripts."""
    options: dict[str, object] = {"cwd": PROJECT_DIR}
    if sys.platform == "win32":
        options["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    subprocess.Popen(command, **options)


class TrioToolsHandler(SimpleHTTPRequestHandler):
    """Serve the local app and a deliberately small set of project APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_DIR), **kwargs)

    def do_GET(self):  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlparse(self.path).path
        if path == "/api/student-ids":
            self._send_json(HTTPStatus.OK, {"student_ids": read_student_ids()})
            return
        if path == "/" or path == "/index.html":
            self.path = "/web_app.html"
        super().do_GET()

    def do_POST(self):  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        if path == "/api/student-ids":
            self._save_student_ids(payload)
            return
        if path == "/api/start-log":
            self._start_log_update()
            return
        if path == "/api/add-year":
            self._add_school_year(payload)
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown action."})

    def _read_json(self) -> dict[str, object]:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid request length.") from error
        if content_length > 1_000_000:
            raise ValueError("Request is too large.")
        try:
            value = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Please send a valid request.") from error
        if not isinstance(value, dict):
            raise ValueError("Please send an object.")
        return value

    def _save_student_ids(self, payload: dict[str, object]) -> None:
        raw_ids = payload.get("student_ids", "")
        if not isinstance(raw_ids, str):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Student IDs must be text."})
            return
        student_ids, invalid_lines = validate_student_ids(raw_ids)
        if invalid_lines:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": "Each non-blank line must contain only one numeric student ID.",
                    "invalid_lines": invalid_lines,
                },
            )
            return
        content = "\n".join(student_ids)
        if content:
            content += "\n"
        try:
            INPUT_FILE.write_text(content, encoding="utf-8")
        except OSError as error:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Could not save input.txt: {error}"})
            return
        self._send_json(HTTPStatus.OK, {"message": f"Saved {len(student_ids)} student IDs."})

    def _start_log_update(self) -> None:
        try:
            launch_automation([sys.executable, "log.py"])
        except OSError as error:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Could not start the log update: {error}"})
            return
        self._send_json(HTTPStatus.OK, {"message": "The log update opened in a separate window."})

    def _add_school_year(self, payload: dict[str, object]) -> None:
        year = payload.get("year", "")
        if not isinstance(year, str) or not YEAR_PATTERN.fullmatch(year.strip()):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Use the format YYYY-YYYY, for example 2027-2028."})
            return
        try:
            launch_automation([sys.executable, "-m", "addTab", year.strip()])
        except OSError as error:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Could not start the school-year tool: {error}"})
            return
        self._send_json(HTTPStatus.OK, {"message": f"Creating {year.strip()} tabs in a separate window."})

    def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, _format, *_args):
        """Keep routine browser requests out of the launcher's console."""


def main() -> None:
    if not WEB_APP_FILE.is_file():
        raise FileNotFoundError(f"Could not find {WEB_APP_FILE.name}.")
    server = ThreadingHTTPServer(("127.0.0.1", 0), TrioToolsHandler)
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"TRIO Tools is running at {url}")
    webbrowser.open_new_tab(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
