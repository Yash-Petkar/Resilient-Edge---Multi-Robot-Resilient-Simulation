import React, { useState } from 'react';
import { FaultTelemetry, RobotTelemetry, UserRole } from '../../types';
import { Flame, ShieldAlert, WifiOff, BatteryWarning, Ban, Radio, RotateCcw, AlertTriangle } from 'lucide-react';

interface FaultInjectorProps {
  activeFaults: FaultTelemetry[];
  robots: RobotTelemetry[];
  onInjectFault: (type: string, target: string, duration: number, parameters?: Record<string, any>) => void;
  onClearFault: (faultId: string) => void;
  onClearAll: () => void;
  currentUserRole: UserRole;
}

export const FaultInjector: React.FC<FaultInjectorProps> = ({
  activeFaults,
  robots,
  onInjectFault,
  onClearFault,
  onClearAll,
  currentUserRole,
}) => {
  const [selectedRobot, setSelectedRobot] = useState('R2');
  const [duration, setDuration] = useState(30);
  const [packetLossRate, setPacketLossRate] = useState(0.35);
  const [latencySec, setLatencySec] = useState(1.2);

  const canInject = currentUserRole === 'ADMIN';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Flame className="w-4 h-4 text-rose-500" />
            Chaos &amp; Fault Injection Console
          </h2>
          <p className="text-xs text-slate-500">
            Inject real hardware, network, and environmental anomalies to evaluate resilience state transitions.
          </p>
        </div>

        {activeFaults.length > 0 && (
          <button
            onClick={onClearAll}
            disabled={!canInject}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs shadow-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Restore All / Clear Faults
          </button>
        )}
      </div>

      {!canInject && (
        <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>Role Restricted: Only <strong>ADMIN</strong> users can inject or clear faults. (Current: {currentUserRole})</span>
        </div>
      )}

      {/* Fault Injection Control Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {/* Robot Hardware Failure */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800 text-xs space-y-3">
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
            <ShieldAlert className="w-4 h-4 text-rose-500" />
            Robot Fatal Failure
          </div>
          <p className="text-slate-500 text-[11px]">
            Instantly forces target robot health to 0%, drops heartbeat, and tests automatic task reassignment.
          </p>

          <div className="flex items-center gap-2">
            <select
              value={selectedRobot}
              onChange={(e) => setSelectedRobot(e.target.value)}
              className="flex-1 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-xs"
            >
              {robots.map((r) => (
                <option key={r.robot_id} value={r.robot_id}>
                  {r.robot_id} ({r.state})
                </option>
              ))}
            </select>

            <button
              onClick={() => onInjectFault('ROBOT_FAILURE', selectedRobot, duration)}
              disabled={!canInject}
              className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-md font-medium transition-colors disabled:opacity-40 cursor-pointer"
            >
              Fail Robot
            </button>
          </div>
        </div>

        {/* Low Battery Fault */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800 text-xs space-y-3">
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
            <BatteryWarning className="w-4 h-4 text-amber-500" />
            Critical Low Battery
          </div>
          <p className="text-slate-500 text-[11px]">
            Forces battery level to 8%, verifying degraded state transition and charging dock priority.
          </p>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onInjectFault('LOW_BATTERY', selectedRobot, duration)}
              disabled={!canInject}
              className="w-full py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-md font-medium transition-colors disabled:opacity-40 cursor-pointer"
            >
              Drain {selectedRobot} Battery
            </button>
          </div>
        </div>

        {/* Blocked Aisle Detour */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800 text-xs space-y-3">
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
            <Ban className="w-4 h-4 text-rose-500" />
            Block Central Aisle
          </div>
          <p className="text-slate-500 text-[11px]">
            Blocks major warehouse thoroughfare cells (8,4)-(9,5) to trigger dynamic A* detour replanning.
          </p>

          <button
            onClick={() =>
              onInjectFault('BLOCKED_AISLE', 'aisle_central', duration, {
                cells: [
                  [8, 4],
                  [8, 5],
                  [9, 4],
                  [9, 5],
                ],
              })
            }
            disabled={!canInject}
            className="w-full py-1 bg-slate-900 dark:bg-blue-600 hover:bg-slate-800 text-white rounded-md font-medium transition-colors disabled:opacity-40 cursor-pointer"
          >
            Block Corridor
          </button>
        </div>

        {/* Packet Loss */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800 text-xs space-y-3">
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
            <WifiOff className="w-4 h-4 text-amber-500" />
            Simulate Packet Loss
          </div>
          <p className="text-slate-500 text-[11px]">
            Simulates lossy wireless environment with {Math.round(packetLossRate * 100)}% message drop rate.
          </p>

          <div className="flex items-center gap-2">
            <select
              value={packetLossRate}
              onChange={(e) => setPacketLossRate(Number(e.target.value))}
              className="flex-1 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-xs"
            >
              <option value={0.2}>20% Loss Rate</option>
              <option value={0.35}>35% Loss Rate</option>
              <option value={0.6}>60% Loss Rate</option>
              <option value={0.85}>85% Severe Loss</option>
            </select>
            <button
              onClick={() => onInjectFault('PACKET_LOSS', 'network', duration, { rate: packetLossRate })}
              disabled={!canInject}
              className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-md font-medium transition-colors disabled:opacity-40 cursor-pointer"
            >
              Apply Loss
            </button>
          </div>
        </div>

        {/* Network Partition */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800 text-xs space-y-3">
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
            <Radio className="w-4 h-4 text-purple-500" />
            Network Partition (Split-Brain)
          </div>
          <p className="text-slate-500 text-[11px]">
            Isolates fleet into subnetworks, testing Local Autonomy and subsequent State Resynchronization.
          </p>

          <button
            onClick={() => onInjectFault('NETWORK_PARTITION', 'network', duration)}
            disabled={!canInject}
            className="w-full py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-md font-medium transition-colors disabled:opacity-40 cursor-pointer"
          >
            Trigger Network Partition
          </button>
        </div>

        {/* Dynamic Obstacle */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800 text-xs space-y-3">
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            Dynamic Obstacle
          </div>
          <p className="text-slate-500 text-[11px]">
            Places an unexpected obstacle at coordinate (10, 8) to test instant reactive obstacle avoidance.
          </p>

          <button
            onClick={() => onInjectFault('DYNAMIC_OBSTACLE', 'pos:10,8', duration, { position: [10, 8] })}
            disabled={!canInject}
            className="w-full py-1 bg-slate-800 hover:bg-slate-700 text-white rounded-md font-medium transition-colors disabled:opacity-40 cursor-pointer"
          >
            Drop Dynamic Obstacle
          </button>
        </div>
      </div>

      {/* Active Faults Live Monitor */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800">
        <h3 className="font-bold text-xs text-slate-900 dark:text-slate-100 mb-2">
          Active Injected Faults ({activeFaults.length})
        </h3>

        {activeFaults.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No faults currently active. Fleet operating in nominal conditions.</p>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {activeFaults.map((f) => (
              <div key={f.fault_id} className="py-2 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  <span className="font-mono font-bold text-rose-600 dark:text-rose-400">{f.fault_type}</span>
                  <span className="text-slate-500">Target: <code className="font-mono text-slate-700 dark:text-slate-300">{f.target}</code></span>
                  <span className="text-slate-400">Duration: {f.duration}s</span>
                </div>

                <button
                  onClick={() => onClearFault(f.fault_id)}
                  disabled={!canInject}
                  className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors disabled:opacity-40 cursor-pointer"
                >
                  Clear Fault
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
