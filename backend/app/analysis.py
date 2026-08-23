from __future__ import annotations
from .engineering import validate_requirements,select_architecture,calculate,status_for
from .retrieval import rank_projects
from .schemas import AnalysisRequest,AnalysisResponse,Claim,RankRequest,PreliminaryStatus

def analyze(request:AnalysisRequest)->AnalysisResponse:
    req=request.requirements; validation=validate_requirements(req); arch=select_architecture(req); calculations=calculate(req,arch); status=status_for(validation,calculations)
    _,projects=rank_projects(RankRequest(requirements=req,query_embedding=request.query_embedding,limit=8))
    closest=next((x for x in projects if x.recommendation_eligible),None)
    claims=[]
    claims.append(Claim(claim_id="CLAIM-STATUS",category="system_inference",text=f"The controlled preliminary status is {status.value.replace('_',' ')}.",source_ids=["PROC-REV-001"]))
    if closest:
        claims.append(Claim(claim_id="CLAIM-PRECEDENT",category="historical_evidence",text=f"{closest.source_id} is the closest eligible fictional precedent; heat-load difference is {closest.differences['heat_load_kw']} kW and flow difference is {closest.differences['flow_lpm']} L/min.",source_ids=[closest.source_id]))
    for c in calculations:
        claims.append(Claim(claim_id=f"CLAIM-{c.calculation_id}",category="calculation",text=f"{c.label}: {c.result}{(' '+c.unit) if c.unit else ''}; boundary check {'passed' if c.passed else 'did not pass' if c.passed is False else 'could not be completed'}.",source_ids=c.source_ids))
    for issue in validation.issues:
        claims.append(Claim(claim_id=f"CLAIM-{issue.code}-{issue.field}",category="missing_information" if issue.code=="missing_required" else "engineering_rule",text=issue.message,source_ids=issue.source_ids))
    failed=[x for x in projects if not x.recommendation_eligible]
    if failed:
        claims.append(Claim(claim_id="CLAIM-DISQUALIFIED",category="failure",text=f"Relevant record {failed[0].source_id} remains evidence but is ineligible: {', '.join(failed[0].disqualification_reasons)}.",source_ids=[failed[0].source_id]+(["BUL-FAIL-002"] if failed[0].source_id=="PRJ-007" else [])))
    citations=sorted({sid for c in claims for sid in c.source_ids})
    headline={PreliminaryStatus.PRELIMINARILY_FEASIBLE:"Inputs fit the selected validated envelope and all completed boundary checks pass.",PreliminaryStatus.CONDITIONALLY_FEASIBLE:"The application needs engineering resolution of one or more margins or compatibility checks.",PreliminaryStatus.INSUFFICIENT_INFORMATION:"Critical information is missing or contradictory; no complete feasibility conclusion is supported.",PreliminaryStatus.OUTSIDE_VALIDATED_RANGE:"At least one requirement exceeds the current fictional validated envelope."}[status]
    assessment=f"{headline} Proposed preliminary architecture: {arch or 'not selected'}. " + (f"Closest eligible precedent: {closest.source_id}. " if closest else "No eligible historical starting design is supported. ") + "A qualified reviewer must inspect the cited requirements, rules, calculations, exclusions, and concept schematic before any concept-review action."
    return AnalysisResponse(application_id=req.application_id,status=status,proposed_architecture=arch,closest_valid_project_id=closest.source_id if closest else None,calculations=calculations,claims=claims,missing_requirements=validation.missing_critical,contradictions=[x.field for x in validation.issues if "contradiction" in x.code],evidence_source_ids=citations,calculation_version="NTS-CALC-1.0",assessment=assessment,review_required="Qualified human engineering concept review required; this preliminary result is not a manufacturing release.")
