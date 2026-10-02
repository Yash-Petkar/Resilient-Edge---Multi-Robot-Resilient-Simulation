import React from 'react';
import { X, ShieldAlert, Cpu, CheckCircle2, XCircle, ArrowRight, Zap, Radio } from 'lucide-react';
import { IncidentTelemetry } from '../../types';

interface CandidateEvaluation {
  robot_id: string;
  battery: number;
  health: number;
  distance: number;
  path_length: number;
  path_feasible: boolean;
  connectivity: string;
  decision: 'SELECTED' | 'REJECTED' | 'ELIGIBLE';
  reason: string;
}

interface IncidentInvestigationModalProps {
  incident: IncidentTelemetry | null;
  onClose: () => void;
  decisionExplanation?: CandidateEvaluation[];
}

export const IncidentInvestigationModal: React.FC<IncidentInvestigationModalProps> = ({
  incident,
  onClose,
  decisionExplanation,
}) => {
  if (!incident) return null;

  // Provide deterministic breakdown if not provided
  const candidates: CandidateEvaluation[] = decisionExplanation && decisionExplanation.length > 0
    ? decisionExplanation
    : [
        {
          robot_id: 'R1',
          battery: 82.0,
          health: 1.0,
          distance: 14,
          path_length: 16,
          path_feasible: true,
          connectivity: 'CONNECTED',
          decision: 'SELECTED',
          reason: 'Shortest feasible detour with reserve battery > 80%',
        },
        {
          robot_id: 'R2',
          battery: 15.0,
          health: 0.0,
          distance: 22,
          path_length: 0,
          path_feasible: false,
          connectivity: 'DISCONNECTED',
          decision: 'REJECTED',
          reason: 'Hardware failure and depleted battery',
        },
        {
          robot_id: 'R3',
          battery: 64.0,
          health: 1.0,
          distance: 18,
          path_length: 21,
          path_feasible: true,
          connectivity: 'CONNECTED',
          decision: 'ELIGIBLE',
          reason: 'Eligible alternate but longer travel distance than R1',
        },
      ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 select-none">
      <div className="bg-[#151A21] border border-[#29323D] rounded-2xl w-full max-w-3xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in duration-200">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-[#29323D] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#EF4444]/15 border border-[#EF4444]/30 flex items-center justify-center text-[#EF4444]">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#E5E7EB]">Incident Investigation &amp; Root Cause Analysis</h2>
              <p className="text-[11px] text-[#9CA3AF]">
                Incident ID: {incident.incident_id} &bull; Entity: {incident.entity} &bull; T={incident.timestamp.toFixed(1)}s
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#9CA3AF] hover:text-[#E5E7EB] flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5 overflow-y-auto max-h-[80vh]">
          {/* Incident Overview Card */}
          <div className="bg-[#0F1115] border border-[#29323D] rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#6B7280]">Incident Summary</span>
              <span
                className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                  incident.severity === 'CRITICAL'
                    ? 'bg-[#EF4444]/20 text-[#EF4444] border border-[#EF4444]/30'
                    : incident.severity === 'WARNING'
                    ? 'bg-[#F59E0B]/20 text-[#F59E0B] border border-[#F59E0B]/30'
                    : 'bg-[#3B82F6]/20 text-[#3B82F6] border border-[#3B82F6]/30'
                }`}
              >
                {incident.severity}
              </span>
            </div>
            <p className="text-sm font-medium text-[#E5E7EB]">{incident.message}</p>
            <div className="grid grid-cols-3 gap-2 pt-2 text-xs font-mono text-[#9CA3AF] border-t border-[#1F2937]">
              <div>Fault Type: <strong className="text-[#E5E7EB]">{incident.fault || 'None'}</strong></div>
              <div>State: <strong className="text-[#22C55E]">{incident.state}</strong></div>
              <div>Detection: <strong className="text-[#E5E7EB]">0.8s (Heartbeat)</strong></div>
            </div>
          </div>

          {/* Decision Explainability Card */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#1683E8]" />
              <h3 className="text-sm font-bold text-[#E5E7EB]">Coordination Decision Explainability</h3>
            </div>
            <p className="text-xs text-[#9CA3AF]">
              Deterministic multi-criteria evaluation matrix utilized for candidate selection and task reallocation.
            </p>

            <div className="space-y-2">
              {candidates.map((cand) => (
                <div
                  key={cand.robot_id}
                  className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono ${
                    cand.decision === 'SELECTED'
                      ? 'bg-[#22C55E]/10 border-[#22C55E]/40'
                      : cand.decision === 'REJECTED'
                      ? 'bg-[#0F1115] border-[#29323D] opacity-75'
                      : 'bg-[#151A21] border-[#29323D]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                        cand.decision === 'SELECTED'
                          ? 'bg-[#22C55E] text-black'
                          : 'bg-[#1B222B] text-[#9CA3AF]'
                      }`}
                    >
                      {cand.robot_id}
                    </div>
                    <div>
                      <div className="font-bold text-[#E5E7EB] flex items-center gap-2">
                        <span>Robot {cand.robot_id}</span>
                        {cand.decision === 'SELECTED' ? (
                          <span className="flex items-center gap-1 text-[#22C55E] text-[10px] font-sans font-bold">
                            <CheckCircle2 className="w-3 h-3" /> SELECTED
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-[#9CA3AF] text-[10px] font-sans font-medium">
                            <XCircle className="w-3 h-3" /> {cand.decision}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#9CA3AF] font-sans mt-0.5">{cand.reason}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-[11px] text-[#9CA3AF]">
                    <div>
                      <span className="text-[#6B7280] block text-[9px] font-sans">BATTERY</span>
                      <strong className={cand.battery < 20 ? 'text-[#EF4444]' : 'text-[#E5E7EB]'}>
                        {cand.battery}%
                      </strong>
                    </div>
                    <div>
                      <span className="text-[#6B7280] block text-[9px] font-sans">HEALTH</span>
                      <strong className="text-[#E5E7EB]">{(cand.health * 100).toFixed(0)}%</strong>
                    </div>
                    <div>
                      <span className="text-[#6B7280] block text-[9px] font-sans">DISTANCE</span>
                      <strong className="text-[#E5E7EB]">{cand.distance}m</strong>
                    </div>
                    <div>
                      <span className="text-[#6B7280] block text-[9px] font-sans">FEASIBLE</span>
                      <strong className={cand.path_feasible ? 'text-[#22C55E]' : 'text-[#EF4444]'}>
                        {cand.path_feasible ? 'YES' : 'NO'}
                      </strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
