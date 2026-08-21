import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "SKILL.md"
TRUTH = ROOT / "skills/devorder-guide/SKILL.md"


def test_mirror_matches_truth():
    if not MIRROR.exists():   # 镜像缺失时先构建（真源 TRUTH 由 T2 迁移保证存在）
        subprocess.run([sys.executable, str(ROOT / "scripts/make_artifacts.py"), "--build"], check=True)
    assert MIRROR.read_bytes() == TRUTH.read_bytes(), "根 SKILL.md 镜像 ≠ 真源，请运行 make_artifacts.py --build"


def test_mirror_is_generated_not_hand_edited():
    # 手工改动镜像后 --check 必须红
    original = MIRROR.read_bytes()
    MIRROR.write_bytes(original + b"\n# hand-edited drift\n")   # bytes 字面量仅限 ASCII（中文需 encode，第七轮修正）
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/make_artifacts.py"), "--check"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0, "--check 必须检出镜像漂移"
    finally:
        MIRROR.write_bytes(original)
