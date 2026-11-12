"""Chapter 14: committed migrations are read-only."""
from helpers import decision, git, run_hook
from test_override import setup


def test_committed_migration_cannot_be_edited(tmp_path):
    repo = setup(tmp_path, branch="spike/x")
    (repo / "migrations").mkdir()
    (repo / "migrations" / "001_init.sql").write_text("CREATE TABLE t (id int);\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "migration")
    def write(name):
        return decision(run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
            "tool_input": {"file_path": str(repo / "migrations" / name), "content": "x"}}, repo))
    assert write("001_init.sql") == "deny"
    assert write("002_next.sql") == "allow"
