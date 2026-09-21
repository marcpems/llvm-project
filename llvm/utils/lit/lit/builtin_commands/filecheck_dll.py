"""In-process, full-fidelity FileCheck implementation backed by the real
LLVM FileCheck engine, loaded once per worker process via ctypes.

Unlike builtin_commands/filecheck.py (a hand-written subset prototype that
only understands a limited slice of directives/flags and falls back to the
real binary for anything else), this module calls into the real,
unmodified CLI driver (llvm/utils/FileCheck/FileCheck.cpp, exported as
FileCheckMain(argc, argv) from a small DLL/shared library build) -- so it
has the exact same behavior as the real FileCheck.exe for every construct,
not just a supported subset. This eliminates a CreateProcess call per
FileCheck invocation (see marcpems/llvm-win-wsl-perf-bench), which is the
single most frequently spawned external tool across the LLVM test suite,
while preserving full correctness.

The library is loaded lazily, once per worker process (the ctypes.CDLL
handle is cached at module scope), the first time run()/is_supported() is
called in that process -- see worker.py's initialize() for where this can
optionally be pre-warmed.

Safety model:
  - If the shared library can't be found/loaded for any reason,
    is_supported() returns False forever in this process, and every
    FileCheck invocation falls back to spawning the real external binary,
    exactly as if this module didn't exist. This module is opt-in via the
    LIT_FILECHECK_DLL environment variable (path to the built shared
    library) specifically so it can never silently activate/change
    behavior in an environment where the DLL wasn't intentionally built
    and pointed to.
  - FileCheckMain is called through the "reentrancy-safe" build target
    (FileCheckCLIEmbed.cpp), which resets cl::opt global state before each
    call, and is called with a private Errs stream so parse errors return
    an error code instead of calling exit() and killing the whole worker.
  - stdin/stdout/stderr are captured via OS-level fd redirection
    (os.dup/os.dup2) onto pipes (not temp files -- see _make_pipe()'s
    docstring for why), since the DLL's llvm::outs()/errs()/stdin are
    plain raw_fd_ostream wrappers around OS fds 1/2/0, not Python
    objects. Any exception during the call restores the original fds
    before propagating, so a failure never leaves stdout/stderr silently
    swapped for the rest of the worker's life.
"""

import ctypes
import os
import sys

if sys.platform == "win32":
    import _winapi
    import msvcrt

# Generously large so that even a verbose/failing FileCheck invocation's
# stdout+stderr (or a large piped stdin) can never fill the pipe's kernel
# buffer before we read it back -- this deliberately avoids ever needing a
# background drain thread per call, which would itself add per-call
# overhead. 4 MiB is far larger than any realistic FileCheck input/output in
# the LLVM test suite.
_PIPE_BUFFER_SIZE = 4 * 1024 * 1024


class UnsupportedFileCheckUsage(Exception):
    """Raised when this invocation can't safely go through the DLL (e.g.
    the DLL isn't configured/available in this process)."""


_dll = None
_dll_load_failed = False


def _get_dll():
    """Returns the cached ctypes.CDLL for FileCheckMain, loading it lazily
    the first time this is called in this process. Returns None (and
    remembers not to try again) if it can't be loaded, e.g. because
    LIT_FILECHECK_DLL isn't set or points to a missing/incompatible file.
    """
    global _dll, _dll_load_failed
    if _dll is not None:
        return _dll
    if _dll_load_failed:
        return None

    dll_path = os.environ.get("LIT_FILECHECK_DLL")
    if not dll_path or not os.path.isfile(dll_path):
        _dll_load_failed = True
        return None

    try:
        dll = ctypes.CDLL(dll_path)
        dll.FileCheckMain.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
        dll.FileCheckMain.restype = ctypes.c_int
    except OSError:
        _dll_load_failed = True
        return None

    _dll = dll
    return _dll


def is_supported(argv, cwd):
    """Whether run() should be able to handle this invocation in-process.

    True whenever the shared library is available in this process -- the
    DLL wraps the real, unmodified FileCheck engine, so (unlike the
    Python-subset prototype) there is no construct-by-construct
    allowlist to check here.
    """
    return _get_dll() is not None


def _make_pipe():
    """Creates a pipe (read_fd, write_fd) with a large kernel buffer (see
    _PIPE_BUFFER_SIZE), avoiding the filesystem entirely -- unlike
    tempfile-based redirection, a pipe is a pure kernel object with no
    CreateFile/DeleteFile (or NTFS journaling) involved at all.
    """
    if sys.platform == "win32":
        read_h, write_h = _winapi.CreatePipe(None, _PIPE_BUFFER_SIZE)
        read_fd = msvcrt.open_osfhandle(read_h, os.O_RDONLY)
        write_fd = msvcrt.open_osfhandle(write_h, 0)
        return read_fd, write_fd
    return os.pipe()


def _read_all(fd):
    chunks = []
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _call_filecheck_main(dll, argv, stdin_bytes):
    """Calls FileCheckMain(argc, argv) with argv's OS-level fd 0/1/2
    redirected to pipes, and returns (exit_code, stdout_bytes,
    stderr_bytes). Restores the original fds before returning, even if
    the call raises.
    """
    n = len(argv)
    argv_c = (ctypes.c_char_p * (n + 1))(
        *[a.encode("utf-8") for a in argv], None
    )

    stdin_r, stdin_w = _make_pipe()
    stdout_r, stdout_w = _make_pipe()
    stderr_r, stderr_w = _make_pipe()

    # Write all of stdin and close the write end up front -- safe without a
    # background thread because _PIPE_BUFFER_SIZE comfortably exceeds any
    # realistic stdin size for a FileCheck invocation.
    os.write(stdin_w, stdin_bytes)
    os.close(stdin_w)

    saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
    try:
        os.dup2(stdin_r, 0)
        os.dup2(stdout_w, 1)
        os.dup2(stderr_w, 2)
        rc = dll.FileCheckMain(n, argv_c)
    finally:
        for fd, saved in enumerate(saved_fds):
            os.dup2(saved, fd)
        for saved in saved_fds:
            os.close(saved)
        os.close(stdin_r)
        os.close(stdout_w)
        os.close(stderr_w)

    out = _read_all(stdout_r)
    err = _read_all(stderr_r)
    os.close(stdout_r)
    os.close(stderr_r)
    return rc, out, err


def run(argv, stdin, stdout, stderr, cwd):
    """Runs the real FileCheck engine in-process via ctypes.

    Args:
        argv: argv[0] is the command name, remaining args are FileCheck's
            usual flags plus the positional check-file path (usually %s).
        stdin: Binary input stream; read and fed to FileCheckMain via a
            temp-file-backed fd 0, matching what a spawned process would
            see on its real stdin.
        stdout: Byte-oriented writer for FileCheckMain's captured stdout.
        stderr: Byte-oriented writer for FileCheckMain's captured stderr.
        cwd: Working directory FileCheckMain should resolve relative
            paths (check-file/--input-file) against, matching what a
            spawned subprocess's cwd would give it.

    Returns:
        FileCheckMain's real exit code (0 success, non-zero failure),
        exactly as the real external FileCheck binary would return.
    """
    dll = _get_dll()
    if dll is None:
        raise UnsupportedFileCheckUsage("FileCheck DLL not available")

    stdin_bytes = stdin.read()
    if isinstance(stdin_bytes, str):
        stdin_bytes = stdin_bytes.encode("utf-8")

    # FileCheckMain resolves relative paths (the check-file, --input-file)
    # against the process's current directory, since it just fopen()s
    # them -- match what a spawned subprocess's cwd would give it.
    saved_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        rc, out, err = _call_filecheck_main(dll, argv, stdin_bytes)
    finally:
        os.chdir(saved_cwd)

    if out:
        stdout.write(out)
    if err:
        stderr.write(err)
    return rc
