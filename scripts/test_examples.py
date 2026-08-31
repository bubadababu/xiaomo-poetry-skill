from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ("shanxing", "tianjingsha-qiusi", "jingyesi")


def run(*args: str) -> None:
    command = [sys.executable, *args]
    print("RUN", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    for name in EXAMPLES:
        content = f"examples/{name}/content.json"
        output = f"outputs/{name}"
        run("scripts/validate_content.py", content)
        run("scripts/build_page_tasks.py", content, "--out", f"{output}/page-tasks.json")
        run("scripts/render_pages.py", content, "--out-dir", output)
        run("scripts/verify_output.py", content, output)
    print("3 首诗测试通过：共生成并验证 12 张 PNG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
