import React, { useRef, useEffect, useState } from 'react';
import {
  Grid,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Layers,
  AlertTriangle,
  Check,
} from 'lucide-react';
import { SimulationWorld, RobotTelemetry, TaskTelemetry } from '../types';

interface SimulationMapProps {
  world: SimulationWorld;
  robots: RobotTelemetry[];
  tasks: TaskTelemetry[];
  selectedRobotId: string | null;
  onSelectRobot: (robotId: string | null) => void;
  onSelectTask?: (taskId: string) => void;
}

export const SimulationMap: React.FC<SimulationMapProps> = ({
  world,
  robots,
  tasks,
  selectedRobotId,
  onSelectRobot,
  onSelectTask,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);
  const [showLayersMenu, setShowLayersMenu] = useState<boolean>(false);

  // Layer visibility toggles
  const [layers, setLayers] = useState({
    robots: true,
    tasks: true,
    plannedPaths: true,
    executedPaths: true,
    reservations: true,
    conflicts: true,
    obstacles: true,
    blockedAreas: true,
  });

  const toggleLayer = (layerKey: keyof typeof layers) => {
    setLayers((prev) => ({ ...prev, [layerKey]: !prev[layerKey] }));
  };

  const handleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  const handleFit = () => {
    setZoomLevel(1.0);
  };

  // Colors based on reference design
  const ROBOT_COLORS: Record<string, string> = {
    R1: '#06B6D4', // Cyan
    R2: '#22C55E', // Green
    R3: '#F59E0B', // Amber
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;

      // Clear full canvas
      ctx.fillStyle = '#F8FAFC';
      ctx.fillRect(0, 0, width, height);

      ctx.save();
      // Apply zoom around center of canvas
      if (zoomLevel !== 1.0) {
        ctx.translate(width / 2, height / 2);
        ctx.scale(zoomLevel, zoomLevel);
        ctx.translate(-width / 2, -height / 2);
      }

      // Warehouse grid dimension: 24 columns x 16 rows
      const gridW = world.width || 24;
      const gridH = world.height || 16;
      const margin = 28;
      const cellW = (width - margin * 2) / gridW;
      const cellH = (height - margin * 2) / gridH;

      // Draw subtle warehouse floor tiles / grid
      ctx.lineWidth = 1;
      ctx.strokeStyle = '#E2E8F0';
      for (let x = 0; x <= gridW; x++) {
        const posX = margin + x * cellW;
        ctx.beginPath();
        ctx.moveTo(posX, margin);
        ctx.lineTo(posX, height - margin);
        ctx.stroke();
      }
      for (let y = 0; y <= gridH; y++) {
        const posY = margin + y * cellH;
        ctx.beginPath();
        ctx.moveTo(margin, posY);
        ctx.lineTo(width - margin, posY);
        ctx.stroke();
      }

      // Draw floor guide lanes
      ctx.strokeStyle = '#CBD5E1';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 6]);
      [margin + 4 * cellH, margin + 8 * cellH, margin + 12 * cellH].forEach((laneY) => {
        ctx.beginPath();
        ctx.moveTo(margin, laneY);
        ctx.lineTo(width - margin, laneY);
        ctx.stroke();
      });
      ctx.setLineDash([]);

      // 1. Charging Bays
      if (layers.obstacles && world.charging_bays) {
        Object.entries(world.charging_bays).forEach(([name, [cx, cy]]) => {
          const x = margin + cx * cellW;
          const y = margin + cy * cellH;
          ctx.fillStyle = '#ECFDF5';
          ctx.strokeStyle = '#22C55E50';
          ctx.lineWidth = 1;
          ctx.fillRect(x + 2, y + 2, cellW - 4, cellH - 4);
          ctx.strokeRect(x + 2, y + 2, cellW - 4, cellH - 4);
          ctx.fillStyle = '#22C55E80';
          ctx.font = '8px JetBrains Mono';
          ctx.fillText(`⚡${name}`, x + 4, y + cellH - 5);
        });
      }

      // 2. Shelf Pods (Racks)
      if (layers.obstacles && world.shelves) {
        world.shelves.forEach(([sx, sy]) => {
          const x = margin + sx * cellW;
          const y = margin + sy * cellH;

          // Shelf drop shadow
          ctx.fillStyle = '#94A3B820';
          ctx.fillRect(x + 4, y + 4, cellW - 4, cellH - 4);

          // Shelf base
          ctx.fillStyle = '#E2E8F0';
          ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);

          // Shelf inner metallic container
          ctx.fillStyle = '#F1F5F9';
          ctx.fillRect(x + 3, y + 3, cellW - 6, cellH - 6);

          // Rack framing border
          ctx.strokeStyle = '#CBD5E1';
          ctx.lineWidth = 1;
          ctx.strokeRect(x + 1, y + 1, cellW - 2, cellH - 2);

          // Cross strut details
          ctx.strokeStyle = '#CBD5E1';
          ctx.beginPath();
          ctx.moveTo(x + 4, y + 4);
          ctx.lineTo(x + cellW - 4, y + cellH - 4);
          ctx.moveTo(x + cellW - 4, y + 4);
          ctx.lineTo(x + 4, y + cellH - 4);
          ctx.stroke();

          // Shelf hazard yellow strip
          ctx.fillStyle = '#F59E0B30';
          ctx.fillRect(x + 2, y + 2, 3, cellH - 4);
        });
      }

      // 3. Reservations (Spatial cells reserved ahead)
      if (layers.reservations) {
        robots.forEach((robot) => {
          if (robot.current_path && robot.current_path.length > 1) {
            // Reserve upcoming cells
            robot.current_path.slice(0, 3).forEach(([rx, ry]) => {
              const x = margin + rx * cellW;
              const y = margin + ry * cellH;
              ctx.strokeStyle = '#F59E0B';
              ctx.lineWidth = 1.2;
              ctx.setLineDash([3, 3]);
              ctx.strokeRect(x + 3, y + 3, cellW - 6, cellH - 6);
              ctx.setLineDash([]);
            });
          }
        });
      }

      // 4. Blocked Aisle / Dynamic Obstacle
      if (layers.blockedAreas) {
        const hasBlockedAisle =
          (world.blocked_aisles && world.blocked_aisles.length > 0) ||
          (world.dynamic_obstacles && world.dynamic_obstacles.length > 0);
        if (hasBlockedAisle) {
          const centerCell = world.blocked_aisles?.[0] || world.dynamic_obstacles?.[0] || [14, 8];
          const cx = margin + centerCell[0] * cellW + cellW / 2;
          const cy = margin + centerCell[1] * cellH + cellH / 2;
          const radius = cellW * 1.8;

          // Radar circle overlay
          ctx.fillStyle = 'rgba(239, 68, 68, 0.12)';
          ctx.beginPath();
          ctx.arc(cx, cy, radius, 0, Math.PI * 2);
          ctx.fill();

          // Dashed red perimeter
          ctx.strokeStyle = '#EF4444';
          ctx.lineWidth = 1.5;
          ctx.setLineDash([5, 4]);
          ctx.beginPath();
          ctx.arc(cx, cy, radius, 0, Math.PI * 2);
          ctx.stroke();
          ctx.setLineDash([]);

          // Crosshairs
          ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
          ctx.beginPath();
          ctx.moveTo(cx - radius, cy);
          ctx.lineTo(cx + radius, cy);
          ctx.moveTo(cx, cy - radius);
          ctx.lineTo(cx, cy + radius);
          ctx.stroke();

          // "Blocked Aisle" Badge
          const badgeW = 92;
          const badgeH = 22;
          ctx.fillStyle = '#FFFFFF';
          ctx.strokeStyle = '#EF4444';
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.roundRect(cx + 8, cy - 11, badgeW, badgeH, 4);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = '#EF4444';
          ctx.font = 'bold 9px Inter';
          ctx.fillText('⚠ Blocked Aisle', cx + 16, cy + 3);
        }
      }

      // 5. Stations & Task Markers
      if (layers.tasks) {
        tasks.forEach((t) => {
          const isDelivery = t.phase === 'DELIVERY' || t.status === 'COMPLETED';
          const targetPos = isDelivery ? t.delivery : t.pickup;
          const [tx, ty] = targetPos;
          const x = margin + tx * cellW;
          const y = margin + ty * cellH;

          const isCompleted = t.status === 'COMPLETED';
          const color = isCompleted ? '#22C55E' : isDelivery ? '#EF4444' : '#06B6D4';

          // Outer dashed square
          ctx.strokeStyle = color;
          ctx.lineWidth = 1.2;
          ctx.setLineDash([3, 3]);
          ctx.strokeRect(x + 2, y + 2, cellW - 4, cellH - 4);
          ctx.setLineDash([]);

          // Solid inner task marker
          ctx.fillStyle = color;
          ctx.fillRect(x + cellW / 2 - 4, y + cellH / 2 - 4, 8, 8);

          // Task Label Card
          if (
            t.status === 'IN_PROGRESS' ||
            t.status === 'ASSIGNED' ||
            t.task_id === 'T01' ||
            t.task_id === 'T02' ||
            t.task_id === 'T03'
          ) {
            const labelW = 76;
            const labelH = 28;
            const labelX = x + cellW + 2;
            const labelY = y - 4;

            ctx.fillStyle = '#FFFFFF';
            ctx.strokeStyle = '#E2E8F0';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.roundRect(labelX, labelY, labelW, labelH, 4);
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = '#0F172A';
            ctx.font = 'bold 10px JetBrains Mono';
            ctx.fillText(`T-${t.task_id.replace('T', '')}`, labelX + 6, labelY + 12);

            ctx.fillStyle = '#64748B';
            ctx.font = '8px Inter';
            ctx.fillText(`${isDelivery ? 'Delivery' : 'Pickup'} ${t.task_id.slice(-1)}`, labelX + 6, labelY + 22);
          }
        });
      }

      // 6. Planned and Executed Paths
      robots.forEach((robot) => {
        const robotColor = ROBOT_COLORS[robot.robot_id] || '#06B6D4';

        // Planned Path (dashed line ahead of robot)
        if (layers.plannedPaths && robot.current_path && robot.current_path.length > 0) {
          ctx.strokeStyle = robotColor;
          ctx.lineWidth = 1.8;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();

          const startX = margin + robot.position[0] * cellW + cellW / 2;
          const startY = margin + robot.position[1] * cellH + cellH / 2;
          ctx.moveTo(startX, startY);

          robot.current_path.forEach(([px, py]) => {
            ctx.lineTo(margin + px * cellW + cellW / 2, margin + py * cellH + cellH / 2);
          });
          ctx.stroke();
          ctx.setLineDash([]);
        }

        // Executed Path (solid trajectory line from spawn position to current position)
        if (layers.executedPaths) {
          const spawnX = robot.robot_id === 'R1' ? 4 : robot.robot_id === 'R2' ? 8 : 12;
          const spawnY = 0;
          ctx.strokeStyle = `${robotColor}80`;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(margin + spawnX * cellW + cellW / 2, margin + spawnY * cellH + cellH / 2);
          ctx.lineTo(margin + robot.position[0] * cellW + cellW / 2, margin + robot.position[1] * cellH + cellH / 2);
          ctx.stroke();
        }
      });

      // 7. Robots Layer
      if (layers.robots) {
        robots.forEach((robot) => {
          const [rx, ry] = robot.position;
          const cx = margin + rx * cellW + cellW / 2;
          const cy = margin + ry * cellH + cellH / 2;
          const radius = cellW * 0.42;

          const isSelected = selectedRobotId === robot.robot_id;
          const baseColor = ROBOT_COLORS[robot.robot_id] || '#06B6D4';

          // Pulse radar ring for active robots
          ctx.strokeStyle = `${baseColor}40`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(cx, cy, radius * 1.6, 0, Math.PI * 2);
          ctx.stroke();

          // Selected halo
          if (isSelected) {
            ctx.strokeStyle = '#FFFFFF';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(cx, cy, radius * 1.9, 0, Math.PI * 2);
            ctx.stroke();
          }

          // Robot base body
          ctx.fillStyle = '#FFFFFF';
          ctx.beginPath();
          ctx.arc(cx, cy, radius, 0, Math.PI * 2);
          ctx.fill();

          ctx.strokeStyle = baseColor;
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.arc(cx, cy, radius, 0, Math.PI * 2);
          ctx.stroke();

          // Inner center core
          ctx.fillStyle = baseColor;
          ctx.beginPath();
          ctx.arc(cx, cy, radius * 0.4, 0, Math.PI * 2);
          ctx.fill();

          // Heading direction pointer
          const headingAngle = robot.orientation || 0;
          const pointerLen = radius * 1.3;
          ctx.strokeStyle = baseColor;
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(cx + Math.cos(headingAngle) * pointerLen, cy + Math.sin(headingAngle) * pointerLen);
          ctx.stroke();

          // Robot ID Badge above robot
          const idBadgeW = 28;
          const idBadgeH = 15;
          ctx.fillStyle = '#FFFFFF';
          ctx.strokeStyle = '#E2E8F0';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.roundRect(cx - idBadgeW / 2, cy - radius - 18, idBadgeW, idBadgeH, 3);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = '#0F172A';
          ctx.font = 'bold 9px JetBrains Mono';
          ctx.textAlign = 'center';
          ctx.fillText(robot.robot_id, cx, cy - radius - 7);
          ctx.textAlign = 'left';
        });
      }

      ctx.restore();
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [world, robots, tasks, selectedRobotId, zoomLevel, layers]);

  return (
    <div
      ref={containerRef}
      className="bg-[#151A21] border border-[#29323D] rounded-xl flex flex-col overflow-hidden shadow-sm h-full"
    >
      {/* Simulation Header Bar */}
      <div className="px-4 py-2.5 border-b border-[#29323D] flex items-center justify-between select-none">
        <div className="flex items-center gap-2">
          <Grid className="w-4 h-4 text-[#1683E8]" />
          <span className="text-sm font-semibold text-[#E5E7EB]">
            Live Simulation — Warehouse A
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* 2D View Indicator (3D removed per instruction) */}
          <div className="bg-[#0F1115] border border-[#29323D] px-2.5 py-1 rounded-md text-xs font-semibold text-[#1683E8]">
            2D View
          </div>

          {/* Environment Label (Warehouse A only) */}
          <div className="bg-[#0F1115] border border-[#29323D] px-2.5 py-1 rounded-md text-xs text-[#9CA3AF] font-mono">
            Warehouse A
          </div>
        </div>
      </div>

      {/* Simulation Canvas Container */}
      <div className="relative flex-1 bg-[#0F1318] min-h-[360px] overflow-hidden">
        {/* Zoom Controls Overlay */}
        <div className="absolute top-3 left-3 flex flex-col gap-1 z-20">
          <button
            onClick={() => setZoomLevel((z) => Math.min(Number((z + 0.15).toFixed(2)), 2.5))}
            title="Zoom In"
            className="w-7 h-7 rounded bg-[#151A21]/90 hover:bg-[#1B222B] border border-[#29323D] text-[#9CA3AF] hover:text-[#E5E7EB] flex items-center justify-center transition-colors shadow-sm cursor-pointer"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoomLevel((z) => Math.max(Number((z - 0.15).toFixed(2)), 0.6))}
            title="Zoom Out"
            className="w-7 h-7 rounded bg-[#151A21]/90 hover:bg-[#1B222B] border border-[#29323D] text-[#9CA3AF] hover:text-[#E5E7EB] flex items-center justify-center transition-colors shadow-sm cursor-pointer"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            title="Fit to Viewport"
            className="w-7 h-7 rounded bg-[#151A21]/90 hover:bg-[#1B222B] border border-[#29323D] text-[#9CA3AF] hover:text-[#E5E7EB] flex items-center justify-center transition-colors shadow-sm cursor-pointer"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setShowLayersMenu(!showLayersMenu)}
            title="Toggle Layers"
            className={`w-7 h-7 rounded border border-[#29323D] flex items-center justify-center transition-colors shadow-sm cursor-pointer ${
              showLayersMenu ? 'bg-[#1683E8] text-white' : 'bg-[#151A21]/90 text-[#9CA3AF] hover:text-[#E5E7EB]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Interactive Layers Dropdown Menu */}
        {showLayersMenu && (
          <div className="absolute top-3 left-12 bg-[#151A21] border border-[#29323D] rounded-lg p-2.5 shadow-xl z-30 text-xs w-44 space-y-1.5 animate-in fade-in duration-150">
            <div className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider px-1 pb-1 border-b border-[#29323D]">
              Layer Visibility
            </div>
            {[
              { key: 'robots', label: 'Robots' },
              { key: 'tasks', label: 'Tasks' },
              { key: 'plannedPaths', label: 'Planned Paths' },
              { key: 'executedPaths', label: 'Executed Paths' },
              { key: 'reservations', label: 'Reservations' },
              { key: 'conflicts', label: 'Conflicts' },
              { key: 'obstacles', label: 'Obstacles' },
              { key: 'blockedAreas', label: 'Blocked Areas' },
            ].map(({ key, label }) => {
              const isActive = layers[key as keyof typeof layers];
              return (
                <button
                  key={key}
                  onClick={() => toggleLayer(key as keyof typeof layers)}
                  className="w-full flex items-center justify-between px-1.5 py-1 rounded hover:bg-[#1B222B] text-left cursor-pointer transition-colors"
                >
                  <span className={isActive ? 'text-[#E5E7EB] font-medium' : 'text-[#6B7280]'}>{label}</span>
                  <div
                    className={`w-4 h-4 rounded border flex items-center justify-center ${
                      isActive ? 'bg-[#1683E8] border-[#1683E8] text-white' : 'border-[#29323D]'
                    }`}
                  >
                    {isActive && <Check className="w-3 h-3" />}
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* 2D Canvas */}
        <canvas
          ref={canvasRef}
          width={840}
          height={480}
          className="w-full h-full object-cover block cursor-crosshair"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;
            const gridW = world.width || 24;
            const gridH = world.height || 16;
            const margin = 28;
            const cellW = (rect.width - margin * 2) / gridW;
            const cellH = (rect.height - margin * 2) / gridH;

            // Check if clicked near a robot
            const clickedRobot = robots.find((r) => {
              const rx = margin + r.position[0] * cellW + cellW / 2;
              const ry = margin + r.position[1] * cellH + cellH / 2;
              const dist = Math.hypot(clickX - rx, clickY - ry);
              return dist < cellW * 0.9;
            });

            if (clickedRobot) {
              onSelectRobot(clickedRobot.robot_id);
            } else {
              onSelectRobot(null);
            }
          }}
        />

        {/* Map Legend Overlay in Bottom Right */}
        <div className="absolute bottom-3 right-3 bg-[#151A21]/95 border border-[#29323D] rounded-lg p-2.5 text-[10px] space-y-1.5 shadow-md pointer-events-none select-none">
          <div className="flex items-center gap-2">
            <span className="w-4 h-0.5 border-t border-dashed border-[#06B6D4]" />
            <span className="text-[#9CA3AF]">Planned Path</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-0.5 bg-[#06B6D4]" />
            <span className="text-[#9CA3AF]">Executed Path</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-2 border border-dashed border-[#F59E0B] rounded-xs" />
            <span className="text-[#9CA3AF]">Reserved Area</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-2 border border-dashed border-[#EF4444] rounded-xs bg-[#EF4444]/20" />
            <span className="text-[#9CA3AF]">Blocked Area</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#06B6D4] border border-white/50" />
            <span className="text-[#9CA3AF]">Robot</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-xs bg-[#F59E0B]" />
            <span className="text-[#9CA3AF]">Task</span>
          </div>
        </div>
      </div>
    </div>
  );
};
