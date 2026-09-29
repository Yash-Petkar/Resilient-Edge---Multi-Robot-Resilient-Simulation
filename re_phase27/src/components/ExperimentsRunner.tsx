import React, { useEffect, useState } from 'react';
import { UserRole } from '../types';
import { roleAllows } from '../permissions';
import { Play, FlaskConical, RefreshCw, AlertCircle } from 'lucide-react';
import { apiService } from '../services/apiService';

interface ScenarioItem { id:string; name:string; description:string; robot_count:number; task_count:number; duration:number; }
const SCENARIOS_CATALOG: ScenarioItem[] = [
  {id:'S01',name:'Normal baseline',description:'Fault-free operation used as the nominal reference.',robot_count:3,task_count:6,duration:45},
  {id:'S02',name:'Single robot failure',description:'R2 fails and assigned work is eligible for recovery.',robot_count:3,task_count:6,duration:50},
  {id:'S03',name:'Multiple robot failure',description:'Two simultaneous robot failures.',robot_count:3,task_count:6,duration:50},
  {id:'S04',name:'Communication latency',description:'Controlled 250 ms communication latency.',robot_count:3,task_count:6,duration:45},
  {id:'S05',name:'Packet loss',description:'Controlled 10% packet loss.',robot_count:3,task_count:6,duration:45},
  {id:'S06',name:'Network partition',description:'Partition and resynchronization experiment.',robot_count:3,task_count:6,duration:50},
  {id:'S07',name:'Task overload',description:'50 tasks against a three-robot fleet.',robot_count:3,task_count:50,duration:60},
  {id:'S08',name:'Path conflict',description:'Crossing trajectories and conflict handling.',robot_count:2,task_count:2,duration:30},
  {id:'S09',name:'Deadlock',description:'Constrained opposing routes exercising deadlock handling.',robot_count:2,task_count:2,duration:30},
  {id:'S10',name:'Failure during active task',description:'Robot failure after active work has started.',robot_count:3,task_count:6,duration:50},
  {id:'S11',name:'Failure + network degradation',description:'Robot failure during packet loss.',robot_count:3,task_count:6,duration:50},
  {id:'S12',name:'Combined multi-fault',description:'Robot failures, blocked aisle and packet loss.',robot_count:3,task_count:6,duration:60},
];

interface Props { onRunScenario:(scenarioId:string)=>void; currentUserRole:UserRole; currentRunningScenario?:string|null; }

export const ExperimentsRunner:React.FC<Props>=({onRunScenario,currentUserRole})=>{
  const canRun=roleAllows(currentUserRole,'experiments');
  const [scenario,setScenario]=useState('S01'); const [config,setConfig]=useState<'baseline'|'resilient'>('resilient');
  const [runs,setRuns]=useState(1); const [seed,setSeed]=useState(42); const [robots,setRobots]=useState<number|''>(''); const [tasks,setTasks]=useState<number|''>('');
  const [result,setResult]=useState<any>(null); const [history,setHistory]=useState<any[]>([]); const [busy,setBusy]=useState(false); const [error,setError]=useState<string|null>(null);

  const loadHistory=async()=>{ try { const r=await apiService.apiFetch('/api/experiments/history'); if(r.ok) setHistory(await r.json()); } catch {} };
  useEffect(()=>{loadHistory();},[]);
  const run=async(compare=false)=>{
    if(!canRun)return; setBusy(true); setError(null);
    try{
      const endpoint=compare?'/api/experiments/compare':'/api/experiments/run';
      const body:any={scenario_id:scenario,seed,runs}; if(!compare) body.config=config; if(robots!=='')body.robots=robots; if(tasks!=='')body.tasks=tasks;
      const r=await apiService.apiFetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const data=await r.json().catch(()=>({})); if(!r.ok)throw new Error(data.detail||data.error||`HTTP ${r.status}`); setResult(data); loadHistory();
    }catch(e:any){setError(e.message||'Experiment failed');}finally{setBusy(false);}
  };
  const selected=SCENARIOS_CATALOG.find(s=>s.id===scenario)!;
  const summary=result?.summary||{};
  const metricRows=['task_completion_rate','makespan','average_task_completion_time','failure_detection_time','task_reassignment_time','planning_latency_ms','conflict_count','deadlock_count','packet_loss_rate','throughput_tasks_per_minute','robot_availability'];
  return <div className="space-y-4">
    <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 space-y-3">
      <div><h2 className="text-base font-bold text-[#E5E7EB] flex items-center gap-2"><FlaskConical className="w-4 h-4 text-blue-500"/>Scientific Experiment Runner</h2><p className="text-xs text-[#9CA3AF]">Deterministic, seed-controlled experiments. Results shown below are produced by actual simulation runs.</p></div>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        <select value={scenario} onChange={e=>setScenario(e.target.value)} className="control">{SCENARIOS_CATALOG.map(s=><option key={s.id} value={s.id}>{s.id} — {s.name}</option>)}</select>
        <select value={config} onChange={e=>setConfig(e.target.value as any)} className="control"><option value="resilient">ResilientEdge</option><option value="baseline">Baseline</option></select>
        <input type="number" min={1} max={100} value={runs} onChange={e=>setRuns(Number(e.target.value))} className="control" title="Runs"/>
        <input type="number" value={seed} onChange={e=>setSeed(Number(e.target.value))} className="control" title="Seed"/>
        <input type="number" min={1} value={robots} placeholder={`${selected.robot_count} robots`} onChange={e=>setRobots(e.target.value?Number(e.target.value):'')} className="control"/>
        <input type="number" min={1} value={tasks} placeholder={`${selected.task_count} tasks`} onChange={e=>setTasks(e.target.value?Number(e.target.value):'')} className="control"/>
      </div>
      <div className="flex gap-2 flex-wrap">
        <button disabled={!canRun||busy} onClick={()=>run(false)} className="btn-primary"><Play className="w-3 h-3"/>{busy?'Running…':'Run Experiment'}</button>
        <button disabled={!canRun||busy} onClick={()=>run(true)} className="btn-secondary"><FlaskConical className="w-3 h-3"/>Baseline vs Resilient</button>
        <button disabled={busy} onClick={loadHistory} className="btn-secondary"><RefreshCw className="w-3 h-3"/>Refresh History</button>
      </div>
      {error&&<div className="text-xs text-red-400 flex items-center gap-2"><AlertCircle className="w-4 h-4"/>{error}</div>}
    </div>

    {result&&<div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 space-y-4">
      <div className="flex justify-between"><div><h3 className="font-bold text-[#E5E7EB]">Result: {scenario}</h3><p className="text-[11px] text-[#9CA3AF]">Requested {result.requested_runs||runs} · Completed {result.completed_runs??'paired'} · Failed {result.failed_runs??0}</p></div><span className="text-xs font-mono text-[#9CA3AF]">seed {seed}</span></div>
      {result.comparisons ? <div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr className="text-[#9CA3AF]"><th className="text-left p-2">Metric</th><th className="p-2">Baseline</th><th className="p-2">Resilient</th><th className="p-2">Difference</th><th className="p-2">N</th></tr></thead><tbody>{Object.entries(result.comparisons).map(([k,v]:any)=><tr key={k} className="border-t border-[#29323D]"><td className="p-2 font-mono">{k}</td><td className="p-2 text-center">{v.baseline.mean}</td><td className="p-2 text-center">{v.resilient.mean}</td><td className="p-2 text-center">{v.absolute_difference}</td><td className="p-2 text-center">{v.statistics.sample_count}</td></tr>)}</tbody></table></div>
      : <div className="grid grid-cols-1 md:grid-cols-3 gap-2">{metricRows.filter(k=>summary[k]).map(k=><div key={k} className="bg-[#0F1115] border border-[#29323D] rounded-lg p-3"><div className="text-[10px] text-[#9CA3AF] font-mono">{k}</div><div className="text-lg font-bold text-[#E5E7EB]">{summary[k].mean}</div><div className="text-[10px] text-[#6B7280]">N={summary[k].sample_count} {summary[k].ci95_low!==undefined?`· 95% CI ${summary[k].ci95_low.toFixed(2)}–${summary[k].ci95_high.toFixed(2)}`:''}</div></div>)}</div>}
    </div>}

    <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4"><h3 className="font-bold text-[#E5E7EB] mb-3">Run History</h3>{history.length===0?<div className="text-xs text-[#6B7280]">No persisted experiment runs found.</div>:<div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr className="text-[#9CA3AF]"><th className="text-left p-2">Run</th><th className="p-2">Scenario</th><th className="p-2">Seed</th><th className="p-2">Status</th><th className="p-2">Duration</th></tr></thead><tbody>{history.slice(0,20).map((h:any)=><tr key={h.run_id||h.id} className="border-t border-[#29323D]"><td className="p-2 font-mono">{h.run_id||'—'}</td><td className="p-2 text-center">{h.scenario||'—'}</td><td className="p-2 text-center">{h.metrics?.seed||'—'}</td><td className="p-2 text-center">{h.status}</td><td className="p-2 text-center">{h.duration??'—'}</td></tr>)}</tbody></table></div>}</div>

    <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4"><h3 className="font-bold text-[#E5E7EB] mb-3">Scenario Catalog S01–S12</h3><div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">{SCENARIOS_CATALOG.map(sc=><button key={sc.id} onClick={()=>{setScenario(sc.id);onRunScenario(sc.id)}} disabled={!canRun} className="text-left rounded-lg p-3 border border-[#29323D] hover:border-blue-500 disabled:opacity-40"><div className="flex justify-between"><span className="font-mono text-blue-400">{sc.id}</span><span className="text-[10px] text-[#9CA3AF]">{sc.robot_count}R / {sc.task_count}T / {sc.duration}s</span></div><div className="text-xs font-semibold text-[#E5E7EB] mt-1">{sc.name}</div><div className="text-[10px] text-[#9CA3AF] mt-1">{sc.description}</div></button>)}</div></div>
    <style>{`.control{background:#0F1115;border:1px solid #29323D;color:#E5E7EB;border-radius:8px;padding:7px;font-size:11px}.btn-primary,.btn-secondary{display:flex;align-items:center;gap:6px;border-radius:8px;padding:7px 11px;font-size:11px;font-weight:600}.btn-primary{background:#1683E8;color:white}.btn-secondary{background:#0F1115;color:#E5E7EB;border:1px solid #29323D}.btn-primary:disabled,.btn-secondary:disabled{opacity:.4}`}</style>
  </div>;
};
