"""Chapter 14: hash-chained logs show tampering."""
import sys

from helpers import HOOKS
from test_override import prompt, setup

sys.path.insert(0, str(HOOKS))
from _gantry import chain_verify  # noqa: E402


def test_tampering_breaks_the_chain(tmp_path):
    repo = setup(tmp_path)
    prompt(repo, "override G-EVIDENCE because first reason with enough words here")
    prompt(repo, "override G-EVIDENCE because second reason with enough words here")
    log = repo / ".gantry" / "overrides.log"
    lines = log.read_text().splitlines()
    lines[0] = lines[0].replace("first", "edited")
    log.write_text("\n".join(lines) + "\n")
    assert chain_verify(log) == 2
