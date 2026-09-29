import React, { useState } from 'react';
import { Play, Pause, SkipForward, RotateCcw, Shield, Moon, Sun, Wifi, WifiOff, AlertTriangle, UserCheck } from 'lucide-react';
import { UserProfile, UserRole } from '../../types';

interface HeaderProps {
  isOnline: boolean;
  onRetryConnection: () => void;
  simTime: number;
  isPaused: boolean;
  timeScale: number;
  onClockAction: (action: 'pause' | 'resume' | 'step' | 'reset', scale?: number) => void;
  currentUser: UserProfile;
  onSwitchUser: (user: UserProfile) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  packetLossRate: number;
  isPartitioned: boolean;
}

const PRESET_USERS: UserProfile[] = [
  { id: 'u1', name: 'Dr. Sarah Chen', email: 'admin@resilientedge.io', role: 'ADMIN', avatar: 'SC' },
  { id: 'u2', name: 'Marcus Vance', email: 'operator@resilientedge.io', role: 'OPERATOR', avatar: 'MV' },
  { id: 'u3', name: 'Elena Rostova', email: 'observer@resilientedge.io', role: 'OBSERVER', avatar: 'ER' },
];

export const Header: React.FC<HeaderProps> = ({
  isOnline,
  onRetryConnection,
  simTime,
  isPaused,
  timeScale,
  onClockAction,
  currentUser,
  onSwitchUser,
  darkMode,
  onToggleDarkMode,
  packetLossRate,
  isPartitioned,
}) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  return (
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-2.5 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Logo and Status */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-slate-900 dark:bg-blue-600 flex items-center justify-center text-white font-mono font-bold text-sm tracking-wider shadow-sm">
              RE
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-base tracking-tight text-slate-900 dark:text-slate-100">
                  ResilientEdge
                </h1>
                <span className="hidden sm:inline-block text-[11px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                  Core Telemetry
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 hidden md:block">
                Multi-Robot Resilience Simulation &amp; Chaos Platform
              </p>
            </div>
          </div>

          {/* Online / Offline status badge */}
          <div className="flex items-center gap-1.5 ml-2">
            {isOnline ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Backend: ONLINE
              </span>
            ) : (
              <button
                onClick={onRetryConnection}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800 hover:bg-rose-100 transition-colors cursor-pointer"
                title="Click to retry backend connection"
              >
                <WifiOff className="w-3 h-3 text-rose-500" />
                Backend: OFFLINE (Retry)
              </button>
            )}

            {/* Critical network warning indicator */}
            {isPartitioned ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-medium bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700 animate-pulse">
                <AlertTriangle className="w-3 h-3" />
                PARTITION ACTIVE
              </span>
            ) : packetLossRate > 0.15 ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-medium bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                <AlertTriangle className="w-3 h-3" />
                LOSS: {Math.round(packetLossRate * 100)}%
              </span>
            ) : null}
          </div>
        </div>

        {/* Clock Controls */}
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 px-2.5 py-1 rounded-md border border-slate-200 dark:border-slate-700 text-xs">
          <div className="font-mono font-semibold text-slate-800 dark:text-slate-200 mr-1">
            t = {simTime.toFixed(1)}s
          </div>

          <div className="h-4 w-px bg-slate-300 dark:bg-slate-700 mx-0.5" />

          {/* Play/Pause */}
          <button
            onClick={() => onClockAction(isPaused ? 'resume' : 'pause')}
            disabled={currentUser.role === 'OBSERVER'}
            className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors disabled:opacity-40"
            title={isPaused ? 'Resume Simulation' : 'Pause Simulation'}
          >
            {isPaused ? <Play className="w-3.5 h-3.5 fill-current" /> : <Pause className="w-3.5 h-3.5 fill-current" />}
          </button>

          {/* Step */}
          <button
            onClick={() => onClockAction('step')}
            disabled={currentUser.role === 'OBSERVER'}
            className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors disabled:opacity-40"
            title="Step One Tick (0.1s)"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>

          {/* Reset */}
          <button
            onClick={() => onClockAction('reset')}
            disabled={currentUser.role === 'OBSERVER'}
            className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors disabled:opacity-40"
            title="Reset Simulation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <div className="h-4 w-px bg-slate-300 dark:bg-slate-700 mx-0.5" />

          {/* Speed presets */}
          <div className="flex items-center gap-1">
            {[0.5, 1.0, 2.0, 5.0].map((scale) => (
              <button
                key={scale}
                onClick={() => onClockAction('resume', scale)}
                disabled={currentUser.role === 'OBSERVER'}
                className={`px-1.5 py-0.5 rounded font-mono text-[10px] transition-colors disabled:opacity-40 ${
                  timeScale === scale
                    ? 'bg-slate-900 text-white dark:bg-blue-600 font-bold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {scale}x
              </button>
            ))}
          </div>
        </div>

        {/* User Role & Dark Mode Toggle */}
        <div className="flex items-center gap-2">
          {/* User Role Switcher */}
          <div className="relative">
            <button
              onClick={() => setShowUserDropdown(!showUserDropdown)}
              className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 text-xs transition-colors"
            >
              <div className="w-5 h-5 rounded-full bg-slate-700 text-white dark:bg-blue-600 flex items-center justify-center font-bold text-[10px]">
                {currentUser.avatar}
              </div>
              <div className="text-left hidden sm:block">
                <span className="font-medium text-slate-800 dark:text-slate-200 block text-xs leading-none">
                  {currentUser.name}
                </span>
                <span className={`text-[10px] uppercase font-bold leading-none ${
                  currentUser.role === 'ADMIN' ? 'text-amber-600 dark:text-amber-400' :
                  currentUser.role === 'OPERATOR' ? 'text-blue-600 dark:text-blue-400' :
                  'text-slate-500'
                }`}>
                  {currentUser.role}
                </span>
              </div>
            </button>

            {showUserDropdown && (
              <div className="absolute right-0 mt-1.5 w-60 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50 py-1.5 text-xs">
                <div className="px-3 py-1.5 border-b border-slate-100 dark:border-slate-700 text-slate-500 dark:text-slate-400">
                  Switch Active Role (RBAC):
                </div>
                {PRESET_USERS.map((u) => (
                  <button
                    key={u.id}
                    onClick={() => {
                      onSwitchUser(u);
                      setShowUserDropdown(false);
                    }}
                    className={`w-full text-left px-3 py-2 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${
                      u.id === currentUser.id ? 'bg-slate-50 dark:bg-slate-700/80 font-semibold' : ''
                    }`}
                  >
                    <div>
                      <div className="text-slate-900 dark:text-slate-100">{u.name}</div>
                      <div className="text-[11px] text-slate-500">{u.email}</div>
                    </div>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                      u.role === 'ADMIN' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' :
                      u.role === 'OPERATOR' ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300' :
                      'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
                    }`}>
                      {u.role}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Theme Toggle */}
          <button
            onClick={onToggleDarkMode}
            className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors"
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
          </button>
        </div>
      </div>
    </header>
  );
};
