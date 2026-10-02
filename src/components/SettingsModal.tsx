import React, { useState } from 'react';
import { X, Settings, Check, RotateCcw } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  timeScale: number;
  onSave: (settings: {
    timeStep: number;
    timeScale: number;
    seed: number;
    telemetryInterval: number;
    defaultRobots: number;
    logLevel: string;
  }) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  timeScale,
  onSave,
}) => {
  const [currentTimeStep, setCurrentTimeStep] = useState<number>(0.1);
  const [currentTimeScale, setCurrentTimeScale] = useState<number>(timeScale || 1.0);
  const [seed, setSeed] = useState<number>(42);
  const [telemetryInterval, setTelemetryInterval] = useState<number>(0.1);
  const [defaultRobots, setDefaultRobots] = useState<number>(3);
  const [logLevel, setLogLevel] = useState<string>('INFO');
  const [isSaved, setIsSaved] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave({
      timeStep: currentTimeStep,
      timeScale: currentTimeScale,
      seed,
      telemetryInterval,
      defaultRobots,
      logLevel,
    });
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
      onClose();
    }, 800);
  };

  const handleResetDefaults = () => {
    setCurrentTimeStep(0.1);
    setCurrentTimeScale(1.0);
    setSeed(42);
    setTelemetryInterval(0.1);
    setDefaultRobots(3);
    setLogLevel('INFO');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs select-none">
      <div className="bg-[#151A21] border border-[#29323D] rounded-xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-[#29323D] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#1683E8]/15 border border-[#1683E8]/30 flex items-center justify-center text-[#1683E8]">
              <Settings className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#E5E7EB]">Simulation Engine Settings</h3>
              <p className="text-[11px] text-[#9CA3AF]">Runtime parameters & telemetry configuration</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#9CA3AF] hover:text-[#E5E7EB] flex items-center justify-center cursor-pointer transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Settings Body */}
        <div className="p-5 space-y-3.5 text-xs">
          {/* Timestep */}
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-[#E5E7EB] block">Simulation Timestep (Δt)</span>
              <span className="text-[10px] text-[#6B7280]">Kinematic integration step in seconds</span>
            </div>
            <select
              value={currentTimeStep}
              onChange={(e) => setCurrentTimeStep(Number(e.target.value))}
              className="bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] rounded px-2.5 py-1 font-mono focus:border-[#1683E8] cursor-pointer"
            >
              <option value="0.05">0.05 s (High Precision)</option>
              <option value="0.1">0.1 s (Default Standard)</option>
              <option value="0.2">0.2 s (Fast Forward)</option>
            </select>
          </div>

          {/* Time Scale */}
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-[#E5E7EB] block">Time Scale Multiplier</span>
              <span className="text-[10px] text-[#6B7280]">Simulation clock speed factor</span>
            </div>
            <select
              value={currentTimeScale}
              onChange={(e) => setCurrentTimeScale(Number(e.target.value))}
              className="bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] rounded px-2.5 py-1 font-mono focus:border-[#1683E8] cursor-pointer"
            >
              <option value="0.5">0.5x</option>
              <option value="1.0">1.0x (Real-time)</option>
              <option value="2.0">2.0x</option>
              <option value="5.0">5.0x</option>
              <option value="10.0">10.0x</option>
            </select>
          </div>

          {/* Seed */}
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-[#E5E7EB] block">Deterministic Seed</span>
              <span className="text-[10px] text-[#6B7280]">Reproducible random generator seed</span>
            </div>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="w-20 bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] rounded px-2.5 py-1 font-mono text-right focus:border-[#1683E8]"
            />
          </div>

          {/* Telemetry Interval */}
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-[#E5E7EB] block">Telemetry Broadcast Rate</span>
              <span className="text-[10px] text-[#6B7280]">WebSocket streaming frequency</span>
            </div>
            <select
              value={telemetryInterval}
              onChange={(e) => setTelemetryInterval(Number(e.target.value))}
              className="bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] rounded px-2.5 py-1 font-mono focus:border-[#1683E8] cursor-pointer"
            >
              <option value="0.05">20 Hz (0.05s)</option>
              <option value="0.1">10 Hz (0.1s)</option>
              <option value="0.25">4 Hz (0.25s)</option>
            </select>
          </div>

          {/* Default Robot Fleet Size */}
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-[#E5E7EB] block">Default Robot Fleet Count</span>
              <span className="text-[10px] text-[#6B7280]">Active robots spawned on reset</span>
            </div>
            <select
              value={defaultRobots}
              onChange={(e) => setDefaultRobots(Number(e.target.value))}
              className="bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] rounded px-2.5 py-1 font-mono focus:border-[#1683E8] cursor-pointer"
            >
              <option value="2">2 Robots</option>
              <option value="3">3 Robots (Standard)</option>
              <option value="4">4 Robots</option>
              <option value="5">5 Robots</option>
            </select>
          </div>

          {/* Environment */}
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-[#E5E7EB] block">Simulation Environment</span>
              <span className="text-[10px] text-[#6B7280]">Active warehouse floorplan</span>
            </div>
            <span className="bg-[#0F1115] border border-[#29323D] text-[#9CA3AF] rounded px-2.5 py-1 font-mono text-[11px]">
              Warehouse A (24×16)
            </span>
          </div>

          {/* Log Level */}
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-[#E5E7EB] block">Engine Logging Level</span>
              <span className="text-[10px] text-[#6B7280]">Verbosity of Python simulation logs</span>
            </div>
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
              className="bg-[#0F1115] border border-[#29323D] text-[#E5E7EB] rounded px-2.5 py-1 font-mono focus:border-[#1683E8] cursor-pointer"
            >
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
            </select>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3 border-t border-[#29323D] flex items-center justify-between bg-[#0F1115]/50">
          <button
            onClick={handleResetDefaults}
            className="flex items-center gap-1.5 text-xs text-[#9CA3AF] hover:text-[#E5E7EB] cursor-pointer transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[#1683E8] hover:bg-[#2B95F5] text-white flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
            >
              {isSaved ? <Check className="w-3.5 h-3.5" /> : null}
              <span>{isSaved ? 'Saved!' : 'Apply Settings'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
