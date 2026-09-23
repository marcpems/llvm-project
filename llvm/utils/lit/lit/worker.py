"""
The functions in this module are meant to run on a separate worker process.
Exception: in single process mode _execute is called directly.

For efficiency, we copy all data needed to execute all tests into each worker
and store it in global variables. This reduces the cost of each task.
"""
import contextlib
import os
import signal
import time
import traceback

import lit.Test
import lit.util
import lit.builtin_commands.filecheck_dll as builtin_filecheck_dll
import lit.builtin_commands.opt_dll as builtin_opt_dll
from lit.TestRunner import TestUpdaterException


_lit_config = None
_parallelism_semaphores = None


def initialize(lit_config, parallelism_semaphores):
    """Copy data shared by all test executions into worker processes"""
    global _lit_config
    global _parallelism_semaphores
    _lit_config = lit_config
    _parallelism_semaphores = parallelism_semaphores

    # Pre-load the in-process FileCheck DLL (if LIT_FILECHECK_DLL is set)
    # once per worker process here, rather than lazily on the first
    # FileCheck invocation, so the ctypes.CDLL cost is paid once at pool
    # startup instead of adding latency to whichever test happens to hit
    # it first. is_supported()/run() cache the loaded handle at module
    # scope, so this is purely a warm-up call; it's a no-op (and safe to
    # skip) if the env var isn't set.
    builtin_filecheck_dll.is_supported(["FileCheck"], os.getcwd())
    builtin_opt_dll.is_supported(["opt"], os.getcwd())

    # We use the following strategy for dealing with Ctrl+C/KeyboardInterrupt in
    # subprocesses created by the multiprocessing.Pool.
    # https://noswap.com/blog/python-multiprocessing-keyboardinterrupt
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def execute(test):
    """Run one test in a multiprocessing.Pool

    Side effects in this function and functions it calls are not visible in the
    main lit process.

    Arguments and results of this function are pickled, so they should be cheap
    to copy.
    """
    with _get_parallelism_semaphore(test):
        result = _execute(test, _lit_config)

    test.setResult(result)
    return test


def execute_batch(tests):
    """Run a batch of tests in a worker process.

    Batching multiple tests per task dispatch reduces inter-process IPC round-trips,
    serialization overhead, and management thread wakeups on high core count systems.
    """
    for test in tests:
        with _get_parallelism_semaphore(test):
            result = _execute(test, _lit_config)
        test.setResult(result)
    return tests


# TODO(python3): replace with contextlib.nullcontext
@contextlib.contextmanager
def NopSemaphore():
    yield


def _get_parallelism_semaphore(test):
    pg = test.config.parallelism_group
    if callable(pg):
        pg = pg(test)
    return _parallelism_semaphores.get(pg, NopSemaphore())


# Do not inline! Directly used by LitTestCase.py
def _execute(test, lit_config):
    start = time.time()
    result = _execute_test_handle_errors(test, lit_config)
    result.elapsed = time.time() - start
    result.start = start
    result.pid = os.getpid()
    return result


def _execute_test_handle_errors(test, lit_config):
    try:
        result = test.config.test_format.execute(test, lit_config)
        return _adapt_result(result)
    except TestUpdaterException as e:
        if lit_config.debug:
            raise
        return lit.Test.Result(lit.Test.UNRESOLVED, str(e))
    except:
        if lit_config.debug:
            raise
        output = "Exception during script execution:\n"
        output += traceback.format_exc()
        output += "\n"
        return lit.Test.Result(lit.Test.UNRESOLVED, output)


# Support deprecated result from execute() which returned the result
# code and additional output as a tuple.
def _adapt_result(result):
    if isinstance(result, lit.Test.Result):
        return result
    assert isinstance(result, tuple)
    code, output = result
    return lit.Test.Result(code, output)
