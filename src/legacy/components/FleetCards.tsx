import React from 'react';
import { RobotTelemetry, UserRole } from '../../types';
import { Bot, Battery, Activity, Wifi, ShieldAlert, Navigation } from 'lucide-react';

interface FleetCardsProps {
  robots: RobotTelemetry[];
  selectedRobotId: string | null;
  onSelectRobot: (robotId: string | null) => void;
  currentUserRole: UserRole;
  onManualStop?: (robotId: string) => void;
}

export const FleetCards: React.FC<FleetCardsProps> = ({
  robots,
  selectedRobotId,
  onSelectRobot,
  currentUserRole,
  onManualStop,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {robots.map((robot) => {
        const isSelected = robot.robot_id === selectedRobotId;
        const isLowBattery = robot.battery < 20;
        const isFailed = robot.state === 'FAILED';

        return (
          <div
            key={robot.robot_id}
            onClick={() => onSelectRobot(isSelected ? null : robot.robot_id)}
            className={`cursor-pointer rounded-xl p-4 border transition-all ${
              isSelected
                ? 'bg-blue-50/50 dark:bg-blue-950/20 border-blue-500 shadow-sm'
                : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
            }`}
          >
            {/* Header: ID & State */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono font-bold text-sm ${
                  isFailed
                    ? 'bg-rose-600 text-white'
                    : 'bg-slate-900 dark:bg-blue-600 text-white'
                }`}>
                  {robot.robot_id}
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 leading-none">
                    Unit {robot.robot_id}
                  </h3>
                  <span className="text-[11px] font-mono text-slate-500">
                    Pos: ({robot.position[0]}, {robot.position[1]})
                  </span>
                </div>
              </div>

              {/* State pill */}
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                isFailed ? 'bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300' :
                robot.state === 'LOCAL_AUTONOMY' ? 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300' :
                robot.state === 'MOVING' ? 'bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300' :
                robot.state === 'TASK_EXECUTION' ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300' :
                'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
              }`}>
                {robot.state}
              </span>
            </div>

            {/* Metrics rows */}
            <div className="space-y-2 text-xs">
              {/* Battery */}
              <div>
                <div className="flex justify-between items-center text-slate-600 dark:text-slate-400 mb-1">
                  <span className="flex items-center gap-1">
                    <Battery className={`w-3.5 h-3.5 ${isLowBattery ? 'text-rose-500' : 'text-slate-500'}`} />
                    Battery
                  </span>
                  <span className="font-mono font-semibold">{robot.battery.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full ${isLowBattery ? 'bg-rose-500' : 'bg-emerald-500'}`}
                    style={{ width: `${robot.battery}%` }}
                  />
                </div>
              </div>

              {/* Task & Network */}
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-slate-600 dark:text-slate-400">
                <span className="flex items-center gap-1">
                  <Navigation className="w-3.5 h-3.5 text-slate-400" />
                  Task:
                </span>
                <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                  {robot.current_task || 'None'}
                </span>
              </div>

              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400">
                <span className="flex items-center gap-1">
                  <Wifi className="w-3.5 h-3.5 text-slate-400" />
                  Network:
                </span>
                <span className={`font-mono text-[11px] ${
                  robot.network_status === 'CONNECTED' ? 'text-emerald-600 dark:text-emerald-400' :
                  robot.network_status === 'DEGRADED' ? 'text-amber-600 dark:text-amber-400' :
                  'text-rose-600 dark:text-rose-400 font-bold'
                }`}>
                  {robot.network_status}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
