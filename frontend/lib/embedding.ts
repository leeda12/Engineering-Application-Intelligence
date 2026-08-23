import type {Requirements} from "./types";

let extractorPromise:Promise<(text:string)=>Promise<number[]>>|null=null;

export function buildSemanticQuery(requirements:Requirements):string{
  const value=(item:unknown,unit="")=>item==null?"unspecified":`${String(item).replaceAll("_"," ")}${unit}`;
  return [
    `Industrial liquid-cooling application ${requirements.application_id}.`,
    `Required heat load ${value(requirements.heat_load_kw," kW")}.`,
    `Coolant ${value(requirements.coolant_type)} at ${value(requirements.coolant_concentration_pct," percent concentration")}.`,
    `Coolant inlet ${value(requirements.coolant_inlet_temp_c," C")} and maximum outlet ${value(requirements.max_outlet_temp_c," C")}.`,
    `Ambient ${value(requirements.ambient_temp_c," C")}; available flow ${value(requirements.available_flow_lpm," L/min")}; maximum pressure drop ${value(requirements.max_pressure_drop_kpa," kPa")}.`,
    `Electrical supply ${value(requirements.supply_voltage_v," V")} ${value(requirements.frequency_hz," Hz")}.`,
    `Maximum envelope ${value(requirements.max_width_mm," mm wide")} by ${value(requirements.max_depth_mm," mm deep")} by ${value(requirements.max_height_mm," mm high")}.`,
    `Redundancy ${value(requirements.redundancy)}; communications ${value(requirements.communication_protocol)}; environmental rating ${value(requirements.environmental_rating)}.`,
    `Customer notes: ${requirements.customer_notes||"none"}.`,
  ].join(" ");
}

export async function embed(text:string):Promise<number[]>{
  if(!extractorPromise) extractorPromise=(async()=>{const {env,pipeline}=await import("@huggingface/transformers");env.allowRemoteModels=false;env.allowLocalModels=true;env.localModelPath="/models/";if(env.backends.onnx?.wasm){env.backends.onnx.wasm.wasmPaths="/wasm/";env.backends.onnx.wasm.proxy=false}const extractor=await pipeline("feature-extraction","all-MiniLM-L6-v2",{dtype:"q8",device:"wasm"});return async(value:string)=>{const output=await extractor(value,{pooling:"mean",normalize:true});return Array.from(output.data as Float32Array)}})();
  return (await extractorPromise)(text);
}
