import React from 'react';
import { Wifi, WifiOff, AlertTriangle, ShieldCheck, Activity, Split } from 'lucide-react';
import { RobotTelemetry } from '../types';

interface NetworkTopologyViewProps {
  robots: RobotTelemetry[];
  network?: {
    latency_ms: number;
    packet_loss_rate: number;
    jitter_ms: number;
    messages_sent: number;
    messages_dropped: number;
    messages_delivered: number;
    messages_duplicated: number;
    messages_reordered: number;
    in_flight_count: number;
    is_partitioned: boolean;
    partition_groups: string[][];
  };
}

export const NetworkTopologyView: React.FC<NetworkTopologyViewProps> = ({ robots, network }) => {
  const latency = network?.latency_ms ?? 12.0;
  const packetLoss = ((network?.packet_loss_rate ?? 0.001) * 100).toFixed(1);
  const jitter = network?.jitter_ms ?? 2.0;
  const isPartitioned = network?.is_partitioned ?? false;
  const sent = network?.messages_sent ?? 0;
  const dropped = network?.messages_dropped ?? 0;
  const delivered = network?.messages_delivered ?? 0;
  const duplicated = network?.messages_duplicated ?? 0;
  const reordered = network?.messages_reordered ?? 0;

  return (
    <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-5 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#29323D] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#1683E8]/15 border border-[#1683E8]/30 flex items-center justify-center text-[#1683E8]">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#E5E7EB]">Mesh Network Topology & Communication Simulation</h3>
            <p className="text-[11px] text-[#9CA3AF]">Authoritative packet flight, drop model, and multi-robot mesh routing</p>
          </div>
        </div>

        {/* Status Pill */}
        <div className="flex items-center gap-2">
          {isPartitioned ? (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EF4444]/15 border border-[#EF4444]/30 text-xs font-semibold text-[#EF4444]">
              <Split className="w-3.5 h-3.5" />
              <span>Network Partition Active</span>
            </div>
          ) : parseFloat(packetLoss) > 10.0 ? (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F59E0B]/15 border border-[#F59E0B]/30 text-xs font-semibold text-[#F59E0B]">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Degraded Link</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#22C55E]/15 border border-[#22C55E]/30 text-xs font-semibold text-[#22C55E]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Optimal Mesh Health</span>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 font-mono text-xs">
        <div className="bg-[#0F1115] p-3 rounded-lg border border-[#29323D]">
          <span className="text-[10px] text-[#6B7280] font-sans block uppercase">RTT Latency</span>
          <div className="text-base font-bold text-[#1683E8] mt-0.5">{latency} ms</div>
        </div>
        <div className="bg-[#0F1115] p-3 rounded-lg border border-[#29323D]">
          <span className="text-[10px] text-[#6B7280] font-sans block uppercase">Packet Loss</span>
          <div className={`text-base font-bold mt-0.5 ${parseFloat(packetLoss) > 5 ? 'text-[#EF4444]' : 'text-[#22C55E]'}`}>
            {packetLoss}%
          </div>
        </div>
        <div className="bg-[#0F1115] p-3 rounded-lg border border-[#29323D]">
          <span className="text-[10px] text-[#6B7280] font-sans block uppercase">Jitter</span>
          <div className="text-base font-bold text-[#E5E7EB] mt-0.5">±{jitter} ms</div>
        </div>
        <div className="bg-[#0F1115] p-3 rounded-lg border border-[#29323D]">
          <span className="text-[10px] text-[#6B7280] font-sans block uppercase">Sent / Delivered</span>
          <div className="text-base font-bold text-[#22C55E] mt-0.5">{sent} / {delivered}</div>
        </div>
        <div className="bg-[#0F1115] p-3 rounded-lg border border-[#29323D]">
          <span className="text-[10px] text-[#6B7280] font-sans block uppercase">Dropped</span>
          <div className="text-base font-bold text-[#EF4444] mt-0.5">{dropped}</div>
        </div>
        <div className="bg-[#0F1115] p-3 rounded-lg border border-[#29323D]">
          <span className="text-[10px] text-[#6B7280] font-sans block uppercase">Duplicated</span>
          <div className="text-base font-bold text-[#F59E0B] mt-0.5">{duplicated}</div>
        </div>
        <div className="bg-[#0F1115] p-3 rounded-lg border border-[#29323D]">
          <span className="text-[10px] text-[#6B7280] font-sans block uppercase">Reordered</span>
          <div className="text-base font-bold text-[#3B82F6] mt-0.5">{reordered}</div>
        </div>
      </div>

      {/* Visual Mesh Topology Diagram */}
      <div className="relative bg-[#0F1115] rounded-xl p-6 border border-[#29323D] flex flex-col items-center justify-center min-h-[220px]">
        {/* Coordinator Node */}
        <div className="flex flex-col items-center mb-10 z-10">
          <div className="w-14 h-14 rounded-2xl bg-[#1683E8]/20 border-2 border-[#1683E8] flex items-center justify-center text-[#1683E8] shadow-lg shadow-[#1683E8]/10">
            <Wifi className="w-6 h-6" />
          </div>
          <span className="text-xs font-bold text-[#E5E7EB] mt-1.5">Coordinator</span>
          <span className="text-[10px] text-[#9CA3AF] font-mono">Central Gateway</span>
        </div>

        {/* Partition Divider Line if partitioned */}
        {isPartitioned && (
          <div className="absolute inset-y-12 w-0.5 border-r-2 border-dashed border-[#EF4444]/60 flex items-center justify-center">
            <div className="bg-[#EF4444] text-white text-[9px] font-bold px-2 py-0.5 rounded shadow rotate-90">
              NETWORK SPLIT
            </div>
          </div>
        )}

        {/* Fleet Nodes */}
        <div className="grid grid-cols-3 gap-12 sm:gap-24 w-full max-w-lg z-10">
          {robots.map((r) => {
            const isCutOff = isPartitioned && r.network_status === 'PARTITIONED';
            const isDegraded = r.network_status === 'DEGRADED';
            return (
              <div key={r.robot_id} className="flex flex-col items-center text-center">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold font-mono transition-all ${
                    r.state === 'FAILED'
                      ? 'bg-[#EF4444]/20 border-2 border-[#EF4444] text-[#EF4444]'
                      : isCutOff
                      ? 'bg-[#F59E0B]/20 border-2 border-[#F59E0B] text-[#F59E0B]'
                      : isDegraded
                      ? 'bg-[#EAB308]/20 border-2 border-[#EAB308] text-[#EAB308]'
                      : 'bg-[#22C55E]/20 border-2 border-[#22C55E] text-[#22C55E]'
                  }`}
                >
                  {r.robot_id}
                </div>
                <span className="text-xs font-bold text-[#E5E7EB] mt-1.5">{r.robot_id}</span>
                <span className="text-[10px] text-[#9CA3AF] font-mono">{r.network_status}</span>
                <span className="text-[9px] text-[#6B7280]">
                  {r.state === 'FAILED' ? 'Offline' : `HB: ${r.last_heartbeat?.toFixed(1) || 0}s`}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
