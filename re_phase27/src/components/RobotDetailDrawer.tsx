import React from 'react';
import {
  X,
  Bot,
  Battery,
  MapPin,
  Compass,
  Gauge,
  Activity,
  Radio,
  RotateCcw,
  Pause,
  Play,
  Share2,
} from 'lucide-react';
import { RobotTelemetry, UserRole } from '../types';
import { roleAllows } from '../permissions';

interface RobotDetailDrawerProps {
  robot: RobotTelemetry | null;
  currentUserRole: UserRole;
  onClose: () => void;
  onAction?: (action: string, robotId: string) => void;
}

export const RobotDetailDrawer: React.FC<RobotDetailDrawerProps> = ({
  robot,
  currentUserRole,
  onClose,
  onAction,
}) => {
  if (!robot) return null;
  const canRecover = roleAllows(currentUserRole, 'recovery');

  return (
    <div className="fixed inset-y-0 right-0 w-80 bg-[#151A21] border-l border-[#29323D] z-50 flex flex-col shadow-2xl select-none animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="p-4 border-b border-[#29323D] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#1683E8]/15 border border-[#1683E8]/30 flex items-center justify-center text-[#1683E8]">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="font-mono text-base font-bold text-[#E5E7EB]">
              Robot {robot.robot_id}
            </div>
            <div className="text-[11px] text-[#9CA3AF]">
              Status: <span className="font-semibold text-[#22C55E]">{robot.state}</span>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-7 h-7 rounded-md bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#9CA3AF] hover:text-[#E5E7EB] flex items-center justify-center cursor-pointer transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body telemetry */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* Vital stats grid */}
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-2.5">
            <span className="text-[10px] text-[#6B7280] uppercase tracking-wider block">Position (X, Y)</span>
            <div className="font-mono text-sm font-bold text-[#E5E7EB] mt-0.5">
              [{robot.position[0]}, {robot.position[1]}]
            </div>
          </div>

          <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-2.5">
            <span className="text-[10px] text-[#6B7280] uppercase tracking-wider block">Battery</span>
            <div className="font-mono text-sm font-bold text-[#22C55E] mt-0.5 flex items-center gap-1">
              <Battery className="w-3.5 h-3.5" />
              <span>{Math.round(robot.battery)}%</span>
            </div>
          </div>

          <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-2.5">
            <span className="text-[10px] text-[#6B7280] uppercase tracking-wider block">Heading</span>
            <div className="font-mono text-sm font-bold text-[#E5E7EB] mt-0.5">
              {(robot.orientation || 0).toFixed(2)} rad
            </div>
          </div>

          <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-2.5">
            <span className="text-[10px] text-[#6B7280] uppercase tracking-wider block">Velocity</span>
            <div className="font-mono text-sm font-bold text-[#E5E7EB] mt-0.5">
              {robot.velocity || 1.0} m/s
            </div>
          </div>
        </div>

        {/* Task Details */}
        <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-3 space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
            Task & Pathing
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Current Task:</span>
              <span className="font-mono font-bold text-[#E5E7EB]">{robot.current_task || 'None'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Planned Path Length:</span>
              <span className="font-mono text-[#E5E7EB]">{robot.current_path?.length || 0} waypoints</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Path Progress:</span>
              <span className="font-mono text-[#E5E7EB]">{robot.path_progress || 0} steps</span>
            </div>
          </div>
        </div>

        {/* Network & Hardware Health */}
        <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-3 space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
            Network & Health
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Link Status:</span>
              <span className="font-bold text-[#22C55E]">{robot.network_status}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Hardware Health:</span>
              <span className="font-mono text-[#E5E7EB]">{(robot.health * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Last Heartbeat:</span>
              <span className="font-mono text-[#9CA3AF]">{robot.last_heartbeat?.toFixed(1) || 0}s</span>
            </div>
          </div>
        </div>

        {/* Control Actions */}
        <div className="space-y-2 pt-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
            Robot Actions
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onAction?.('pause', robot.robot_id)}
              disabled={!canRecover}
              className="px-2.5 py-1.5 bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] rounded font-medium text-xs flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Pause</span>
            </button>
            <button
              onClick={() => onAction?.('resume', robot.robot_id)}
              disabled={!canRecover}
              className="px-2.5 py-1.5 bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] rounded font-medium text-xs flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Resume</span>
            </button>
            <button
              onClick={() => onAction?.('reassign', robot.robot_id)}
              disabled={!canRecover}
              className="px-2.5 py-1.5 bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] rounded font-medium text-xs flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
            >
              <Share2 className="w-3.5 h-3.5" />
              <span>Reassign</span>
            </button>
            <button
              onClick={() => onAction?.('reset', robot.robot_id)}
              disabled={!canRecover}
              className="px-2.5 py-1.5 bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] rounded font-medium text-xs flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
