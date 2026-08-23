import {readFile,writeFile} from "node:fs/promises";
import {createServer} from "node:http";
import {dirname,join} from "node:path";
import {fileURLToPath,pathToFileURL} from "node:url";
import * as ort from "onnxruntime-web";

const root=join(dirname(fileURLToPath(import.meta.url)),"..");
const server=createServer(async(req,res)=>{try{const relative=decodeURIComponent(req.url||"").replace(/^\/(models|wasm)\//,"");const base=(req.url||"").startsWith("/models/")?join(root,"frontend/public/models"):join(root,"node_modules/@huggingface/transformers/dist");const body=await readFile(join(base,relative));res.writeHead(200,{"Content-Type":relative.endsWith(".wasm")?"application/wasm":"application/octet-stream"});res.end(body)}catch{res.writeHead(404);res.end()}});
await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
const port=server.address().port;
const savedProcess=globalThis.process;globalThis.process=undefined;
const {env,AutoTokenizer}=await import("../node_modules/@huggingface/transformers/dist/transformers.web.js");
globalThis.process=savedProcess;
env.allowRemoteModels=false;env.allowLocalModels=true;env.localModelPath=`http://127.0.0.1:${port}/models/`;
ort.env.wasm.numThreads=1;ort.env.wasm.proxy=false;ort.env.wasm.wasmPaths={mjs:pathToFileURL(join(root,"node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.mjs")),wasm:pathToFileURL(join(root,"node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.wasm"))};ort.env.wasm.wasmBinary=await readFile(join(root,"node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.wasm"));

const manifest=JSON.parse(await readFile(join(root,"data/model_manifest.json"),"utf8"));
const sources=JSON.parse(await readFile(join(root,"data/corpus/sources.json"),"utf8"));
const applications=JSON.parse(await readFile(join(root,"data/fixtures/applications.json"),"utf8"));
const tokenizer=await AutoTokenizer.from_pretrained("all-MiniLM-L6-v2");
const modelBytes=await readFile(join(root,"frontend/public/models/all-MiniLM-L6-v2/onnx/model_quantized.onnx"));
const session=await ort.InferenceSession.create(modelBytes,{executionProviders:["wasm"]});
async function encode(text){
  const encoded=tokenizer(text,{padding:true,truncation:true,max_length:256});const feeds={};
  for(const name of session.inputNames){const tensor=encoded[name];feeds[name]=new ort.Tensor("int64",BigInt64Array.from(tensor.data,BigInt),tensor.dims)}
  const output=await session.run(feeds);const hidden=output[session.outputNames[0]];const mask=encoded.attention_mask.data;const vector=new Array(manifest.dimensions).fill(0);let tokens=0;
  for(let i=0;i<mask.length;i++){if(Number(mask[i])===0)continue;tokens++;for(let j=0;j<manifest.dimensions;j++)vector[j]+=hidden.data[i*manifest.dimensions+j]}
  let norm=0;for(let j=0;j<vector.length;j++){vector[j]/=tokens;norm+=vector[j]*vector[j]}norm=Math.sqrt(norm);for(let j=0;j<vector.length;j++)vector[j]/=norm;return vector;
}
const vectors={};
for(const [index,source] of sources.entries()){
  const text=`${source.source_id}. ${source.title}. ${source.document_type}. Revision ${source.revision}. Status ${source.status}. Architecture ${source.product_architecture}. ${source.text}`;
  vectors[source.source_id]=await encode(text);console.log(`${index+1}/${sources.length} ${source.source_id}`);
}
const evaluation=JSON.parse(await readFile(join(root,"data/evaluation/known_answers.json"),"utf8"));const queries={};for(const item of evaluation)queries[item.id]=await encode(item.query);
function applicationSemanticQuery(requirements){
  const value=(item,unit="")=>item==null?"unspecified":`${String(item).replaceAll("_"," ")}${unit}`;
  return [`Industrial liquid-cooling application ${requirements.application_id}.`,`Required heat load ${value(requirements.heat_load_kw," kW")}.`,`Coolant ${value(requirements.coolant_type)} at ${value(requirements.coolant_concentration_pct," percent concentration")}.`,`Coolant inlet ${value(requirements.coolant_inlet_temp_c," C")} and maximum outlet ${value(requirements.max_outlet_temp_c," C")}.`,`Ambient ${value(requirements.ambient_temp_c," C")}; available flow ${value(requirements.available_flow_lpm," L/min")}; maximum pressure drop ${value(requirements.max_pressure_drop_kpa," kPa")}.`,`Electrical supply ${value(requirements.supply_voltage_v," V")} ${value(requirements.frequency_hz," Hz")}.`,`Maximum envelope ${value(requirements.max_width_mm," mm wide")} by ${value(requirements.max_depth_mm," mm deep")} by ${value(requirements.max_height_mm," mm high")}.`,`Redundancy ${value(requirements.redundancy)}; communications ${value(requirements.communication_protocol)}; environmental rating ${value(requirements.environmental_rating)}.`,`Customer notes: ${requirements.customer_notes||"none"}.`].join(" ");
}
const application_queries={};for(const application of applications)application_queries[application.application_id]=await encode(applicationSemanticQuery(application));
await writeFile(join(root,"data/generated/embeddings.json"),JSON.stringify({model_id:manifest.model_id,revision:manifest.revision,dimensions:manifest.dimensions,pooling:manifest.pooling,normalize:manifest.normalize,generated_at:new Date().toISOString(),vectors,queries,application_queries}));
server.close();
