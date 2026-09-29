import React from 'react';
import {
  Bot,
  Battery,
  ChevronRight,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { RobotTelemetry, TaskTelemetry } from '../types';

interface RobotStatusPanelProps {
  robots: RobotTelemetry[];
  tasks?: TaskTelemetry[];
  selectedRobotId: string | null;
  onSelectRobot: (robotId: string) => void;
  onViewAll?: () => void;
}

export const RobotStatusPanel: React.FC<RobotStatusPanelProps> = ({
  robots,
  tasks = [],
  selectedRobotId,
  onSelectRobot,
  onViewAll,
}) => {
  const getStatusBadge = (state: string) => {
    switch (state) {
      case 'NORMAL':
      case 'IDLE':
      case 'MOVING':
      case 'PLANNING':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 uppercase">
            NORMAL
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30 uppercase">
            DEGRADED
          </span>
        );
      case 'LOCAL_AUTONOMY':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide bg-[#8B5CF6]/15 text-[#8B5CF6] border border-[#8B5CF6]/30 uppercase">
            LOCAL AUTONOMY
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 uppercase">
            FAILED
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide bg-[#1683E8]/15 text-[#1683E8] border border-[#1683E8]/30 uppercase">
            {state}
          </span>
        );
    }
  };

  const getRobotAccent = (robotId: string) => {
    switch (robotId) {
      case 'R1':
        return {
          bg: 'bg-[#06B6D4]/15',
          border: 'border-[#06B6D4]/30',
          text: 'text-[#06B6D4]',
          sparkColor: '#06B6D4',
        };
      case 'R2':
        return {
          bg: 'bg-[#22C55E]/15',
          border: 'border-[#22C55E]/30',
          text: 'text-[#22C55E]',
          sparkColor: '#22C55E',
        };
      case 'R3':
      default:
        return {
          bg: 'bg-[#F59E0B]/15',
          border: 'border-[#F59E0B]/30',
          text: 'text-[#F59E0B]',
          sparkColor: '#F59E0B',
        };
    }
  };

  const getRobotEta = (robot: RobotTelemetry) => {
    if (robot.state === 'FAILED') return 'OFFLINE';
    if (!robot.current_task) return 'IDLE';
    const remainingSteps = robot.current_path
      ? Math.max(1, robot.current_path.length - robot.path_progress)
      : 8;
    const speed = Math.max(0.5, robot.velocity || 1.0);
    const secs = Math.round(remainingSteps / speed);
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `ETA ${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-[#151A21] border border-[#29323D] rounded-xl flex flex-col overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-4 py-2.5 border-b border-[#29323D] flex items-center justify-between select-none">
        <div className="text-sm font-semibold text-[#E5E7EB]">
          Robot Status ({robots.length})
        </div>
        <button
          onClick={onViewAll}
          className="text-xs font-medium text-[#1683E8] hover:text-[#2B95F5] flex items-center gap-1 cursor-pointer transition-colors"
        >
          <span>View All</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Robot Rows */}
      <div className="divide-y divide-[#29323D]/60">
        {robots.map((robot) => {
          const accent = getRobotAccent(robot.robot_id);
          const isSelected = selectedRobotId === robot.robot_id;
          const batteryVal = Math.round(robot.battery);
          const matchedTask = tasks.find((t) => t.task_id === robot.current_task);
          const etaText = getRobotEta(robot);

          return (
            <div
              key={robot.robot_id}
              onClick={() => onSelectRobot(robot.robot_id)}
              className={`p-3.5 flex items-center justify-between gap-3 cursor-pointer transition-colors select-none ${
                isSelected ? 'bg-[#1B222B]' : 'hover:bg-[#1B222B]/60'
              }`}
            >
              {/* Left: Icon & Identity */}
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-9 h-9 rounded-lg ${accent.bg} border ${accent.border} flex items-center justify-center ${accent.text} shrink-0`}
                >
                  <Bot className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-[#E5E7EB]">
                      {robot.robot_id}
                    </span>
                    {getStatusBadge(robot.state)}
                  </div>
                  <div className="text-xs text-[#9CA3AF] mt-0.5 truncate flex items-center gap-2">
                    <span className="font-mono">Task: {robot.current_task || 'None'}</span>
                    {matchedTask && (
                      <span className="text-[#6B7280]">
                        {matchedTask.phase === 'DELIVERY' ? 'Deliver' : 'Pickup'}
                      </span>
                    )}
                    <span className="text-[10px] text-[#06B6D4] font-mono">{etaText}</span>
                  </div>
                </div>
              </div>

              {/* Right: Battery, Sparkline & Chevron */}
              <div className="flex items-center gap-3 shrink-0">
                <div className="flex flex-col items-end">
                  <div className="flex items-center gap-1.5 text-xs font-mono font-medium text-[#E5E7EB]">
                    <Battery
                      className={`w-3.5 h-3.5 ${
                        batteryVal > 50 ? 'text-[#22C55E]' : batteryVal > 20 ? 'text-[#F59E0B]' : 'text-[#EF4444]'
                      }`}
                    />
                    <span>{batteryVal}%</span>
                  </div>
                  {/* Mini Trend Line */}
                  <svg className="w-14 h-3.5 mt-0.5" viewBox="0 0 60 14">
                    <path
                      d={
                        robot.robot_id === 'R1'
                          ? 'M0,10 Q15,4 30,8 T60,2'
                          : robot.robot_id === 'R2'
                          ? 'M0,4 Q15,12 30,6 T60,8'
                          : 'M0,8 Q15,2 30,11 T60,5'
                      }
                      fill="none"
                      stroke={accent.sparkColor}
                      strokeWidth="1.5"
                    />
                  </svg>
                </div>

                <ChevronRight className="w-4 h-4 text-[#6B7280]" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
