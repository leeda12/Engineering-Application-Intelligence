from xml.etree import ElementTree as ET

import pytest

from backend.app.data import applications
from backend.app.main import fixture_to_req
from backend.app.schemas import SchematicRequest
from backend.app.schematic import SchematicGenerationError,generate_svg


def parsed(svg): return ET.fromstring(svg)
def count(root,selector): return len(root.findall(selector))

def valid_requirements(architecture):
    if architecture=="single_loop": return fixture_to_req(applications()[1])
    if architecture=="dual_loop": return fixture_to_req(applications()[0])
    base=fixture_to_req(applications()[3])
    return base.model_copy(update={"heat_load_kw":350,"ambient_temp_c":40,"max_width_mm":1800,"max_depth_mm":1400,"max_height_mm":2200,"max_pressure_drop_kpa":50})

@pytest.mark.parametrize("architecture,expected_circuits,expected_exchangers",[("single_loop",1,0),("dual_loop",2,1),("modular_array",1,2)])
def test_architectures_have_distinct_controlled_topologies(architecture,expected_circuits,expected_exchangers):
    root=parsed(generate_svg(SchematicRequest(requirements=valid_requirements(architecture),architecture=architecture)))
    assert root.attrib["data-architecture"]==architecture
    assert count(root,".//*[@data-circuit]")==expected_circuits
    assert count(root,".//*[@data-component='heat-exchanger']")==expected_exchangers
    if architecture=="dual_loop": assert count(root,".//*[@data-boundary='hydraulic-isolation']")==1 and "Facility-side circuit" in "".join(root.itertext()) and "Customer/load-side circuit" in "".join(root.itertext())
    if architecture=="modular_array": assert {x.attrib["data-module"] for x in root.findall(".//*[@data-module]")}=={"A","B"}

def test_redundancy_changes_pump_arrangement_without_duplicate_coordinates():
    base=valid_requirements("dual_loop")
    n_plus_one=parsed(generate_svg(SchematicRequest(requirements=base,architecture="dual_loop")))
    two_n=parsed(generate_svg(SchematicRequest(requirements=base.model_copy(update={"redundancy":"2n"}),architecture="dual_loop")))
    assert count(n_plus_one,".//*[@data-redundancy='parallel']")==2
    assert count(two_n,".//*[@data-redundancy='2n-independent']")==2
    for root in (n_plus_one,two_n):
        coordinates=[(circle.attrib["cx"],circle.attrib["cy"]) for circle in root.findall(".//{http://www.w3.org/2000/svg}circle")]
        assert len(coordinates)==len(set(coordinates))

def test_dual_loop_pump_banks_connect_to_circuit_centerlines_and_labels_do_not_rotate():
    svg=generate_svg(SchematicRequest(requirements=valid_requirements("dual_loop"),architecture="dual_loop"))
    assert 'M80 225H165M295 225H445' in svg
    assert 'M535 225H585M655 225H670M800 225H885' in svg
    assert 'rotate(' not in svg
    assert '>Plate</text>' in svg and '>heat exchanger</text>' in svg

@pytest.mark.parametrize("index,architecture",[(2,"single_loop"),(3,"modular_array"),(4,"dual_loop")])
def test_prohibited_scenarios_do_not_generate_schematic(index,architecture):
    with pytest.raises(SchematicGenerationError): generate_svg(SchematicRequest(requirements=fixture_to_req(applications()[index]),architecture=architecture))
