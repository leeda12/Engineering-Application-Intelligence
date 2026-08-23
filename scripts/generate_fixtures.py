"""Generate deterministic, entirely fictional corpus and controlled PDF fixtures."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

ARCHITECTURES = {
    "single_loop": {
        "name": "Aquila SL-90 single-loop CDU",
        "topology": "One shared customer cooling circuit with no hydraulic isolation heat exchanger.",
        "topology_source_id": "MAN-THERM-002",
        "capacity_kw": 120, "max_flow_lpm": 150, "pressure_drop_kpa": 24,
        "voltages": [208, 400], "redundancy": ["none", "n+1_pumps"],
        "min_width_mm": 620, "min_depth_mm": 900, "min_height_mm": 1750,
    },
    "dual_loop": {
        "name": "Borealis DL-240 facility-isolated CDU",
        "topology": "Two hydraulically isolated facility-side and customer-side circuits exchanging heat only across a plate heat exchanger.",
        "topology_source_id": "MAN-THERM-002",
        "capacity_kw": 260, "max_flow_lpm": 310, "pressure_drop_kpa": 32,
        "voltages": [400, 480], "redundancy": ["n+1_pumps", "2n"],
        "min_width_mm": 980, "min_depth_mm": 1100, "min_height_mm": 1980,
    },
    "modular_array": {
        "name": "Cirrus MA-400 modular cooling array",
        "topology": "A facility header feeding parallel isolated cooling modules with separate customer branches.",
        "topology_source_id": "MAN-THERM-002",
        "capacity_kw": 400, "max_flow_lpm": 480, "pressure_drop_kpa": 45,
        "voltages": [400, 480], "redundancy": ["n+1_pumps", "2n"],
        "min_width_mm": 1600, "min_depth_mm": 1200, "min_height_mm": 2100,
    },
}

APPS = [
    {"application_id":"APP-001","scenario":"clearly_feasible","heat_load_kw":"180","coolant_type":"propylene_glycol","coolant_concentration_pct":"25","coolant_inlet_temp_c":"20","max_outlet_temp_c":"32","ambient_temp_c":"35","available_flow_lpm":"245","max_pressure_drop_kpa":"38","supply_voltage_v":"400","frequency_hz":"50","max_width_mm":"1200","max_depth_mm":"1300","max_height_mm":"2100","redundancy":"n+1_pumps","communication_protocol":"Modbus TCP","environmental_rating":"IP54","customer_notes":"Fictional compute hall B; facility-water isolation required."},
    {"application_id":"APP-002","scenario":"conditionally_feasible","heat_load_kw":"110","coolant_type":"water","coolant_concentration_pct":"0","coolant_inlet_temp_c":"22","max_outlet_temp_c":"28","ambient_temp_c":"39","available_flow_lpm":"285","max_pressure_drop_kpa":"26","supply_voltage_v":"400","frequency_hz":"50","max_width_mm":"1000","max_depth_mm":"1150","max_height_mm":"2000","redundancy":"n+1_pumps","communication_protocol":"BACnet/IP","environmental_rating":"IP44","customer_notes":"Fictional lab expansion; acoustic review required."},
    {"application_id":"APP-003","scenario":"missing_critical_information","heat_load_kw":"95","coolant_type":"propylene_glycol","coolant_concentration_pct":"20","coolant_inlet_temp_c":"20","max_outlet_temp_c":"","ambient_temp_c":"32","available_flow_lpm":"","max_pressure_drop_kpa":"35","supply_voltage_v":"208","frequency_hz":"60","max_width_mm":"800","max_depth_mm":"1000","max_height_mm":"1900","redundancy":"none","communication_protocol":"Modbus TCP","environmental_rating":"IP44","customer_notes":"Outlet limit and available flow pending."},
    {"application_id":"APP-004","scenario":"outside_validated_range","heat_load_kw":"465","coolant_type":"water","coolant_concentration_pct":"0","coolant_inlet_temp_c":"18","max_outlet_temp_c":"25","ambient_temp_c":"46","available_flow_lpm":"520","max_pressure_drop_kpa":"55","supply_voltage_v":"480","frequency_hz":"60","max_width_mm":"2200","max_depth_mm":"1500","max_height_mm":"2300","redundancy":"2n","communication_protocol":"EtherNet/IP","environmental_rating":"IP54","customer_notes":"Demand exceeds fictional validated architecture range."},
    {"application_id":"APP-005","scenario":"contradictory_requirements","heat_load_kw":"140","coolant_type":"propylene_glycol","coolant_concentration_pct":"30","coolant_inlet_temp_c":"29","max_outlet_temp_c":"25","ambient_temp_c":"36","available_flow_lpm":"160","max_pressure_drop_kpa":"20","supply_voltage_v":"208","frequency_hz":"50","max_width_mm":"700","max_depth_mm":"950","max_height_mm":"1800","redundancy":"2n","communication_protocol":"Modbus TCP","environmental_rating":"IP54","customer_notes":"Outlet temperature is stated below inlet; 2N requested in single-loop footprint."},
]

def source(source_id, title, kind, revision, date, locator, status, arch, text, constraints=None, provenance=None, **extra):
    return {"source_id":source_id,"title":title,"document_type":kind,"revision":revision,"effective_date":date,"locator":locator,"status":status,"product_architecture":arch,"text":text,"applicable_constraints":constraints or {},"provenance":provenance or {"origin":"fictional Northstar controlled corpus","created_for":"portfolio demonstration"},**extra}

def build_corpus():
    records=[]
    heat_values=[72,95,118,145,205,255,160,88,310,225,105,175,198,340,65,150,275,125,235,385,115,290,82,180]
    flows=[90,112,142,170,245,300,155,108,365,270,130,210,235,405,80,180,325,150,282,455,138,340,100,240]
    for i,(heat,flow) in enumerate(zip(heat_values,flows),1):
        arch="single_loop" if heat<=125 else ("dual_loop" if heat<=260 else "modular_array")
        status="historical"
        outcome="passed"
        evidence=[f"VAL-{((i-1)%6)+1:03d}"]
        notes="Completed fictional acceptance validation with traceable thermal and hydraulic evidence."
        if i==7:
            outcome="failed"; notes="Failed validation after pump inlet cavitation at the specified low static head; corrective bulletin applies."; evidence=["VAL-004","BUL-FAIL-002"]
        if i==16:
            outcome="missing_evidence"; notes="Thermal run sheet is absent; record is relevant but ineligible as a recommendation."; evidence=[]
        if i==19:
            notes="Thermally comparable but disqualified for a 480 V-only panel and a 1450 mm width envelope."
        if i==24:
            notes="Near-exact current precedent for APP-001 with facility isolation, N+1 pumps, 400 V, IP54, and Modbus TCP."
        records.append(source(
            f"PRJ-{i:03d}", f"Project Polaris {i:02d} — fictional cooling application", "historical_project", "A", f"202{1+(i%5)}-{1+(i%9):02d}-15", "Project summary pp. 1–4", status, arch,
            f"{notes} Design duty {heat} kW at {flow} L/min using {'water' if i%3==0 else '25% propylene glycol'}. Architecture {ARCHITECTURES[arch]['name']}.",
            {"heat_load_kw":heat,"flow_lpm":flow},
            validation_outcome=outcome, validation_evidence_ids=evidence,
            project_parameters={"heat_load_kw":heat,"flow_lpm":flow,"inlet_temp_c":20 if i==24 else 18+(i%5),"outlet_temp_c":32 if i==24 else 26+(i%4),"pressure_drop_kpa":ARCHITECTURES[arch]["pressure_drop_kpa"]+(i%3-1)*2,"voltage_v":480 if i in (9,19,20) else (208 if arch=="single_loop" else 400),"frequency_hz":50 if i==24 else (60 if i%4==0 else 50),"width_mm":1450 if i==19 else ARCHITECTURES[arch]["min_width_mm"]+(i%3)*80,"depth_mm":ARCHITECTURES[arch]["min_depth_mm"],"height_mm":ARCHITECTURES[arch]["min_height_mm"],"redundancy":"2n" if heat>300 else ("n+1_pumps" if heat>120 else "none"),"communication_protocol":"Modbus TCP" if i%2==0 else "BACnet/IP","environmental_rating":"IP54" if i==24 or i%3 else "IP44"}
        ))
    records += [
        source("MAN-THERM-001","Thermal Application Manual","manual","1.4","2022-03-01","§3.2 pp. 18–22","superseded","all","Allowed propylene glycol concentration through 40% and ambient temperature through 45 °C. This revision is superseded and must not control selection.",{"max_glycol_pct":40,"max_ambient_c":45}),
        source("MAN-THERM-002","Thermal Application Manual","manual","2.1","2026-01-10","§3.2 pp. 20–25","current","all","Current validated envelope: heat load 40–400 kW, ambient 5–42 °C, propylene glycol 0–35%, inlet 15–30 °C. Applications outside require additional information and new validation.",{"min_heat_kw":40,"max_heat_kw":400,"max_ambient_c":42,"max_glycol_pct":35}),
        source("MAN-CONTROL-001","Electrical and Controls Integration Manual","manual","1.3","2025-11-04","§4–7 pp. 30–58","current","all","Supported supplies are architecture-specific at 50 or 60 Hz. Current protocols: Modbus TCP, BACnet/IP, and EtherNet/IP. 2N controls require dual-loop or modular architecture."),
        source("VAL-001","Aquila SL-90 thermal validation","validation_report","B","2025-02-12","Test 4 pp. 11–16","current","single_loop","Passed 120 kW steady-state duty and 150 L/min flow boundary with water and 25% propylene glycol."),
        source("VAL-002","Borealis DL-240 thermal validation","validation_report","C","2026-02-20","Tests 6–9 pp. 18–31","current","dual_loop","Passed 260 kW thermal duty, 310 L/min, N+1 pump changeover, 400/480 V panels, and IP54 enclosure tests."),
        source("VAL-003","Cirrus MA-400 thermal validation","validation_report","B","2026-04-08","Tests 2–10 pp. 9–38","current","modular_array","Passed 400 kW and 480 L/min validated boundary with 2N control paths at 400 and 480 V."),
        source("VAL-004","Low-static-head pump investigation","validation_report","A","2024-07-19","Failure run 7 pp. 14–19","historical","dual_loop","PRJ-007 failed: pump inlet cavitation caused unstable flow. The configuration is prohibited without corrected inlet head."),
        source("VAL-005","Footprint and service-clearance verification","validation_report","A","2025-08-22","§5 pp. 12–17","current","all","Minimum stated product envelopes exclude site service clearance; customer maximum dimensions must contain the equipment envelope."),
        source("VAL-006","Extended-load exploratory trial","validation_report","DRAFT","2026-06-03","Draft §6 pp. 22–28","draft","modular_array","Exploratory 430 kW points are not validated and must not extend the current 400 kW operating envelope."),
        source("BUL-FAIL-001","Corrective bulletin: glycol seal compatibility","failure_bulletin","2","2025-10-10","Action 2 p. 3","current","all","Concentrations above 35% are outside the current validated seal-material envelope."),
        source("BUL-FAIL-002","Corrective bulletin: pump inlet cavitation","failure_bulletin","1","2024-08-01","Required action p. 2","current","dual_loop","Disqualify PRJ-007 as a starting configuration. Verify inlet static head and use revised pump inlet geometry."),
        source("BUL-FAIL-003","Corrective bulletin: 208 V contactor derating","failure_bulletin","1","2025-05-14","Applicability p. 1","current","single_loop","208 V is supported only by Aquila single-loop panels; it is incompatible with Borealis and Cirrus architectures."),
        source("BUL-FAIL-004","Corrective bulletin: compact 2N cabinet clearance","failure_bulletin","1","2026-03-12","Constraint p. 2","current","all","A 2N arrangement cannot be packaged below 980 mm width and requires dual-loop or modular controls."),
        source("REV-001","Revision notice: Thermal Manual 2.1","revision_notice","1","2026-01-10","Change table p. 1","current","all","MAN-THERM-002 supersedes MAN-THERM-001. Current glycol maximum is 35%, ambient maximum 42 °C.",{"supersedes":"MAN-THERM-001","current_source":"MAN-THERM-002"}),
        source("REV-002","Revision notice: glycol envelope reduction","revision_notice","1","2025-10-10","Change 04 p. 2","current","all","The former 40% glycol allowance is withdrawn; use 35% maximum pending further validation."),
        source("REV-003","Revision notice: controls protocol list","revision_notice","2","2026-02-01","Change 02 p. 1","current","all","EtherNet/IP added for Cirrus; supported protocol list aligned with MAN-CONTROL-001 revision 1.3."),
        source("PROC-REV-001","Preliminary engineering concept review procedure","procedure","3","2026-05-01","Steps 1–8 pp. 4–9","current","all","A qualified reviewer must inspect requirements, calculations, evidence, exclusions, and schematic. Missing critical fields or outside-range status prohibits approval for concept review."),
    ]
    return records

def build_rules():
    return {"calculation_version":"NTS-CALC-1.0","source_ids":["MAN-THERM-002","MAN-CONTROL-001","VAL-001","VAL-002","VAL-003","VAL-005","BUL-FAIL-003","BUL-FAIL-004"],"coolants":{"water":{"0":{"density_kg_l":0.998,"cp_kj_kgk":4.18,"source_id":"MAN-THERM-002"}},"propylene_glycol":{"20":{"density_kg_l":1.018,"cp_kj_kgk":3.82,"source_id":"MAN-THERM-002"},"25":{"density_kg_l":1.023,"cp_kj_kgk":3.72,"source_id":"MAN-THERM-002"},"30":{"density_kg_l":1.029,"cp_kj_kgk":3.61,"source_id":"MAN-THERM-002"},"35":{"density_kg_l":1.035,"cp_kj_kgk":3.48,"source_id":"MAN-THERM-002"}}},"validated_envelope":{"min_heat_kw":40,"max_heat_kw":400,"min_inlet_c":15,"max_inlet_c":30,"max_ambient_c":42,"max_glycol_pct":35,"source_id":"MAN-THERM-002"},"architectures":ARCHITECTURES}

def create_pdfs():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        print("reportlab unavailable; JSON fixtures generated, PDFs pending dependency installation")
        return
    out=DATA/"application_sheets"; out.mkdir(parents=True,exist_ok=True)
    labels=[("application_id","Application ID"),("heat_load_kw","Required heat load (kW)"),("coolant_type","Coolant type"),("coolant_concentration_pct","Coolant concentration (%)"),("coolant_inlet_temp_c","Coolant inlet temperature (°C)"),("max_outlet_temp_c","Maximum outlet temperature (°C)"),("ambient_temp_c","Ambient operating temperature (°C)"),("available_flow_lpm","Available flow (L/min)"),("max_pressure_drop_kpa","Maximum pressure drop (kPa)"),("supply_voltage_v","Supply voltage (V)"),("frequency_hz","Frequency (Hz)"),("max_width_mm","Maximum width (mm)"),("max_depth_mm","Maximum depth (mm)"),("max_height_mm","Maximum height (mm)"),("redundancy","Redundancy"),("communication_protocol","Communication protocol"),("environmental_rating","Environmental rating"),("customer_notes","Customer notes")]
    for app in APPS:
        path=out/f"{app['application_id']}_{app['scenario']}.pdf"; c=canvas.Canvas(str(path),pagesize=letter,invariant=1); c.setTitle(f"NTS-CAF-001 {app['application_id']} (FICTIONAL)")
        c.setFont("Helvetica-Bold",16); c.drawString(48,755,"NORTHSTAR THERMAL SYSTEMS — CUSTOMER APPLICATION FORM")
        c.setFont("Helvetica",8); c.drawString(48,740,"NTS-CAF-001 Rev 1 · CONTROLLED DIGITAL PDF · COMPLETELY FICTIONAL")
        y=712
        for name,label in labels:
            c.setFont("Helvetica",7); c.drawString(48,y+7,label)
            h=28 if name=="customer_notes" else 16; c.acroForm.textfield(name=name,value=app.get(name,""),x=245,y=y,width=315,height=h,borderWidth=0.5,fontName="Helvetica",fontSize=8,forceBorder=True)
            y-=34 if name=="customer_notes" else 25
        c.setFont("Helvetica-Bold",8); c.drawString(48,46,"PRELIMINARY INPUT — REQUIRES ENGINEERING REVIEW")
        c.save()

def main():
    (DATA/"corpus").mkdir(parents=True,exist_ok=True); (DATA/"fixtures").mkdir(parents=True,exist_ok=True); (DATA/"generated").mkdir(parents=True,exist_ok=True)
    (DATA/"corpus"/"sources.json").write_text(json.dumps(build_corpus(),indent=2),encoding="utf-8")
    (DATA/"fixtures"/"applications.json").write_text(json.dumps(APPS,indent=2),encoding="utf-8")
    (DATA/"engineering_rules.json").write_text(json.dumps(build_rules(),indent=2),encoding="utf-8")
    create_pdfs(); print(f"Generated {len(build_corpus())} source records and {len(APPS)} controlled applications")

if __name__ == "__main__": main()
