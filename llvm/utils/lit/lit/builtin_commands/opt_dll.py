"""In-process opt implementation backed by the real LLVM opt driver.

Each long-lived lit worker process can load the shared library once via
LIT_OPT_DLL, then reuse that same process for many opt invocations. Default
behavior is unchanged when the environment variable is unset.
"""

import atexit
import json
import os
import ctypes
import sys
import threading

if sys.platform == "win32":
    import _winapi
    import msvcrt


class UnsupportedOptUsage(Exception):
    """Raised when this invocation should fall back to spawning real opt."""


_dll = None
_dll_load_failed = False
_PIPE_BUFFER_SIZE = 4 * 1024 * 1024
_stats_lock = threading.Lock()
_stats = {
    "dll_selected": 0,
    "dll_completed": 0,
    "dll_exceptions": 0,
    "spawn_fallback": 0,
    "spawn_fallback_reasons": {},
}


def _bump_stat(key, amount=1):
    with _stats_lock:
        _stats[key] = _stats.get(key, 0) + amount


def _bump_reason(reason):
    with _stats_lock:
        reasons = _stats.setdefault("spawn_fallback_reasons", {})
        reasons[reason] = reasons.get(reason, 0) + 1


def record_dispatch(mode, reason=None):
    if mode == "dll":
        _bump_stat("dll_selected")
        return
    if mode == "spawn":
        _bump_stat("spawn_fallback")
        if reason:
            _bump_reason(reason)
        return
    raise ValueError(f"unknown opt dispatch mode: {mode}")


def _write_stats():
    stats_dir = os.environ.get("LIT_OPT_DLL_STATS_DIR")
    if not stats_dir:
        return

    with _stats_lock:
        snapshot = {
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "dll_selected": _stats["dll_selected"],
            "dll_completed": _stats["dll_completed"],
            "dll_exceptions": _stats["dll_exceptions"],
            "spawn_fallback": _stats["spawn_fallback"],
            "spawn_fallback_reasons": dict(_stats["spawn_fallback_reasons"]),
        }

    if not (
        snapshot["dll_selected"]
        or snapshot["dll_completed"]
        or snapshot["dll_exceptions"]
        or snapshot["spawn_fallback"]
    ):
        return

    os.makedirs(stats_dir, exist_ok=True)
    stats_path = os.path.join(stats_dir, f"opt-dll-stats-{os.getpid()}.json")
    with open(stats_path, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2, sort_keys=True)


atexit.register(_write_stats)
_UNSUPPORTED_ARGS = {
    "--help",
    "-help",
    "--help-hidden",
    "-help-hidden",
    "--version",
    "-version",
}


def _get_dll():
    global _dll, _dll_load_failed
    if _dll is not None:
        return _dll
    if _dll_load_failed:
        return None

    dll_path = os.environ.get("LIT_OPT_DLL")
    if not dll_path or not os.path.isfile(dll_path):
        _dll_load_failed = True
        return None

    try:
        dll = ctypes.CDLL(dll_path)
        dll.OptMain.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
        dll.OptMain.restype = ctypes.c_int
    except OSError:
        _dll_load_failed = True
        return None

    _dll = dll
    return _dll


def is_supported(argv, cwd):
    if _get_dll() is None:
        return False
    return not any(arg in _UNSUPPORTED_ARGS for arg in argv[1:])


def fallback_reason(argv):
    if _get_dll() is None:
        return "dll-unavailable"
    if any(arg in _UNSUPPORTED_ARGS for arg in argv[1:]):
        return "unsupported-args"
    return "unknown"


def _make_pipe():
    if sys.platform == "win32":
        read_h, write_h = _winapi.CreatePipe(None, _PIPE_BUFFER_SIZE)
        read_fd = msvcrt.open_osfhandle(read_h, os.O_RDONLY)
        write_fd = msvcrt.open_osfhandle(write_h, 0)
        return read_fd, write_fd
    return os.pipe()


def _read_all(fd, chunks, index):
    data = []
    try:
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            data.append(chunk)
    finally:
        os.close(fd)
    chunks[index] = b"".join(data)


def _write_all(fd, data):
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
    except OSError:
        pass
    finally:
        os.close(fd)


def _call_opt_main(dll, argv, stdin_bytes):
    n = len(argv)
    argv_c = (ctypes.c_char_p * (n + 1))(*[a.encode("utf-8") for a in argv], None)

    stdin_r, stdin_w = _make_pipe()
    stdout_r, stdout_w = _make_pipe()
    stderr_r, stderr_w = _make_pipe()

    captured = [b"", b""]
    out_thread = threading.Thread(target=_read_all, args=(stdout_r, captured, 0))
    err_thread = threading.Thread(target=_read_all, args=(stderr_r, captured, 1))
    in_thread = threading.Thread(target=_write_all, args=(stdin_w, stdin_bytes))
    out_thread.start()
    err_thread.start()
    in_thread.start()

    saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
    try:
        os.dup2(stdin_r, 0)
        os.dup2(stdout_w, 1)
        os.dup2(stderr_w, 2)
        rc = dll.OptMain(n, argv_c)
        _bump_stat("dll_completed")
    finally:
        for fd, saved in enumerate(saved_fds):
            os.dup2(saved, fd)
        for saved in saved_fds:
            os.close(saved)
        os.close(stdin_r)
        os.close(stdout_w)
        os.close(stderr_w)
        in_thread.join()
        out_thread.join()
        err_thread.join()

    return rc, captured[0], captured[1]


def run(argv, stdin, stdout, stderr, cwd):
    dll = _get_dll()
    if dll is None:
        raise UnsupportedOptUsage("Opt DLL not available")

    stdin_bytes = stdin.read()
    if isinstance(stdin_bytes, str):
        stdin_bytes = stdin_bytes.encode("utf-8")

    saved_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        rc, out, err = _call_opt_main(dll, argv, stdin_bytes)
    except Exception:
        _bump_stat("dll_exceptions")
        raise
    finally:
        os.chdir(saved_cwd)

    if out:
        stdout.write(out)
    if err:
        stderr.write(err)
    return rc
