# Max diff characters allowed in any single context payload.
# Priority on truncation: keep metadata + file list, trim the diff.
MAX_DIFF_CHARS = 30_000


def guard_diff(diff: str) -> str:
    if len(diff) <= MAX_DIFF_CHARS:
        return diff
    dropped = len(diff) - MAX_DIFF_CHARS
    return (
        diff[:MAX_DIFF_CHARS]
        + f"\n\n[DIFF TRUNCATED — {dropped:,} characters omitted."
        + " Use the get_pr_diff tool directly to fetch the full diff.]"
    )
