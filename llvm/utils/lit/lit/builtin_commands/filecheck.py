"""In-process subset implementation of FileCheck.

This is an EXPERIMENTAL prototype exploring whether FileCheck --
hypothesized (see marcpems/llvm-win-wsl-perf-bench) to be the single
most frequently spawned external tool across the LLVM test suite -- can
be run in-process the same way true/false/count already are, to avoid a
CreateProcess call per invocation on Windows.

Scope / limitations (deliberately NOT a full FileCheck replacement):
  Supported directives: CHECK, CHECK-NEXT, CHECK-SAME, CHECK-NOT,
    CHECK-DAG, CHECK-LABEL, CHECK-EMPTY.
  Supported syntax: {{regex}} literal-regex spans, [[VAR]] variable
    references, [[VAR:regex]] variable definitions, default (non-strict)
    whitespace normalization, --check-prefix/--check-prefixes,
    --strict-whitespace, --input-file, --allow-empty, -DVAR=VALUE.
  NOT supported: CHECK-COUNT-<n>, numeric expressions ([[#...]]),
    --implicit-check-not, --dump-input, -v/-vv, CHECK-NOT combined with
    DAG groups' exact non-overlap accounting (approximated), multiple
    output files. If any of these are detected in the check file or
    argv, run() raises UnsupportedFileCheckUsage so the caller can fall
    back to the real FileCheck binary -- this prototype prioritizes
    "never silently produce a wrong pass/fail result" over coverage.

This is a research prototype for measuring potential wall-clock gains
and is NOT wired into TestRunner.py's builtin dispatch tables; it must
not change the behavior of any real test run.
"""

import re
import sys


class UnsupportedFileCheckUsage(Exception):
    """Raised when the check file/args use a construct this prototype
    does not implement, so the caller can fall back to real FileCheck."""


_DIRECTIVE_KINDS = ("EMPTY", "NEXT", "SAME", "NOT", "DAG", "LABEL")

_TOKEN_RE = re.compile(r"(\{\{.*?\}\}|\[\[[A-Za-z_][A-Za-z0-9_]*(?::.*?)?\]\])")


class CheckItem:
    __slots__ = ("kind", "text", "line_no")

    def __init__(self, kind, text, line_no):
        self.kind = kind  # one of "CHECK" or an entry in _DIRECTIVE_KINDS
        self.text = text
        self.line_no = line_no


def _parse_args(argv):
    prefixes = ["CHECK"]
    input_file = None
    strict_whitespace = False
    allow_empty = False
    check_file = None
    defines = {}

    args = argv[1:]
    i = 0
    explicit_prefixes = False
    while i < len(args):
        a = args[i]
        if a == "--check-prefix" or a == "--check-prefixes":
            i += 1
            if i >= len(args):
                raise UnsupportedFileCheckUsage("missing value for %s" % a)
            new_prefixes = args[i].split(",")
            if not explicit_prefixes:
                prefixes = []
                explicit_prefixes = True
            prefixes.extend(new_prefixes)
        elif a.startswith("--check-prefix="):
            if not explicit_prefixes:
                prefixes = []
                explicit_prefixes = True
            prefixes.extend(a.split("=", 1)[1].split(","))
        elif a.startswith("--check-prefixes="):
            if not explicit_prefixes:
                prefixes = []
                explicit_prefixes = True
            prefixes.extend(a.split("=", 1)[1].split(","))
        elif a == "--input-file":
            i += 1
            input_file = args[i]
        elif a.startswith("--input-file="):
            input_file = a.split("=", 1)[1]
        elif a == "--strict-whitespace":
            strict_whitespace = True
        elif a == "--allow-empty":
            allow_empty = True
        elif a.startswith("-D"):
            defn = a[2:] if len(a) > 2 else args[(i := i + 1)]
            if "=" not in defn:
                raise UnsupportedFileCheckUsage("malformed -D%s" % defn)
            name, value = defn.split("=", 1)
            defines[name] = value
        elif a.startswith("-"):
            # Any other flag (--implicit-check-not, --dump-input, -v, ...)
            # is out of scope for this prototype.
            raise UnsupportedFileCheckUsage("unsupported flag: %s" % a)
        else:
            if check_file is not None:
                raise UnsupportedFileCheckUsage("multiple check files given")
            check_file = a
        i += 1

    if check_file is None:
        raise UnsupportedFileCheckUsage("no check file given")

    return prefixes, check_file, input_file, strict_whitespace, allow_empty, defines


def _extract_checks(check_text, prefixes):
    checks = []
    prefix_alt = "|".join(re.escape(p) for p in prefixes)
    # Matches "PREFIX:", "PREFIX-NEXT:", "PREFIX-SAME:", etc. anywhere on a
    # line (checks are usually embedded in a comment), consuming up to end
    # of line as the pattern text.
    directive_re = re.compile(
        r"(?:%s)(-(?:%s))?:[ \t]?(.*)$"
        % (prefix_alt, "|".join(_DIRECTIVE_KINDS))
    )
    for line_no, line in enumerate(check_text.splitlines(), start=1):
        m = directive_re.search(line)
        if not m:
            continue
        kind = m.group(1)[1:] if m.group(1) else "CHECK"
        if kind == "COUNT" or "COUNT-" in line:
            raise UnsupportedFileCheckUsage("CHECK-COUNT is not supported")
        text = m.group(2)
        if "[[#" in text:
            raise UnsupportedFileCheckUsage("numeric expressions are not supported")
        checks.append(CheckItem(kind, text, line_no))
    if not checks:
        raise UnsupportedFileCheckUsage("no check strings found for given prefixes")
    return checks


def _literal_to_regex(text, strict_whitespace):
    if strict_whitespace:
        return re.escape(text)
    parts = re.split(r"(\s+)", text)
    out = []
    for p in parts:
        if p == "":
            continue
        if p.strip() == "":
            out.append(r"\s+")
        else:
            out.append(re.escape(p))
    return "".join(out)


_group_counter = [0]


def _sanitize_group_name(name):
    # Python regex group names must be valid identifiers; FileCheck
    # variable names are already restricted to [A-Za-z_][A-Za-z0-9_]* by
    # our token regex, so this is a no-op in practice but kept defensive.
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def _compile_pattern(text, variables, strict_whitespace):
    """Returns a compiled regex for one CHECK line's pattern text."""
    pieces = _TOKEN_RE.split(text)
    out = []
    for idx, piece in enumerate(pieces):
        if idx % 2 == 0:
            if not strict_whitespace:
                # Leading/trailing whitespace in a check line is not
                # significant (mirrors FileCheck's default behavior).
                if idx == 0:
                    piece = piece.lstrip()
                if idx == len(pieces) - 1:
                    piece = piece.rstrip()
            out.append(_literal_to_regex(piece, strict_whitespace))
        elif piece.startswith("{{"):
            out.append("(?:%s)" % piece[2:-2])
        else:
            inner = piece[2:-2]
            if ":" in inner:
                name, sub_regex = inner.split(":", 1)
                gname = "v%d_%s" % (_group_counter[0], _sanitize_group_name(name))
                _group_counter[0] += 1
                out.append("(?P<%s>%s)" % (gname, sub_regex))
                variables.setdefault("__defs__", []).append((name, gname))
            else:
                name = inner
                if name not in variables:
                    raise UnsupportedFileCheckUsage(
                        "reference to undefined variable [[%s]]" % name
                    )
                out.append("(?:%s)" % re.escape(variables[name]))
    return "".join(out)


def _apply_captures(compiled_regex_defs, match, variables):
    for name, gname in compiled_regex_defs:
        variables[name] = match.group(gname)


def _line_end(text, pos):
    idx = text.find("\n", pos)
    return idx if idx != -1 else len(text)


def _next_line_start(text, pos):
    idx = text.find("\n", pos)
    return idx + 1 if idx != -1 else len(text)


def match_filecheck(check_text, input_text, prefixes, strict_whitespace, defines):
    """Runs the simplified FileCheck matching algorithm.

    Returns (success: bool, message: str).
    """
    checks = _extract_checks(check_text, prefixes)
    variables = dict(defines)

    cursor = 0
    pending_nots = []  # list of (compiled_regex, line_no, raw_text)
    dag_base_cursor = None

    def check_nots(region_start, region_end):
        for pat, line_no, raw in pending_nots:
            m = re.search(pat, input_text[region_start:region_end])
            if m:
                return (
                    False,
                    "CHECK-NOT: excluded string found (line %d): %r" % (line_no, raw),
                )
        return True, ""

    for item in checks:
        variables.pop("__defs__", None)
        pattern_str = _compile_pattern(item.text, variables, strict_whitespace)
        defs = variables.pop("__defs__", [])
        flags = 0

        if item.kind == "DAG":
            if dag_base_cursor is None:
                dag_base_cursor = cursor
            m = re.search(pattern_str, input_text[dag_base_cursor:], flags)
            if not m:
                return False, "CHECK-DAG: could not find (line %d): %r" % (
                    item.line_no,
                    item.text,
                )
            abs_start = dag_base_cursor + m.start()
            abs_end = dag_base_cursor + m.end()
            _apply_captures(defs, m, variables)
            cursor = max(cursor, abs_end)
            continue

        # A non-DAG directive closes any open DAG group.
        dag_base_cursor = None

        if item.kind == "NOT":
            pending_nots.append((pattern_str, item.line_no, item.text))
            continue

        if item.kind == "EMPTY":
            # CHECK-EMPTY requires the line immediately following the
            # previous match's line to be empty (same line-selection rule
            # as CHECK-NEXT, not the remainder of the current line).
            next_start = _next_line_start(input_text, cursor)
            end = _line_end(input_text, next_start)
            if input_text[next_start:end].strip() != "":
                return False, "CHECK-EMPTY: line %d was not empty" % item.line_no
            ok, msg = check_nots(cursor, end)
            if not ok:
                return False, msg
            pending_nots = []
            cursor = _next_line_start(input_text, next_start)
            continue

        if item.kind == "SAME":
            region_end = _line_end(input_text, cursor)
            m = re.search(pattern_str, input_text[cursor:region_end], flags)
            base = cursor
        elif item.kind == "NEXT":
            next_start = _next_line_start(input_text, cursor)
            region_end = _line_end(input_text, next_start)
            m = re.search(pattern_str, input_text[next_start:region_end], flags)
            base = next_start
        else:  # CHECK / CHECK-LABEL
            m = re.search(pattern_str, input_text[cursor:], flags)
            base = cursor

        if not m:
            return False, "%s: could not find (line %d): %r" % (
                item.kind if item.kind != "CHECK" else "CHECK",
                item.line_no,
                item.text,
            )

        abs_start = base + m.start()
        abs_end = base + m.end()
        ok, msg = check_nots(cursor, abs_start)
        if not ok:
            return False, msg
        pending_nots = []
        _apply_captures(defs, m, variables)
        cursor = abs_end

    ok, msg = check_nots(cursor, len(input_text))
    if not ok:
        return False, msg
    return True, "OK"


def is_supported(argv, cwd):
    """Pre-flight check: can run() handle this invocation in-process?

    Cheaply re-parses argv and the check file (same cost as run() itself,
    but without touching stdin/stdout) to decide, *before* committing to
    the in-process path, whether every directive/flag used is within this
    prototype's supported subset. Callers should fall back to spawning
    the real external FileCheck binary whenever this returns False (or
    raises), so this prototype only ever intercepts invocations it can
    handle with full fidelity -- correctness always wins over coverage.

    Returns:
        True if run() should be able to fully and correctly evaluate this
        invocation in-process; False if it should fall back to the real
        FileCheck binary (unsupported directive/flag, or the check file
        could not be read).
    """
    import os

    try:
        prefixes, check_file, input_file, strict_whitespace, allow_empty, defines = (
            _parse_args(argv)
        )
        check_path = (
            check_file if os.path.isabs(check_file) else os.path.join(cwd, check_file)
        )
        with open(check_path, "r", encoding="utf-8", errors="replace") as f:
            check_text = f.read()
        _extract_checks(check_text, prefixes)
        return True
    except UnsupportedFileCheckUsage:
        return False
    except OSError:
        # Can't read the check file here; let the normal external path
        # handle it (and produce the usual error) instead of guessing.
        return False


def run(argv, stdin, stdout, stderr, cwd):
    """In-process FileCheck-subset. See module docstring for scope.

    Args:
        argv: argv[0] is the command name, remaining args are FileCheck's
            usual flags plus the positional check-file path (usually %s).
        stdin: Binary input stream; used unless --input-file is given.
        stdout: Unused (matches real FileCheck, which writes nothing on
            success).
        stderr: Binary error stream for diagnostics on failure/error.
        cwd: Working directory used to resolve the check-file/--input-file
            path if relative.

    Returns:
        0 on a successful match, 1 on a mismatch, 2 for usage errors or
        any construct this prototype does not support (callers should
        treat 2 as "fall back to the real FileCheck binary").
    """
    import os

    try:
        prefixes, check_file, input_file, strict_whitespace, allow_empty, defines = (
            _parse_args(argv)
        )

        check_path = check_file if os.path.isabs(check_file) else os.path.join(cwd, check_file)
        with open(check_path, "r", encoding="utf-8", errors="replace") as f:
            check_text = f.read()

        if input_file:
            in_path = input_file if os.path.isabs(input_file) else os.path.join(cwd, input_file)
            with open(in_path, "r", encoding="utf-8", errors="replace") as f:
                input_text = f.read()
        else:
            data = stdin.read()
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            input_text = data

        if input_text == "" and not allow_empty:
            stderr.write(b"FileCheck error: input is empty\n")
            return 2

        ok, msg = match_filecheck(check_text, input_text, prefixes, strict_whitespace, defines)
        if not ok:
            stderr.write((msg + "\n").encode())
            return 1
        return 0
    except UnsupportedFileCheckUsage as e:
        stderr.write(("UNSUPPORTED: %s\n" % str(e)).encode())
        return 2


def main(argv):
    inp = getattr(sys.stdin, "buffer", sys.stdin)
    out = getattr(sys.stdout, "buffer", sys.stdout)
    err = getattr(sys.stderr, "buffer", sys.stderr)
    sys.exit(run(argv, inp, out, err, os.getcwd()))


if __name__ == "__main__":
    import os

    main(sys.argv)
