"""Keep tests off real credentials and the network."""

import pytest

SECRET_ENV = (
    "X_API_KEY",
    "X_API_SECRET",
    "QUEEN_ACCESS_TOKEN",
    "QUEEN_ACCESS_TOKEN_SECRET",
    "XAI_API_KEY",
    "OPENAI_API_KEY",
    "XAI_MODEL",
    "OPENAI_MODEL",
)


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    monkeypatch.setenv("FURBYBOTS_SKIP_DOTENV", "1")
    monkeypatch.setenv("FURBYBOTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FURBYBOTS_TOKEN_DIR", str(tmp_path / "tokens"))
    for name in SECRET_ENV:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def queen_env(monkeypatch):
    monkeypatch.setenv("X_API_KEY", "test-api-key")
    monkeypatch.setenv("X_API_SECRET", "test-api-secret")
    monkeypatch.setenv("QUEEN_ACCESS_TOKEN", "test-access-token")
    monkeypatch.setenv("QUEEN_ACCESS_TOKEN_SECRET", "test-access-secret")
