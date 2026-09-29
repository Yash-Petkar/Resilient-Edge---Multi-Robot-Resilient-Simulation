import React, { useState } from 'react';
import { RobotTelemetry, SimulationWorld, TaskTelemetry } from '../../types';
import { Bot, Battery, Zap, AlertCircle, Compass, CheckCircle2, Crosshair } from 'lucide-react';

interface SimulationCanvasProps {
  world: SimulationWorld;
  robots: RobotTelemetry[];
  tasks: TaskTelemetry[];
  selectedRobotId: string | null;
  onSelectRobot: (robotId: string | null) => void;
  onQuickDispatch?: (pickup: [number, number], delivery: [number, number]) => void;
}

export const SimulationCanvas: React.FC<SimulationCanvasProps> = ({
  world,
  robots,
  tasks,
  selectedRobotId,
  onSelectRobot,
}) => {
  const [hoveredCell, setHoveredCell] = useState<[number, number] | null>(null);

  const cellWidth = 36;
  const cellHeight = 36;
  const svgWidth = world.width * cellWidth;
  const svgHeight = world.height * cellHeight;

  // Set lookups
  const shelfSet = new Set(world.shelves.map(([x, y]) => `${x},${y}`));
  const blockedSet = new Set(world.blocked_aisles.map(([x, y]) => `${x},${y}`));
  const dynObstacleSet = new Set(world.dynamic_obstacles.map(([x, y]) => `${x},${y}`));

  const selectedRobot = robots.find((r) => r.robot_id === selectedRobotId);

  return (
    <div className="relative flex flex-col lg:flex-row gap-4 items-start w-full">
      {/* Canvas Container */}
      <div className="flex-1 w-full overflow-x-auto bg-slate-950 rounded-xl p-3 border border-slate-800 shadow-inner">
        <div className="flex items-center justify-between mb-2 text-xs text-slate-400 font-mono">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-slate-800 border border-slate-700" /> Storage Rack
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-sky-950 border border-sky-500 text-[9px] text-sky-400 font-bold flex items-center justify-center">P</span> Pickup
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-emerald-950 border border-emerald-500 text-[9px] text-emerald-400 font-bold flex items-center justify-center">D</span> Delivery
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-amber-950 border border-amber-500 text-[9px] text-amber-400 font-bold flex items-center justify-center">C</span> Charging
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-rose-950/80 border border-rose-600" /> Blocked
            </span>
          </div>
          <div>Grid: {world.width} × {world.height} (0.1s tick)</div>
        </div>

        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full max-w-none select-none rounded bg-slate-900 border border-slate-800"
          style={{ minWidth: '760px', aspectRatio: `${world.width} / ${world.height}` }}
        >
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width={cellWidth} height={cellHeight} patternUnits="userSpaceOnUse">
              <path d={`M ${cellWidth} 0 L 0 0 0 ${cellHeight}`} fill="none" stroke="#1e293b" strokeWidth="0.8" />
            </pattern>
            {/* Blocked hatch pattern */}
            <pattern id="blockedHatch" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="6" stroke="#f43f5e" strokeWidth="1.5" />
            </pattern>
          </defs>

          {/* Grid background */}
          <rect width={svgWidth} height={svgHeight} fill="url(#grid)" />

          {/* Shelves */}
          {world.shelves.map(([x, y]) => (
            <g key={`shelf-${x}-${y}`}>
              <rect
                x={x * cellWidth + 2}
                y={y * cellHeight + 2}
                width={cellWidth - 4}
                height={cellHeight - 4}
                rx="3"
                className="fill-slate-800 stroke-slate-700"
                strokeWidth="1.2"
              />
              <line
                x1={x * cellWidth + 6}
                y1={y * cellHeight + cellHeight / 2}
                x2={(x + 1) * cellWidth - 6}
                y2={y * cellHeight + cellHeight / 2}
                stroke="#475569"
                strokeWidth="1"
              />
            </g>
          ))}

          {/* Blocked Aisles */}
          {world.blocked_aisles.map(([x, y]) => (
            <rect
              key={`blocked-${x}-${y}`}
              x={x * cellWidth + 1}
              y={y * cellHeight + 1}
              width={cellWidth - 2}
              height={cellHeight - 2}
              fill="url(#blockedHatch)"
              stroke="#ef4444"
              strokeWidth="1"
            />
          ))}

          {/* Dynamic Obstacles */}
          {world.dynamic_obstacles.map(([x, y]) => (
            <g key={`dyn-${x}-${y}`}>
              <rect
                x={x * cellWidth + 2}
                y={y * cellHeight + 2}
                width={cellWidth - 4}
                height={cellHeight - 4}
                rx="4"
                className="fill-amber-600/30 stroke-amber-500 animate-pulse"
                strokeWidth="1.5"
              />
              <text
                x={x * cellWidth + cellWidth / 2}
                y={y * cellHeight + cellHeight / 2 + 4}
                textAnchor="middle"
                className="fill-amber-400 font-mono text-[10px] font-bold"
              >
                !
              </text>
            </g>
          ))}

          {/* Pickup Stations */}
          {Object.entries(world.pickup_stations).map(([name, [x, y]]) => (
            <g key={`p-${name}`}>
              <rect
                x={x * cellWidth + 2}
                y={y * cellHeight + 2}
                width={cellWidth - 4}
                height={cellHeight - 4}
                rx="4"
                className="fill-sky-950/80 stroke-sky-500"
                strokeWidth="1.5"
              />
              <text
                x={x * cellWidth + cellWidth / 2}
                y={y * cellHeight + cellHeight / 2 + 4}
                textAnchor="middle"
                className="fill-sky-400 font-mono text-[10px] font-bold"
              >
                {name}
              </text>
            </g>
          ))}

          {/* Delivery Stations */}
          {Object.entries(world.delivery_stations).map(([name, [x, y]]) => (
            <g key={`d-${name}`}>
              <rect
                x={x * cellWidth + 2}
                y={y * cellHeight + 2}
                width={cellWidth - 4}
                height={cellHeight - 4}
                rx="4"
                className="fill-emerald-950/80 stroke-emerald-500"
                strokeWidth="1.5"
              />
              <text
                x={x * cellWidth + cellWidth / 2}
                y={y * cellHeight + cellHeight / 2 + 4}
                textAnchor="middle"
                className="fill-emerald-400 font-mono text-[10px] font-bold"
              >
                {name}
              </text>
            </g>
          ))}

          {/* Charging Bays */}
          {Object.entries(world.charging_bays).map(([name, [x, y]]) => (
            <g key={`c-${name}`}>
              <rect
                x={x * cellWidth + 2}
                y={y * cellHeight + 2}
                width={cellWidth - 4}
                height={cellHeight - 4}
                rx="4"
                className="fill-amber-950/60 stroke-amber-500"
                strokeWidth="1.2"
              />
              <text
                x={x * cellWidth + cellWidth / 2}
                y={y * cellHeight + cellHeight / 2 + 4}
                textAnchor="middle"
                className="fill-amber-400 font-mono text-[10px] font-bold"
              >
                {name}
              </text>
            </g>
          ))}

          {/* Robot Trajectory Paths */}
          {robots.map((robot) => {
            if (!robot.current_path || robot.current_path.length < 2) return null;
            const pointsStr = robot.current_path
              .slice(robot.path_progress)
              .map(([px, py]) => `${px * cellWidth + cellWidth / 2},${py * cellHeight + cellHeight / 2}`)
              .join(' ');

            const isSelected = robot.robot_id === selectedRobotId;
            const strokeColor =
              robot.state === 'FAILED' ? '#ef4444' :
              robot.state === 'LOCAL_AUTONOMY' ? '#f59e0b' :
              isSelected ? '#38bdf8' : '#3b82f6';

            return (
              <g key={`path-${robot.robot_id}`}>
                <polyline
                  points={pointsStr}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={isSelected ? '2.5' : '1.5'}
                  strokeDasharray={isSelected ? '4 2' : '3 3'}
                  strokeOpacity={isSelected ? 0.9 : 0.6}
                />
                {/* Waypoint dots */}
                {robot.current_path.slice(robot.path_progress).map(([wx, wy], idx) => (
                  <circle
                    key={`wp-${robot.robot_id}-${idx}`}
                    cx={wx * cellWidth + cellWidth / 2}
                    cy={wy * cellHeight + cellHeight / 2}
                    r={isSelected ? 2.5 : 1.5}
                    fill={strokeColor}
                    fillOpacity={0.8}
                  />
                ))}
              </g>
            );
          })}

          {/* Robots */}
          {robots.map((robot) => {
            const cx = robot.position[0] * cellWidth + cellWidth / 2;
            const cy = robot.position[1] * cellHeight + cellHeight / 2;
            const isSelected = robot.robot_id === selectedRobotId;

            // State based styling
            let bodyColor = '#2563eb'; // blue
            let strokeColor = '#60a5fa';

            if (robot.state === 'FAILED') {
              bodyColor = '#dc2626'; // red
              strokeColor = '#f87171';
            } else if (robot.state === 'LOCAL_AUTONOMY') {
              bodyColor = '#d97706'; // amber
              strokeColor = '#fbbf24';
            } else if (robot.state === 'TASK_EXECUTION') {
              bodyColor = '#059669'; // emerald
              strokeColor = '#34d399';
            } else if (robot.state === 'WAITING') {
              bodyColor = '#7c3aed'; // purple
              strokeColor = '#a78bfa';
            }

            return (
              <g
                key={`robot-${robot.robot_id}`}
                onClick={() => onSelectRobot(isSelected ? null : robot.robot_id)}
                className="cursor-pointer transition-transform duration-200"
              >
                {/* Selection halo */}
                {isSelected && (
                  <circle cx={cx} cy={cy} r={cellWidth / 2 + 5} fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="3 3" className="animate-spin origin-center" />
                )}

                {/* Robot body */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={cellWidth / 2 - 4}
                  fill={bodyColor}
                  stroke={strokeColor}
                  strokeWidth={isSelected ? '2.5' : '1.5'}
                  className="filter drop-shadow-md"
                />

                {/* Heading Arrow indicator */}
                <line
                  x1={cx}
                  y1={cy}
                  x2={cx + Math.cos(robot.orientation) * 12}
                  y2={cy + Math.sin(robot.orientation) * 12}
                  stroke="#ffffff"
                  strokeWidth="2"
                  strokeLinecap="round"
                />

                {/* Robot ID label */}
                <text
                  x={cx}
                  y={cy + 3}
                  textAnchor="middle"
                  className="fill-white font-mono font-bold text-[9px] pointer-events-none"
                >
                  {robot.robot_id}
                </text>

                {/* Mini battery bar below */}
                <rect
                  x={cx - 10}
                  y={cy + cellHeight / 2 - 2}
                  width="20"
                  height="3"
                  rx="1"
                  fill="#1e293b"
                />
                <rect
                  x={cx - 10}
                  y={cy + cellHeight / 2 - 2}
                  width={Math.max(2, (robot.battery / 100) * 20)}
                  height="3"
                  rx="1"
                  fill={robot.battery > 30 ? '#10b981' : '#ef4444'}
                />
              </g>
            );
          })}
        </svg>
      </div>

      {/* Robot Details Inspector Drawer */}
      {selectedRobot && (
        <div className="w-full lg:w-72 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm text-xs">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2 mb-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-blue-600 text-white flex items-center justify-center font-mono font-bold text-xs">
                {selectedRobot.robot_id}
              </div>
              <div>
                <span className="font-bold text-slate-900 dark:text-slate-100">Telemetry Details</span>
                <div className="text-[10px] text-slate-500 font-mono">
                  Pos: ({selectedRobot.position[0]}, {selectedRobot.position[1]})
                </div>
              </div>
            </div>
            <button
              onClick={() => onSelectRobot(null)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2.5">
            <div className="flex justify-between items-center">
              <span className="text-slate-500">State:</span>
              <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${
                selectedRobot.state === 'FAILED' ? 'bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300' :
                selectedRobot.state === 'LOCAL_AUTONOMY' ? 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300' :
                selectedRobot.state === 'MOVING' ? 'bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300' :
                selectedRobot.state === 'TASK_EXECUTION' ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300' :
                'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
              }`}>
                {selectedRobot.state}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-500">Battery:</span>
              <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                {selectedRobot.battery.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full ${selectedRobot.battery > 25 ? 'bg-emerald-500' : 'bg-rose-500'}`}
                style={{ width: `${selectedRobot.battery}%` }}
              />
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-500">Hardware Health:</span>
              <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                {(selectedRobot.health * 100).toFixed(0)}%
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-500">Network Link:</span>
              <span className="font-mono text-[11px] text-slate-700 dark:text-slate-300">
                {selectedRobot.network_status}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-500">Assigned Task:</span>
              <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                {selectedRobot.current_task || 'None (Idle)'}
              </span>
            </div>

            {selectedRobot.current_path && selectedRobot.current_path.length > 0 && (
              <div>
                <span className="text-slate-500 block mb-1">Path Trajectory:</span>
                <div className="font-mono text-[10px] bg-slate-50 dark:bg-slate-800 p-1.5 rounded text-slate-600 dark:text-slate-400 max-h-20 overflow-y-auto">
                  {selectedRobot.current_path.map((p, i) => (
                    <span key={i} className={i === selectedRobot.path_progress ? 'font-bold text-blue-500 underline' : ''}>
                      [{p[0]},{p[1]}]{i < selectedRobot.current_path.length - 1 ? ' → ' : ''}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
