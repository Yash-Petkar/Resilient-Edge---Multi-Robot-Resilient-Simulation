import React from 'react';
import { X, ClipboardList, MapPin, Clock, ArrowRight, UserCheck, AlertTriangle, Share2 } from 'lucide-react';
import { TaskTelemetry, RobotTelemetry, UserRole } from '../types';
import { roleAllows } from '../permissions';

interface TaskDetailDrawerProps {
  task: TaskTelemetry | null;
  robots: RobotTelemetry[];
  currentUserRole: UserRole;
  onClose: () => void;
  onReassignTask?: (taskId: string) => void;
  onAssignTask?: (taskId: string, robotId: string) => void;
  onCancelTask?: (taskId: string) => void;
}

export const TaskDetailDrawer: React.FC<TaskDetailDrawerProps> = ({
  task,
  robots,
  currentUserRole,
  onClose,
  onReassignTask,
  onAssignTask,
  onCancelTask,
}) => {
  if (!task) return null;

  const assignedRobot = robots.find((r) => r.robot_id === task.assigned_robot);
  const canManageTasks = roleAllows(currentUserRole, 'task_dispatch');

  const calculateEta = () => {
    if (task.status === 'COMPLETED') return 'Completed';
    if (task.status === 'FAILED' || task.status === 'CANCELLED') return 'Stopped';
    if (!assignedRobot) return 'Waiting for Robot';
    const remainingSteps = assignedRobot.current_path
      ? Math.max(1, assignedRobot.current_path.length - assignedRobot.path_progress)
      : 12;
    const speed = Math.max(0.5, assignedRobot.velocity || 1.0);
    const secs = Math.round(remainingSteps / speed);
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-y-0 right-0 w-84 bg-[#151A21] border-l border-[#29323D] z-50 flex flex-col shadow-2xl select-none animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="p-4 border-b border-[#29323D] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#F59E0B]/15 border border-[#F59E0B]/30 flex items-center justify-center text-[#F59E0B]">
            <ClipboardList className="w-4 h-4" />
          </div>
          <div>
            <div className="font-mono text-base font-bold text-[#E5E7EB]">
              Task {task.task_id.startsWith('T') ? task.task_id : `T${task.task_id}`}
            </div>
            <div className="text-[11px] text-[#9CA3AF]">
              Priority Level: <span className="font-bold text-[#E5E7EB]">{task.priority}</span>
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

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* Status & ETA */}
        <div className="grid grid-cols-2 gap-2 font-mono">
          <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-2.5">
            <span className="text-[10px] text-[#6B7280] uppercase tracking-wider block font-sans">Status</span>
            <div className="text-sm font-bold text-[#1683E8] mt-0.5">
              {task.status}
            </div>
          </div>
          <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-2.5">
            <span className="text-[10px] text-[#6B7280] uppercase tracking-wider block font-sans">Calculated ETA</span>
            <div className="text-sm font-bold text-[#22C55E] mt-0.5">
              {calculateEta()}
            </div>
          </div>
        </div>

        {/* Stations & Waypoints */}
        <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-3 space-y-2.5 font-mono">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280] font-sans">
            Logistics Stations
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[#06B6D4]">
              <MapPin className="w-3.5 h-3.5" />
              <span>Pickup: [{task.pickup[0]}, {task.pickup[1]}]</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-[#6B7280]" />
            <div className="flex items-center gap-1.5 text-[#F59E0B]">
              <MapPin className="w-3.5 h-3.5" />
              <span>Deliver: [{task.delivery[0]}, {task.delivery[1]}]</span>
            </div>
          </div>
          <div className="pt-1 text-[11px] text-[#9CA3AF] font-sans">
            Phase: <strong className="text-[#E5E7EB]">{task.phase}</strong>
          </div>
        </div>

        {/* Assignment */}
        <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-3 space-y-2 text-xs">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
            Assigned Fleet Robot
          </div>
          <div className="flex items-center justify-between font-mono">
            <span className="text-[#9CA3AF]">Robot ID:</span>
            <span className="font-bold text-[#E5E7EB]">{task.assigned_robot || 'Unassigned (In Queue)'}</span>
          </div>
          {assignedRobot && (
            <div className="flex items-center justify-between font-mono">
              <span className="text-[#9CA3AF]">Robot State:</span>
              <span className="font-bold text-[#22C55E]">{assignedRobot.state}</span>
            </div>
          )}
        </div>

        {/* Reassignment / Cancellation Controls */}
        <div className="space-y-2 pt-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280]">
            Task Operations
          </div>
          <div className="space-y-2">
            {task.status !== 'COMPLETED' && task.status !== 'CANCELLED' && task.assigned_robot && (
              <button
                onClick={() => onReassignTask?.(task.task_id)}
                disabled={!canManageTasks}
                className="w-full px-3 py-2 bg-[#F59E0B]/15 hover:bg-[#F59E0B]/25 border border-[#F59E0B]/30 text-[#F59E0B] rounded font-semibold text-xs flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>Auto Reassign Task</span>
              </button>
            )}

            <div className="text-[10px] text-[#6B7280] pt-1">Manual assignment</div>
            {robots.map((r) => (
              <button
                key={r.robot_id}
                onClick={() => onAssignTask?.(task.task_id, r.robot_id)}
                disabled={!canManageTasks || r.robot_id === task.assigned_robot || r.state === 'FAILED'}
                className="w-full px-3 py-1.5 bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] rounded font-medium text-xs flex items-center justify-between cursor-pointer transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <span>Assign to {r.robot_id} ({r.state})</span>
                <UserCheck className="w-3.5 h-3.5 text-[#1683E8]" />
              </button>
            ))}

            {task.status !== 'COMPLETED' && task.status !== 'CANCELLED' && (
              <button
                onClick={() => onCancelTask?.(task.task_id)}
                disabled={!canManageTasks}
                className="w-full px-3 py-1.5 bg-[#EF4444]/15 hover:bg-[#EF4444]/25 border border-[#EF4444]/30 text-[#EF4444] rounded font-medium text-xs flex items-center justify-center gap-1.5 cursor-pointer transition-colors mt-2"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Cancel Task</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
