from __future__ import annotations
import re
from .data import corpus
from .repository import repository
from .schemas import Requirements, SearchRequest, SearchHit, ScoreComponent, RankRequest, RankedProject

TOKENS=re.compile(r"[a-z0-9+.-]+")
def token_set(text:str)->set[str]: return {x for x in TOKENS.findall(text.lower()) if len(x)>2}
def keyword_score(query:str,text:str)->float:
    q=token_set(query); t=token_set(text)
    return len(q&t)/len(q) if q else 0.0
def clamp(x:float)->float: return max(0.0,min(1.0,x))
def component(name,raw,weight): return ScoreComponent(name=name,raw=round(raw,4),weight=weight,contribution=round(raw*weight,4))

def semantic_query(req:Requirements)->str:
    def value(item,unit=""):
        return "unspecified" if item is None else f"{str(item).replace('_',' ')}{unit}"
    return " ".join((
        f"Industrial liquid-cooling application {req.application_id}.",
        f"Required heat load {value(req.heat_load_kw,' kW')}.",
        f"Coolant {value(req.coolant_type)} at {value(req.coolant_concentration_pct,' percent concentration')}.",
        f"Coolant inlet {value(req.coolant_inlet_temp_c,' C')} and maximum outlet {value(req.max_outlet_temp_c,' C')}.",
        f"Ambient {value(req.ambient_temp_c,' C')}; available flow {value(req.available_flow_lpm,' L/min')}; maximum pressure drop {value(req.max_pressure_drop_kpa,' kPa')}.",
        f"Electrical supply {value(req.supply_voltage_v,' V')} {value(req.frequency_hz,' Hz')}.",
        f"Maximum envelope {value(req.max_width_mm,' mm wide')} by {value(req.max_depth_mm,' mm deep')} by {value(req.max_height_mm,' mm high')}.",
        f"Redundancy {value(req.redundancy)}; communications {value(req.communication_protocol)}; environmental rating {value(req.environmental_rating)}.",
        f"Customer notes: {req.customer_notes or 'none'}.",
    ))

def eligibility(record:dict)->tuple[bool,list[str]]:
    reasons=[]
    if record["status"] in ("superseded","draft"): reasons.append(f"document status is {record['status']}")
    if record.get("validation_outcome")=="failed": reasons.append("historical design failed validation")
    if record.get("validation_outcome")=="missing_evidence": reasons.append("required validation evidence is missing")
    return not reasons,reasons

def search(req:SearchRequest):
    repo=repository(); sem=repo.semantic(req.query_embedding); exact_ids={x.upper() for x in re.findall(r"(?:PRJ|MAN|VAL|BUL|REV|PROC)-[A-Z0-9-]+",req.query.upper())}
    hits=[]
    for rec in repo.records():
        if req.architecture not in (None,"all") and rec["product_architecture"] not in (req.architecture,"all"): continue
        semantic=sem.get(rec["source_id"],0.0); keyword=keyword_score(req.query,rec["title"]+" "+rec["text"]+" "+rec["source_id"])
        arch=1.0 if req.architecture and rec["product_architecture"] in (req.architecture,"all") else .65
        current=1.0 if rec["status"]=="current" else (.7 if rec["status"]=="historical" else .1)
        priority=1.0 if rec["document_type"] in ("manual","failure_bulletin","revision_notice") else .7
        parts=[component("semantic_similarity",semantic,.55),component("keyword_relevance",keyword,.20),component("architecture_applicability",arch,.10),component("current_status",current,.10),component("document_type_priority",priority,.05)]
        score=sum(x.contribution for x in parts)+(0.35 if rec["source_id"] in exact_ids else 0)
        ok,reasons=eligibility(rec)
        hits.append(SearchHit(source_id=rec["source_id"],title=rec["title"],document_type=rec["document_type"],revision=rec["revision"],status=rec["status"],locator=rec["locator"],product_architecture=rec["product_architecture"],excerpt=rec["text"][:330],score=round(min(1,score)*100,2),score_breakdown=parts,recommendation_eligible=ok,disqualification_reasons=reasons))
    hits.sort(key=lambda x:(x.score,x.status=="current"),reverse=True)
    return repo.mode,hits[:req.limit]

def numerical_proximity(req:Requirements,p:dict)->float:
    pairs=((req.heat_load_kw,p.get("heat_load_kw"),400),(req.available_flow_lpm,p.get("flow_lpm"),480),(req.coolant_inlet_temp_c,p.get("inlet_temp_c"),30),(req.max_outlet_temp_c,p.get("outlet_temp_c"),30),(req.max_pressure_drop_kpa,p.get("pressure_drop_kpa"),60),(req.max_width_mm,p.get("width_mm"),2200),(req.max_depth_mm,p.get("depth_mm"),1800),(req.max_height_mm,p.get("height_mm"),2600))
    vals=[clamp(1-abs(a-b)/scale) for a,b,scale in pairs if a is not None and b is not None]
    return sum(vals)/len(vals) if vals else 0

def hard_compat(req:Requirements,p:dict)->float:
    checks=[]
    for a,b in ((req.supply_voltage_v,p.get("voltage_v")),(req.frequency_hz,p.get("frequency_hz")),(req.redundancy,p.get("redundancy")),(req.communication_protocol,p.get("communication_protocol")),(req.environmental_rating,p.get("environmental_rating"))):
        if a is not None and b is not None: checks.append(a==b)
    for maximum,actual in ((req.max_width_mm,p.get("width_mm")),(req.max_depth_mm,p.get("depth_mm")),(req.max_height_mm,p.get("height_mm"))):
        if maximum is not None and actual is not None: checks.append(actual<=maximum)
    return sum(checks)/len(checks) if checks else 0

def rank_projects(request:RankRequest):
    repo=repository(); sem=repo.semantic(request.query_embedding); query=semantic_query(request.requirements)
    ranked=[]
    for rec in corpus():
        if rec["document_type"]!="historical_project": continue
        p=rec["project_parameters"]; semantic=sem.get(rec["source_id"],0); keyword=keyword_score(query,rec["text"]); numerical=numerical_proximity(request.requirements,p); hard=hard_compat(request.requirements,p); current=.8 if rec["status"]=="historical" else 1; outcome=1 if rec.get("validation_outcome")=="passed" else 0
        parts=[component("semantic_similarity",semantic,.35),component("keyword_relevance",keyword,.15),component("numerical_proximity",numerical,.20),component("hard_constraint_compatibility",hard,.15),component("revision_status",current,.05),component("validation_outcome",outcome,.10)]
        ok,reasons=eligibility(rec); score=sum(x.contribution for x in parts)
        diffs={"heat_load_kw":round(request.requirements.heat_load_kw-p["heat_load_kw"],1) if request.requirements.heat_load_kw else None,"flow_lpm":round(request.requirements.available_flow_lpm-p["flow_lpm"],1) if request.requirements.available_flow_lpm else None,"width_margin_mm":round(request.requirements.max_width_mm-p["width_mm"],1) if request.requirements.max_width_mm else None,"voltage_match":request.requirements.supply_voltage_v==p["voltage_v"],"redundancy_match":request.requirements.redundancy==p["redundancy"]}
        ranked.append(RankedProject(source_id=rec["source_id"],title=rec["title"],document_type=rec["document_type"],revision=rec["revision"],status=rec["status"],locator=rec["locator"],product_architecture=rec["product_architecture"],excerpt=rec["text"][:330],score=round(score*100,2),score_breakdown=parts,recommendation_eligible=ok,disqualification_reasons=reasons,differences=diffs))
    ranked.sort(key=lambda x:x.score,reverse=True)
    return repo.mode,ranked[:request.limit]
