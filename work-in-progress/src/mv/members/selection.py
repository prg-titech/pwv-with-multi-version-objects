from __future__ import annotations


VERSION_SELECTION_CONTINUITY = "continuity"
VERSION_SELECTION_LATEST = "latest"
VERSION_SELECTION_STRATEGIES = (
    VERSION_SELECTION_CONTINUITY,
    VERSION_SELECTION_LATEST,
)


def normalize_version_selection(strategy: str) -> str:
    if strategy not in VERSION_SELECTION_STRATEGIES:
        raise ValueError(
            f"Unknown class version selection strategy: {strategy!r}. "
            f"Expected one of {VERSION_SELECTION_STRATEGIES!r}"
        )
    return strategy
