from fastapi.testclient import TestClient
from backend.app.main import app,fixture_to_req
from backend.app.data import applications
from backend.app.repository import PgVectorConfigurationError
from backend.app.retrieval import rank_projects
from backend.app.schemas import RankRequest
import backend.app.main as main_module
client=TestClient(app)

def test_health_is_honest():
    body=client.get("/api/v1/health").json(); assert body["generative_model"] is None and body["retrieval_mode"] in {"compatibility_file_vector","postgresql_pgvector"}
def test_schema_error_is_stable():
    res=client.post("/api/v1/requirements/validate",json={"application_id":"bad"}); assert res.status_code==422 and res.json()["error"]["code"]=="schema_validation_error"
def test_analysis_schema(application_embedding):
    req=fixture_to_req(applications()[0]); res=client.post("/api/v1/analysis/preliminary",json={"requirements":req.model_dump(),"query_embedding":application_embedding(req.application_id)}); assert res.status_code==200 and res.json()["calculation_version"]=="NTS-CALC-1.0"
def test_evidence_404(): assert client.get("/api/v1/evidence/DOES-NOT-EXIST").status_code==404
def test_security_headers(): assert client.get("/api/v1/health").headers["x-frame-options"]=="DENY"
def test_root_service_discovery():
    response=client.get("/"); assert response.status_code==200; assert response.json()=={"service":"engineering-application-intelligence","version":"0.1.0","health_path":"/api/v1/health","documentation_path":"/docs","openapi_path":"/openapi.json"}
def test_openapi_schema_and_local_documentation_available():
    schema=client.get("/openapi.json"); docs=client.get("/docs"); script=client.get("/docs-assets/api-docs.js"); stylesheet=client.get("/docs-assets/api-docs.css"); assert schema.status_code==docs.status_code==script.status_code==stylesheet.status_code==200; assert "/api/v1/projects/rank" in schema.json()["paths"]; assert "cdn" not in docs.text.lower(); assert "/docs-assets/api-docs.js" in docs.text
def test_rank_api_exposes_direct_calculated_components(application_embedding):
    req=fixture_to_req(applications()[0]); vector=application_embedding(req.application_id); direct=rank_projects(RankRequest(requirements=req,query_embedding=vector,limit=8))[1]; response=client.post("/api/v1/projects/rank",json={"requirements":req.model_dump(),"query_embedding":vector,"limit":8}); assert response.status_code==200; api_project=next(x for x in response.json()["projects"] if x["source_id"]=="PRJ-024"); direct_project=next(x for x in direct if x.source_id=="PRJ-024"); assert api_project["score_breakdown"]==[x.model_dump() for x in direct_project.score_breakdown]
def test_review_prohibition_has_stable_error_code():
    proposal={"application_id":"APP-003","proposed_architecture":None,"evidence_source_ids":["PROC-REV-001"],"calculation_version":"NTS-CALC-1.0","approval_permitted":False,"prohibited_reasons":["critical requirements are missing"],"allowed_actions":["return_for_additional_information","reject_preliminary_configuration"]}
    body={"application_id":"APP-003","proposal":proposal,"action":"approve_for_concept_review","reviewer_note":"Approval must remain prohibited.","idempotency_key":"stable-prohibited-key"}
    response=client.post("/api/v1/reviews/decision",json=body); assert response.status_code==409; assert response.json()["error"]["code"]=="review_action_prohibited"

def test_configured_incompatible_postgres_returns_stable_503(monkeypatch):
    def incompatible_repository():
        raise PgVectorConfigurationError("Configured PostgreSQL/pgvector is incompatible: test contract mismatch")
    monkeypatch.setattr(main_module,"repository",incompatible_repository)
    response=client.get("/api/v1/health")
    assert response.status_code==503
    assert response.json()["error"]["code"]=="pgvector_configuration_error"
