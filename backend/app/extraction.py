from __future__ import annotations
from io import BytesIO
from pypdf import PdfReader
from .schemas import Requirements

FORM_ID="NTS-CAF-001"
NUMERIC_FLOAT={"heat_load_kw","coolant_concentration_pct","coolant_inlet_temp_c","max_outlet_temp_c","ambient_temp_c","available_flow_lpm","max_pressure_drop_kpa","max_width_mm","max_depth_mm","max_height_mm"}
NUMERIC_INT={"supply_voltage_v","frequency_hz"}

def extract_controlled_pdf(content: bytes)->Requirements:
    if not content.startswith(b"%PDF"): raise ValueError("Only PDF files are accepted")
    reader=PdfReader(BytesIO(content),strict=True)
    metadata=str(reader.metadata or {})
    text=" ".join((p.extract_text() or "") for p in reader.pages)
    if FORM_ID not in text and FORM_ID not in metadata: raise ValueError(f"Unsupported PDF: expected controlled form {FORM_ID}")
    fields=reader.get_fields() or {}
    raw={name:str(info.get("/V","")).strip() for name,info in fields.items()}
    payload={}
    for name,value in raw.items():
        if name in NUMERIC_FLOAT: payload[name]=float(value) if value else None
        elif name in NUMERIC_INT: payload[name]=int(float(value)) if value else None
        else: payload[name]=value or None
    payload["customer_notes"]=payload.get("customer_notes") or ""
    return Requirements.model_validate(payload)
