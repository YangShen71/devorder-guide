import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "skills/devorder-guide"


def run(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts/make_artifacts.py"), *args],
                          capture_output=True, text=True)


def test_build_produces_zip_with_required_files():
    r = run("--build")
    assert r.returncode == 0, r.stderr
    with zipfile.ZipFile(ROOT / "dist/devorder-guide.skill") as z:
        names = set(z.namelist())
    for req in ("SKILL.md", "src/guide_gate.py", "configs/constants.json",
                "configs/contract.json", "references/category-enum.md", "LICENSE"):
        assert req in names, f"包内缺少 {req}"


def test_build_produces_plugin_copy_and_marketplace():
    r = run("--build")
    assert r.returncode == 0, r.stderr
    plugin_json = json.loads((ROOT / "plugins/devorder-guide/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert plugin_json["name"] == "devorder-guide"
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_artifacts
    assert plugin_json["version"] == make_artifacts.version()  # 动态断言：始终等于 pyproject 真源（硬编码版本会在当前 0.5.26 时必红）
    mp = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert mp["plugins"][0]["name"] == "devorder-guide"
    assert (ROOT / "plugins/devorder-guide/SKILL.md").exists()


def test_check_detects_plugin_drift():
    run("--build")
    p = ROOT / "plugins/devorder-guide/src/guide_gate.py"
    original = p.read_bytes()
    p.write_bytes(b"# drift\n")
    try:
        r = run("--check")
        assert r.returncode != 0, "--check 必须检出 plugin 漂移"
    finally:
        p.write_bytes(original)
