from __future__ import annotations

from html import escape

from .data import rules
from .engineering import select_architecture, validate_requirements
from .schemas import SchematicRequest


class SchematicGenerationError(ValueError):
    code = "schematic_generation_prohibited"


def _pump(x: int, y: int, label: str, classes: str) -> str:
    return (
        f'<g class="component pump {classes}" data-component="pump">'
        f'<circle cx="{x}" cy="{y}" r="24"/><text x="{x}" y="{y + 5}">{escape(label)}</text></g>'
    )


def _pump_pair(x: int, y: int, prefix: str, classes: str, redundancy: str | None) -> str:
    redundant = redundancy in ("n+1_pumps", "2n")
    primary = _pump(x, y - (30 if redundant else 0), f"{prefix}1", classes)
    if not redundant:
        return primary
    secondary = _pump(x, y + 34, f"{prefix}2", classes)
    if redundancy == "2n":
        return (
            f'<g class="pump-bank independent-trains {classes}" data-redundancy="2n-independent">'
            f'<path class="pipe branch" d="M{x - 65} {y}V{y - 30}H{x - 24} M{x - 65} {y}V{y + 34}H{x - 24} '
            f'M{x + 24} {y - 30}H{x + 65}V{y} M{x + 24} {y + 34}H{x + 65}V{y}"/>'
            f'<rect class="isolation-valve" x="{x - 52}" y="{y - 37}" width="14" height="14"/>'
            f'<rect class="isolation-valve" x="{x - 52}" y="{y + 27}" width="14" height="14"/>{primary}{secondary}</g>'
        )
    return (
        f'<g class="pump-bank {classes}" data-redundancy="parallel">'
        f'<path class="pipe branch" d="M{x - 65} {y} V{y - 30} H{x - 24} M{x - 65} {y} V{y + 34} H{x - 24} '
        f'M{x + 24} {y - 30} H{x + 65} V{y} M{x + 24} {y + 34} H{x + 65} V{y}"/>{primary}{secondary}</g>'
    )


def _frame(request: SchematicRequest) -> tuple[str, str]:
    r = request.requirements
    topology = rules()["architectures"][request.architecture]["topology"]
    width = int(r.max_width_mm or 0)
    depth = int(r.max_depth_mm or 0)
    height = int(r.max_height_mm or 0)
    opening = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 620" role="img" aria-labelledby="title desc" data-architecture="{escape(request.architecture)}" data-redundancy="{escape(str(r.redundancy))}"><title id="title">{escape(request.architecture)} preliminary cooling concept</title><desc id="desc">{escape(topology)}</desc><defs><marker id="flow-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" class="arrow"/></marker></defs><style>.bg{{fill:#f6f4ee}}.pipe{{fill:none;stroke:#176b74;stroke-width:7}}.return{{stroke:#c05a3c}}.facility{{stroke:#315f9b}}.branch{{stroke-width:5}}.component rect,.component circle{{fill:#fff;stroke:#172522;stroke-width:2}}.isolation{{fill:#fff9e8;stroke:#8b6b16;stroke-width:2;stroke-dasharray:7 5}}text{{font-family:Arial,sans-serif;fill:#172522;font-size:14px;text-anchor:middle}}.small{{font-size:11px;fill:#5e6a66}}.loop-label{{font-size:15px;font-weight:bold}}.warning{{fill:#a33b28;font-weight:bold;font-size:17px}}.arrow{{fill:#176b74}}</style><rect class="bg" width="980" height="620"/><text class="warning" x="490" y="32">PRELIMINARY CONCEPT — NOT FOR MANUFACTURING</text><text x="490" y="56">{escape(request.architecture.replace('_',' ').title())} · {escape(str(r.redundancy))} redundancy · {escape(r.application_id)}</text>'''
    closing = f'''<g class="component control-panel" data-component="control-panel"><rect x="365" y="490" width="250" height="64" rx="8"/><text x="490" y="518">Control panel</text><text x="490" y="539" class="small">{escape(str(r.supply_voltage_v))} V · {escape(str(r.communication_protocol))}</text></g><text x="760" y="579">Customer envelope: {width} W × {depth} D × {height} H mm</text><text class="small" x="760" y="600">NTS-SVG-1.1 · requirement envelope, not fabrication dimensions</text></svg>'''
    return opening, closing


def _single_loop(request: SchematicRequest) -> str:
    opening, closing = _frame(request)
    pumps = _pump_pair(325, 230, "P", "customer-pump", request.requirements.redundancy)
    return opening + f'''<g class="circuit customer-circuit" data-circuit="customer"><text class="loop-label" x="490" y="100">Shared customer cooling circuit</text><path class="pipe supply" marker-end="url(#flow-arrow)" d="M110 230H260M390 230H460M540 230H780"/><path class="pipe return" marker-end="url(#flow-arrow)" d="M780 340H110V260"/><g class="component reservoir" data-component="reservoir"><rect x="80" y="180" width="95" height="100" rx="8"/><text x="127" y="222">Reservoir</text><text class="small" x="127" y="242">shared loop</text></g>{pumps}<g class="component filter" data-component="filter"><rect x="460" y="198" width="80" height="64"/><text x="500" y="235">Filter</text></g><g class="component cooler" data-component="heat-rejection"><rect x="585" y="185" width="115" height="90" rx="6"/><path d="M600 205h85M600 225h85M600 245h85"/><text x="642" y="297">Heat rejection</text></g><g class="component load" data-component="load"><rect x="780" y="170" width="120" height="180" rx="8"/><text x="840" y="222">Customer load</text><text class="small" x="840" y="246">{escape(str(request.requirements.heat_load_kw))} kW</text></g></g>''' + closing


def _dual_loop(request: SchematicRequest) -> str:
    opening, closing = _frame(request)
    facility_pumps = _pump_pair(230, 225, "F", "facility-pump", request.requirements.redundancy)
    customer_pumps = _pump_pair(735, 225, "C", "customer-pump", request.requirements.redundancy)
    return opening + f'''<rect class="isolation" x="445" y="105" width="90" height="350" rx="8" data-boundary="hydraulic-isolation"/><text class="loop-label" x="245" y="100">Facility-side circuit</text><text class="loop-label" x="735" y="100">Customer/load-side circuit</text><g class="circuit facility-circuit" data-circuit="facility"><path class="pipe facility supply" marker-end="url(#flow-arrow)" d="M80 225H165M295 225H445"/><path class="pipe facility return" marker-end="url(#flow-arrow)" d="M445 360H80V260"/><g class="component facility-connection" data-component="facility-connection"><rect x="55" y="165" width="100" height="115" rx="8"/><text x="105" y="208">Facility water</text><text class="small" x="105" y="230">supply / return</text></g>{facility_pumps}</g><g class="component heat-exchanger" data-component="heat-exchanger"><rect x="460" y="165" width="60" height="225" rx="6"/><path d="M472 185h36M472 215h36M472 245h36M472 275h36M472 305h36M472 335h36M472 365h36"/><text class="small" x="490" y="414">Plate</text><text class="small" x="490" y="430">heat exchanger</text></g><g class="circuit customer-circuit" data-circuit="customer"><path class="pipe supply" marker-end="url(#flow-arrow)" d="M535 225H585M655 225H670M800 225H885"/><path class="pipe return" marker-end="url(#flow-arrow)" d="M885 360H535"/><g class="component filter" data-component="filter"><rect x="585" y="193" width="70" height="64"/><text x="620" y="230">Filter</text></g>{customer_pumps}<g class="component load" data-component="load"><rect x="835" y="155" width="100" height="225" rx="8"/><text x="885" y="220">Customer load</text><text class="small" x="885" y="244">{escape(str(request.requirements.heat_load_kw))} kW</text></g><g class="component reservoir" data-component="reservoir"><rect x="620" y="325" width="105" height="70" rx="8"/><text x="672" y="366">Reservoir</text></g></g><text class="small" x="490" y="468">HYDRAULIC ISOLATION BOUNDARY — circuits exchange heat only</text>''' + closing


def _modular_array(request: SchematicRequest) -> str:
    opening, closing = _frame(request)
    facility_pumps = _pump_pair(205, 210, "F", "facility-pump", request.requirements.redundancy)
    module_a_pumps = _pump_pair(675, 180, "A", "module-pump", request.requirements.redundancy)
    module_b_pumps = _pump_pair(675, 355, "B", "module-pump", request.requirements.redundancy)
    return opening + f'''<text class="loop-label" x="235" y="100">Facility header circuit</text><text class="loop-label" x="700" y="100">Parallel isolated customer modules</text><g class="circuit facility-circuit" data-circuit="facility"><path class="pipe facility supply" marker-end="url(#flow-arrow)" d="M70 210H140M270 210H390V155H455M390 210V335H455"/><path class="pipe facility return" marker-end="url(#flow-arrow)" d="M455 245H350V400H70V270M455 425H350"/><g class="component facility-connection" data-component="facility-connection"><rect x="45" y="180" width="100" height="110" rx="8"/><text x="95" y="222">Facility water</text><text class="small" x="95" y="244">header</text></g>{facility_pumps}</g><g class="module module-a" data-module="A"><rect class="isolation" x="455" y="125" width="455" height="145" rx="8"/><text x="520" y="148">Module A</text><g class="component heat-exchanger" data-component="heat-exchanger"><rect x="480" y="160" width="65" height="80"/><path d="M490 175h45M490 195h45M490 215h45"/></g><path class="pipe supply" marker-end="url(#flow-arrow)" d="M545 180H610M740 180H845"/><path class="pipe return" d="M845 235H545"/>{module_a_pumps}<g class="component load" data-component="load"><rect x="825" y="155" width="70" height="95"/><text x="860" y="190">Load A</text></g></g><g class="module module-b" data-module="B"><rect class="isolation" x="455" y="300" width="455" height="145" rx="8"/><text x="520" y="323">Module B</text><g class="component heat-exchanger" data-component="heat-exchanger"><rect x="480" y="335" width="65" height="80"/><path d="M490 350h45M490 370h45M490 390h45"/></g><path class="pipe supply" marker-end="url(#flow-arrow)" d="M545 355H610M740 355H845"/><path class="pipe return" d="M845 410H545"/>{module_b_pumps}<g class="component load" data-component="load"><rect x="825" y="330" width="70" height="95"/><text x="860" y="365">Load B</text></g></g>''' + closing


def generate_svg(request: SchematicRequest) -> str:
    validation = validate_requirements(request.requirements)
    selected = select_architecture(request.requirements)
    if validation.missing_critical or validation.has_contradiction or validation.outside_validated_range:
        raise SchematicGenerationError("A concept schematic cannot be generated for incomplete, contradictory, or outside-range requirements")
    if selected is None or request.architecture != selected:
        raise SchematicGenerationError("Requested architecture does not match the controlled architecture selection")
    generators = {"single_loop": _single_loop, "dual_loop": _dual_loop, "modular_array": _modular_array}
    return generators[request.architecture](request)
