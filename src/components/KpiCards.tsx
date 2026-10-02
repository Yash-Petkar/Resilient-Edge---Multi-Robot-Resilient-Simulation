import React from 'react';
import {
  Bot,
  ClipboardList,
  AlertTriangle,
  ShieldCheck,
  Radio,
} from 'lucide-react';
import { RobotTelemetry, TaskTelemetry, FaultTelemetry, SimulationMetrics } from '../types';

interface KpiCardsProps {
  robots: RobotTelemetry[];
  tasks: TaskTelemetry[];
  faults: FaultTelemetry[];
  resilienceState: string;
  metrics: SimulationMetrics;
  isOnline: boolean;
}

export const KpiCards: React.FC<KpiCardsProps> = ({
  robots,
  tasks,
  faults,
  resilienceState,
  metrics,
  isOnline,
}) => {
  const totalRobots = robots.length || 3;
  const onlineRobots = robots.filter((r) => r.state !== 'FAILED').length;

  const totalTasks = tasks.length || 6;
  const activeTasks = tasks.filter((t) => t.status === 'ASSIGNED' || t.status === 'IN_PROGRESS').length;

  const activeFaultsCount = faults.filter((f) => f.status === 'ACTIVE').length;

  // Network stats
  const packetLossFault = faults.find((f) => f.fault_type === 'PACKET_LOSS' && f.status === 'ACTIVE');
  const packetLossRate = packetLossFault ? Number(packetLossFault.parameters.rate || 0.35) * 100 : 0.2;
  const latencyFault = faults.find((f) => f.fault_type === 'NETWORK_LATENCY' && f.status === 'ACTIVE');
  const latencyMs = latencyFault ? Number(latencyFault.parameters.delay_ms || 250) : 12;

  const isResilienceNormal = resilienceState === 'NORMAL';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 select-none">
      {/* 1. Robots Card */}
      <div className="relative bg-[#151A21] border border-[#29323D] rounded-xl p-3.5 flex flex-col justify-between overflow-hidden shadow-sm">
        <div className="flex items-start justify-between">
          <div className="w-9 h-9 rounded-lg bg-[#1683E8]/15 border border-[#1683E8]/30 flex items-center justify-center text-[#1683E8]">
            <Bot className="w-5 h-5" />
          </div>
          <div className="text-right">
            <span className="text-[11px] font-medium text-[#9CA3AF] block">Robots</span>
            <div className="font-mono text-xl font-bold text-[#E5E7EB] mt-0.5">
              {onlineRobots} / {totalRobots}
            </div>
            <div className="text-[11px] font-semibold text-[#22C55E]">Online</div>
          </div>
        </div>
        {/* Accent Bar */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-[#22C55E]/80" />
      </div>

      {/* 2. Tasks Card */}
      <div className="relative bg-[#151A21] border border-[#29323D] rounded-xl p-3.5 flex flex-col justify-between overflow-hidden shadow-sm">
        <div className="flex items-start justify-between">
          <div className="w-9 h-9 rounded-lg bg-[#F59E0B]/15 border border-[#F59E0B]/30 flex items-center justify-center text-[#F59E0B]">
            <ClipboardList className="w-5 h-5" />
          </div>
          <div className="text-right">
            <span className="text-[11px] font-medium text-[#9CA3AF] block">Tasks</span>
            <div className="font-mono text-xl font-bold text-[#E5E7EB] mt-0.5">
              {activeTasks} / {totalTasks}
            </div>
            <div className="text-[11px] font-semibold text-[#06B6D4]">Active</div>
          </div>
        </div>
        {/* Accent Bar */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-[#06B6D4]/80" />
      </div>

      {/* 3. Faults Card */}
      <div className="relative bg-[#151A21] border border-[#29323D] rounded-xl p-3.5 flex flex-col justify-between overflow-hidden shadow-sm">
        <div className="flex items-start justify-between">
          <div className="w-9 h-9 rounded-lg bg-[#EF4444]/15 border border-[#EF4444]/30 flex items-center justify-center text-[#EF4444]">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="text-right">
            <span className="text-[11px] font-medium text-[#9CA3AF] block">Faults</span>
            <div className="font-mono text-xl font-bold text-[#E5E7EB] mt-0.5">
              {activeFaultsCount}
            </div>
            <div className={`text-[11px] font-semibold ${activeFaultsCount > 0 ? 'text-[#EF4444]' : 'text-[#9CA3AF]'}`}>
              {activeFaultsCount > 0 ? 'Active Fault' : 'Active'}
            </div>
          </div>
        </div>
      </div>

      {/* 4. Resilience State Card */}
      <div className="relative bg-[#151A21] border border-[#29323D] rounded-xl p-3.5 flex flex-col justify-between overflow-hidden shadow-sm">
        <div className="flex items-start justify-between">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${
            isResilienceNormal
              ? 'bg-[#22C55E]/15 border border-[#22C55E]/30 text-[#22C55E]'
              : 'bg-[#F59E0B]/15 border border-[#F59E0B]/30 text-[#F59E0B]'
          }`}>
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="text-right">
            <span className="text-[11px] font-medium text-[#9CA3AF] block">Resilience State</span>
            <div className={`font-mono text-lg font-bold mt-0.5 ${
              isResilienceNormal ? 'text-[#22C55E]' : 'text-[#F59E0B]'
            }`}>
              {resilienceState}
            </div>
            <div className="text-[11px] font-medium text-[#9CA3AF]">
              {isResilienceNormal ? 'Fleet Healthy' : 'Degraded Mode'}
            </div>
          </div>
        </div>
        {/* Accent Bar */}
        <div className={`absolute bottom-0 left-0 right-0 h-1 ${
          isResilienceNormal ? 'bg-[#22C55E]/80' : 'bg-[#F59E0B]/80'
        }`} />
      </div>

      {/* 5. Network Card */}
      <div className="relative bg-[#151A21] border border-[#29323D] rounded-xl p-3.5 flex flex-col justify-between overflow-hidden shadow-sm">
        <div className="flex items-start justify-between">
          <div className="w-9 h-9 rounded-lg bg-[#1683E8]/15 border border-[#1683E8]/30 flex items-center justify-center text-[#1683E8]">
            <Radio className="w-5 h-5" />
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[10px] font-medium text-[#9CA3AF] block">Network</span>
              <div className="font-mono text-base font-bold text-[#E5E7EB] mt-0.5">
                {latencyMs} ms
              </div>
              <div className="text-[9px] font-medium text-[#6B7280]">Latency</div>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-medium text-[#9CA3AF] block opacity-0">.</span>
              <div className="font-mono text-base font-bold text-[#E5E7EB] mt-0.5">
                {packetLossRate.toFixed(1)}%
              </div>
              <div className="text-[9px] font-medium text-[#6B7280]">Packet Loss</div>
            </div>
            {/* Mini visual signal bars */}
            <div className="flex items-end gap-0.5 h-6 self-center pl-1">
              <span className="w-1 h-2 rounded-xs bg-[#1683E8]" />
              <span className="w-1 h-3.5 rounded-xs bg-[#1683E8]" />
              <span className="w-1 h-5 rounded-xs bg-[#1683E8]" />
              <span className="w-1 h-4 rounded-xs bg-[#1683E8]" />
              <span className="w-1 h-6 rounded-xs bg-[#1683E8]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
