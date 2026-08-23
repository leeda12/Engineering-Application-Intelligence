import pytest

from backend.app.config import settings
from backend.app.repository import (
    FileVectorRepository,
    PgVectorConfigurationError,
    PgVectorRepository,
    repository,
)


def test_unconfigured_database_uses_honest_file_mode(monkeypatch):
    monkeypatch.setattr(settings,"database_url",None)
    monkeypatch.setattr(settings,"retrieval_mode","auto")
    selected=repository()
    assert isinstance(selected,FileVectorRepository)
    assert selected.mode=="compatibility_file_vector"


def test_explicit_postgresql_mode_requires_database_url(monkeypatch):
    monkeypatch.setattr(settings,"database_url",None)
    monkeypatch.setattr(settings,"retrieval_mode","postgresql")
    with pytest.raises(PgVectorConfigurationError,match="requires DATABASE_URL"):
        repository()


def test_configured_database_validation_failure_does_not_fall_back(monkeypatch):
    monkeypatch.setattr(settings,"database_url","postgresql://configured.invalid/example")
    monkeypatch.setattr(settings,"retrieval_mode","auto")

    def incompatible(self):
        raise PgVectorConfigurationError("incompatible test database")

    monkeypatch.setattr(PgVectorRepository,"validate_readiness",incompatible)
    with pytest.raises(PgVectorConfigurationError,match="incompatible test database"):
        repository()


def test_explicit_file_mode_can_ignore_database_configuration(monkeypatch):
    monkeypatch.setattr(settings,"database_url","postgresql://configured.invalid/example")
    monkeypatch.setattr(settings,"retrieval_mode","file")
    assert isinstance(repository(),FileVectorRepository)
