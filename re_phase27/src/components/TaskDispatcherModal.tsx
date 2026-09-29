import React, { useState } from 'react';
import { TaskTelemetry, UserRole } from '../types';
import { roleAllows } from '../permissions';
import { Plus, CheckCircle2, Clock, AlertCircle, ArrowRight, X } from 'lucide-react';

interface TaskDispatcherModalProps {
  tasks: TaskTelemetry[];
  onDispatchTask: (pickup: [number, number], delivery: [number, number], priority: number, deadline: number) => void;
  currentUserRole: UserRole;
  pickupStations: Record<string, [number, number]>;
  deliveryStations: Record<string, [number, number]>;
}

export const TaskDispatcherModal: React.FC<TaskDispatcherModalProps> = ({
  tasks,
  onDispatchTask,
  currentUserRole,
  pickupStations,
  deliveryStations,
}) => {
  const [showModal, setShowModal] = useState(false);
  const [pickupKey, setPickupKey] = useState('P1');
  const [deliveryKey, setDeliveryKey] = useState('D1');
  const [priority, setPriority] = useState(2);
  const [deadline, setDeadline] = useState(300);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const p = pickupStations[pickupKey] || [2, 2];
    const d = deliveryStations[deliveryKey] || [21, 2];
    onDispatchTask(p, d, priority, deadline);
    setShowModal(false);
  };

  const canDispatch = roleAllows(currentUserRole, 'task_dispatch');

  return (
    <div className="space-y-4">
      {/* Top action bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Task Management &amp; Dispatcher
          </h2>
          <p className="text-xs text-slate-500">
            Monitor real-time task lifecycles, allocation priorities, and execution phases.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          disabled={!canDispatch}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          Dispatch New Task
        </button>
      </div>

      {/* Task Queue Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Available Tasks */}
        <div className="bg-slate-50 dark:bg-slate-900/60 rounded-xl p-3 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold text-xs text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-amber-500" />
              Available Queue
            </span>
            <span className="text-xs font-mono font-bold bg-amber-100 dark:bg-amber-950/80 text-amber-700 dark:text-amber-300 px-1.5 py-0.5 rounded">
              {tasks.filter((t) => t.status === 'AVAILABLE').length}
            </span>
          </div>

          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {tasks
              .filter((t) => t.status === 'AVAILABLE')
              .map((task) => (
                <div key={task.task_id} className="bg-white dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs shadow-2xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-slate-900 dark:text-slate-100">{task.task_id}</span>
                    <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
                      Pri: {task.priority}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-mono">
                    <span>({task.pickup[0]},{task.pickup[1]})</span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                    <span>({task.delivery[0]},{task.delivery[1]})</span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* In Progress Tasks */}
        <div className="bg-slate-50 dark:bg-slate-900/60 rounded-xl p-3 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold text-xs text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-blue-500" />
              In Progress
            </span>
            <span className="text-xs font-mono font-bold bg-blue-100 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded">
              {tasks.filter((t) => t.status === 'ASSIGNED' || t.status === 'IN_PROGRESS').length}
            </span>
          </div>

          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {tasks
              .filter((t) => t.status === 'ASSIGNED' || t.status === 'IN_PROGRESS')
              .map((task) => (
                <div key={task.task_id} className="bg-white dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs shadow-2xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-slate-900 dark:text-slate-100">{task.task_id}</span>
                    <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                      {task.assigned_robot || 'Assigned'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mb-1 font-mono">Phase: {task.phase}</div>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-mono">
                    <span>({task.pickup[0]},{task.pickup[1]})</span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                    <span>({task.delivery[0]},{task.delivery[1]})</span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Completed Tasks */}
        <div className="bg-slate-50 dark:bg-slate-900/60 rounded-xl p-3 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold text-xs text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              Completed
            </span>
            <span className="text-xs font-mono font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 px-1.5 py-0.5 rounded">
              {tasks.filter((t) => t.status === 'COMPLETED').length}
            </span>
          </div>

          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {tasks
              .filter((t) => t.status === 'COMPLETED')
              .map((task) => (
                <div key={task.task_id} className="bg-white dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs shadow-2xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-slate-900 dark:text-slate-100">{task.task_id}</span>
                    <span className="font-mono text-[10px] text-emerald-600 dark:text-emerald-400 font-bold">
                      ✓ Done
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-mono">
                    <span>({task.pickup[0]},{task.pickup[1]})</span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                    <span>({task.delivery[0]},{task.delivery[1]})</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Creation Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl max-w-md w-full p-5 shadow-xl text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                Dispatch New Autonomous Task
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                  Pickup Station
                </label>
                <select
                  value={pickupKey}
                  onChange={(e) => setPickupKey(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {Object.keys(pickupStations).map((k) => (
                    <option key={k} value={k}>
                      {k} - Coordinates ({pickupStations[k][0]}, {pickupStations[k][1]})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                  Delivery Station
                </label>
                <select
                  value={deliveryKey}
                  onChange={(e) => setDeliveryKey(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {Object.keys(deliveryStations).map((k) => (
                    <option key={k} value={k}>
                      {k} - Coordinates ({deliveryStations[k][0]}, {deliveryStations[k][1]})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Priority (1-5)
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-slate-900 dark:text-slate-100 focus:outline-none"
                  >
                    {[1, 2, 3, 4, 5].map((p) => (
                      <option key={p} value={p}>
                        Priority {p} {p === 5 ? '(Critical)' : p === 1 ? '(Low)' : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">
                    Deadline (seconds)
                  </label>
                  <input
                    type="number"
                    value={deadline}
                    onChange={(e) => setDeadline(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-slate-900 dark:text-slate-100 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm"
                >
                  Dispatch Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
