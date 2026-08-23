from backend.app.data import applications,corpus
from backend.app.main import fixture_to_req
from backend.app.retrieval import search,rank_projects,eligibility,keyword_score
from backend.app.schemas import SearchRequest,RankRequest

def test_exact_identifier_retrieval():
    _,hits=search(SearchRequest(query="PRJ-024 exact precedent",limit=5)); assert hits[0].source_id=="PRJ-024"
def test_current_revision_ranks_over_superseded():
    _,hits=search(SearchRequest(query="MAN-THERM-001 MAN-THERM-002 current glycol envelope",limit=20)); ids=[x.source_id for x in hits]; assert ids.index("MAN-THERM-002")<ids.index("MAN-THERM-001")
def test_failed_project_disqualified():
    rec=next(x for x in corpus() if x["source_id"]=="PRJ-007"); ok,reasons=eligibility(rec); assert not ok and "failed validation" in reasons[0]
def test_missing_evidence_disqualified():
    rec=next(x for x in corpus() if x["source_id"]=="PRJ-016"); assert eligibility(rec)[0] is False
def component_value(project,name): return next(x for x in project.score_breakdown if x.name==name)
def test_rank_exposes_six_independently_traceable_components(application_embedding):
    req=fixture_to_req(applications()[0]); _,ranked=rank_projects(RankRequest(requirements=req,query_embedding=application_embedding(req.application_id),limit=5)); assert [x.name for x in ranked[0].score_breakdown]==["semantic_similarity","keyword_relevance","numerical_proximity","hard_constraint_compatibility","revision_status","validation_outcome"]
def test_recommended_project_never_failed(application_embedding):
    req=fixture_to_req(applications()[0]); _,ranked=rank_projects(RankRequest(requirements=req,query_embedding=application_embedding(req.application_id),limit=12)); first=next(x for x in ranked if x.recommendation_eligible); assert first.source_id not in {"PRJ-007","PRJ-016"}
def test_genuine_embedding_affects_rank_and_near_exact_precedent(application_embedding):
    req=fixture_to_req(applications()[0]); vector=application_embedding(req.application_id); _,ranked=rank_projects(RankRequest(requirements=req,query_embedding=vector,limit=12)); precedent=next(x for x in ranked if x.source_id=="PRJ-024"); semantic=component_value(precedent,"semantic_similarity"); assert semantic.raw>0 and semantic.contribution>0
def test_changed_semantic_query_changes_semantic_component(application_embedding):
    req=fixture_to_req(applications()[0]); _,matching=rank_projects(RankRequest(requirements=req,query_embedding=application_embedding("APP-001"),limit=12)); _,changed=rank_projects(RankRequest(requirements=req,query_embedding=application_embedding("APP-004"),limit=12)); one=component_value(next(x for x in matching if x.source_id=="PRJ-024"),"semantic_similarity"); two=component_value(next(x for x in changed if x.source_id=="PRJ-024"),"semantic_similarity"); assert abs(one.raw-two.raw)>0.01
def test_rank_request_requires_query_embedding():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError): RankRequest(requirements=fixture_to_req(applications()[0]))
def test_keyword_score_is_transparent(): assert keyword_score("glycol current","current glycol manual")==1
