import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugins" / "gantry" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
