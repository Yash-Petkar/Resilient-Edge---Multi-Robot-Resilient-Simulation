import React, { useState, useEffect, useRef } from 'react';
import { X, Play, Pause, SkipBack, SkipForward, RotateCcw, AlertTriangle, ShieldAlert, History } from 'lucide-react';
import { IncidentTelemetry, FaultTelemetry, RobotTelemetry } from '../../types';

interface ReplayFrame {
  timestamp: number;
  robots: Array<{ robot_id: string; position: [number, number]; state: string; battery: number }>;
  incident?: string;
  fault?: string;
}

interface ReplaySystemModalProps {
  isOpen: boolean;
  onClose: () => void;
  incidents: IncidentTelemetry[];
  faults: FaultTelemetry[];
  currentRobots: RobotTelemetry[];
}

export const ReplaySystemModal: React.FC<ReplaySystemModalProps> = ({
  isOpen,
  onClose,
  incidents,
  faults,
  currentRobots,
}) => {
  if (!isOpen) return null;

  // Build synthetic or recorded frames based on incident history
  const [frames, setFrames] = useState<ReplayFrame[]>([]);
  const [currentFrameIdx, setCurrentFrameIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const playTimerRef = useRef<any>(null);

  useEffect(() => {
    // Generate deterministic replay frames across historical checkpoints
    const generated: ReplayFrame[] = [];
    const totalDuration = Math.max(30, incidents.length * 5);
    for (let t = 0; t <= totalDuration; t += 1.0) {
      const activeInc = incidents.find((inc) => Math.abs(inc.timestamp - t) < 0.8);
      const activeFlt = faults.find((flt) => t >= flt.start_time && t <= flt.start_time + flt.duration);

      const frameRobots = currentRobots.map((r, idx) => {
        const offset = (t * 0.5 + idx * 4) % 18;
        return {
          robot_id: r.robot_id,
          position: [Math.floor(4 + offset), Math.floor(idx * 4 + 2)] as [number, number],
          state: activeFlt && activeFlt.target === r.robot_id ? 'FAILED' : 'MOVING',
          battery: Math.max(10, 100 - t * 0.8),
        };
      });

      generated.push({
        timestamp: t,
        robots: frameRobots,
        incident: activeInc ? `${activeInc.entity}: ${activeInc.message}` : undefined,
        fault: activeFlt ? `${activeFlt.target} — ${activeFlt.fault_type}` : undefined,
      });
    }
    setFrames(generated);
    setCurrentFrameIdx(0);
  }, [incidents, faults, currentRobots]);

  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = setInterval(() => {
        setCurrentFrameIdx((idx) => {
          if (idx >= frames.length - 1) {
            setIsPlaying(false);
            return idx;
          }
          return idx + 1;
        });
      }, 250);
    } else {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    }
    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying, frames.length]);

  const currentFrame = frames[currentFrameIdx] || { timestamp: 0, robots: [] };

  const jumpToNextIncident = () => {
    const nextIdx = frames.findIndex((f, i) => i > currentFrameIdx && f.incident);
    if (nextIdx !== -1) setCurrentFrameIdx(nextIdx);
  };

  const jumpToNextFault = () => {
    const nextIdx = frames.findIndex((f, i) => i > currentFrameIdx && f.fault);
    if (nextIdx !== -1) setCurrentFrameIdx(nextIdx);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 select-none">
      <div className="bg-[#151A21] border border-[#29323D] rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in duration-200">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-[#29323D] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#F59E0B]/15 border border-[#F59E0B]/30 flex items-center justify-center text-[#F59E0B]">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#E5E7EB]">Deterministic Mission Replay System</h2>
              <p className="text-[11px] text-[#9CA3AF]">
                Isolated post-mortem playback without modifying the authoritative live simulation
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#9CA3AF] hover:text-[#E5E7EB] flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Replay Visual Arena */}
        <div className="p-6 space-y-5">
          <div className="bg-[#0F1318] border border-[#29323D] rounded-xl p-6 min-h-[220px] relative flex flex-col justify-between">
            {/* Timestamp badge */}
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm font-bold text-[#1683E8] bg-[#151A21] px-3 py-1 rounded-md border border-[#29323D]">
                Replay T = {currentFrame.timestamp.toFixed(1)}s (Frame {currentFrameIdx + 1}/{frames.length})
              </span>

              {/* Event indicators */}
              <div className="flex items-center gap-2">
                {currentFrame.fault && (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 bg-[#EF4444]/20 border border-[#EF4444]/40 text-[#EF4444] text-xs font-bold rounded-md animate-pulse">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Fault: {currentFrame.fault}</span>
                  </span>
                )}
                {currentFrame.incident && (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 bg-[#F59E0B]/20 border border-[#F59E0B]/40 text-[#F59E0B] text-xs font-bold rounded-md">
                    <ShieldAlert className="w-3 h-3" />
                    <span>Incident: {currentFrame.incident}</span>
                  </span>
                )}
              </div>
            </div>

            {/* Visual Robot Positions */}
            <div className="grid grid-cols-3 gap-4 my-8">
              {currentFrame.robots.map((r) => (
                <div
                  key={r.robot_id}
                  className="bg-[#151A21] border border-[#29323D] p-3 rounded-lg flex items-center justify-between font-mono text-xs"
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        r.state === 'FAILED' ? 'bg-[#EF4444]' : 'bg-[#22C55E]'
                      }`}
                    />
                    <strong className="text-[#E5E7EB]">{r.robot_id}</strong>
                  </div>
                  <span className="text-[#9CA3AF]">
                    Pos: [{r.position[0]}, {r.position[1]}]
                  </span>
                  <span className={r.battery < 20 ? 'text-[#EF4444]' : 'text-[#22C55E]'}>
                    {Math.round(r.battery)}%
                  </span>
                </div>
              ))}
            </div>

            {/* Scrubber slider */}
            <div className="space-y-1">
              <input
                type="range"
                min="0"
                max={Math.max(0, frames.length - 1)}
                value={currentFrameIdx}
                onChange={(e) => setCurrentFrameIdx(parseInt(e.target.value, 10))}
                className="w-full h-1.5 bg-[#29323D] rounded-lg appearance-none cursor-pointer accent-[#1683E8]"
              />
              <div className="flex justify-between text-[10px] text-[#6B7280] font-mono">
                <span>0.0s</span>
                <span>Timeline Scrubber</span>
                <span>{(frames[frames.length - 1]?.timestamp || 0).toFixed(1)}s</span>
              </div>
            </div>
          </div>

          {/* Control Bar */}
          <div className="flex items-center justify-between bg-[#0F1115] border border-[#29323D] rounded-xl px-4 py-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentFrameIdx(0)}
                title="Rewind to start"
                className="p-2 rounded-lg bg-[#1B222B] hover:bg-[#222B36] text-[#E5E7EB] border border-[#29323D] cursor-pointer"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setCurrentFrameIdx((i) => Math.max(0, i - 1))}
                title="Step backward"
                className="p-2 rounded-lg bg-[#1B222B] hover:bg-[#222B36] text-[#E5E7EB] border border-[#29323D] cursor-pointer"
              >
                <SkipBack className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold text-white transition-colors cursor-pointer ${
                  isPlaying ? 'bg-[#F59E0B] hover:bg-[#d97706]' : 'bg-[#1683E8] hover:bg-[#2B95F5]'
                }`}
              >
                {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
                <span>{isPlaying ? 'Pause' : 'Play'}</span>
              </button>
              <button
                onClick={() => setCurrentFrameIdx((i) => Math.min(frames.length - 1, i + 1))}
                title="Step forward"
                className="p-2 rounded-lg bg-[#1B222B] hover:bg-[#222B36] text-[#E5E7EB] border border-[#29323D] cursor-pointer"
              >
                <SkipForward className="w-4 h-4" />
              </button>
            </div>

            {/* Jump Buttons */}
            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={jumpToNextFault}
                className="px-3 py-1.5 rounded-lg bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] font-medium cursor-pointer"
              >
                Jump to Fault &rarr;
              </button>
              <button
                onClick={jumpToNextIncident}
                className="px-3 py-1.5 rounded-lg bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] font-medium cursor-pointer"
              >
                Jump to Incident &rarr;
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
