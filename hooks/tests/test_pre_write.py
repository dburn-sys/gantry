from helpers import decision, make_repo, run_hook

KEY = "k8f2Qz9LmV3xT7pW1sD4hJ6nB0cR5yUe"


def write(repo, path, content, env=None):
    return decision(run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
        "tool_input": {"file_path": str(repo / path), "content": content}}, repo, env))


def test_hardcoded_signing_key_refused(tmp_path):
    repo = make_repo(tmp_path)
    assert write(repo, "test/fixtures/auth.ts", f'export const signingKey = "{KEY}";') == "deny"


def test_runtime_generated_key_allowed(tmp_path):
    repo = make_repo(tmp_path)
    code = 'export const TEST_SIGNING_KEY = randomBytes(32).toString("hex");'
    assert write(repo, "test/fixtures/auth.ts", code) == "allow"


def test_placeholder_in_example_allowed(tmp_path):
    repo = make_repo(tmp_path)
    assert write(repo, ".env.example", 'TALLY_SIGNING_KEY="your-signing-key-here"') == "allow"


def test_allowlist_file_protected(tmp_path):
    repo = make_repo(tmp_path)
    assert write(repo, ".gantry/secrets-allow.txt", "k8f2***") == "deny"


def test_allowlisted_preview_passes(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "secrets-allow.txt").write_text(KEY[:4] + "***\n")
    assert write(repo, "src/x.ts", f'const apiKey = "{KEY}";') == "allow"


def test_plugin_files_protected(tmp_path):
    repo = make_repo(tmp_path)
    plugin = repo / "plugin"
    plugin.mkdir()
    assert write(repo, "plugin/hooks/pre_bash.py", "x = 1", {"CLAUDE_PLUGIN_ROOT": str(plugin)}) == "deny"
