from pathlib import Path
import sys


def bootstrap_src() -> None:
    """Add the repository src directory to sys.path for direct script execution."""

    src_path = Path(__file__).resolve().parents[1] / "src"
    src_path_text = str(src_path)

    if src_path_text not in sys.path:
        sys.path.insert(0, src_path_text)
