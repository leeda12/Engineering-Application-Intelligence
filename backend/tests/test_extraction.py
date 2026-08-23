from pathlib import Path
import pytest
from backend.app.extraction import extract_controlled_pdf
from backend.app.config import ROOT

def test_controlled_pdf_extracts_fields():
    path=next((ROOT/"data/application_sheets").glob("APP-001*.pdf")); req=extract_controlled_pdf(path.read_bytes()); assert req.application_id=="APP-001" and req.heat_load_kw==180
def test_non_pdf_rejected():
    with pytest.raises(ValueError,match="PDF"): extract_controlled_pdf(b"not a document")
