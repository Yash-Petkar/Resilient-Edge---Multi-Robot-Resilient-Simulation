import React, { useState } from 'react';
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';
import { FaultTelemetry, RobotTelemetry, UserRole } from '../types';
import { roleAllows } from '../permissions';

interface FaultInjectionPanelProps {
  activeFaults: FaultTelemetry[];
  robots: RobotTelemetry[];
  currentUserRole: UserRole;
  onInjectFault: (
    type: string,
    target: string,
    duration: number,
    parameters?: Record<string, any>
  ) => Promise<boolean | void>;
  onClearFault: (faultId: string) => Promise<boolean | void>;
  onClearAll: () => Promise<boolean | void>;
}

export const FaultInjectionPanel: React.FC<FaultInjectionPanelProps> = ({
  activeFaults,
  robots,
  currentUserRole,
  onInjectFault,
  onClearFault,
  onClearAll,
}) => {
  const [activeTab, setActiveTab] = useState<'Robot' | 'Network' | 'Environment'>('Robot');

  // Form states
  const [faultType, setFaultType] = useState<string>('ROBOT_FAILURE');
  const [targetRobot, setTargetRobot] = useState<string>('R2');
  const [duration, setDuration] = useState<number>(30);
  const [packetLossRate, setPacketLossRate] = useState<number>(0.35);
  const [latencyMs, setLatencyMs] = useState<number>(150);

  // Status feedback
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const canInject = roleAllows(currentUserRole, 'fault_injection');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canInject) return;
    setIsSubmitting(true);
    setFeedback(null);

    try {
      let typeToSend = faultType;
      let targetToSend = targetRobot;
      let params: Record<string, any> = {};

      if (activeTab === 'Robot') {
        typeToSend = faultType;
        targetToSend = targetRobot;
      } else if (activeTab === 'Network') {
        targetToSend = 'network';
        if (faultType === 'PACKET_LOSS') {
          typeToSend = 'PACKET_LOSS';
          params = { rate: packetLossRate };
        } else if (faultType === 'LATENCY') {
          typeToSend = 'LATENCY';
          params = { delay_ms: latencyMs };
        } else if (faultType === 'JITTER') {
          typeToSend = 'JITTER';
          params = { jitter_ms: 40 };
        } else if (faultType === 'MESSAGE_DUPLICATION') {
          typeToSend = 'MESSAGE_DUPLICATION';
          params = { dup_rate: 0.25 };
        } else if (faultType === 'MESSAGE_REORDERING') {
          typeToSend = 'MESSAGE_REORDERING';
          params = { reorder_rate: 0.25 };
        } else if (faultType === 'NETWORK_PARTITION') {
          typeToSend = 'NETWORK_PARTITION';
          params = { group_a: ['R1'], group_b: ['R2', 'R3'] };
        }
      } else {
        // Environment
        targetToSend = faultType === 'BLOCKED_AISLE' ? 'AISLE_CENTRAL' : 'CELL:10,8';
        typeToSend = faultType;
        if (faultType === 'BLOCKED_AISLE') {
          params = { cells: [[14, 8], [14, 9]] };
        } else {
          params = { position: [10, 8] };
        }
      }

      await onInjectFault(typeToSend, targetToSend, duration, params);
      setFeedback({
        type: 'success',
        message: `Fault injected: ${targetToSend} — ${typeToSend}`,
      });
      setTimeout(() => setFeedback(null), 4000);
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.message || 'Failed to inject fault.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-[#151A21] border border-[#29323D] rounded-xl flex flex-col overflow-hidden shadow-sm h-full">
      {/* Header & Tabs */}
      <div className="px-4 py-2.5 border-b border-[#29323D] flex items-center justify-between select-none">
        <div className="text-sm font-semibold text-[#E5E7EB]">
          Fault Injection
        </div>

        {/* Category Tabs */}
        <div className="bg-[#0F1115] border border-[#29323D] p-0.5 rounded-lg flex items-center text-xs">
          <button
            type="button"
            onClick={() => {
              setActiveTab('Robot');
              setFaultType('ROBOT_FAILURE');
            }}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
              activeTab === 'Robot' ? 'bg-[#1683E8] text-white' : 'text-[#9CA3AF] hover:text-[#E5E7EB]'
            }`}
          >
            Robot
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('Network');
              setFaultType('PACKET_LOSS');
            }}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
              activeTab === 'Network' ? 'bg-[#1683E8] text-white' : 'text-[#9CA3AF] hover:text-[#E5E7EB]'
            }`}
          >
            Network
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('Environment');
              setFaultType('BLOCKED_AISLE');
            }}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
              activeTab === 'Environment' ? 'bg-[#1683E8] text-white' : 'text-[#9CA3AF] hover:text-[#E5E7EB]'
            }`}
          >
            Environment
          </button>
        </div>
      </div>

      <div className="p-3.5 space-y-3 flex-1 flex flex-col justify-between">
        {/* Form Controls */}
        <form onSubmit={handleSubmit} className="space-y-2.5 text-xs">
          <div className="grid grid-cols-3 gap-2">
            {/* Fault Type */}
            <div>
              <label className="text-[10px] text-[#9CA3AF] font-medium block mb-1">
                Fault Type
              </label>
              <select
                value={faultType}
                disabled={!canInject}
                onChange={(e) => setFaultType(e.target.value)}
                className="w-full bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] text-xs rounded px-2 py-1.5 focus:outline-none focus:border-[#1683E8] cursor-pointer"
              >
                {activeTab === 'Robot' && (
                  <>
                    <option value="ROBOT_FAILURE">Robot Failure</option>
                    <option value="LOW_BATTERY">Low Battery</option>
                  </>
                )}
                {activeTab === 'Network' && (
                  <>
                    <option value="PACKET_LOSS">Packet Loss</option>
                    <option value="LATENCY">Latency</option>
                    <option value="JITTER">Jitter</option>
                    <option value="MESSAGE_DUPLICATION">Msg Duplication</option>
                    <option value="MESSAGE_REORDERING">Msg Reordering</option>
                    <option value="NETWORK_PARTITION">Network Partition</option>
                  </>
                )}
                {activeTab === 'Environment' && (
                  <>
                    <option value="BLOCKED_AISLE">Blocked Aisle</option>
                    <option value="DYNAMIC_OBSTACLE">Dynamic Obstacle</option>
                  </>
                )}
              </select>
            </div>

            {/* Target Robot / Target */}
            <div>
              <label className="text-[10px] text-[#9CA3AF] font-medium block mb-1">
                {activeTab === 'Robot' ? 'Target Robot' : 'Target'}
              </label>
              {activeTab === 'Robot' ? (
                <select
                  value={targetRobot}
                  disabled={!canInject}
                  onChange={(e) => setTargetRobot(e.target.value)}
                  className="w-full bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] text-xs rounded px-2 py-1.5 focus:outline-none focus:border-[#1683E8] cursor-pointer font-mono"
                >
                  {robots.map((r) => (
                    <option key={r.robot_id} value={r.robot_id}>
                      {r.robot_id}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  disabled
                  value={activeTab === 'Network' ? 'Fleet Mesh' : 'Central Aisle'}
                  className="w-full bg-[#0F1115] border border-[#29323D] text-[#9CA3AF] text-xs rounded px-2 py-1.5 font-mono"
                />
              )}
            </div>

            {/* Trigger Time */}
            <div>
              <label className="text-[10px] text-[#9CA3AF] font-medium block mb-1">
                Trigger Time
              </label>
              <div className="flex items-center justify-between bg-[#0F1115] border border-[#29323D] rounded px-2 py-1.5 text-[#E5E7EB]">
                <span>Now</span>
                <Calendar className="w-3.5 h-3.5 text-[#6B7280]" />
              </div>
            </div>
          </div>

          {/* Row 2: Duration & Button */}
          <div className="grid grid-cols-3 gap-2 items-end">
            <div>
              <label className="text-[10px] text-[#9CA3AF] font-medium block mb-1">
                Duration
              </label>
              <select
                value={duration}
                disabled={!canInject}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="w-full bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] text-xs rounded px-2 py-1.5 focus:outline-none focus:border-[#1683E8] cursor-pointer"
              >
                <option value={99999}>Permanent</option>
                <option value={15}>15 seconds</option>
                <option value={30}>30 seconds</option>
                <option value={60}>60 seconds</option>
              </select>
            </div>

            <div className="col-span-2">
              <button
                type="submit"
                disabled={isSubmitting || !canInject}
                className="w-full bg-[#EF4444] hover:bg-[#dc2626] text-white font-semibold py-1.5 px-3 rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer shadow-sm disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 fill-current" />
                )}
                <span>{isSubmitting ? 'Injecting...' : 'Inject Fault'}</span>
              </button>
            </div>
          </div>

          {/* Feedback banner */}
          {feedback && (
            <div
              className={`p-2 rounded text-[11px] flex items-center gap-1.5 ${
                feedback.type === 'success'
                  ? 'bg-[#22C55E]/15 border border-[#22C55E]/30 text-[#22C55E]'
                  : 'bg-[#EF4444]/15 border border-[#EF4444]/30 text-[#EF4444]'
              }`}
            >
              {feedback.type === 'success' ? (
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              ) : (
                <XCircle className="w-3.5 h-3.5 shrink-0" />
              )}
              <span className="truncate">{feedback.message}</span>
            </div>
          )}
        </form>

        {/* Active Faults List */}
        <div className="border-t border-[#29323D]/60 pt-2.5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
              Active Faults ({activeFaults.length})
            </span>
            {activeFaults.length > 0 && (
              <button
                onClick={() => onClearAll()}
                disabled={!canInject}
                className="text-[10px] text-[#EF4444] hover:underline cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Resolve All
              </button>
            )}
          </div>

          {activeFaults.length > 0 ? (
            <div className="space-y-1 max-h-[85px] overflow-y-auto">
              {activeFaults.map((f) => (
                <div
                  key={f.fault_id}
                  className="bg-[#0F1115] border border-[#EF4444]/30 rounded px-2.5 py-1.5 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444] animate-pulse" />
                    <span className="font-semibold text-[#E5E7EB]">{f.fault_type}</span>
                    <span className="text-[#9CA3AF] font-mono text-[11px]">→ {f.target}</span>
                  </div>
                  <button
                    onClick={() => onClearFault(f.fault_id)}
                    disabled={!canInject}
                    className="text-[11px] font-medium text-[#22C55E] hover:text-[#16a34a] px-1.5 py-0.5 rounded bg-[#22C55E]/10 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Clear
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-2 text-xs text-[#6B7280]">
              No active faults
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
