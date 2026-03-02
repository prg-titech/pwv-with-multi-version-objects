import atexit
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_LOG_ENV_VAR = "MVO_ACCESS_PROFILE_LOG"
_CALLSITE_FRAME_DEPTH = 4
_LOG_FILE = None

def emit_access_event(
    *,
    class_name: str,
    access_kind: str,
    member_name: str,
    resolved_version: int,
    latest_version: int,
) -> None:
    log_file = _get_log_file()
    if log_file is None:
        return

    callsite = _get_callsite()
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "class_name": class_name,
        "access_kind": access_kind,
        "member_name": member_name,
        "resolved_version": resolved_version,
        "latest_version": latest_version,
        "callsite_file": callsite["file"],
        "callsite_line": callsite["line"],
        "callsite_function": callsite["function"],
    }
    json.dump(payload, log_file, ensure_ascii=True)
    log_file.write("\n")
    log_file.flush()

def _get_log_file():
    global _LOG_FILE
    if _LOG_FILE is not None:
        return _LOG_FILE

    log_path = os.environ.get(_LOG_ENV_VAR)
    if not log_path:
        return None

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _LOG_FILE = path.open("a", encoding="utf-8")
    atexit.register(_close_log_file)
    return _LOG_FILE

def _close_log_file() -> None:
    global _LOG_FILE
    if _LOG_FILE is None:
        return
    _LOG_FILE.close()
    _LOG_FILE = None

def _get_callsite() -> dict[str, object]:
    try:
        frame = sys._getframe(_CALLSITE_FRAME_DEPTH)
    except ValueError:
        return {"file": "<unknown>", "line": 0, "function": "<unknown>"}

    code = frame.f_code
    return {
        "file": code.co_filename,
        "line": frame.f_lineno,
        "function": code.co_name,
    }
