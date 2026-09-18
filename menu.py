"""Menu machinery: the numbered lists and prompts nacre is driven by.

Three calls, agreeing on how a user backs out -- ctrl-c or ctrl-d, never a
blank line, which always just asks again -- so nothing built on them can
answer that question differently.

This is the one file in git-shell-commands/ that is not a command. Every
plain name in that directory is something a user can type at git-shell's
prompt, but git-shell refuses any name containing a dot, so a module can sit
beside the commands without becoming one. Importing it needs nothing else:
nacre runs from this directory, so it is already on the path.
"""

PAGE = 10                      # menu rows per page, once a list outgrows one


def prompt(text: str, default: str = "") -> str | None:
    """Read one stripped line, or None if the user backs out (ctrl-c,
    ctrl-d). A blank line yields default."""
    try:
        ans = input(text).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    return ans or default


def confirm(text: str) -> bool:
    """A [y/N] question: only an explicit yes is a yes, so backing out
    declines."""
    ans = prompt(f"{text} [y/N] ")
    return ans is not None and ans.lower().startswith("y")


def choose(header: str, items: list[str]) -> int | None:
    """Print a numbered menu and return the chosen 0-based index, or None
    if the user backs out.

    A list longer than PAGE is shown a page at a time, entered as "prev..."
    at 0 and "next..." just past the last row; the rows stay numbered
    1..PAGE on every page, so a number means the same row wherever you are
    in the list. No caller opts in, because the lists that can grow are the
    ones nobody thinks about -- repositories and projects accumulate, and a
    menu that outgrows a page starts paging on its own rather than running
    off the top of the terminal.
    """
    if not items:
        return None
    offset = 0
    while True:
        window = items[offset:offset + PAGE]
        print(header)
        lo = 1
        if offset:
            lo = 0
            print(f"{0:>3}. prev...")
        for n, label in enumerate(window, 1):
            print(f"{n:>3}. {label}")
        hi = len(window)
        nxt = 0
        if offset + PAGE < len(items):
            hi += 1
            nxt = hi
            print(f"{hi:>3}. next...")
        while True:
            ans = prompt("> ")
            if ans is None:
                return None
            if not ans:
                continue
            if ans.isdigit() and lo <= int(ans) <= hi:
                break
            print(f"  pick {lo}-{hi}")
        i = int(ans)
        if nxt and i == nxt:
            offset += PAGE
        elif i == 0:
            offset -= PAGE
        else:
            return offset + i - 1
