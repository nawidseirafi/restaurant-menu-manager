import subprocess
from pathlib import Path


def test_menu_selection_javascript():
    script = Path(__file__).parent / "js_selection_test.js"
    result = subprocess.run(["node", str(script)], check=True, text=True, capture_output=True)
    assert "selection tests passed" in result.stdout
