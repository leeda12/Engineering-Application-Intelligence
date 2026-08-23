# Engineering methodology and calculation reference

Version `NTS-CALC-1.0` is a deliberately simplified preliminary screen.

- Thermal transfer: `Q_kW = mass_flow_kg_s × cp_kJ_kgK × delta_T_K`
- Required volumetric flow: `Q / (cp × delta_T × density)`, converted to L/min
- Thermal margin: `(available_capacity - required_heat_load) / required_heat_load × 100`
- Operating margin: minimum of thermal, flow, pressure-drop, footprint, and electrical checks
- Pressure boundary: architecture-specific predicted pressure drop must not exceed the customer limit
- Electrical/footprint/redundancy: exact controlled-rule compatibility checks
- Historical delta: normalized heat-load, flow, temperature, footprint, voltage, and redundancy differences

Coolant density/specific heat values and architecture limits live in `data/engineering_rules.json`; every table entry cites a fictional current manual source and revision. Execution never creates missing constants.

Only four statuses are emitted: `preliminarily_feasible`, `conditionally_feasible`, `insufficient_information`, and `outside_validated_range`. They never imply approval, certification, safety, guarantee, or production readiness.
