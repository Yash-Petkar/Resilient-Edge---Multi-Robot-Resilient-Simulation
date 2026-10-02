import React, { useState, useEffect } from 'react';
import { Layers, ShieldCheck, Check, X, Play, RefreshCw, AlertCircle } from 'lucide-react';
import { apiService } from '../services/apiService';

interface ComparisonData {
  system: string;
  architecture: string;
  task_completion_rate: number;
  makespan: number;
  average_waiting_time: number;
  conflicts_detected: number;
  deadlocks_detected?: number;
  resilience_recovery: boolean;
}

interface BaselineComparisonProps {
  currentMetrics?: {
    task_completion_rate: number;
    makespan: number;
    average_waiting_time: number;
    conflict_count: number;
  };
}

export const BaselineComparison: React.FC<BaselineComparisonProps> = ({ currentMetrics }) => {
  const [selectedScenario, setSelectedScenario] = useState<string>('S06');
  const [comparisons, setComparisons] = useState<ComparisonData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBaselineBenchmarks = async (scenario: string = selectedScenario) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiService.apiFetch(`/api/baseline?scenario_id=${scenario}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data && data.comparisons) {
        setComparisons(data.comparisons);
      }
    } catch (err: any) {
      setError(`Failed to execute baseline simulations: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBaselineBenchmarks('S06');
  }, []);

  return (
    <div className="space-y-5">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#151A21] border border-[#29323D] rounded-xl p-4">
        <div>
          <h2 className="text-base font-bold text-[#E5E7EB] flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#1683E8]" />
            Comparative Resilience &amp; Coordination Benchmark
          </h2>
          <p className="text-xs text-[#9CA3AF]">
            Real, independent simulation runs of Baseline A (Stop/Wait), Baseline B (Centralized Lock), and ResilientEdge. Zero fabricated multipliers.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <select
            value={selectedScenario}
            onChange={(e) => {
              setSelectedScenario(e.target.value);
              fetchBaselineBenchmarks(e.target.value);
            }}
            className="bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] text-xs rounded-lg px-2.5 py-1.5 font-mono focus:outline-none focus:border-[#1683E8]"
          >
            <option value="S01">S01: Nominal Operations</option>
            <option value="S04">S04: Crossing Conflict</option>
            <option value="S06">S06: Robot Failure (R2)</option>
            <option value="S08">S08: Packet Loss (35%)</option>
            <option value="S10">S10: Network Partition</option>
            <option value="S12">S12: Combined Chaos</option>
          </select>

          <button
            onClick={() => fetchBaselineBenchmarks(selectedScenario)}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1683E8] hover:bg-[#2B95F5] text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer disabled:opacity-50"
          >
            {isLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>{isLoading ? 'Simulating...' : 'Run Benchmark'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-[#EF4444]/15 border border-[#EF4444]/30 rounded-xl p-3 text-xs text-[#EF4444] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Comparison Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {comparisons.map((c) => {
          const isResilientEdge = c.system.includes('ResilientEdge');

          return (
            <div
              key={c.system}
              className={`rounded-xl p-5 border text-xs flex flex-col justify-between transition-all ${
                isResilientEdge
                  ? 'bg-[#1683E8]/10 border-[#1683E8] shadow-lg shadow-[#1683E8]/5 ring-1 ring-[#1683E8]/30'
                  : 'bg-[#151A21] border-[#29323D]'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-sm text-[#E5E7EB]">{c.system}</h3>
                  {isResilientEdge && (
                    <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-[#1683E8] text-white">
                      PROPOSED
                    </span>
                  )}
                </div>

                <p className="text-[#9CA3AF] text-[11px] leading-relaxed mb-4 min-h-[44px]">
                  {c.architecture}
                </p>

                <div className="space-y-3 pt-3 border-t border-[#29323D]">
                  {/* Task Completion Rate */}
                  <div>
                    <div className="flex justify-between items-center text-[#9CA3AF] mb-1 font-mono">
                      <span>Completion Rate:</span>
                      <strong className={`text-sm ${c.task_completion_rate >= 80 ? 'text-[#22C55E]' : 'text-[#F59E0B]'}`}>
                        {c.task_completion_rate}%
                      </strong>
                    </div>
                    <div className="w-full bg-[#0F1115] rounded-full h-1.5 overflow-hidden border border-[#29323D]">
                      <div
                        className={`h-full ${isResilientEdge ? 'bg-[#1683E8]' : 'bg-[#6B7280]'}`}
                        style={{ width: `${c.task_completion_rate}%` }}
                      />
                    </div>
                  </div>

                  {/* Makespan */}
                  <div className="flex justify-between items-center font-mono">
                    <span className="text-[#9CA3AF]">Makespan Duration:</span>
                    <strong className="text-[#E5E7EB]">{c.makespan}s</strong>
                  </div>

                  {/* Average Waiting Time */}
                  <div className="flex justify-between items-center font-mono">
                    <span className="text-[#9CA3AF]">Avg Waiting Time:</span>
                    <strong className="text-[#E5E7EB]">{c.average_waiting_time}s</strong>
                  </div>

                  {/* Conflict Count */}
                  <div className="flex justify-between items-center font-mono">
                    <span className="text-[#9CA3AF]">Conflicts Detected:</span>
                    <strong className={c.conflicts_detected > 0 ? 'text-[#F59E0B]' : 'text-[#22C55E]'}>
                      {c.conflicts_detected}
                    </strong>
                  </div>

                  {/* Dynamic Recovery Capability */}
                  <div className="flex justify-between items-center pt-1 font-sans">
                    <span className="text-[#9CA3AF]">Fault Recovery:</span>
                    {c.resilience_recovery ? (
                      <span className="flex items-center gap-1 text-[#22C55E] font-bold text-xs">
                        <Check className="w-3.5 h-3.5" /> Supported
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[#EF4444] font-medium text-xs">
                        <X className="w-3.5 h-3.5" /> None
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
