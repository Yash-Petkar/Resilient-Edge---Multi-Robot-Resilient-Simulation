import React from 'react';
import { ArrowRight, Plus } from 'lucide-react';
import { TaskTelemetry, RobotTelemetry } from '../types';

interface CurrentTasksPanelProps {
  tasks: TaskTelemetry[];
  robots: RobotTelemetry[];
  onOpenDispatcher?: () => void;
  onSelectTask?: (task: TaskTelemetry) => void;
}

export const CurrentTasksPanel: React.FC<CurrentTasksPanelProps> = ({
  tasks,
  robots,
  onOpenDispatcher,
  onSelectTask,
}) => {
  const getPriorityBadge = (priority: number) => {
    if (priority >= 3) {
      return (
        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 uppercase">
          HIGH
        </span>
      );
    }
    if (priority === 2) {
      return (
        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30 uppercase">
          MED
        </span>
      );
    }
    return (
      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#1683E8]/15 text-[#1683E8] border border-[#1683E8]/30 uppercase">
        LOW
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 uppercase">
            COMPLETED
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#1683E8]/15 text-[#1683E8] border border-[#1683E8]/30 uppercase">
            IN PROGRESS
          </span>
        );
      case 'ASSIGNED':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#06B6D4]/15 text-[#06B6D4] border border-[#06B6D4]/30 uppercase">
            ASSIGNED
          </span>
        );
      case 'BLOCKED':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 uppercase">
            BLOCKED
          </span>
        );
      case 'REASSIGNED':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#8B5CF6]/15 text-[#8B5CF6] border border-[#8B5CF6]/30 uppercase">
            REASSIGNED
          </span>
        );
      case 'FAILED':
      case 'CANCELLED':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 uppercase">
            {status}
          </span>
        );
      case 'AVAILABLE':
      default:
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide bg-[#6B7280]/15 text-[#9CA3AF] border border-[#6B7280]/30 uppercase">
            AVAILABLE
          </span>
        );
    }
  };

  const calculateEta = (task: TaskTelemetry) => {
    if (task.status === 'COMPLETED') return '—';
    if (task.status === 'FAILED' || task.status === 'CANCELLED') return 'ERR';
    if (!task.assigned_robot) return 'Queue';
    const robot = robots.find((r) => r.robot_id === task.assigned_robot);
    if (!robot) return '—';

    const remainingSteps = robot.current_path
      ? Math.max(1, robot.current_path.length - robot.path_progress)
      : 12;
    const speed = Math.max(0.5, robot.velocity || 1.0);
    const secs = Math.round(remainingSteps / speed);
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-[#151A21] border border-[#29323D] rounded-xl flex flex-col overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-4 py-2.5 border-b border-[#29323D] flex items-center justify-between select-none">
        <div className="text-sm font-semibold text-[#E5E7EB]">
          Current Tasks ({tasks.length})
        </div>
        <div className="flex items-center gap-2">
          {onOpenDispatcher && (
            <button
              onClick={onOpenDispatcher}
              className="text-xs font-medium text-[#E5E7EB] bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] px-2 py-1 rounded flex items-center gap-1 cursor-pointer transition-colors"
            >
              <Plus className="w-3 h-3 text-[#1683E8]" />
              <span>New Task</span>
            </button>
          )}
          <button
            onClick={onOpenDispatcher}
            className="text-xs font-medium text-[#1683E8] hover:text-[#2B95F5] flex items-center gap-1 cursor-pointer transition-colors"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Compact Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#29323D] text-[10px] uppercase font-semibold text-[#6B7280] bg-[#0F1115]/50">
              <th className="py-2 px-3">ID</th>
              <th className="py-2 px-3">Type</th>
              <th className="py-2 px-3">Priority</th>
              <th className="py-2 px-3">Status</th>
              <th className="py-2 px-3">Robot</th>
              <th className="py-2 px-3 text-right">ETA</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#29323D]/50 font-mono">
            {tasks.slice(0, 6).map((task) => {
              const isDelivery = task.phase === 'DELIVERY' || task.status === 'COMPLETED';
              const formattedId = `T-${task.task_id.replace('T', '')}`;
              const eta = calculateEta(task);

              return (
                <tr
                  key={task.task_id}
                  onClick={() => onSelectTask?.(task)}
                  className="hover:bg-[#1B222B]/60 cursor-pointer transition-colors"
                >
                  <td className="py-2 px-3 font-semibold text-[#E5E7EB]">{formattedId}</td>
                  <td className="py-2 px-3 text-[#9CA3AF] font-sans">{isDelivery ? 'Delivery' : 'Pickup'}</td>
                  <td className="py-2 px-3">{getPriorityBadge(task.priority)}</td>
                  <td className="py-2 px-3">{getStatusBadge(task.status)}</td>
                  <td className="py-2 px-3 text-[#E5E7EB] font-sans">{task.assigned_robot || '—'}</td>
                  <td className="py-2 px-3 text-right text-[#9CA3AF]">{eta}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
