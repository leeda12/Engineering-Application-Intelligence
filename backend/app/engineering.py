from __future__ import annotations
from .data import rules
from .schemas import Requirements, ValidationIssue, ValidationResult, Calculation, PreliminaryStatus

CRITICAL=("heat_load_kw","coolant_type","coolant_concentration_pct","coolant_inlet_temp_c","max_outlet_temp_c","ambient_temp_c","available_flow_lpm","max_pressure_drop_kpa","supply_voltage_v","frequency_hz","max_width_mm","max_depth_mm","max_height_mm","redundancy")

def validate_requirements(req:Requirements)->ValidationResult:
    cfg=rules(); envelope=cfg["validated_envelope"]; issues=[]
    missing=[x for x in CRITICAL if getattr(req,x) is None]
    for field in missing: issues.append(ValidationIssue(code="missing_required",field=field,severity="critical",message=f"{field.replace('_',' ')} is required for preliminary analysis.",source_ids=["PROC-REV-001"]))
    contradictions=[]
    if req.coolant_inlet_temp_c is not None and req.max_outlet_temp_c is not None and req.max_outlet_temp_c<=req.coolant_inlet_temp_c:
        contradictions.append("max_outlet_temp_c"); issues.append(ValidationIssue(code="temperature_contradiction",field="max_outlet_temp_c",severity="critical",message="Maximum outlet temperature must exceed inlet temperature.",source_ids=["MAN-THERM-002"]))
    outside=[]
    checks=(("heat_load_kw",req.heat_load_kw,envelope["min_heat_kw"],envelope["max_heat_kw"]),("coolant_inlet_temp_c",req.coolant_inlet_temp_c,envelope["min_inlet_c"],envelope["max_inlet_c"]),("ambient_temp_c",req.ambient_temp_c,None,envelope["max_ambient_c"]),("coolant_concentration_pct",req.coolant_concentration_pct,None,envelope["max_glycol_pct"]))
    for field,value,low,high in checks:
        if value is not None and ((low is not None and value<low) or value>high):
            outside.append(field); issues.append(ValidationIssue(code="outside_validated_range",field=field,severity="critical",message=f"{field.replace('_',' ')} is outside the current validated envelope.",source_ids=[envelope["source_id"]]))
    return ValidationResult(requirements=req,issues=issues,missing_critical=missing,has_contradiction=bool(contradictions),outside_validated_range=bool(outside))

def coolant_properties(req:Requirements)->dict|None:
    if req.coolant_type is None or req.coolant_concentration_pct is None: return None
    concentration=str(int(req.coolant_concentration_pct))
    return rules()["coolants"].get(req.coolant_type,{}).get(concentration)

def select_architecture(req:Requirements)->str|None:
    if req.heat_load_kw is None: return None
    for key in ("single_loop","dual_loop","modular_array"):
        a=rules()["architectures"][key]
        if req.heat_load_kw<=a["capacity_kw"] and req.redundancy in a["redundancy"]: return key
    return None

def calculate(req:Requirements,architecture:str|None)->list[Calculation]:
    if architecture is None: return []
    a=rules()["architectures"][architecture]; props=coolant_properties(req); out=[]
    if props and req.heat_load_kw and req.coolant_inlet_temp_c is not None and req.max_outlet_temp_c is not None:
        dt=req.max_outlet_temp_c-req.coolant_inlet_temp_c
        required=None if dt<=0 else req.heat_load_kw/(props["cp_kj_kgk"]*dt*props["density_kg_l"])*60
        out.append(Calculation(calculation_id="CALC-FLOW",label="Required flow",expression="Q / (cp × ΔT × density) × 60",result=round(required,2) if required else None,unit="L/min",passed=(req.available_flow_lpm>=required) if required and req.available_flow_lpm else None,source_ids=[props["source_id"]]))
    margin=(a["capacity_kw"]-req.heat_load_kw)/req.heat_load_kw*100 if req.heat_load_kw else None
    out.append(Calculation(calculation_id="CALC-THERMAL-MARGIN",label="Thermal capacity margin",expression="(architecture capacity − required load) / required load × 100",result=round(margin,1) if margin is not None else None,unit="%",passed=margin>=10 if margin is not None else None,source_ids=["VAL-001" if architecture=="single_loop" else "VAL-002" if architecture=="dual_loop" else "VAL-003"]))
    electrical=bool(req.supply_voltage_v in a["voltages"] and req.frequency_hz in (50,60)) if req.supply_voltage_v and req.frequency_hz else False
    out.append(Calculation(calculation_id="CALC-ELECTRICAL",label="Electrical compatibility",expression="supply ∈ architecture voltage table and frequency ∈ {50,60}",result=electrical,passed=electrical,source_ids=["MAN-CONTROL-001","BUL-FAIL-003"]))
    footprint=bool(req.max_width_mm and req.max_depth_mm and req.max_height_mm and req.max_width_mm>=a["min_width_mm"] and req.max_depth_mm>=a["min_depth_mm"] and req.max_height_mm>=a["min_height_mm"])
    out.append(Calculation(calculation_id="CALC-FOOTPRINT",label="Footprint compatibility",expression="customer maxima ≥ architecture envelope",result=footprint,passed=footprint,source_ids=["VAL-005","BUL-FAIL-004"] if req.redundancy=="2n" else ["VAL-005"]))
    pressure=bool(req.max_pressure_drop_kpa and req.max_pressure_drop_kpa>=a["pressure_drop_kpa"])
    out.append(Calculation(calculation_id="CALC-PRESSURE",label="Pressure-drop boundary",expression=f"allowable pressure drop ≥ {a['pressure_drop_kpa']} kPa architecture estimate",result=a["pressure_drop_kpa"],unit="kPa",passed=pressure,source_ids=["VAL-001" if architecture=="single_loop" else "VAL-002" if architecture=="dual_loop" else "VAL-003"]))
    redundancy=req.redundancy in a["redundancy"]
    out.append(Calculation(calculation_id="CALC-REDUNDANCY",label="Redundancy compatibility",expression="requested redundancy ∈ architecture capability",result=redundancy,passed=redundancy,source_ids=["MAN-CONTROL-001","BUL-FAIL-004"]))
    return out

def status_for(validation:ValidationResult,calculations:list[Calculation])->PreliminaryStatus:
    if validation.missing_critical or validation.has_contradiction: return PreliminaryStatus.INSUFFICIENT_INFORMATION
    if validation.outside_validated_range: return PreliminaryStatus.OUTSIDE_VALIDATED_RANGE
    if any(x.passed is False for x in calculations): return PreliminaryStatus.CONDITIONALLY_FEASIBLE
    if any(x.calculation_id=="CALC-THERMAL-MARGIN" and isinstance(x.result,float) and x.result<15 for x in calculations): return PreliminaryStatus.CONDITIONALLY_FEASIBLE
    return PreliminaryStatus.PRELIMINARILY_FEASIBLE
