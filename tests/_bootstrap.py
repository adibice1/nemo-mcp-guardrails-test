from pathlib import Path
import sys


def bootstrap_src() -> None:
    """Add repository src and scripts directories to sys.path for tests."""

    repo_root = Path(__file__).resolve().parents[1]
    paths = (
        repo_root / "src",
        repo_root / "scripts",
    )

    for path in paths:
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)
