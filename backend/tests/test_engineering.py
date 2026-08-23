import pytest
from backend.app.data import applications,rules
from backend.app.main import fixture_to_req
from backend.app.engineering import validate_requirements,coolant_properties,select_architecture,calculate,status_for
from backend.app.schemas import PreliminaryStatus

def req(index=0): return fixture_to_req(applications()[index])

def test_feasible_fixture_is_complete():
    result=validate_requirements(req(0)); assert not result.issues
def test_missing_fields_are_critical():
    result=validate_requirements(req(2)); assert set(result.missing_critical)=={"max_outlet_temp_c","available_flow_lpm"}
def test_temperature_contradiction_detected():
    result=validate_requirements(req(4)); assert result.has_contradiction
def test_outside_envelope_detected():
    result=validate_requirements(req(3)); assert result.outside_validated_range
def test_controlled_property_lookup():
    p=coolant_properties(req(0)); assert p=={"density_kg_l":1.023,"cp_kj_kgk":3.72,"source_id":"MAN-THERM-002"}
def test_no_silent_material_interpolation():
    r=req(0).model_copy(update={"coolant_concentration_pct":27}); assert coolant_properties(r) is None
def test_architecture_selection(): assert select_architecture(req(0))=="dual_loop"
def test_required_flow_formula():
    flow=next(x for x in calculate(req(0),"dual_loop") if x.calculation_id=="CALC-FLOW"); assert flow.result==236.5 and flow.passed is True
def test_thermal_margin_formula():
    margin=next(x for x in calculate(req(0),"dual_loop") if x.calculation_id=="CALC-THERMAL-MARGIN"); assert margin.result==44.4
def test_electrical_boundary():
    r=req(0).model_copy(update={"supply_voltage_v":208}); c=next(x for x in calculate(r,"dual_loop") if x.calculation_id=="CALC-ELECTRICAL"); assert c.passed is False
def test_footprint_boundary():
    r=req(0).model_copy(update={"max_width_mm":900}); c=next(x for x in calculate(r,"dual_loop") if x.calculation_id=="CALC-FOOTPRINT"); assert c.passed is False
def test_pressure_boundary():
    r=req(0).model_copy(update={"max_pressure_drop_kpa":31}); c=next(x for x in calculate(r,"dual_loop") if x.calculation_id=="CALC-PRESSURE"); assert c.passed is False
def test_status_precedence_missing_over_range():
    r=req(3).model_copy(update={"available_flow_lpm":None}); v=validate_requirements(r); assert status_for(v,[])==PreliminaryStatus.INSUFFICIENT_INFORMATION
