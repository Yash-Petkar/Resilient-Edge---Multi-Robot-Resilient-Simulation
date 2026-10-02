"""Controlled parameter sweeps using actual simulation runs."""
from typing import Any, Dict, List
from dataclasses import replace
from experiments.runner import build_simulation, run_one
from experiments.schema import build_definition

DEFAULTS={
    "robot_count":[3,5,10,20,50,100],
    "task_count":[5,10,25,50,100,250],
    "packet_loss":[0.0,0.01,0.05,0.10,0.25,0.50],
    "latency":[0.0,0.05,0.10,0.25,0.50],
}

def _run(defn):
    r=run_one(defn,1,persist=True)
    return r

def run_parameter_sweep(param_type: str="robot_count", values: List[Any]=None, seed: int=42) -> Dict[str, Any]:
    vals=values or DEFAULTS.get(param_type)
    if vals is None: raise ValueError(f"Unsupported sweep parameter: {param_type}")
    results=[]
    for idx,val in enumerate(vals):
        robots=3; tasks=6
        if param_type=="robot_count": robots=int(val)
        elif param_type=="task_count": tasks=int(val)
        defn=build_definition("S01","resilient",seed,robots,tasks)
        schedule=[]
        if param_type=="packet_loss" and float(val)>0:
            schedule=[{"type":"PACKET_LOSS","target":"network","start_time":0.0,"duration":defn.simulation_duration,"parameters":{"rate":float(val)}}]
        elif param_type=="latency" and float(val)>0:
            schedule=[{"type":"LATENCY","target":"network","start_time":0.0,"duration":defn.simulation_duration,"parameters":{"latency_seconds":float(val)}}]
        defn=replace(defn, experiment_id=f"SWEEP-{param_type}-{val}-{seed}", fault_schedule=schedule)
        r=_run(defn)
        results.append({"parameter_value":val,"status":r["status"],"metrics":r.get("metrics",{}),"run_id":r["run_id"]})
    return {"parameter_type":param_type,"seed":seed,"sweep_results":results}
