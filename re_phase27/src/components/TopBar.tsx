import React from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  StepForward,
  Settings,
  WifiOff,
  LogOut,
  Database,
  CloudOff,
  Cloud,
} from 'lucide-react';
import { UserProfile } from '../types';
import { roleAllows } from '../permissions';

interface TopBarProps {
  isOnline: boolean;
  isWsConnected: boolean;
  simTime: number;
  isPaused: boolean;
  timeScale: number;
  currentUser: UserProfile;
  databaseStatus: { isConnected: boolean; statusLabel: string; database?: 'local' | 'error' | 'unknown' };
  onClockAction: (action: 'pause' | 'resume' | 'step' | 'reset', scale?: number) => void;
  onRetry: () => void;
  onOpenSettings: () => void;
  onSignOut: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  isOnline,
  isWsConnected,
  simTime,
  isPaused,
  timeScale,
  currentUser,
  databaseStatus,
  onClockAction,
  onRetry,
  onOpenSettings,
  onSignOut,
}) => {
  const isAdmin = roleAllows(currentUser.role, 'settings');
  const isObserver = !roleAllows(currentUser.role, 'simulation_control');
  const roleLabel = currentUser.role === 'ADMIN' ? 'Administrator' : currentUser.role === 'OPERATOR' ? 'Operator' : currentUser.role === 'OBSERVER' ? 'Observer' : 'Viewer';

  // Format simTime into hh:mm:ss
  const formatTime = (seconds: number) => {
    const totalSecs = Math.floor(seconds);
    const hrs = Math.floor(totalSecs / 3600);
    const mins = Math.floor((totalSecs % 3600) / 60);
    const secs = totalSecs % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <header className="h-16 bg-[#0F1115] border-b border-[#29323D] px-4 flex items-center justify-between select-none shrink-0 z-30">
      {/* Left: Brand Identity */}
      <div className="flex items-center gap-3 min-w-[210px]">
        <div className="w-9 h-9 rounded-lg bg-[#1683E8]/15 border border-[#1683E8]/40 flex items-center justify-center text-[#1683E8] shadow-sm">
          <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
        <div>
          <div className="text-base font-bold tracking-tight text-[#E5E7EB] leading-none">
            ResilientEdge
          </div>
          <div className="text-[11px] text-[#9CA3AF] font-medium leading-tight mt-0.5">
            Multi-Robot Resilience Simulation
          </div>
        </div>
      </div>

      {/* Center: Simulation Status, Clock & Controls */}
      <div className="flex items-center gap-4">
        {/* Simulation Running / Paused Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151A21] border border-[#29323D] text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              !isOnline
                ? 'bg-[#6B7280]'
                : isPaused
                ? 'bg-[#F59E0B]'
                : 'bg-[#22C55E] animate-pulse'
            }`}
          />
          <span className="font-medium text-[#E5E7EB]">
            {!isOnline ? 'Simulation Offline' : isPaused ? 'Simulation Paused' : 'Simulation Running'}
          </span>
        </div>

        {/* Simulation Time Display */}
        <div className="flex flex-col items-center justify-center px-4 py-1 rounded-lg bg-[#151A21] border border-[#29323D] min-w-[105px]">
          <div className="font-mono text-sm font-bold text-[#1683E8] leading-tight tracking-wider">
            {formatTime(simTime)}
          </div>
          <div className="text-[9px] text-[#6B7280] font-medium uppercase tracking-wider">
            Simulation Time
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1.5">
          {/* Pause / Resume Button */}
          <button
            onClick={() => onClockAction(isPaused ? 'resume' : 'pause')}
            disabled={!isOnline || !roleAllows(currentUser.role, 'simulation_control')}
            title={isObserver ? 'Observer access is read-only' : undefined}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer shadow-sm ${
              isPaused
                ? 'bg-[#22C55E] hover:bg-[#16a34a] text-white'
                : 'bg-[#1683E8] hover:bg-[#2B95F5] text-white'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isPaused ? <Play className="w-3.5 h-3.5 fill-current" /> : <Pause className="w-3.5 h-3.5 fill-current" />}
            <span>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>

          {/* Step Button */}
          <button
            onClick={() => onClockAction('step')}
            disabled={!isOnline || !roleAllows(currentUser.role, 'simulation_control')}
            title={isObserver ? 'Observer access is read-only' : undefined}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <StepForward className="w-3.5 h-3.5" />
            <span>Step</span>
          </button>

          {/* Reset Button */}
          <button
            onClick={() => onClockAction('reset')}
            disabled={!isOnline || !roleAllows(currentUser.role, 'simulation_control')}
            title={isObserver ? 'Observer access is read-only' : undefined}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>

        {/* Time Scale slider & dropdown */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#29323D]">
          <span className="text-[11px] text-[#9CA3AF] font-medium whitespace-nowrap">Time Scale</span>
          <input
            type="range"
            min="0.2"
            max="5.0"
            step="0.1"
            value={timeScale}
            disabled={!roleAllows(currentUser.role, 'simulation_control')}
            onChange={(e) => onClockAction(isPaused ? 'pause' : 'resume', parseFloat(e.target.value))}
            className="w-16 h-1 bg-[#29323D] rounded-lg appearance-none cursor-pointer accent-[#1683E8] disabled:opacity-50"
          />
          <select
            value={timeScale}
            disabled={!roleAllows(currentUser.role, 'simulation_control')}
            onChange={(e) => onClockAction(isPaused ? 'pause' : 'resume', parseFloat(e.target.value))}
            className="bg-[#151A21] border border-[#29323D] text-[#E5E7EB] text-xs rounded px-1.5 py-1 font-mono focus:outline-none focus:border-[#1683E8] cursor-pointer disabled:opacity-50"
          >
            <option value="0.5">0.5x</option>
            <option value="1.0">1.0x</option>
            <option value="2.0">2.0x</option>
            <option value="5.0">5.0x</option>
            <option value="10.0">10.0x</option>
          </select>
        </div>

        {/* Seed & Delta T */}
        <div className="hidden xl:flex items-center gap-3 text-xs text-[#9CA3AF] font-mono pl-2 border-l border-[#29323D]">
          <span>Seed: <strong className="text-[#E5E7EB]">42</strong></span>
          <span>Δt: <strong className="text-[#E5E7EB]">0.1 s</strong></span>
        </div>
      </div>

      {/* Right: RBAC User, Database Status, Backend Status & Settings */}
      <div className="flex items-center gap-2.5">
        {/* Database Status Pill */}
        <div
          title={databaseStatus.statusLabel}
          className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium ${
            databaseStatus.isConnected
              ? 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]'
              : 'bg-[#6B7280]/15 border-[#6B7280]/30 text-[#9CA3AF]'
          }`}
        >
          {databaseStatus.isConnected ? <Cloud className="w-3 h-3 text-[#10B981]" /> : <CloudOff className="w-3 h-3 text-[#9CA3AF]" />}
          <span>{databaseStatus.isConnected ? 'Local Database Online' : 'Local Database Offline'}</span>
        </div>

        {/* Authenticated identity */}
        <div className="flex items-center gap-2 bg-[#151A21] border border-[#29323D] px-2.5 py-1 rounded-lg">
          <div className="text-right leading-tight">
            <div className="text-[11px] font-semibold text-[#E5E7EB]">{currentUser.name}</div>
            <div className="text-[9px] text-[#9CA3AF]">{roleLabel}</div>
          </div>
          <button onClick={onSignOut} title="Sign out" className="w-7 h-7 rounded-md hover:bg-[#222B36] flex items-center justify-center text-[#9CA3AF] hover:text-[#E5E7EB]">
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Backend Connectivity Status */}
        {isOnline ? (
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#22C55E]/10 border border-[#22C55E]/20 text-xs text-[#22C55E] font-medium">
            <span className="w-2 h-2 rounded-full bg-[#22C55E] animate-pulse" />
            <span className="hidden sm:inline">Backend Online</span>
          </div>
        ) : (
          <button
            onClick={onRetry}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#EF4444]/15 border border-[#EF4444]/30 text-xs text-[#EF4444] font-medium hover:bg-[#EF4444]/25 cursor-pointer transition-colors"
          >
            <WifiOff className="w-3 h-3" />
            <span>Backend Offline</span>
          </button>
        )}

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          disabled={!isAdmin}
          title="System Settings"
          className="w-8 h-8 rounded-lg bg-[#151A21] hover:bg-[#1B222B] border border-[#29323D] flex items-center justify-center text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
