import shutil
from pathlib import Path


def apply_harness(harness_path: Path, output_dir: Path) -> list[str]:
    applied: list[str] = []

    claude_md = harness_path / "CLAUDE.md"
    if claude_md.is_file():
        dest_name = "CLAUDE.md" if not (output_dir / "CLAUDE.md").exists() else "CLAUDE.harness.md"
        dest = output_dir / dest_name
        _move_file(claude_md, dest)
        applied.append(str(dest))

    for entry in sorted(harness_path.iterdir()):
        if entry.name == "CLAUDE.md":
            continue
        applied.extend(_merge_into(entry, output_dir / entry.name))

    shutil.rmtree(harness_path)
    return applied


def _merge_into(src: Path, dst: Path) -> list[str]:
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        moved: list[str] = []
        for child in sorted(src.iterdir()):
            moved.extend(_merge_into(child, dst / child.name))
        return moved

    _move_file(src, dst)
    return [str(dst)]


def _move_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
