import pytest
from _secrets import scan

GITHUB = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
LIVE = "sk_" + "live_" + "a1B2c3D4e5F6g7H8i9J0k1L2"
CLOUD = "AKIA" + "ABCDEFGH12345678"
RANDOM_32 = "k8f2Qz9LmV3xT7pW1sD4hJ6nB0cR5yUe"


@pytest.mark.parametrize("text,kind", [
    ("-----BEGIN RSA PRIVATE KEY-----", "private-key"),          # OB-1
    (f"token: {GITHUB}", "github-token"),                        # OB-2
    (f"key = {LIVE}", "payment-live-key"),                        # OB-3
    (f"id = {CLOUD}", "cloud-access-key"),                        # OB-4
    (f'signingKey = "{RANDOM_32}"', "assignment"),                # OB-5
])
def test_ob1_to_ob5_detects(text, kind):
    assert [f.kind for f in scan(text)] == [kind]


@pytest.mark.parametrize("text", [
    'password = "changeme-please"',       # OB-6 placeholder
    "apiKey: process.env.API_KEY",        # OB-7 reference
    'token = "short"',                    # OB-8 too short
    'token = "aaaaaaaaaaaaaaaa"',         # OB-9 low entropy
    "",                                   # OB-12 empty
])
def test_ob6_to_ob9_and_ob12_ignores(text):
    assert scan(text) == []


def test_ob10_preview_is_redacted():
    (finding,) = scan(f'signingKey = "{RANDOM_32}"')
    assert finding.preview == RANDOM_32[:4] + "***"


def test_ob11_line_numbers_are_one_based():
    text = "line one\nline two\n" + f'secret = "{RANDOM_32}"'
    (finding,) = scan(text)
    assert finding.line == 3
