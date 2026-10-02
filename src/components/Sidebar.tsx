import React from 'react';
import {
  LayoutDashboard,
  Grid,
  Bot,
  ClipboardList,
  AlertTriangle,
  History,
  RotateCcw,
  FlaskConical,
  BarChart2,
  Layers,
  Radio,
  Database,
  Settings, Users, ScrollText,
} from 'lucide-react';
import { UserRole } from '../types';
import { roleAllows } from '../permissions';

export type NavTab =
  | 'dashboard'
  | 'simulation'
  | 'fleet'
  | 'tasks'
  | 'faults'
  | 'incidents'
  | 'recovery'
  | 'experiments'
  | 'metrics'
  | 'baseline'
  | 'network'
  | 'database'
  | 'settings'
  | 'admin-users'
  | 'admin-audit';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isOnline: boolean;
  isWsConnected: boolean;
  isSimulationRunning: boolean;
  currentUserRole: UserRole;
  databaseStatus: { database?: 'local' | 'error' | 'unknown'; isConnected: boolean; statusLabel: string };
}

interface NavItem {
  id: NavTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  isOnline,
  isWsConnected,
  isSimulationRunning,
  currentUserRole,
  databaseStatus,
}) => {
  const sections: NavSection[] = [
    {
      title: 'OVERVIEW',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'simulation', label: 'Simulation', icon: Grid },
        { id: 'fleet', label: 'Fleet', icon: Bot },
      ],
    },
    {
      title: 'OPERATIONS',
      items: [
        { id: 'tasks', label: 'Tasks', icon: ClipboardList },
        { id: 'faults', label: 'Fault Injection', icon: AlertTriangle },
      ],
    },
    {
      title: 'RESILIENCE',
      items: [
        { id: 'incidents', label: 'Incidents', icon: History },
        { id: 'recovery', label: 'Recovery', icon: RotateCcw },
      ],
    },
    {
      title: 'ANALYSIS',
      items: [
        { id: 'experiments', label: 'Experiments', icon: FlaskConical },
        { id: 'metrics', label: 'Metrics', icon: BarChart2 },
        { id: 'baseline', label: 'Baseline Comparison', icon: Layers },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { id: 'network', label: 'Network', icon: Radio },
        { id: 'database', label: 'Database', icon: Database },
        { id: 'settings', label: 'Settings', icon: Settings },
      ],
    },
    ...(roleAllows(currentUserRole, 'user_admin') ? [{ title: 'ADMINISTRATION', items: [
      { id: 'admin-users' as NavTab, label: 'Users & Roles', icon: Users },
      { id: 'admin-audit' as NavTab, label: 'Audit Logs', icon: ScrollText },
    ] }] : []),
  ];

  return (
    <aside className="w-[210px] bg-[#0B1016] border-r border-[#29323D] flex flex-col justify-between select-none shrink-0 h-full overflow-y-auto">
      {/* Navigation Sections */}
      <div className="py-4 px-2 space-y-4">
        {sections.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 text-[10px] font-bold tracking-wider text-[#6B7280] uppercase">
              {section.title}
            </div>
            <div className="space-y-0.5">
              {section.items
                .filter((item) => {
                  if (item.id === 'settings') return roleAllows(currentUserRole, 'settings');
                  if (item.id === 'database') return roleAllows(currentUserRole, 'database_admin');
                  if (item.id === 'faults') return roleAllows(currentUserRole, 'fault_injection');
                  if (item.id === 'recovery') return roleAllows(currentUserRole, 'recovery');
                  if (item.id === 'experiments') return roleAllows(currentUserRole, 'experiments');
                  if (item.id === 'baseline') return roleAllows(currentUserRole, 'experiments');
                  if (item.id === 'admin-users') return roleAllows(currentUserRole, 'user_admin');
                  if (item.id === 'admin-audit') return roleAllows(currentUserRole, 'audit_read');
                  return true;
                })
                .map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onSelectTab(item.id)}
                    className={`w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                      isActive
                        ? 'bg-[#1683E8] text-white'
                        : 'text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#151A21]'
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-[#6B7280]'}`} />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Bottom: System Status Panel */}
      <div className="p-3 border-t border-[#29323D] bg-[#0F1115]/50">
        <div className="text-[10px] font-bold uppercase tracking-wider text-[#6B7280] mb-2">
          System Status
        </div>
        <div className="space-y-1.5 text-[11px] font-medium">
          <div className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-[#22C55E]' : 'bg-[#EF4444]'}`} />
            <span className={isOnline ? 'text-[#E5E7EB]' : 'text-[#EF4444]'}>
              {isOnline ? 'Backend Online' : 'Backend Offline'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${isWsConnected ? 'bg-[#22C55E]' : 'bg-[#EF4444]'}`} />
            <span className={isWsConnected ? 'text-[#E5E7EB]' : 'text-[#9CA3AF]'}>
              {isWsConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${isSimulationRunning ? 'bg-[#22C55E]' : 'bg-[#F59E0B]'}`} />
            <span className="text-[#E5E7EB]">
              {isSimulationRunning ? 'Simulation Running' : 'Simulation Paused'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${
              databaseStatus.isConnected
                ? 'bg-[#22C55E]'
                : databaseStatus.isConnected
                ? 'bg-[#F59E0B]'
                : 'bg-[#EF4444]'
            }`} />
            <span className={
              databaseStatus.isConnected
                ? 'text-[#E5E7EB]'
                : databaseStatus.isConnected
                ? 'text-[#F59E0B]'
                : 'text-[#EF4444]'
            }>
              {databaseStatus.isConnected
                ? 'Local Database Online'
                : databaseStatus.isConnected
                ? 'Local Database'
                : databaseStatus.statusLabel}
            </span>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t border-[#29323D]/60 text-[10px] font-mono text-[#6B7280]">
          ResilientEdge v1.0.0
        </div>
      </div>
    </aside>
  );
};
