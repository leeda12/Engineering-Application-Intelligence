from __future__ import annotations
import uuid
from fastapi import FastAPI,File,UploadFile,Request,HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from .config import ROOT,settings
from .data import applications,corpus_by_id
from .schemas import *
from .extraction import extract_controlled_pdf
from .engineering import validate_requirements
from .retrieval import search,rank_projects
from .analysis import analyze
from .schematic import SchematicGenerationError,generate_svg
from .repository import PgVectorConfigurationError,repository
from .audit import ReviewDecisionError,decide,history

app=FastAPI(title="Engineering Application Intelligence API",version="0.1.0",docs_url=None,redoc_url=None)
app.mount("/docs-assets",StaticFiles(directory=ROOT/"backend/app/static"),name="docs-assets")
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin,"http://localhost:3000"],allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Content-Type","Idempotency-Key"])

def error(code:str,message:str,details=None,status=400,request_id=None):
    return JSONResponse(status_code=status,content={"error":{"code":code,"message":message,"details":details,"request_id":request_id or str(uuid.uuid4())}})

@app.middleware("http")
async def security_headers(request:Request,call_next):
    response=await call_next(request)
    response.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer","Permissions-Policy":"camera=(), microphone=(), geolocation=()","Content-Security-Policy":"default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'","Cache-Control":"no-store"})
    return response

@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError): return error("schema_validation_error","Request did not match the strict API schema",exc.errors(),422,request.headers.get("x-request-id"))
@app.exception_handler(HTTPException)
async def http_error(request:Request,exc:HTTPException): return error("http_error",str(exc.detail),status=exc.status_code,request_id=request.headers.get("x-request-id"))
@app.exception_handler(PgVectorConfigurationError)
async def pgvector_configuration_error(request:Request,exc:PgVectorConfigurationError):
    return error("pgvector_configuration_error",str(exc),status=503,request_id=request.headers.get("x-request-id"))
@app.exception_handler(SchematicGenerationError)
async def schematic_generation_error(request:Request,exc:SchematicGenerationError):
    return error(exc.code,str(exc),status=409,request_id=request.headers.get("x-request-id"))
@app.exception_handler(ReviewDecisionError)
async def review_decision_error(request:Request,exc:ReviewDecisionError):
    return error(exc.code,str(exc),status=409,request_id=request.headers.get("x-request-id"))

def fixture_to_req(raw:dict)->Requirements:
    numbers_float={"heat_load_kw","coolant_concentration_pct","coolant_inlet_temp_c","max_outlet_temp_c","ambient_temp_c","available_flow_lpm","max_pressure_drop_kpa","max_width_mm","max_depth_mm","max_height_mm"}; numbers_int={"supply_voltage_v","frequency_hz"}; payload={k:v for k,v in raw.items() if k!="scenario"}
    for k in numbers_float: payload[k]=float(payload[k]) if payload.get(k) not in (None,"") else None
    for k in numbers_int: payload[k]=int(payload[k]) if payload.get(k) not in (None,"") else None
    return Requirements.model_validate(payload)

@app.get("/",response_model=ServiceDiscovery)
def discovery():
    return ServiceDiscovery(service="engineering-application-intelligence",version="0.1.0",health_path="/api/v1/health",documentation_path="/docs",openapi_path="/openapi.json")

@app.get("/docs",response_class=HTMLResponse,include_in_schema=False)
def api_documentation():
    return """<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Engineering Application Intelligence API</title><link rel=\"stylesheet\" href=\"/docs-assets/api-docs.css\"></head><body><header><p>LOCAL API REFERENCE</p><h1>Engineering Application Intelligence API</h1><span>Fictional data · deterministic analysis · PostgreSQL/pgvector retrieval</span></header><main><section id=\"status\" aria-live=\"polite\">Loading local OpenAPI schema…</section><section id=\"operations\"></section></main><script src=\"/docs-assets/api-docs.js\" defer></script></body></html>"""

@app.get("/api/v1/health")
def health():
    repo=repository(); return {"status":"ok","service":"engineering-application-intelligence","version":"0.1.0","retrieval_mode":repo.mode,"pgvector_active":repo.mode=="postgresql_pgvector","embedding_model":"Xenova/all-MiniLM-L6-v2","generative_model":None,"fictional_data_only":True}

@app.get("/api/v1/applications")
def list_applications(): return [{"scenario":x["scenario"],"requirements":fixture_to_req(x)} for x in applications()]

@app.post("/api/v1/applications/extract",response_model=Requirements)
async def extract_application(file:UploadFile=File(...)):
    if file.content_type!="application/pdf": raise HTTPException(415,"Only application/pdf uploads are accepted")
    content=await file.read(settings.max_upload_bytes+1)
    if len(content)>settings.max_upload_bytes: raise HTTPException(413,"PDF exceeds configured upload limit")
    try: return extract_controlled_pdf(content)
    except (ValueError,TypeError) as exc: raise HTTPException(422,str(exc)) from exc

@app.post("/api/v1/requirements/validate",response_model=ValidationResult)
def validate(body:Requirements): return validate_requirements(body)

@app.post("/api/v1/evidence/search",response_model=SearchResponse)
def evidence_search(body:SearchRequest):
    mode,hits=search(body); return SearchResponse(retrieval_mode=mode,model_id="Xenova/all-MiniLM-L6-v2",hits=hits)

@app.post("/api/v1/projects/rank",response_model=RankResponse)
def project_rank(body:RankRequest):
    mode,projects=rank_projects(body); recommended=next((x.source_id for x in projects if x.recommendation_eligible),None); return RankResponse(retrieval_mode=mode,projects=projects,recommended_source_id=recommended)

@app.post("/api/v1/analysis/preliminary",response_model=AnalysisResponse)
def preliminary(body:AnalysisRequest): return analyze(body)

@app.post("/api/v1/schematic/generate",response_model=SchematicResponse)
def schematic(body:SchematicRequest): return SchematicResponse(svg=generate_svg(body),architecture=body.architecture,drawing_version="NTS-SVG-1.1")

@app.post("/api/v1/reviews/propose",response_model=ReviewProposal)
def propose(body:ReviewProposalRequest):
    a=body.analysis; prohibited=[]
    if a.missing_requirements: prohibited.append("critical requirements are missing")
    if a.contradictions: prohibited.append("requirements contain contradictions")
    if a.status==PreliminaryStatus.OUTSIDE_VALIDATED_RANGE: prohibited.append("application is outside the validated range")
    if a.proposed_architecture is None: prohibited.append("no preliminary architecture is supported")
    permitted=not prohibited
    return ReviewProposal(application_id=a.application_id,proposed_architecture=a.proposed_architecture,evidence_source_ids=a.evidence_source_ids,calculation_version=a.calculation_version,approval_permitted=permitted,prohibited_reasons=prohibited,allowed_actions=[ReviewAction.APPROVE,ReviewAction.RETURN,ReviewAction.REJECT] if permitted else [ReviewAction.RETURN,ReviewAction.REJECT])

@app.post("/api/v1/reviews/decision",response_model=AuditEvent)
def review_decision(body:ReviewDecisionRequest):
    event,_=decide(body); return event

@app.get("/api/v1/audit/{application_id}",response_model=list[AuditEvent])
def audit_history(application_id:str): return history(application_id)

@app.get("/api/v1/evidence/{source_id}")
def evidence(source_id:str):
    rec=corpus_by_id().get(source_id.upper())
    if not rec: raise HTTPException(404,"Evidence source does not exist")
    return rec
