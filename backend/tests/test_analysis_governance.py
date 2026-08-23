from pathlib import Path
import pytest
from backend.app.config import ROOT
from backend.app.data import applications,corpus_by_id
from backend.app.main import fixture_to_req
from backend.app.analysis import analyze
from backend.app.schemas import AnalysisRequest,ReviewProposal,ReviewProposalRequest,ReviewDecisionRequest,ReviewAction
from backend.app.audit import ReviewActionProhibited,ReviewTransitionProhibited,decide,history
from backend.app.main import propose

def request(index,application_embedding):
    req=fixture_to_req(applications()[index]); return AnalysisRequest(requirements=req,query_embedding=application_embedding(req.application_id))
def test_every_claim_has_support(application_embedding):
    a=analyze(request(0,application_embedding)); assert all(c.source_ids for c in a.claims)
def test_every_citation_exists(application_embedding):
    a=analyze(request(0,application_embedding)); assert all(x in corpus_by_id() for x in a.evidence_source_ids)
def test_insufficient_information_is_explicit(application_embedding):
    a=analyze(request(2,application_embedding)); assert a.status.value=="insufficient_information" and a.missing_requirements
def test_outside_range_is_explicit(application_embedding):
    a=analyze(request(3,application_embedding)); assert a.status.value=="outside_validated_range"
def test_prohibited_approval():
    proposal=ReviewProposal(application_id="APP-003",proposed_architecture=None,evidence_source_ids=["PROC-REV-001"],calculation_version="NTS-CALC-1.0",approval_permitted=False,prohibited_reasons=["missing"],allowed_actions=[ReviewAction.RETURN,ReviewAction.REJECT])
    request=ReviewDecisionRequest(application_id="APP-003",proposal=proposal,action=ReviewAction.APPROVE,reviewer_note="Cannot approve.",idempotency_key="test-prohibited-approval")
    from backend.app.audit import ReviewActionProhibited
    with pytest.raises(ReviewActionProhibited): decide(request)
def test_idempotency_returns_same_event(tmp_path,monkeypatch):
    import backend.app.audit as audit
    monkeypatch.setattr(audit,"PATH",tmp_path/"audit.jsonl")
    proposal=ReviewProposal(application_id="APP-001",proposed_architecture="dual_loop",evidence_source_ids=["VAL-002"],calculation_version="NTS-CALC-1.0",approval_permitted=True,prohibited_reasons=[],allowed_actions=list(ReviewAction))
    request=ReviewDecisionRequest(application_id="APP-001",proposal=proposal,action=ReviewAction.RETURN,reviewer_note="Verify flow margin.",idempotency_key="test-idempotency-key")
    one,created=decide(request); two,created_again=decide(request); assert created and not created_again and one==two

@pytest.mark.parametrize("index",[2,3,4])
def test_invalid_scenarios_allow_return_and_reject_but_not_approval(index,application_embedding):
    proposal=propose(ReviewProposalRequest(analysis=analyze(request(index,application_embedding))))
    assert proposal.approval_permitted is False
    assert proposal.allowed_actions==[ReviewAction.RETURN,ReviewAction.REJECT]

@pytest.mark.parametrize("index",[2,3,4])
@pytest.mark.parametrize("action",[ReviewAction.RETURN,ReviewAction.REJECT])
def test_permitted_invalid_action_is_exactly_once(index,action,application_embedding):
    analysis=analyze(request(index,application_embedding)); proposal=propose(ReviewProposalRequest(analysis=analysis)); key=f"{analysis.application_id}-{action.value}-isolated"
    decision=ReviewDecisionRequest(application_id=analysis.application_id,proposal=proposal,action=action,reviewer_note="Valid fictional reviewer note.",idempotency_key=key)
    first,created=decide(decision); second,created_again=decide(decision)
    assert created is True and created_again is False and first==second and len(history(analysis.application_id))==1

def test_explicit_terminal_transition_is_prohibited(application_embedding):
    analysis=analyze(request(2,application_embedding)); proposal=propose(ReviewProposalRequest(analysis=analysis))
    first=ReviewDecisionRequest(application_id=analysis.application_id,proposal=proposal,action=ReviewAction.RETURN,reviewer_note="Request the missing input.",idempotency_key="transition-first-key")
    decide(first)
    second=ReviewDecisionRequest(application_id=analysis.application_id,proposal=proposal,action=ReviewAction.REJECT,reviewer_note="Attempt a second transition.",idempotency_key="transition-second-key")
    with pytest.raises(ReviewTransitionProhibited,match="additional_information_requested"): decide(second)
