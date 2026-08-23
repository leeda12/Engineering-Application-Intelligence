"use strict";
(async()=>{
  const status=document.getElementById("status");
  const operations=document.getElementById("operations");
  try{
    const response=await fetch("/openapi.json",{headers:{Accept:"application/json"}});
    if(!response.ok)throw new Error(`OpenAPI request failed (${response.status})`);
    const schema=await response.json();
    const entries=[];
    for(const [path,methods] of Object.entries(schema.paths||{}))for(const [method,operation] of Object.entries(methods))entries.push({path,method:method.toUpperCase(),operation});
    status.textContent=`${schema.info.title} · version ${schema.info.version} · ${entries.length} documented operations`;
    for(const entry of entries){
      const wrapper=document.createElement("details");wrapper.className="operation";
      const summary=document.createElement("summary");
      const method=document.createElement("span");method.className="method";method.textContent=entry.method;
      const path=document.createElement("code");path.className="path";path.textContent=entry.path;
      const title=document.createElement("span");title.className="summary";title.textContent=entry.operation.summary||"Documented operation";
      summary.append(method,path,title);wrapper.append(summary);
      const details=document.createElement("div");details.className="details";
      const description=document.createElement("p");description.textContent=entry.operation.description||"Strict request and response schemas are available below.";
      const pre=document.createElement("pre");pre.textContent=JSON.stringify({requestBody:entry.operation.requestBody||null,responses:entry.operation.responses||{}},null,2);
      details.append(description,pre);wrapper.append(details);operations.append(wrapper);
    }
  }catch(error){status.textContent=`Documentation unavailable: ${error instanceof Error?error.message:"unknown error"}`;status.setAttribute("role","alert");}
})();
