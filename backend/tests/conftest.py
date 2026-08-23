import json,sys,uuid
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.generate_fixtures import main
main()

@pytest.fixture
def application_embedding():
    payload=json.loads((ROOT/"data/generated/embeddings.json").read_text(encoding="utf-8"))
    return lambda application_id: payload["application_queries"][application_id]

@pytest.fixture(autouse=True)
def isolated_audit_store(monkeypatch):
    import backend.app.audit as audit
    folder=ROOT/"data/generated/test-audit"
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/f"{uuid.uuid4().hex}.jsonl"
    monkeypatch.setattr(audit,"PATH",path)
    yield
    path.unlink(missing_ok=True)
    try: folder.rmdir()
    except OSError: pass
