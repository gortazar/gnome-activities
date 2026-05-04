"""App launching and closing utilities."""
import logging
import subprocess
import shlex
import shutil

logger = logging.getLogger(__name__)


def launch_app(exec_cmd: str, files: list[str] = None) -> bool:
    """Launch an app with optional files. Returns True on success."""
    if files is None:
        files = []

    if not exec_cmd or not exec_cmd.strip():
        logger.error("Empty exec_cmd provided")
        return False

    # Build command: exec_cmd + files (files are validated)
    cmd_parts = shlex.split(exec_cmd)
    for f in files:
        # Basic path validation - no shell metacharacters
        safe_f = _sanitize_path(f)
        if safe_f:
            cmd_parts.append(safe_f)

    try:
        subprocess.Popen(cmd_parts, start_new_session=True)
        logger.info(f"Launched: {exec_cmd}")
        return True
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.warning(f"Failed to launch '{exec_cmd}': {e}")
        return False


def close_app(app_id: str) -> bool:
    """Close an app by its app_id/name using wmctrl or pkill."""
    if not app_id or not app_id.strip():
        logger.error("Empty app_id provided")
        return False

    safe_id = _sanitize_app_id(app_id)
    if not safe_id:
        logger.error(f"Invalid app_id: {app_id!r}")
        return False

    # Try wmctrl first
    if shutil.which("wmctrl"):
        try:
            result = subprocess.run(
                ["wmctrl", "-c", safe_id],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Closed app '{safe_id}' via wmctrl")
                return True
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.warning(f"wmctrl failed for '{safe_id}': {e}")

    # Fallback to pkill
    if shutil.which("pkill"):
        try:
            result = subprocess.run(
                ["pkill", "-f", safe_id],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Closed app '{safe_id}' via pkill")
                return True
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.warning(f"pkill failed for '{safe_id}': {e}")

    logger.warning(f"Could not close app '{safe_id}' (wmctrl/pkill not available or failed)")
    return False


def _sanitize_path(path: str) -> str:
    """Return path only if it contains no shell metacharacters or path traversal."""
    import re
    # Block path traversal
    if ".." in path:
        return ""
    # Allow alphanumeric, space, /, ., -, _, ~
    if re.match(r'^[\w/.\-~ ]+$', path):
        return path
    return ""


def _sanitize_app_id(app_id: str) -> str:
    """Return app_id only if it's safe (alphanumeric, dash, underscore, dot)."""
    import re
    if re.match(r'^[\w.\-]+$', app_id):
        return app_id
    return ""
