"""A small shell lexer: splits a command line into simple commands. It never runs anything.

It understands quotes, escapes, pipes and lists (; && || & |), redirections, here-documents, command and
process substitution ($(...), `...`, <(...)), comments, loop and conditional keywords, and leading VAR=value
assignments. Text it cannot parse safely raises ParseError, and the caller must then fail closed.
Standard library only.
"""
import itertools
import re

_pipeline_ids = itertools.count()
MAX_DEPTH = 5
REDIRECT_OPS = {">", ">>", "<", "<<", "<<-", "<<<", ">&", "<&", "&>", "&>>", ">|"}
SEPARATORS = {";", "&&", "||", "&", "|", "|&", "\n", "(", ")", ";;"}
OPERATORS = sorted(REDIRECT_OPS | SEPARATORS, key=len, reverse=True)
RESERVED_PREFIX = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "esac", "{", "}", "!",
                   "time", "coproc"}
HEADER_WORDS = {"for", "case", "select", "function"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\+?=")


class ParseError(Exception):
    """The command line cannot be split reliably."""


class Simple:
    """One simple command: its words, assignments and redirections."""

    def __init__(self):
        self.words = []
        self.assignments = []
        self.redirects = []          # (operator, target)
        self.heredoc = None
        self.pipeline = 0
        self.via_substitution = False


def find_close(text, open_index):
    """Index of the ')' matching the '(' at open_index, skipping quotes and escapes."""
    depth, i, n = 0, open_index, len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            j = text.find("'", i + 1)
            if j == -1:
                raise ParseError("unbalanced single quote")
            i = j + 1
            continue
        if c == '"':
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
            i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ParseError("unbalanced parenthesis")


def read_double_quoted(text, start, subs):
    """Return (next_index, value) for the double-quoted string starting at text[start]."""
    out, j, n = [], start + 1, len(text)
    while j < n:
        c = text[j]
        if c == "\\" and j + 1 < n and text[j + 1] in '"\\$`\n':
            out.append("" if text[j + 1] == "\n" else text[j + 1])
            j += 2
        elif c == '"':
            return j + 1, "".join(out)
        elif c == "$" and text.startswith("$(", j) and not text.startswith("$((", j):
            k = find_close(text, j + 1)
            subs.append(text[j + 2:k])
            out.append("$(...)")
            j = k + 1
        elif c == "`":
            k = text.find("`", j + 1)
            if k == -1:
                raise ParseError("unbalanced backtick")
            subs.append(text[j + 1:k])
            out.append("`...`")
            j = k + 1
        else:
            out.append(c)
            j += 1
    raise ParseError("unbalanced double quote")


def lex(text):
    """Return (tokens, substitutions, heredoc_bodies). A token is ("word", text) or ("op", text)."""
    tokens, subs, bodies = [], [], {}
    buf, in_word, expect_delim, pending = [], False, None, []
    i, n = 0, len(text)

    def flush():
        nonlocal buf, in_word, expect_delim
        if in_word:
            word = "".join(buf)
            tokens.append(("word", word))
            if expect_delim is not None:
                pending.append((len(tokens) - 1, word, expect_delim))
                expect_delim = None
        buf, in_word = [], False

    while i < n:
        c = text[i]
        if c == "\\":
            if i + 1 < n and text[i + 1] == "\n":
                i += 2
                continue
            buf.append(text[i + 1] if i + 1 < n else "\\")
            in_word = True
            i += 2
            continue
        if c == "'":
            j = text.find("'", i + 1)
            if j == -1:
                raise ParseError("unbalanced single quote")
            buf.append(text[i + 1:j])
            in_word = True
            i = j + 1
            continue
        if c == '"':
            i, piece = read_double_quoted(text, i, subs)
            buf.append(piece)
            in_word = True
            continue
        if c == "$" and text.startswith("$((", i):
            j = text.find("))", i)
            if j == -1:
                raise ParseError("unbalanced arithmetic expansion")
            buf.append(text[i:j + 2])
            in_word = True
            i = j + 2
            continue
        if c == "$" and text.startswith("$(", i):
            j = find_close(text, i + 1)
            subs.append(text[i + 2:j])
            buf.append("$(...)")
            in_word = True
            i = j + 1
            continue
        if c == "$" and text.startswith("${", i):
            j = text.find("}", i)
            if j == -1:
                raise ParseError("unbalanced parameter expansion")
            buf.append(text[i:j + 1])
            in_word = True
            i = j + 1
            continue
        if c == "`":
            j = text.find("`", i + 1)
            if j == -1:
                raise ParseError("unbalanced backtick")
            subs.append(text[i + 1:j])
            buf.append("`...`")
            in_word = True
            i = j + 1
            continue
        if c in "<>" and text.startswith("(", i + 1):
            j = find_close(text, i + 1)
            subs.append(text[i + 2:j])
            buf.append(c + "(...)")
            in_word = True
            i = j + 1
            continue
        if c in " \t\r":
            flush()
            i += 1
            continue
        if c == "\n":
            flush()
            tokens.append(("op", "\n"))
            i += 1
            for index, delimiter, strip_tabs in pending:
                lines, found = [], False
                while i < n:
                    end = text.find("\n", i)
                    line = text[i:] if end == -1 else text[i:end]
                    i = n if end == -1 else end + 1
                    if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                        found = True
                        break
                    lines.append(line)
                bodies[index] = "\n".join(lines)
                if not found:
                    break
            pending.clear()
            continue
        if c == "#" and not in_word:
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        op = next((o for o in OPERATORS if text.startswith(o, i)), None)
        if op:
            if op in REDIRECT_OPS and in_word and "".join(buf).isdigit():
                buf, in_word = [], False          # a file descriptor number such as the 2 in 2>&1
            else:
                flush()
            tokens.append(("op", op))
            if op in ("<<", "<<-"):
                expect_delim = op == "<<-"
            i += len(op)
            continue
        buf.append(c)
        in_word = True
        i += 1
    flush()
    return tokens, subs, bodies


def finalize(cmd):
    words = cmd.words
    while words and words[0] in RESERVED_PREFIX:
        words = words[1:]
    if words and words[0] in HEADER_WORDS:
        words = []
    while words and ASSIGNMENT.match(words[0]):
        cmd.assignments.append(words[0])
        words = words[1:]
    cmd.words = words
    return cmd


def parse(text, depth=0):
    """Split text into a flat list of Simple commands, including those inside substitutions."""
    if depth > MAX_DEPTH:
        raise ParseError("commands are nested too deeply")
    tokens, subs, bodies = lex(text)
    commands, cur, pipeline = [], Simple(), next(_pipeline_ids)
    target_of = None

    def close(pipe):
        nonlocal cur, pipeline
        finalize(cur)
        if cur.words or cur.redirects:
            cur.pipeline = pipeline
            commands.append(cur)
        cur = Simple()
        if not pipe:
            pipeline = next(_pipeline_ids)

    for index, (kind, value) in enumerate(tokens):
        if kind == "word":
            if target_of is not None:
                cur.redirects.append((target_of, value))
                if target_of in ("<<", "<<-"):
                    cur.heredoc = bodies.get(index)
                target_of = None
            else:
                cur.words.append(value)
        elif value in REDIRECT_OPS:
            target_of = value
        else:
            target_of = None
            close(pipe=value in ("|", "|&"))
    close(pipe=False)
    for sub in subs:
        for inner in parse(sub, depth + 1):
            inner.via_substitution = True
            commands.append(inner)
    return commands
