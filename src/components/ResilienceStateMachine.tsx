import React from 'react';
import { ArrowRight, CheckCircle2, Info, AlertTriangle, RefreshCw } from 'lucide-react';
import { IncidentTelemetry } from '../types';

interface ResilienceStateMachineProps {
  currentState: string;
  incidents: IncidentTelemetry[];
}

export const ResilienceStateMachine: React.FC<ResilienceStateMachineProps> = ({
  currentState,
  incidents,
}) => {
  const states = [
    { id: 'NORMAL', label: 'NORMAL', color: '#22C55E' },
    { id: 'DEGRADED', label: 'DEGRADED', color: '#F59E0B' },
    { id: 'LOCAL_AUTONOMY', label: 'LOCAL AUTONOMY', color: '#06B6D4' },
    { id: 'RECOVERY', label: 'RECOVERY', color: '#8B5CF6' },
    { id: 'RESYNC', label: 'RESYNC', color: '#9CA3AF' },
  ];

  // Derive recent transitions from real incidents and telemetry
  const recentTransitions = incidents.slice(-6).reverse();

  const formatTime = (ts: number) => {
    const mins = Math.floor(ts / 60);
    const secs = Math.floor(ts % 60);
    return `00:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-[#151A21] border border-[#29323D] rounded-xl flex flex-col overflow-hidden shadow-sm h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#29323D] flex items-center justify-between select-none">
        <div className="text-sm font-semibold text-[#E5E7EB]">
          Resilience State Machine
        </div>
      </div>

      <div className="p-4 flex flex-col justify-between flex-1 gap-4">
        {/* Horizontal State Flow */}
        <div className="flex items-center justify-between px-2 pt-2 pb-1">
          {states.map((st, idx) => {
            const isActive = currentState === st.id;
            return (
              <React.Fragment key={st.id}>
                {/* Node */}
                <div className="flex flex-col items-center gap-1.5 select-none">
                  <div
                    className={`relative w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                      isActive ? 'scale-110 shadow-md' : 'opacity-70'
                    }`}
                    style={{
                      backgroundColor: `${st.color}15`,
                      border: `2px solid ${st.color}`,
                      boxShadow: isActive ? `0 0 12px ${st.color}40` : 'none',
                    }}
                  >
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: st.color }}
                    />
                  </div>
                  <span
                    className={`text-[9px] font-bold tracking-tight text-center max-w-[64px] leading-tight ${
                      isActive ? 'text-[#E5E7EB]' : 'text-[#6B7280]'
                    }`}
                  >
                    {st.label}
                  </span>
                </div>

                {/* Connector Arrow */}
                {idx < states.length - 1 && (
                  <div className="flex-1 flex items-center justify-center px-1 mb-4">
                    <div className="h-0.5 w-full bg-[#29323D] relative flex items-center justify-end">
                      <div className="w-1.5 h-1.5 border-t border-r border-[#6B7280] transform rotate-45 mr-0.5" />
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Recent Transitions Section */}
        <div className="border-t border-[#29323D]/60 pt-3">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280] mb-2">
            Recent Transitions
          </div>
          <div className="space-y-1.5 max-h-[135px] overflow-y-auto font-mono text-xs">
            {recentTransitions.length > 0 ? (
              recentTransitions.map((inc, i) => {
                const isResolved = inc.message.includes('restored') || inc.message.includes('NORMAL');
                return (
                  <div key={inc.incident_id || i} className="flex items-center gap-2 text-[#9CA3AF]">
                    <span className="text-[#6B7280] text-[11px] shrink-0">{formatTime(inc.timestamp)}</span>
                    {isResolved ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#22C55E] shrink-0" />
                    ) : inc.severity === 'CRITICAL' ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-[#EF4444] shrink-0" />
                    ) : (
                      <Info className="w-3.5 h-3.5 text-[#06B6D4] shrink-0" />
                    )}
                    <span className="truncate text-[#E5E7EB] font-sans text-xs">
                      {inc.message}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className="text-[#6B7280] text-xs font-sans">No recent transitions recorded.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
