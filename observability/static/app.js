// AGM Architecture Observatory client. Mirrors observability/events.py::fold_state in JS so that
// state at any replay position is recomputed from recorded events only.
const STAGE = {RUN_STARTED:"OBSERVE",ENVIRONMENT_OBSERVED:"OBSERVE",CONSTRAINT_CHANGED:"OBSERVE",CAPABILITY_REQUIREMENT_INFERRED:"REQUIREMENTS",
 MEMORY_RETRIEVED:"MEMORY",PRINCIPLE_RETRIEVED:"MEMORY",ARCHITECTURE_GENERATED:"CANDIDATES",ARCHITECTURE_REJECTED:"ECONOMICS",ADAPTATION_DECISION:"ECONOMICS",
 DO_NOT_ADAPT:"DECIDE",ARCHITECTURE_SELECTED:"DECIDE",VALIDATION_STARTED:"VALIDATE",VALIDATION_FAILED:"VALIDATE",COMPILATION_STARTED:"VALIDATE",
 EXECUTION_STARTED:"EXECUTE",EXECUTION_COMPLETED:"EXECUTE",EXECUTION_FAILED:"EXECUTE",RESOURCE_LIMIT_HIT:"EXECUTE",RESULT_EVALUATED:"EVALUATE",
 PRINCIPLE_CREATED:"LEARN",PRINCIPLE_SUPPORTED:"LEARN",PRINCIPLE_CONTRADICTED:"LEARN",TRANSFER_ATTEMPTED:"MEMORY",TRANSFER_COMPLETED:"LEARN",RUN_COMPLETED:"LEARN"};
const PIPELINE=["OBSERVE","UNDERSTAND","REQUIREMENTS","MEMORY","CANDIDATES","ECONOMICS","DECIDE","VALIDATE","EXECUTE","EVALUATE","LEARN"];
const $=s=>document.querySelector(s);
let events=[], pos=-1, mode="idle", ws=null, timer=null, runMeta=null, expl=[], selectedNode=null;

function fold(evs, upto){
 const st={stage:"OBSERVE",env:{},constraints:{},objective:{},current:null,archs:{},cands:[],decisions:[],principles:{retrieved:[],created:[],supported:[],contradicted:[],transfer:[]},
  memory:[],execs:[],evals:[],failures:[],series:[],counters:{evals:0,adapt_cost:0,exec_cost:0,failures:0,dna:0,adapt:0},completed:false,step:null,t:null,domain:null};
 const n = upto==null? evs.length : upto+1;
 for(let i=0;i<n;i++){const e=evs[i], p=e.payload||{}, t=e.event_type;
  if(e.step!=null) st.step=e.step; if(e.logical_time_s!=null) st.t=e.logical_time_s; if(e.domain) st.domain=e.domain;
  if(e.environment_state&&Object.keys(e.environment_state).length) st.env=e.environment_state; st.stage=STAGE[t]||"OBSERVE";
  if(t=="RUN_STARTED"){st.objective=p.objective||{};st.constraints=p.constraints||{};}
  else if(t=="CONSTRAINT_CHANGED") st.constraints=p.after||st.constraints;
  else if(t=="ENVIRONMENT_OBSERVED"){st.cands=[];st.principles.retrieved=[];st.memory=[];}
  else if(t=="MEMORY_RETRIEVED") st.memory.push(p);
  else if(t=="PRINCIPLE_RETRIEVED"){if(p.principles&&Array.isArray(p.principles)){st.principles.retrieved=p.principles;st.principles.transfer=p.principles.filter(q=>q.source_domains&&!q.source_domains.includes(st.domain));}}
  else if(t=="ARCHITECTURE_GENERATED"){for(const c of (e.candidate_architectures||[])){const cc={...c,status:"generated"};st.cands.push(cc);
    if(!st.archs[c.hash]) st.archs[c.hash]={alias:c.alias,hash:c.hash,name:c.name,parent:c.parent_hash,source:c.source,created_step:e.step,reason:c.reason,perf:[]};}}
  else if(t=="ARCHITECTURE_REJECTED"){for(const c of st.cands) if(c.hash==e.architecture_hash){c.status="rejected";c.reason=e.reason;}}
  else if(t=="ARCHITECTURE_SELECTED"){for(const c of st.cands) if(c.hash==e.architecture_hash){c.status="selected";c.reason=e.reason;}
    st.current={alias:e.selected_architecture,hash:e.architecture_hash,...p};
    if(!st.archs[e.architecture_hash]) st.archs[e.architecture_hash]={alias:e.selected_architecture,hash:e.architecture_hash,name:p.name,parent:p.parent_hash,source:p.source,created_step:e.step,reason:e.reason,perf:[]};}
  else if(t=="ADAPTATION_DECISION"||t=="DO_NOT_ADAPT"){if(p.phase=="settled"){const d=st.decisions.find(x=>x.decision_id==p.decision_id);if(d){d.actual_cost=e.actual_cost;d.decision_error=p.decision_error;}}
    else{const d={seq:e.seq,step:e.step,outcome:p.outcome,reason:e.reason,expected_gain:e.expected_gain,estimated_cost:e.estimated_cost,decision_id:p.decision_id};st.decisions.push(d);
    if(p.outcome=="DO_NOT_ADAPT") st.counters.dna++; else if(p.outcome=="ADAPT"||p.outcome=="PARTIAL_ADAPT") st.counters.adapt++;}}
  else if(t=="VALIDATION_FAILED") st.failures.push({seq:e.seq,step:e.step,kind:"validation",arch:e.selected_architecture,reason:e.reason});
  else if(t=="EXECUTION_COMPLETED"||t=="EXECUTION_FAILED"){const r={seq:e.seq,step:e.step,arch:e.selected_architecture,hash:e.architecture_hash,purpose:p.purpose,ok:t=="EXECUTION_COMPLETED",runtime_s:p.runtime_s,cpu:p.cpu_time_s,mem:p.max_memory_mb,cost:p.cost};
    st.execs.push(r); if(p.purpose=="candidate_evaluation"){st.counters.evals++;st.counters.adapt_cost+=(p.cost||0);} else st.counters.exec_cost+=(p.cost||0);
    st.series.push({seq:e.seq,cpu:p.cpu_time_s||0,mem:p.max_memory_mb||0,lat:(p.runtime_s||0)*1000,evals:st.counters.evals,acost:st.counters.adapt_cost});
    if(t=="EXECUTION_FAILED"){st.counters.failures++;st.failures.push({seq:e.seq,step:e.step,kind:"execution",arch:e.selected_architecture,reason:e.reason});}}
  else if(t=="RESOURCE_LIMIT_HIT") st.failures.push({seq:e.seq,step:e.step,kind:"resource",arch:e.selected_architecture,reason:e.reason});
  else if(t=="RESULT_EVALUATED"){st.evals.push({seq:e.seq,step:e.step,arch:e.selected_architecture,...p}); if(st.archs[e.architecture_hash]) st.archs[e.architecture_hash].perf.push({step:e.step,purpose:p.purpose,quality:p.quality});}
  else if(t=="PRINCIPLE_CREATED") st.principles.created.push(p); else if(t=="PRINCIPLE_SUPPORTED") st.principles.supported.push(p); else if(t=="PRINCIPLE_CONTRADICTED") st.principles.contradicted.push(p);
  else if(t=="RUN_COMPLETED"){st.completed=true;st.summary=p;}
 }
 return st;
}
function summarize(e){const p=e.payload||{},t=e.event_type,a=e.selected_architecture||"";
 if(t=="CONSTRAINT_CHANGED") return `constraint changed: ${(p.event||{}).type} ${JSON.stringify((p.event||{}).params||{})}`;
 if(t=="ARCHITECTURE_GENERATED") return `generated ${(e.candidate_architectures||[]).length} candidate(s): ${(e.candidate_architectures||[]).map(c=>c.alias).join(", ")}`;
 if(t=="ARCHITECTURE_REJECTED") return `rejected ${a} — ${e.reason}`; if(t=="ARCHITECTURE_SELECTED") return `selected ${a} — ${e.reason}`;
 if(t=="ADAPTATION_DECISION"||t=="DO_NOT_ADAPT") return p.phase=="settled"?`decision settled: actual cost ${fmt(e.actual_cost)} (error ${fmt(p.decision_error)})`:`${p.outcome} — ${e.reason}`;
 if(t=="EXECUTION_COMPLETED") return `execution of ${a} completed (${p.purpose}, ${fmt(p.runtime_s)}s)`; if(t=="EXECUTION_FAILED") return `execution of ${a} failed — ${e.reason}`;
 if(t=="RESULT_EVALUATED") return `${a} quality ${fmt(p.quality)} (${p.purpose})`; if(t=="ENVIRONMENT_OBSERVED"){const v=e.environment_state||{};return `observed env: memory ${v.memory_mb}MB cpu ${v.cpu} network ${v.network} priority ${v.priority}`;}
 if(t.startsWith("PRINCIPLE")) return `${t.toLowerCase().replace(/_/g," ")} ${p.principle_id||((p.principles||[]).map(q=>q.id).join(","))}`;
 if(t=="MEMORY_RETRIEVED") return `memory retrieved ${p.n||0} pattern(s)`; return e.reason||t.toLowerCase().replace(/_/g," ");}
const fmt=x=>x==null?"—":(typeof x=="number"?(Math.abs(x)<0.01&&x!=0?x.toExponential(2):+x.toFixed(3)):x);
const kv=(el,obj)=>{el.innerHTML=Object.entries(obj).map(([k,v])=>`<b>${k}</b><span>${typeof v=="object"?JSON.stringify(v):fmt(v)}</span>`).join("");};

function render(){
 const st=fold(events,pos<0?null:pos); const e=events[pos]||null;
 const env=st.env||{}; kv($("#env"),{domain:st.domain,step:st.step,"t (s)":st.t,memory_mb:env.memory_mb,cpu:env.cpu,latency_ms:env.latency_ms,network:env.network,priority:env.priority,cost_budget:env.cost_budget,capabilities:(env.available_capabilities||[]).length,
  uncertainty:(runMeta&&runMeta.manifest)?runMeta.manifest.task.noise:"—",objective:st.objective.quality_threshold,constraints:st.constraints.memory_mb?`mem ${st.constraints.memory_mb}MB, deadline ${st.constraints.deadline_s}s`:"—"});
 const c=st.current||{}; const par=c.parent_hash&&st.archs[c.parent_hash]?st.archs[c.parent_hash].alias:(c.parent_hash?c.parent_hash.slice(0,8):"—");
 kv($("#arch"),{id:c.alias||"—",hash:(c.hash||"").slice(0,12),name:c.name,parent:par,source:c.source,principle:c.principle_id||"—","dist→initial":c.distance_to_initial,"dist→previous":c.distance_to_previous,novelty:c.novelty_level||"—",components:(c.components||[]).join(", "),topology:c.reasoning?`${c.reasoning} / mem ${c.memory} / verif ${c.verification}`:"—",estimate:c.estimates?`${fmt(c.estimates.memory_mb)}MB, $${fmt(c.estimates.cost_per_batch)}, ${fmt(c.estimates.latency_ms)}ms`:"—"});
 const steps=(runMeta&&runMeta.manifest)?runMeta.manifest.schedule.steps:"?"; const done=st.evals.filter(x=>x.purpose=="task").length;
 kv($("#exp"),{run:st.summary?"completed":(mode=="live"?"running":"replay"),experiment:runMeta?runMeta.experiment.name:"—",seed:runMeta?runMeta.experiment.seed:"—",agent:runMeta?runMeta.run_id.split(".").pop():"—",domain:st.domain,step:st.step,completed:done,failed:st.counters.failures,remaining:steps=="?"?"?":Math.max(0,steps-done),evaluations:st.counters.evals,"adapt / do-not-adapt":`${st.counters.adapt} / ${st.counters.dna}`,event:`${pos+1}/${events.length}`});
 const P=st.principles; const badge=q=>`<span class="badge ${q.status||""}">${q.status||"?"}</span>`;
 $("#mem").innerHTML=`<b>retrieved</b> ${P.retrieved.length?P.retrieved.map(q=>`<div>${badge(q)} ${q.name} conf ${fmt(q.confidence)} app ${fmt(q.applicability)} ${q.source_domains?"from "+q.source_domains.join("/"):""}</div>`).join(""):"—"}
  <b>new / merged</b> ${P.created.length?P.created.slice(-5).map(q=>`<div>${badge(q)} ${q.rule} (evidence ${q.evidence_count})</div>`).join(""):"—"}
  <b>supported</b> ${P.supported.length?P.supported.map(q=>`<div>${q.principle_id} conf ${fmt(q.confidence)}</div>`).join(""):"—"}
  <b>contradicted</b> ${P.contradicted.length?P.contradicted.map(q=>`<div>${q.principle_id}</div>`).join(""):"—"}
  <b>transfer candidates</b> ${P.transfer.length?P.transfer.map(q=>`<div>${q.name} ← ${q.source_domains.join("/")}</div>`).join(""):"—"} <b>structural patterns</b> ${st.memory.length?st.memory.map(m=>m.n+" retrieved").join(", "):"—"}`;
 $("#pipe").innerHTML=PIPELINE.map(s=>`<span class="stage ${s==st.stage?"active":""}">${s}</span>`).join("<span style='color:var(--muted)'>→</span>");
 $("#cands tbody").innerHTML=st.cands.map(x=>`<tr><td>${x.alias}</td><td>${x.name||""}</td><td>${x.source||""}${x.cross_domain?" ⇄":""}</td><td>${fmt(x.distance_to_current)}</td><td>${fmt(x.predicted_quality)}</td><td>${fmt(x.estimated_cost)}</td><td>${fmt(x.estimated_latency_ms)}</td><td class="st-${x.status}">${x.status}</td><td>${x.reason||""}</td></tr>`).join("")||"<tr><td colspan=9>no candidates recorded at this point</td></tr>";
 const tr=$("#trace"); tr.innerHTML=events.slice(Math.max(0,pos-200),pos+1).map((x,i)=>{const idx=Math.max(0,pos-200)+i;return `<div class="${idx==pos?"cur":""}" data-i="${idx}"><span class="t">${x.timestamp.slice(11,19)}</span> #${x.seq} ${summarize(x)}</div>`;}).join(""); tr.scrollTop=tr.scrollHeight;
 drawRes(st.series); drawLineage(st); $("#pos").textContent=e?`seq ${e.seq} · ${e.event_type} · step ${e.step??"—"}`:"—"; $("#barfill").style.width=events.length?((pos+1)/events.length*100)+"%":"0";
 const ex=expl.find(x=>x.step==st.step); $("#expl").innerHTML=ex?["observed","retrieved","considered","rejected","selected","expected","actual","learned"].map(k=>`<b>${k}</b><ul>${(ex[k]||[]).map(v=>`<li>${v}</li>`).join("")||"<li>—</li>"}</ul>`).join(""):"no explanation for this step yet";
 if(selectedNode&&st.archs[selectedNode]) showNode(st,selectedNode);
}
function drawRes(series){const cv=$("#res");const W=cv.width=cv.clientWidth*2,H=cv.height=240;const g=cv.getContext("2d");g.clearRect(0,0,W,H);if(!series.length)return;
 const keys=[["cpu","#5aa9ff"],["mem","#4fd18b"],["lat","#f2b544"],["evals","#8f7bff"],["acost","#ff6b6b"]];let leg=[];
 keys.forEach(([k,col],ki)=>{const vals=series.map(s=>s[k]);const mx=Math.max(...vals,1e-9);g.strokeStyle=col;g.lineWidth=2;g.beginPath();vals.forEach((v,i)=>{const x=10+(W-20)*i/Math.max(1,vals.length-1),y=H-10-(H-20)*v/mx;i?g.lineTo(x,y):g.moveTo(x,y);});g.stroke();leg.push(`<span style="color:${col}">${k}: ${fmt(vals[vals.length-1])} (max ${fmt(mx)})</span>`);});
 $("#reslegend").innerHTML=leg.join(" · ");}
function drawLineage(st){const svg=$("#lineage");const nodes=Object.values(st.archs);const children={};nodes.forEach(n=>{const p=n.parent&&st.archs[n.parent]?n.parent:null;(children[p]=children[p]||[]).push(n);});
 const roots=children[null]||[];let x=0;const posn={};const depth=(n,d)=>{const ch=children[n.hash]||[];if(!ch.length){posn[n.hash]={x:x++,y:d};return;}ch.forEach(c=>depth(c,d+1));posn[n.hash]={x:ch.reduce((a,c)=>a+posn[c.hash].x,0)/ch.length,y:d};};
 roots.forEach(r=>depth(r,0));const cols=Math.max(1,x),rows=Math.max(...Object.values(posn).map(p=>p.y),0)+1;const w=svg.clientWidth||600,cw=Math.max(70,w/cols),rh=52;svg.setAttribute("height",Math.max(220,rows*rh+20));
 let out="";nodes.forEach(n=>{const p=posn[n.hash];if(!p)return;const par=n.parent&&posn[n.parent];if(par)out+=`<line class="edge" x1="${par.x*cw+cw/2}" y1="${par.y*rh+36}" x2="${p.x*cw+cw/2}" y2="${p.y*rh+10}"/>`;});
 nodes.forEach(n=>{const p=posn[n.hash];if(!p)return;const ex=st.execs.some(e=>e.hash==n.hash),cur=st.current&&st.current.hash==n.hash;out+=`<g class="node ${ex?"exec":""} ${cur?"cur":""}" data-h="${n.hash}"><rect x="${p.x*cw+4}" y="${p.y*rh+10}" width="${cw-8}" height="26" rx="4"/><text x="${p.x*cw+cw/2}" y="${p.y*rh+27}" text-anchor="middle">${n.alias} ${n.source?"·"+n.source.slice(0,6):""}</text></g>`;});
 svg.innerHTML=out;svg.querySelectorAll(".node").forEach(g=>g.onclick=()=>{selectedNode=g.dataset.h;showNode(st,selectedNode);});}
async function showNode(st,h){const n=st.archs[h];const par=n.parent&&st.archs[n.parent];const kids=Object.values(st.archs).filter(k=>k.parent==h).map(k=>k.alias);
 let diff="";if(par){try{const d=await (await fetch(`/architectures/${h}/diff/${n.parent}${dbq("?")}`)).json();diff=`<pre>structural distance ${fmt(d.distance.structural_distance)}; ${Object.entries(d.diff.diff).map(([k,v])=>`${k}: ${JSON.stringify(v[1])} → ${JSON.stringify(v[0])}`).join("; ")||"parameters only"}</pre>`;}catch(e){diff="(diff unavailable)";}}
 $("#nodeinfo").innerHTML=`<kv><b>node</b><span>${n.alias} (${h.slice(0,12)}) ${n.name||""}</span><b>parent</b><span>${par?par.alias:"—"}</span><b>children</b><span>${kids.join(", ")||"—"}</span><b>created</b><span>step ${n.created_step} · source ${n.source||"—"}</span><b>reason</b><span>${n.reason||"—"}</span><b>performance</b><span>${n.perf.map(p=>`${p.purpose[0]}${p.step}:${fmt(p.quality)}`).join(" ")||"—"}</span><b>environment</b><span>${JSON.stringify(st.env)}</span><b>experiment</b><span>${runMeta?runMeta.experiment.experiment_id:"—"}</span><b>diff vs parent</b><span>${diff||"—"}</span></kv>`;}
let runDb={};
const dbq=pfx=>{const p=new URLSearchParams(location.search).get("db_path")||runDb[$("#runs").value];return p?`${pfx}db_path=${encodeURIComponent(p)}`:"";};
async function loadRuns(){const rs=await (await fetch("/runs")).json();runDb={};rs.forEach(r=>runDb[r.run_id]=r.db_path);
 $("#runs").innerHTML=rs.slice().reverse().map(r=>`<option value="${r.run_id}">${r.experiment||"?"} · ${r.agent} · seed ${r.seed} · ${r.domain} · ${r.status||"?"} (${r.n_events} ev)</option>`).join("");}
setInterval(()=>{if(mode=="idle")loadRuns();},15000);
async function loadRun(id){runMeta=await (await fetch(`/runs/${id}${dbq("?")}`)).json();expl=await (await fetch(`/runs/${id}/explanations${dbq("?")}`)).json();}
function setMode(m,txt){mode=m;const el=$("#mode");el.className="mode "+m;el.textContent=m=="live"?"LIVE · tailing recorded events":m=="demo"?"DEMO · replaying stored run":"NO RUN";$("#status").textContent=txt||"";}
async function startDemo(){stop();const id=$("#runs").value;await loadRun(id);events=await (await fetch(`/runs/${id}/events${dbq("?")}`)).json();pos=-1;setMode("demo",`${events.length} stored events`);render();play();}
async function startLive(){stop();const id=$("#runs").value;await loadRun(id);events=[];pos=-1;setMode("live","connecting…");
 ws=new WebSocket(`${location.protocol=="https:"?"wss":"ws"}://${location.host}/ws/runs/${id}?after=-1${dbq("&")}`);
 ws.onmessage=async m=>{const e=JSON.parse(m.data);if(e.event_type=="_HEARTBEAT"){$("#status").textContent=`waiting for new events (seq ${e.seq})`;return;}if(e.event_type=="_STREAM_END"){$("#status").textContent="run completed";expl=await (await fetch(`/runs/${id}/explanations${dbq("?")}`)).json();render();return;}events.push(e);pos=events.length-1;$("#status").textContent=`live · ${events.length} events`;if(events.length%25==0) expl=await (await fetch(`/runs/${id}/explanations${dbq("?")}`)).json();render();};
 ws.onclose=()=>{$("#status").textContent="stream closed";};}
function stop(){if(ws){ws.close();ws=null;}pause();}
function play(){pause();const sp=parseFloat($("#speed").value);timer=setInterval(()=>{if(pos<events.length-1){pos++;render();}else pause();},Math.max(20,400/sp));}
function pause(){if(timer){clearInterval(timer);timer=null;}}
$("#replay").onclick=ev=>{const a=ev.target.dataset.a;if(!a)return;if(mode=="live"&&a!="pause")setMode("demo","paused live stream → replay of received events");
 if(a=="play")play();else if(a=="pause")pause();else if(a=="back"){pause();if(pos>0){pos--;render();}}else if(a=="fwd"){pause();if(pos<events.length-1){pos++;render();}}
 else if(a=="jump"){pause();const s=parseInt($("#jump").value);const i=events.findIndex(e=>e.seq==s);if(i>=0){pos=i;render();}}};
$("#bar").onclick=ev=>{pause();const r=ev.currentTarget.getBoundingClientRect();pos=Math.min(events.length-1,Math.max(0,Math.floor((ev.clientX-r.left)/r.width*events.length)));render();};
$("#trace").onclick=ev=>{const d=ev.target.closest("div[data-i]");if(d){pause();pos=parseInt(d.dataset.i);render();}};
$("#speed").onchange=()=>{if(timer)play();};$("#btnDemo").onclick=startDemo;$("#btnLive").onclick=startLive;
loadRuns();
