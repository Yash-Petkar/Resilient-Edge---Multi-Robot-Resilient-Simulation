import React, { useState, useEffect } from 'react';
import {
  Database,
  Cloud,
  CloudOff,
  RefreshCw,
  Trash2,
  ShieldCheck,
  AlertTriangle,
  Server,
  Layers,
  History,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { apiService } from '../services/apiService';
import { UserRole } from '../types';
import { roleAllows } from '../permissions';

interface DatabaseDashboardProps {
  currentUserRole: UserRole;
  isOnline: boolean;
  onNotification?: (msg: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const DatabaseDashboard: React.FC<DatabaseDashboardProps> = ({
  currentUserRole,
  isOnline,
  onNotification,
}) => {
  const [stats, setStats] = useState<Record<string, any>>({});
  const [recentIncidents, setRecentIncidents] = useState<any[]>([]);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [confirmClearOpen, setConfirmClearOpen] = useState<boolean>(false);
  const [activeSubTab, setActiveSubTab] = useState<'tables' | 'events' | 'schema'>('tables');

  const databaseStatus = apiService.getStatus();

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      // 1. Fetch table counts & stats from API
      const res = await apiService.apiFetch('/api/database/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      } else {
        // Fallback to Local Database service client stats
        const data = await apiService.fetchDatabaseStats();
        setStats(data);
      }

      // 2. Fetch recent incidents
      const incRes = await apiService.apiFetch('/api/database/incidents?limit=10');
      if (incRes.ok) {
        const incData = await incRes.json();
        setRecentIncidents(incData);
      }

      // 3. Fetch recent decision events
      const evRes = await apiService.apiFetch('/api/database/events?limit=10');
      if (evRes.ok) {
        const evData = await evRes.json();
        setRecentEvents(evData);
      }
    } catch (err) {
      console.warn('[DatabaseDashboard] Failed to fetch database stats:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 6000);
    return () => clearInterval(interval);
  }, []);

  const handleManualSync = async () => {
    setIsSyncing(true);
    try {
      await apiService.checkConnection();
      await fetchStats();
      if (onNotification) {
        onNotification('Persistent data store synchronized successfully.', 'success');
      }
    } catch (err: any) {
      if (onNotification) {
        onNotification(`Sync failed: ${err.message}`, 'error');
      }
    } finally {
      setIsSyncing(false);
    }
  };

  const handleClearDatabase = async () => {
    if (!roleAllows(currentUserRole, 'database_admin')) {
      if (onNotification) {
        onNotification('Permission denied: Only ADMIN role can clear persistent records.', 'error');
      }
      return;
    }

    try {
      const res = await apiService.apiFetch('/api/database/clear', { method: 'POST' });
      if (res.ok) {
        if (onNotification) {
          onNotification('Persistent tables purged successfully.', 'success');
        }
        setConfirmClearOpen(false);
        fetchStats();
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (err: any) {
      if (onNotification) {
        onNotification(`Clear failed: ${err.message}`, 'error');
      }
    }
  };

  const tables = [
    { name: 'robots', label: 'Robots Telemetry', desc: 'Fleet positions, battery, health & state records' },
    { name: 'tasks', label: 'Tasks Register', desc: 'Active & archived task states, pickup/delivery stations' },
    { name: 'faults', label: 'Injected Faults', desc: 'Hardware, environmental, and network anomaly history' },
    { name: 'incidents', label: 'Incident Audit Trail', desc: 'Chronological safety, failure, and state transitions' },
    { name: 'decision_events', label: 'Decision Log', desc: 'Authoritative dynamic task reassignment metrics' },
    { name: 'experiments', label: 'Experiments', desc: 'Monte Carlo, S01-S06 scenarios, parameter sweep runs' },
    { name: 'experiment_runs', label: 'Run Details', desc: 'Run-by-run execution benchmarks and metrics' },
    { name: 'reservations', label: 'Spatial Reservations', desc: 'Cell reservation space-time windows' },
    { name: 'metrics', label: 'Aggregated Metrics', desc: 'Makespan, waiting time, resilience duration history' },
  ];

  return (
    <div className="space-y-5 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-[#151A21] border border-[#29323D] rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#1683E8]/15 border border-[#1683E8]/30 flex items-center justify-center text-[#1683E8]">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-[#E5E7EB] flex items-center gap-2">
              Persistent Storage & SQLite Database Layer
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1683E8]/15 text-[#1683E8] border border-[#1683E8]/30">
                Phase 11–15
              </span>
            </h2>
            <p className="text-xs text-[#9CA3AF]">
              Asynchronous event-driven persistence with Row Level Security (RLS) and offline queue
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleManualSync}
            disabled={isSyncing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1B222B] hover:bg-[#222B36] border border-[#29323D] text-[#E5E7EB] rounded-lg text-xs font-semibold cursor-pointer transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
          </button>

          {roleAllows(currentUserRole, 'database_admin') && (
            <button
              onClick={() => setConfirmClearOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#EF4444]/15 hover:bg-[#EF4444]/25 border border-[#EF4444]/30 text-[#EF4444] rounded-lg text-xs font-semibold cursor-pointer transition-colors shadow-sm"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Persistent Data</span>
            </button>
          )}
        </div>
      </div>

      {/* Connectivity & Permission Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Storage Engine Status */}
        <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#9CA3AF] font-medium">Storage Engine</span>
            {databaseStatus.isConnected ? (
              <span className="flex items-center gap-1 text-[#22C55E] font-bold">
                <Cloud className="w-3.5 h-3.5" /> Local Database
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[#F59E0B] font-bold">
                <Server className="w-3.5 h-3.5" /> SQLite Local (Auto-Buffered)
              </span>
            )}
          </div>
          <div className="text-sm font-bold text-[#E5E7EB]">
            {stats.storage_mode || (databaseStatus.isConnected ? 'SQLite Database' : 'SQLite Persistent Database')}
          </div>
          <div className="text-[11px] text-[#9CA3AF]">
            Offline Queue: <strong className="text-[#E5E7EB] font-mono">{databaseStatus.queueLength} events buffered</strong>
          </div>
        </div>

        {/* Active RBAC Role */}
        <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#9CA3AF] font-medium">Active RBAC Profile</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#1683E8]/15 text-[#1683E8] border border-[#1683E8]/30">
              {currentUserRole}
            </span>
          </div>
          <div className="text-sm font-bold text-[#E5E7EB] flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#22C55E]" />
            <span>{databaseStatus.isConnected ? 'Local Database Connected' : 'Local API Role Checks'}</span>
          </div>
          <div className="text-[11px] text-[#9CA3AF]">
            {currentUserRole === 'ADMIN'
              ? 'Full read/write/truncate permissions across all tables'
              : currentUserRole === 'OPERATOR'
              ? 'Simulation control, task dispatch, faults, recovery & experiments'
              : 'Read-only access (Simulation observation only)'}
          </div>
        </div>

        {/* Database Health & Transactions */}
        <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#9CA3AF] font-medium">Database Health</span>
            <span className={`flex items-center gap-1 font-bold ${
              databaseStatus.isConnected
                ? 'text-[#22C55E]'
                : databaseStatus.isConnected
                ? 'text-[#F59E0B]'
                : 'text-[#EF4444]'
            }`}>
              {databaseStatus.isConnected
                ? <><CheckCircle2 className="w-3.5 h-3.5" /> LOCAL DATABASE ONLINE</>
                : databaseStatus.isConnected
                ? <><Server className="w-3.5 h-3.5" /> LOCAL DB</>
                : <><CloudOff className="w-3.5 h-3.5" /> DATABASE ERROR</>}
            </span>
          </div>
          <div className="text-sm font-bold text-[#E5E7EB]">
            {databaseStatus.statusLabel}
          </div>
          <div className="text-[11px] text-[#9CA3AF]">
            Simulation tick rate is isolated from database I/O latency.
          </div>
        </div>
      </div>

      {/* Sub-Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-[#29323D] pb-2">
        <button
          onClick={() => setActiveSubTab('tables')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-colors ${
            activeSubTab === 'tables'
              ? 'bg-[#1683E8] text-white shadow-sm'
              : 'text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#151A21]'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Tables & Counts ({tables.length})</span>
        </button>
        <button
          onClick={() => setActiveSubTab('events')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-colors ${
            activeSubTab === 'events'
              ? 'bg-[#1683E8] text-white shadow-sm'
              : 'text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#151A21]'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Decision & Incident Events</span>
        </button>
        <button
          onClick={() => setActiveSubTab('schema')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-colors ${
            activeSubTab === 'schema'
              ? 'bg-[#1683E8] text-white shadow-sm'
              : 'text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#151A21]'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>PostgreSQL Schema (local database schema)</span>
        </button>
      </div>

      {/* Tab 1: Tables & Counts */}
      {activeSubTab === 'tables' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {tables.map((tbl) => {
            const count = stats[tbl.name] ?? 0;
            return (
              <div
                key={tbl.name}
                className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 flex flex-col justify-between hover:border-[#1683E8]/50 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-xs font-bold text-[#1683E8]">{tbl.name}</span>
                    <span className="font-mono text-sm font-bold text-[#E5E7EB] bg-[#0F1115] px-2.5 py-0.5 rounded border border-[#29323D]">
                      {count} {count === 1 ? 'record' : 'records'}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-[#E5E7EB]">{tbl.label}</h4>
                  <p className="text-[11px] text-[#9CA3AF] mt-1 leading-snug">{tbl.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Tab 2: Decision & Incident Events */}
      {activeSubTab === 'events' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Decision Events */}
          <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-[#29323D] pb-2">
              <h4 className="text-xs font-bold text-[#E5E7EB] flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-[#1683E8]" />
                Recent Decision Events (Task Reassignments)
              </h4>
              <span className="text-[10px] text-[#9CA3AF] font-mono">{recentEvents.length} events</span>
            </div>
            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {recentEvents.length === 0 ? (
                <div className="text-xs text-[#6B7280] italic py-6 text-center">
                  No reassignment decision events logged yet. Reassign a robot or run Scenario S02/S03.
                </div>
              ) : (
                recentEvents.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-[#0F1115] border border-[#29323D] rounded-lg text-xs space-y-1 font-mono"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-[#1683E8] font-bold">{ev.event_type}</span>
                      <span className="text-[#6B7280]">{ev.timestamp?.toFixed(1) || 0}s</span>
                    </div>
                    <div className="text-[#E5E7EB] text-[11px] font-sans">
                      Robot: <strong>{ev.robot_id}</strong> | Task: <strong>{ev.task_id}</strong>
                    </div>
                    {ev.details && (
                      <div className="text-[10px] text-[#9CA3AF] truncate">
                        {typeof ev.details === 'object' ? JSON.stringify(ev.details) : ev.details}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Incident Trail */}
          <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-[#29323D] pb-2">
              <h4 className="text-xs font-bold text-[#E5E7EB] flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-[#F59E0B]" />
                Recent Incident Audit Records
              </h4>
              <span className="text-[10px] text-[#9CA3AF] font-mono">{recentIncidents.length} records</span>
            </div>
            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {recentIncidents.length === 0 ? (
                <div className="text-xs text-[#6B7280] italic py-6 text-center">
                  No incident records logged yet.
                </div>
              ) : (
                recentIncidents.map((inc, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-[#0F1115] border border-[#29323D] rounded-lg text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span
                        className={`font-bold px-1.5 py-0.2 rounded ${
                          inc.severity === 'CRITICAL'
                            ? 'bg-[#EF4444]/15 text-[#EF4444]'
                            : inc.severity === 'WARNING'
                            ? 'bg-[#F59E0B]/15 text-[#F59E0B]'
                            : 'bg-[#22C55E]/15 text-[#22C55E]'
                        }`}
                      >
                        {inc.severity}
                      </span>
                      <span className="text-[#6B7280]">{inc.timestamp?.toFixed(1) || 0}s</span>
                    </div>
                    <div className="text-[#E5E7EB] text-xs font-medium">
                      [{inc.entity}] {inc.message}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: PostgreSQL Schema */}
      {activeSubTab === 'schema' && (
        <div className="bg-[#151A21] border border-[#29323D] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#29323D] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#E5E7EB]">Production Local Database SQL Migrations</h3>
              <p className="text-xs text-[#9CA3AF]">
                Stored at <code className="text-[#1683E8]">/local database schema/20260926000000_initial_schema.sql</code>
              </p>
            </div>
            <span className="px-2.5 py-1 rounded bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/30 text-xs font-bold">
              RLS Enabled (10 Policies)
            </span>
          </div>

          <div className="bg-[#0F1115] border border-[#29323D] rounded-lg p-4 font-mono text-xs text-[#9CA3AF] overflow-x-auto max-h-[350px]">
            <pre>{`-- SQLite Database Schema Overview
-- Tables Created:
• profiles (id UUID PK, email TEXT, full_name TEXT, role VARCHAR(20))
• robots (robot_id VARCHAR(50) PK, position_x, position_y, state, battery, health, current_task)
• tasks (task_id VARCHAR(50) PK, pickup_x, pickup_y, delivery_x, delivery_y, priority, status)
• faults (fault_id VARCHAR(50) PK, fault_type, target, start_time, duration, status)
• incidents (incident_id VARCHAR(100) PK, timestamp, entity, fault, severity, state, message)
• reservations (reservation_id VARCHAR(100) PK, robot_id, cell_x, cell_y, start_time, end_time)
• decision_events (id UUID PK, event_type, robot_id, task_id, timestamp, details JSONB)
• experiments (experiment_id VARCHAR(50) PK, scenario, seed, robot_count, task_count, metrics JSONB)
• experiment_runs (run_id VARCHAR(50) PK, experiment_id FK, run_index, seed, status, metrics JSONB)
• metrics (id BIGSERIAL PK, timestamp, task_completion_rate, makespan, metrics_json JSONB)

-- Security:
• Row Level Security (RLS) enabled on all tables
• ADMIN: Full ALL operations
• OPERATOR: SELECT, INSERT, UPDATE telemetry and tasks
• OBSERVER: Strict SELECT only`}</pre>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Clearing Database */}
      {confirmClearOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
          <div className="bg-[#151A21] border border-[#EF4444]/50 rounded-xl p-5 max-w-md w-full space-y-4 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3 text-[#EF4444]">
              <div className="w-10 h-10 rounded-full bg-[#EF4444]/20 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[#E5E7EB]">Confirm Persistent Data Purge</h3>
                <p className="text-xs text-[#9CA3AF]">This will clear all records across database tables.</p>
              </div>
            </div>

            <p className="text-xs text-[#9CA3AF] bg-[#0F1115] p-3 rounded border border-[#29323D]">
              Are you sure you want to purge the database? This action is irreversible and resets all historical incidents, tasks, experiments, and decision events.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setConfirmClearOpen(false)}
                className="px-3.5 py-1.5 rounded-lg border border-[#29323D] text-xs font-semibold text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#1B222B] cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleClearDatabase}
                className="px-3.5 py-1.5 rounded-lg bg-[#EF4444] hover:bg-[#DC2626] text-white text-xs font-bold cursor-pointer shadow-sm"
              >
                Yes, Purge Database
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
