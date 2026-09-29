import React, { useState } from 'react';
import {
  ChevronDown,
  CheckCircle2,
  Info,
  AlertTriangle,
  RotateCcw,
  Zap,
} from 'lucide-react';
import { IncidentTelemetry } from '../types';

interface IncidentTimelinePanelProps {
  incidents: IncidentTelemetry[];
}

export const IncidentTimelinePanel: React.FC<IncidentTimelinePanelProps> = ({ incidents }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');

  const filtered = incidents.filter((inc) => {
    if (filterSeverity === 'ALL') return true;
    return inc.severity === filterSeverity;
  }).reverse();

  const formatTime = (ts: number) => {
    const mins = Math.floor(ts / 60);
    const secs = Math.floor(ts % 60);
    return `00:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getEventIcon = (inc: IncidentTelemetry) => {
    const msg = inc.message.toLowerCase();
    if (msg.includes('restored') || msg.includes('started') || msg.includes('completed') || msg.includes('normal')) {
      return <CheckCircle2 className="w-3.5 h-3.5 text-[#22C55E] shrink-0" />;
    }
    if (msg.includes('failure') || msg.includes('blocked') || msg.includes('dropped') || inc.severity === 'CRITICAL') {
      return <AlertTriangle className="w-3.5 h-3.5 text-[#EF4444] shrink-0" />;
    }
    if (msg.includes('latency') || msg.includes('packet loss') || msg.includes('degradation') || inc.severity === 'WARNING') {
      return <Zap className="w-3.5 h-3.5 text-[#F59E0B] shrink-0" />;
    }
    if (msg.includes('recovery')) {
      return <RotateCcw className="w-3.5 h-3.5 text-[#8B5CF6] shrink-0" />;
    }
    return <Info className="w-3.5 h-3.5 text-[#06B6D4] shrink-0" />;
  };

  return (
    <div className="bg-[#151A21] border border-[#29323D] rounded-xl flex flex-col overflow-hidden shadow-sm h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#29323D] flex items-center justify-between select-none">
        <div className="text-sm font-semibold text-[#E5E7EB]">
          Incident Timeline
        </div>
        <div className="relative">
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] text-xs rounded pl-2.5 pr-6 py-1 appearance-none focus:outline-none focus:border-[#1683E8] cursor-pointer"
          >
            <option value="ALL">All</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="CRITICAL">Critical</option>
          </select>
          <ChevronDown className="w-3 h-3 text-[#9CA3AF] absolute right-1.5 top-2 pointer-events-none" />
        </div>
      </div>

      {/* Events Table */}
      <div className="flex-1 overflow-y-auto max-h-[220px]">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#29323D] text-[10px] uppercase font-semibold text-[#6B7280] bg-[#0F1115]/50">
              <th className="py-2 px-3 w-20">Time</th>
              <th className="py-2 px-3">Event</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#29323D]/50 font-sans">
            {filtered.slice(0, 10).map((inc, i) => (
              <tr key={inc.incident_id || i} className="hover:bg-[#1B222B]/60 transition-colors">
                <td className="py-2 px-3 font-mono text-[#6B7280] text-[11px] whitespace-nowrap">
                  {formatTime(inc.timestamp)}
                </td>
                <td className="py-2 px-3 text-[#E5E7EB]">
                  <div className="flex items-center gap-2">
                    {getEventIcon(inc)}
                    <span className="truncate">{inc.message}</span>
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={2} className="py-4 text-center text-[#6B7280]">
                  No incidents recorded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
