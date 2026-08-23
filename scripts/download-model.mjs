import {mkdir,writeFile} from "node:fs/promises";
import {dirname,join} from "node:path";
import {fileURLToPath} from "node:url";
const root=join(dirname(fileURLToPath(import.meta.url)),"..");
const out=join(root,"frontend/public/models/all-MiniLM-L6-v2");
const revision=process.env.MODEL_REVISION||"main";
const files=["config.json","tokenizer.json","tokenizer_config.json","special_tokens_map.json","vocab.txt","onnx/model_quantized.onnx","README.md","LICENSE"];
await mkdir(out,{recursive:true});
for(const file of files){const url=`https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/${revision}/${file}`;const response=await fetch(url,{redirect:"follow"});if(!response.ok){if(file==="LICENSE"){const license=await fetch(`https://www.apache.org/licenses/LICENSE-2.0.txt`);await writeFile(join(out,"LICENSE"),Buffer.from(await license.arrayBuffer()));continue}throw new Error(`${file}: ${response.status}`)}const target=join(out,file);await mkdir(dirname(target),{recursive:true});await writeFile(target,Buffer.from(await response.arrayBuffer()));console.log(`Downloaded ${file}`)}
await writeFile(join(out,"MODEL_PROVENANCE.md"),`# Bundled model\n\nXenova/all-MiniLM-L6-v2, revision ${revision}, Apache-2.0. Semantic retrieval only. Runtime remote model access is disabled.\n`);
