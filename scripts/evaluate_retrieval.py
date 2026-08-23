from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.retrieval import rank_projects,search
from backend.app.schemas import SearchRequest,AnalysisRequest,RankRequest
from backend.app.analysis import analyze
from backend.app.data import applications,corpus_by_id
from backend.app.main import fixture_to_req

cases=json.loads((ROOT/"data/evaluation/known_answers.json").read_text(encoding="utf-8")); vector_payload=json.loads((ROOT/"data/generated/embeddings.json").read_text(encoding="utf-8")); recalls=[]; precisions=[]; rr=[]; revision=0; top_result_ordering={}
for case in cases:
    _,hits=search(SearchRequest(query=case["query"],query_embedding=vector_payload["queries"][case["id"]],limit=8)); ids=[x.source_id for x in hits]; expected=set(case["expected"]); found=expected&set(ids); recalls.append(len(found)/len(expected)); precisions.append(len(found)/len(ids)); ranks=[ids.index(x)+1 for x in found]; rr.append(1/min(ranks) if ranks else 0)
    top_result_ordering[case["id"]]=ids
    if case["kind"]=="revision_precedence": revision=int(ids.index("MAN-THERM-002")<ids.index("MAN-THERM-001")) if "MAN-THERM-002" in ids and "MAN-THERM-001" in ids else 0
analyses=[analyze(AnalysisRequest(requirements=fixture_to_req(x),query_embedding=vector_payload["application_queries"][x["application_id"]])) for x in applications()]; claims=[c for a in analyses for c in a.claims]; valid_citations=sum(all(s in corpus_by_id() for s in c.source_ids) for c in claims)
app_one=fixture_to_req(applications()[0]); _,app_one_projects=rank_projects(RankRequest(requirements=app_one,query_embedding=vector_payload["application_queries"][app_one.application_id],limit=8))
metrics={"recall_at_8":sum(recalls)/len(recalls),"precision_at_8":sum(precisions)/len(precisions),"mean_reciprocal_rank":sum(rr)/len(rr),"correct_current_revision":revision,"citation_validity":valid_citations/len(claims),"unsupported_claim_count":sum(not c.source_ids for c in claims),"top_result_ordering":top_result_ordering,"app_001_project_ordering":[x.source_id for x in app_one_projects]}
(ROOT/"docs/evaluation-results.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
print(json.dumps(metrics,indent=2))
