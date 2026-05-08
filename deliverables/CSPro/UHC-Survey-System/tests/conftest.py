"""pytest config — adds the workspace root to sys.path so tests can import shared/*."""
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
