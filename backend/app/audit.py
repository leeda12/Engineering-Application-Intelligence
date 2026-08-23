from __future__ import annotations
import json
from datetime import datetime,timezone
from .config import ROOT
from .schemas import ReviewDecisionRequest,AuditEvent,ReviewAction

PATH=ROOT/"data/generated/audit.jsonl"

class ReviewDecisionError(ValueError):
    code="review_decision_conflict"

class ReviewActionProhibited(ReviewDecisionError):
    code="review_action_prohibited"

class ReviewTransitionProhibited(ReviewDecisionError):
    code="review_transition_prohibited"

class IdempotencyConflict(ReviewDecisionError):
    code="idempotency_conflict"

def history(application_id:str|None=None)->list[AuditEvent]:
    if not PATH.exists(): return []
    items=[AuditEvent.model_validate_json(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [x for x in items if application_id is None or x.application_id==application_id]
def decide(req:ReviewDecisionRequest)->tuple[AuditEvent,bool]:
    for existing in history():
        if existing.idempotency_key==req.idempotency_key:
            if existing.application_id!=req.application_id or existing.reviewer_action!=req.action: raise IdempotencyConflict("Idempotency key was already used for a different decision")
            return existing,False
    if req.application_id!=req.proposal.application_id:
        raise ReviewActionProhibited("Review application does not match the proposed application")
    if req.action not in req.proposal.allowed_actions:
        raise ReviewActionProhibited("Requested review action is not allowed by this proposal")
    if req.action==ReviewAction.APPROVE and not req.proposal.approval_permitted:
        raise ReviewActionProhibited("Approval is prohibited for this preliminary state")
    prior=history(req.application_id)
    before=prior[-1].after_state if prior else "proposed"
    if before!="proposed":
        raise ReviewTransitionProhibited(f"Review transition from {before} is prohibited")
    after={ReviewAction.APPROVE:"concept_review",ReviewAction.RETURN:"additional_information_requested",ReviewAction.REJECT:"preliminary_configuration_rejected"}[req.action]
    event=AuditEvent(timestamp=datetime.now(timezone.utc).isoformat(),application_id=req.application_id,proposed_architecture=req.proposal.proposed_architecture,evidence_source_ids=req.proposal.evidence_source_ids,calculation_version=req.proposal.calculation_version,reviewer_action=req.action,reviewer_note=req.reviewer_note,before_state=before,after_state=after,idempotency_key=req.idempotency_key)
    PATH.parent.mkdir(parents=True,exist_ok=True)
    with PATH.open("a",encoding="utf-8") as f: f.write(event.model_dump_json()+"\n")
    return event,True
