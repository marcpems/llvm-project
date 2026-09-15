import sys


def run(argv, stdin, stdout, stderr, cwd):
    """In-process 'count'.

    Faithful port of llvm/utils/count/count.c: reads all of stdin, counts
    '\\n' bytes, and compares the total against the single required numeric
    argument. Runs in-process (no CreateProcess/fork+exec) whenever
    possible, since this is one of the most frequently invoked trivial
    wrapper tools in the test suite and process creation is disproportionately
    expensive on Windows (see marcpems/llvm-win-wsl-perf-bench for the
    underlying measurement).

    Since it never calls sys.exit, this is safe to run inside the lit worker
    as well as from the standalone main below.

    Args:
        argv: A list of command-line arguments. argv[0] is the command name,
            argv[1] is the required expected line count.
        stdin: Binary input stream to count lines from.
        stdout: Binary output stream (unused; count never writes to stdout,
            matching count.c).
        stderr: Binary error stream for usage/mismatch messages.
        cwd: Unused; present for a uniform builtin 'run' signature.

    Returns:
        0 if the counted and expected line counts match, 1 if they don't,
        2 for a usage error (wrong argument count or a non-numeric argument),
        matching count.c's exit codes exactly.
    """
    args = argv[1:]
    if len(args) != 1:
        stderr.write(("usage: %s <expected line count>\n" % argv[0]).encode())
        return 2

    try:
        expected = int(args[0])
        if expected < 0:
            raise ValueError
    except ValueError:
        stderr.write(
            ("%s: invalid count argument '%s'\n" % (argv[0], args[0])).encode()
        )
        return 2

    data = stdin.read()
    if isinstance(data, str):
        data = data.encode()
    actual = data.count(b"\n")

    if actual != expected:
        stderr.write(
            ("Expected %d lines, got %d.\n" % (expected, actual)).encode()
        )
        return 1
    return 0


def main(argv):
    out = getattr(sys.stdout, "buffer", sys.stdout)
    err = getattr(sys.stderr, "buffer", sys.stderr)
    inp = getattr(sys.stdin, "buffer", sys.stdin)
    sys.exit(run(argv, inp, out, err, ""))


if __name__ == "__main__":
    main(sys.argv)
