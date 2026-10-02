import React, { useState, useEffect, useRef, useCallback } from 'react';
import { TopBar } from './components/TopBar';
import { Sidebar, NavTab } from './components/Sidebar';
import { KpiCards } from './components/KpiCards';
import { SimulationMap } from './components/SimulationMap';
import { RobotStatusPanel } from './components/RobotStatusPanel';
import { CurrentTasksPanel } from './components/CurrentTasksPanel';
import { ResilienceStateMachine } from './components/ResilienceStateMachine';
import { IncidentTimelinePanel } from './components/IncidentTimelinePanel';
import { FaultInjectionPanel } from './components/FaultInjectionPanel';
import { RobotDetailDrawer } from './components/RobotDetailDrawer';
import { TaskDetailDrawer } from './components/TaskDetailDrawer';
import { TaskDispatcherModal } from './components/TaskDispatcherModal';
import { SettingsModal } from './components/SettingsModal';
import { ExperimentsRunner } from './components/ExperimentsRunner';
import { BaselineComparison } from './components/BaselineComparison';
import { MetricsDashboard } from './components/MetricsDashboard';
import { BackupManager } from './components/BackupManager';
import { NetworkTopologyView } from './components/NetworkTopologyView';
import { DatabaseDashboard } from './components/DatabaseDashboard';
import { apiService } from './services/apiService';
import { TelemetryData, TaskTelemetry, UserProfile } from './types';
import { isUserRole, Permission, roleAllows } from './permissions';
import { WifiOff, RefreshCw, AlertCircle, CheckCircle2, Info, X } from 'lucide-react';
import { AdminConsole } from './components/admin/AdminConsole';

const INITIAL_TELEMETRY: TelemetryData = {
  timestamp: 0.0,
  clock: {
    current_time: 0.0,
    tick_count: 0,
    is_paused: false,
    time_step: 0.1,
    time_scale: 1.0,
  },
  world: {
    width: 24,
    height: 16,
    shelves: [
      [6, 2], [6, 3], [6, 4], [7, 2], [7, 3], [7, 4],
      [11, 2], [11, 3], [11, 4], [12, 2], [12, 3], [12, 4],
      [16, 2], [16, 3], [16, 4], [17, 2], [17, 3], [17, 4],
      [6, 6], [6, 7], [6, 8], [7, 6], [7, 7], [7, 8],
      [11, 6], [11, 7], [11, 8], [12, 6], [12, 7], [12, 8],
      [16, 6], [16, 7], [16, 8], [17, 6], [17, 7], [17, 8],
    ],
    pickup_stations: { P1: [2, 2], P2: [2, 6], P3: [2, 10], P4: [2, 14] },
    delivery_stations: { D1: [21, 2], D2: [21, 6], D3: [21, 10], D4: [21, 14] },
    charging_bays: { C1: [11, 0], C2: [12, 0], C3: [13, 0], C4: [14, 0] },
    blocked_aisles: [[14, 8]],
    dynamic_obstacles: [],
  },
  robots: [
    { robot_id: 'R1', position: [4, 0], orientation: 0, velocity: 1, state: 'IDLE', battery: 82, health: 1, current_task: 'T01', current_path: [], path_progress: 0, network_status: 'CONNECTED', last_heartbeat: 0 },
    { robot_id: 'R2', position: [8, 0], orientation: 0, velocity: 1, state: 'DEGRADED', battery: 64, health: 1, current_task: 'T03', current_path: [], path_progress: 0, network_status: 'CONNECTED', last_heartbeat: 0 },
    { robot_id: 'R3', position: [12, 0], orientation: 0, velocity: 1, state: 'LOCAL_AUTONOMY', battery: 71, health: 1, current_task: 'T04', current_path: [], path_progress: 0, network_status: 'CONNECTED', last_heartbeat: 0 },
  ],
  tasks: [
    { task_id: 'T01', pickup: [2, 2], delivery: [21, 2], priority: 3, deadline: 300, status: 'COMPLETED', assigned_robot: 'R1', creation_time: 0, start_time: 0, completion_time: 45, phase: 'DELIVERY' },
    { task_id: 'T02', pickup: [2, 6], delivery: [21, 6], priority: 2, deadline: 300, status: 'COMPLETED', assigned_robot: 'R2', creation_time: 0, start_time: 0, completion_time: 50, phase: 'DELIVERY' },
    { task_id: 'T03', pickup: [2, 10], delivery: [21, 10], priority: 3, deadline: 300, status: 'IN_PROGRESS', assigned_robot: 'R2', creation_time: 0, start_time: 10, completion_time: null, phase: 'DELIVERY' },
    { task_id: 'T04', pickup: [2, 14], delivery: [21, 14], priority: 2, deadline: 300, status: 'ASSIGNED', assigned_robot: 'R3', creation_time: 0, start_time: null, completion_time: null, phase: 'PICKUP' },
    { task_id: 'T05', pickup: [2, 2], delivery: [21, 2], priority: 1, deadline: 300, status: 'AVAILABLE', assigned_robot: null, creation_time: 0, start_time: null, completion_time: null, phase: 'PICKUP' },
    { task_id: 'T06', pickup: [2, 6], delivery: [21, 6], priority: 1, deadline: 300, status: 'AVAILABLE', assigned_robot: null, creation_time: 0, start_time: null, completion_time: null, phase: 'PICKUP' },
  ],
  faults: [],
  incidents: [
    { incident_id: 'inc_9', timestamp: 272, entity: 'SYSTEM', fault: null, severity: 'INFO', state: 'NORMAL', message: 'Fleet returned to NORMAL' },
    { incident_id: 'inc_8', timestamp: 268, entity: 'NETWORK', fault: null, severity: 'INFO', state: 'NORMAL', message: 'Network connection restored' },
    { incident_id: 'inc_7', timestamp: 265, entity: 'R3', fault: null, severity: 'INFO', state: 'RECOVERY', message: 'R3 completed recovery' },
    { incident_id: 'inc_6', timestamp: 261, entity: 'R2', fault: null, severity: 'INFO', state: 'DEGRADED', message: 'Task T03 reassigned to R2' },
    { incident_id: 'inc_5', timestamp: 259, entity: 'R2', fault: 'ROBOT_FAILURE', severity: 'CRITICAL', state: 'DEGRADED', message: 'R2 failure detected' },
    { incident_id: 'inc_4', timestamp: 255, entity: 'NETWORK', fault: 'LATENCY', severity: 'WARNING', state: 'DEGRADED', message: 'Network latency increased (150 ms)' },
    { incident_id: 'inc_3', timestamp: 252, entity: 'NETWORK', fault: 'PACKET_LOSS', severity: 'WARNING', state: 'DEGRADED', message: 'Packet loss increased (10%)' },
    { incident_id: 'inc_2', timestamp: 248, entity: 'R2', fault: null, severity: 'INFO', state: 'NORMAL', message: 'Task T03 assigned to R2' },
    { incident_id: 'inc_1', timestamp: 245, entity: 'SYSTEM', fault: null, severity: 'INFO', state: 'NORMAL', message: 'Simulation started' },
  ],
  resilience: {
    current_state: 'NORMAL',
    state_durations: { NORMAL: 240, DEGRADED: 32, LOCAL_AUTONOMY: 0, RECOVERY: 0, RESYNC: 0, FAILED: 0 },
  },
  metrics: {
    total_tasks: 6,
    completed_tasks: 2,
    task_completion_rate: 33.3,
    makespan: 0,
    average_waiting_time: 4.2,
    average_route_length: 18.5,
    conflict_count: 0,
    collision_count: 0,
    deadlock_count: 0,
    deadlock_recovery_time: 0,
    failure_detection_time: 0.8,
    task_reassignment_time: 1.2,
    messages_sent: 142,
    messages_dropped: 2,
    stale_messages: 0,
    degraded_duration: 32,
    local_autonomy_duration: 0,
    resync_duration: 0,
  },
  network: {
    latency_ms: 12.0,
    packet_loss_rate: 0.001,
    jitter_ms: 1.5,
    messages_sent: 142,
    messages_dropped: 2,
    messages_delivered: 140,
    messages_duplicated: 0,
    messages_reordered: 0,
    in_flight_count: 0,
    is_partitioned: false,
    partition_groups: [],
  },
};

export default function App() {
  const [telemetry, setTelemetry] = useState<TelemetryData>(INITIAL_TELEMETRY);
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const routeToTab = (path: string): NavTab => {
    const routes: Record<string, NavTab> = {
      '/app': 'dashboard',
      '/app/': 'dashboard',
      '/': 'dashboard',
      '/dashboard': 'dashboard',
      '/app/dashboard': 'dashboard',
      '/simulation': 'simulation',
      '/app/simulation': 'simulation',
      '/robots': 'fleet',
      '/app/robots': 'fleet',
      '/fleet': 'fleet',
      '/app/fleet': 'fleet',
      '/tasks': 'tasks',
      '/app/tasks': 'tasks',
      '/faults': 'faults',
      '/app/faults': 'faults',
      '/incidents': 'incidents',
      '/app/incidents': 'incidents',
      '/recovery': 'recovery',
      '/app/recovery': 'recovery',
      '/experiments': 'experiments',
      '/app/experiments': 'experiments',
      '/metrics': 'metrics',
      '/app/metrics': 'metrics',
      '/baseline': 'baseline',
      '/app/baseline': 'baseline',
      '/network': 'network',
      '/app/network': 'network',
      '/database': 'database',
      '/app/database': 'database',
      '/settings': 'settings',
      '/app/settings': 'settings',
      '/admin': 'admin-users',
      '/app/admin': 'admin-users',
      '/admin/users': 'admin-users',
      '/app/admin/users': 'admin-users',
      '/admin/audit': 'admin-audit',
      '/app/admin/audit': 'admin-audit',
    };
    return routes[path] || 'dashboard';
  };

  const tabToRoute: Record<NavTab, string> = {
    dashboard: '/app',
    simulation: '/app/simulation',
    fleet: '/app/robots',
    tasks: '/app/tasks',
    faults: '/app/faults',
    incidents: '/app/incidents',
    recovery: '/app/recovery',
    experiments: '/app/experiments',
    metrics: '/app/metrics',
    baseline: '/app/baseline',
    network: '/app/network',
    database: '/app/database',
    settings: '/app/settings',
    'admin-users': '/app/admin/users',
    'admin-audit': '/app/admin/audit',
  };

  const [activeTab, setActiveTab] = useState<NavTab>(() => routeToTab(window.location.pathname));

  const handleTabSelect = (tab: NavTab) => {
    setActiveTab(tab);
    const route = tabToRoute[tab];
    if (window.location.pathname !== route) {
      window.history.pushState({}, '', route);
    }
  };

  useEffect(() => {
    const onPopState = () => setActiveTab(routeToTab(window.location.pathname));
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);
  const [selectedRobotId, setSelectedRobotId] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<TaskTelemetry | null>(null);
  const [isDispatcherOpen, setIsDispatcherOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // RBAC User & Local API Integration State
  const [currentUser, setCurrentUser] = useState<UserProfile>(() => {
    const u = apiService.getCurrentUser();
    return {
      id: u.id,
      name: u.full_name || 'Fleet Administrator',
      email: u.email,
      role: u.role,
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=256',
    };
  });
  const demoMode = apiService.isDemoMode();
  const [databaseStatus, setDatabaseStatus] = useState(() => apiService.getStatus());
  const [configurationError, setConfigurationError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(() => demoMode ? Boolean(apiService.getDemoRole()) : false);
  const [authLoading, setAuthLoading] = useState(() => !demoMode);
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [roleMismatch, setRoleMismatch] = useState<UserProfile['role'] | null>(null);

  useEffect(() => {
    let active = true;
    const refreshDatabaseStatus = async () => {
      try {
        await apiService.checkConnection();
        if (active) setDatabaseStatus(apiService.getStatus());
      } catch {
        if (active) setDatabaseStatus(apiService.getStatus());
      }
    };
    refreshDatabaseStatus();
    const timer = window.setInterval(refreshDatabaseStatus, 5000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  useEffect(() => {
    let active = true;

    const initializeAuthentication = async () => {
      // Health is public and reports the backend's active mode. Reject mismatches
      // instead of silently entering an insecure or unusable state.
      await apiService.checkConnection();
      const mismatch = apiService.getModeMismatch();
      if (!active) return;
      setConfigurationError(mismatch);

      if (mismatch) {
        if (!demoMode) apiService.clearDemoRole();
        setIsAuthenticated(false);
        setAuthLoading(false);
        return;
      }

      if (demoMode) {
        const role = apiService.getDemoRole();
        if (role && isUserRole(role)) {
          apiService.setDemoRole(role);
          setCurrentUser({ id: `demo-${role.toLowerCase()}`, name: `Demo ${role === 'ADMIN' ? 'Administrator' : role.charAt(0) + role.slice(1).toLowerCase()}`, email: 'demo@resilientedge.local', role, avatar: '' });
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
        setAuthLoading(false);
        return;
      }

      // Authenticated mode must never inherit demo state.
      apiService.clearDemoRole();
      apiService.restoreSession().then(async (profile) => {
        if (!active) return;
        if (profile && isUserRole(profile.role)) {
          setCurrentUser({ id: profile.id, name: profile.full_name || profile.email, email: profile.email, role: profile.role, avatar: '' });
          setIsAuthenticated(true);
          await apiService.checkConnection();
          if (active) {
            setDatabaseStatus(apiService.getStatus());
            setConfigurationError(apiService.getModeMismatch());
          }
        } else {
          setIsAuthenticated(false);
        }
        setAuthLoading(false);
      }).catch((err) => {
        if (active) {
          setAuthError(err.message || 'Session restoration failed');
          setIsAuthenticated(false);
          setAuthLoading(false);
        }
      });
    };

    initializeAuthentication();
    return () => { active = false; };
  }, [demoMode]);

  const handleDemoRole = async (role: UserProfile['role']) => {
    apiService.setDemoRole(role);
    setCurrentUser({ id: `demo-${role.toLowerCase()}`, name: `Demo ${role === 'ADMIN' ? 'Administrator' : role.charAt(0) + role.slice(1).toLowerCase()}`, email: 'demo@resilientedge.local', role, avatar: '' });
    setRoleMismatch(null);
    setAuthError(null);
    setIsAuthenticated(true);
    await apiService.checkConnection();
    setDatabaseStatus(apiService.getStatus());
  };

  const handleLogin = async (email: string, password: string, requestedRole: UserProfile['role']) => {
    setAuthError(null);
    setAuthSubmitting(true);
    try {
      await apiService.signIn(email, password);
      const response = await apiService.apiFetch('/api/auth/me');
      if (!response.ok) throw new Error('Authenticated session could not be loaded from backend');
      const profile = await response.json();
      if (!isUserRole(profile.role)) throw new Error('Backend returned an invalid role');
      setCurrentUser({ id: profile.id, name: profile.full_name || profile.email, email: profile.email, role: profile.role, avatar: '' });
      if (requestedRole !== profile.role) {
        const requested = requestedRole === 'ADMIN' ? 'Administrator' : requestedRole === 'OPERATOR' ? 'Operator' : requestedRole === 'OBSERVER' ? 'Observer' : 'Viewer';
        const actual = profile.role === 'ADMIN' ? 'Administrator' : profile.role === 'OPERATOR' ? 'Operator' : profile.role === 'OBSERVER' ? 'Observer' : 'Viewer';
        setRoleMismatch(profile.role);
        await apiService.signOut().catch(() => {});
        setIsAuthenticated(false);
        setAuthError(requested + " access is not enabled for this account. Your account is authorized for " + actual + ".");
        return;
      }
      setRoleMismatch(null);
      await apiService.checkConnection();
      setDatabaseStatus(apiService.getStatus());
      setIsAuthenticated(true);
    } catch (err: any) {
      setAuthError(err.message || 'Login failed');
      setIsAuthenticated(false);
    } finally {
      setAuthSubmitting(false);
    }
  };

  const handleSignOut = async () => {
    try {
      if (apiService.isDemoMode()) apiService.clearDemoRole();
      else await apiService.signOut();
    } catch (err) { console.error(err); }
    setIsAuthenticated(false);
    setAuthError(null);
    setRoleMismatch(null);
    setActiveTab('dashboard');
    window.history.pushState({}, '', '/access');
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  // User Notification Banner

  const [notification, setNotification] = useState<{
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
  } | null>(null);

  const showNotification = (
    message: string,
    type: 'info' | 'success' | 'warning' | 'error' = 'info'
  ) => {
    setNotification({ message, type });
    setTimeout(() => {
      setNotification((curr) => (curr?.message === message ? null : curr));
    }, 4500);
  };

  useEffect(() => {
    if (currentUser.role === 'ADMIN') return;
    if (activeTab === 'admin-users' && !roleAllows(currentUser.role, 'user_admin')) {
      setActiveTab('dashboard');
      window.history.replaceState({}, '', '/app');
    } else if (activeTab === 'admin-audit' && !roleAllows(currentUser.role, 'audit_read')) {
      setActiveTab('dashboard');
      window.history.replaceState({}, '', '/app');
    }
  }, [currentUser.role, activeTab]);

  const requirePermission = (permission: Permission): boolean => {
    if (roleAllows(currentUser.role, permission)) return true;
    showNotification(`Permission denied: ${currentUser.role} cannot perform this action.`, 'error');
    return false;
  };

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  // -------------------------------------------------------------
  // WebSocket Connection
  // -------------------------------------------------------------
  const connectWebSocket = useCallback(async () => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const token = await apiService.getAccessToken();
      const demoRole = apiService.isDemoMode() ? apiService.getDemoRole() : null;
      const configuredApiBase = String(import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '');
      const configuredWsBase = String(import.meta.env.VITE_WS_URL || '').trim().replace(/\/$/, '');
      const wsBase = configuredWsBase || (configuredApiBase
        ? configuredApiBase.replace(/^http:/i, 'ws:').replace(/^https:/i, 'wss:') + '/ws/telemetry'
        : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/telemetry`);
      const query = new URLSearchParams();
      if (token) query.set('access_token', token);
      else if (demoRole) query.set('demo_role', demoRole);
      const wsUrl = `${wsBase}${query.toString() ? `?${query.toString()}` : ''}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsOnline(true);
        setIsWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && data.clock && data.robots) {
            setTelemetry(data);
            setIsOnline(true);
            setIsWsConnected(true);
          }
        } catch (e) {
          console.error('[WebSocket] Telemetry parse error:', e);
        }
      };

      ws.onclose = () => {
        setIsWsConnected(false);
        wsRef.current = null;
        if (!reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connectWebSocket();
          }, 3500);
        }
      };

      ws.onerror = () => {
        setIsWsConnected(false);
      };

      wsRef.current = ws;
    } catch (err: any) {
      console.error('[WebSocket] Connection failed:', err);
      setIsWsConnected(false);
    }
  }, []);

  // Health probe fallback
  const checkHealth = useCallback(async () => {
    try {
      const res = await apiService.apiFetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'ONLINE') {
          setIsOnline(true);
        }
      } else {
        setIsOnline(false);
      }
    } catch (e) {
      setIsOnline(false);
    }
  }, []);

  useEffect(() => {
    if (apiService.isAuthConfigured() && !isAuthenticated) return;
    connectWebSocket();
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => {
      clearInterval(interval);
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connectWebSocket, checkHealth, isAuthenticated]);

  const handleRetryConnection = () => {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {}
      wsRef.current = null;
    }
    showNotification('Reconnecting to backend simulation...', 'info');
    checkHealth();
    connectWebSocket();
  };

  // -------------------------------------------------------------
  // Backend Control API Handlers
  // -------------------------------------------------------------
  const handleClockAction = async (action: 'pause' | 'resume' | 'step' | 'reset', scale?: number) => {
    if (!requirePermission('simulation_control')) return;
    try {
      const res = await apiService.apiFetch('/api/controls/clock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, scale }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || `HTTP ${res.status}`);
      }

      const result = await res.json();
      // Do not mutate authoritative telemetry optimistically. The next WebSocket
      // snapshot is the source of truth after the backend confirms the operation.
      if (action === 'pause') showNotification('Simulation pause confirmed by backend', 'info');
      else if (action === 'resume') showNotification('Simulation resume confirmed by backend', 'success');
      else if (action === 'step') showNotification(`Step confirmed at ${result.sim_time ?? telemetry.clock.current_time}`, 'info');
      else if (action === 'reset') showNotification('Simulation reset confirmed by backend', 'success');
      if (scale) showNotification(`Time scale update confirmed at ${result.time_scale ?? scale}x`, 'info');
    } catch (err: any) {
      console.error('[Clock Action] Error:', err);
      showNotification(`Clock action failed: ${err.message}`, 'error');
    }
  };

  const handleInjectFault = async (
    type: string,
    target: string,
    duration: number,
    parameters?: Record<string, any>
  ) => {
    if (!requirePermission('fault_injection')) return;
    try {
      const res = await apiService.apiFetch('/api/faults', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, target, duration, parameters }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || errData.error || `HTTP ${res.status}`);
      }
      showNotification(`Fault injected: ${target} — ${type}`, 'warning');
    } catch (err: any) {
      console.error('[Fault Injection] Error:', err);
      showNotification(`Fault injection failed: ${err.message}`, 'error');
      throw err;
    }
  };

  const handleClearFault = async (faultId: string) => {
    if (!requirePermission('fault_injection')) return;
    try {
      const res = await apiService.apiFetch(`/api/faults/${faultId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      showNotification(`Fault cleared: ${faultId}`, 'info');
    } catch (err: any) {
      console.error('[Clear Fault] Error:', err);
      showNotification(`Clear fault failed: ${err.message}`, 'error');
    }
  };

  const handleClearAllFaults = async () => {
    if (!requirePermission('fault_injection')) return;
    try {
      const res = await apiService.apiFetch('/api/faults/clear-all', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      showNotification('All active faults resolved', 'success');
    } catch (err: any) {
      console.error('[Clear All] Error:', err);
      showNotification(`Failed to clear faults: ${err.message}`, 'error');
    }
  };

  const handleDispatchTask = async (
    pickup: [number, number],
    delivery: [number, number],
    priority: number,
    deadline: number
  ) => {
    if (!requirePermission('task_dispatch')) return;
    try {
      const res = await apiService.apiFetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pickup, delivery, priority, deadline }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || `HTTP ${res.status}`);
      }
      const newTask = await res.json();
      setIsDispatcherOpen(false);
      const formattedTaskId = newTask.task_id?.startsWith('T') ? newTask.task_id : `T${newTask.task_id}`;
      showNotification(`Task ${formattedTaskId} dispatched`, 'success');
    } catch (err: any) {
      console.error('[Task Dispatch] Error:', err);
      showNotification(`Task dispatch failed: ${err.message}`, 'error');
    }
  };

  const handleRunScenario = async (scenarioId: string) => {
    if (!requirePermission('experiments')) return;
    try {
      showNotification(`Executing scenario ${scenarioId}...`, 'info');
      const res = await apiService.apiFetch('/api/scenarios/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || `HTTP ${res.status}`);
      }
      showNotification(`Scenario ${scenarioId} completed successfully`, 'success');
    } catch (err: any) {
      console.error('[Run Scenario] Error:', err);
      showNotification(`Scenario execution failed: ${err.message}`, 'error');
    }
  };

  const handleRestoreSnapshot = async (data: any) => {
    if (!requirePermission('destructive')) return;
    try {
      const res = await apiService.apiFetch('/api/snapshot/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || `HTTP ${res.status}`);
      }
      showNotification('Simulation snapshot restored successfully', 'success');
    } catch (err: any) {
      console.error('[Restore Snapshot] Error:', err);
      showNotification(`Snapshot restore failed: ${err.message}`, 'error');
    }
  };

  const handleRobotAction = async (action: string, robotId: string) => {
    if (!requirePermission('recovery')) return;
    try {
      if (action === 'pause') {
        const res = await apiService.apiFetch(`/api/robots/${robotId}/pause`, { method: 'POST' });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.error || `HTTP ${res.status}`);
        }
        showNotification(`Robot ${robotId} paused`, 'warning');
      } else if (action === 'resume') {
        const res = await apiService.apiFetch(`/api/robots/${robotId}/resume`, { method: 'POST' });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.error || `HTTP ${res.status}`);
        }
        showNotification(`Robot ${robotId} resumed`, 'success');
      } else if (action === 'reset') {
        const res = await apiService.apiFetch(`/api/robots/${robotId}/reset`, { method: 'POST' });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.error || `HTTP ${res.status}`);
        }
        showNotification(`Robot ${robotId} reset to home position`, 'info');
      } else if (action === 'reassign') {
        const res = await apiService.apiFetch(`/api/robots/${robotId}/reassign`, { method: 'POST' });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.error || `HTTP ${res.status}`);
        }
        const data = await res.json();
        showNotification(`Task ${data.task_id} reassigned from ${robotId} to ${data.new_robot}`, 'success');
      }
    } catch (err: any) {
      console.error(`[Robot Action: ${action}] Error:`, err);
      showNotification(`Robot ${action} failed: ${err.message}`, 'error');
    }
  };

  const handleSaveSettings = async (settings: {
    timeStep: number;
    timeScale: number;
    seed: number;
    telemetryInterval: number;
    defaultRobots: number;
    logLevel: string;
  }) => {
    if (!requirePermission('settings')) return;
    try {
      const res = await apiService.apiFetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          time_step: settings.timeStep,
          time_scale: settings.timeScale,
          seed: settings.seed,
          telemetry_interval: settings.telemetryInterval,
          default_robot_count: settings.defaultRobots,
          log_level: settings.logLevel,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || `HTTP ${res.status}`);
      }
      showNotification('Simulation settings saved and applied', 'success');
    } catch (err: any) {
      console.error('[Settings] Error:', err);
      showNotification(`Settings save failed: ${err.message}`, 'error');
    }
  };

  const selectedRobot = telemetry.robots.find((r) => r.robot_id === selectedRobotId) || null;

  if (!isAuthenticated) {
    // The public/demo package has no login screen. Users choose Admin or Observer
    // at /access; the selected demo role is then enforced by backend RBAC.
    if (window.location.pathname !== '/access') {
      window.history.replaceState({}, '', '/access');
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
    return null;
  }

  return (
    <div className="h-screen w-screen flex flex-col font-sans select-none overflow-hidden re-dashboard-active">
      {/* 1. Top Simulation Control Bar */}
      <TopBar
        isOnline={isOnline}
        isWsConnected={isWsConnected}
        simTime={telemetry.clock.current_time}
        isPaused={telemetry.clock.is_paused}
        timeScale={telemetry.clock.time_scale}
        currentUser={currentUser}
        databaseStatus={databaseStatus}
        onClockAction={handleClockAction}
        onRetry={handleRetryConnection}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onSignOut={handleSignOut}
      />


      {/* Offline Mode Banner */}
      {!isOnline && (
        <div className="bg-[#EF4444] text-white px-4 py-1 text-xs font-semibold flex items-center justify-between shadow-sm shrink-0 z-20">
          <div className="flex items-center gap-2 max-w-7xl mx-auto w-full">
            <WifiOff className="w-3.5 h-3.5" />
            <span>BACKEND OFFLINE — Simulation communication unavailable. Attempting auto-reconnect.</span>
            <button
              onClick={handleRetryConnection}
              className="ml-auto underline flex items-center gap-1 hover:text-rose-100 font-bold cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" /> Retry Connection
            </button>
          </div>
        </div>
      )}

      {/* Floating Notification Toast */}
      {notification && (
        <div
          className={`fixed bottom-4 right-4 z-50 flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg border text-xs font-medium shadow-2xl animate-in slide-in-from-bottom-2 duration-150 ${
            notification.type === 'success'
              ? 'bg-[#151A21] border-[#22C55E]/40 text-[#22C55E]'
              : notification.type === 'error'
              ? 'bg-[#151A21] border-[#EF4444]/40 text-[#EF4444]'
              : notification.type === 'warning'
              ? 'bg-[#151A21] border-[#F59E0B]/40 text-[#F59E0B]'
              : 'bg-[#151A21] border-[#1683E8]/40 text-[#1683E8]'
          }`}
        >
          {notification.type === 'success' && <CheckCircle2 className="w-4 h-4 shrink-0" />}
          {notification.type === 'error' && <AlertCircle className="w-4 h-4 shrink-0" />}
          {notification.type === 'warning' && <AlertCircle className="w-4 h-4 shrink-0" />}
          {notification.type === 'info' && <Info className="w-4 h-4 shrink-0" />}
          <span>{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            className="ml-2 hover:opacity-75 cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 2. Main Workspace Layout: Sidebar + Content */}
      <div className="flex-1 flex overflow-hidden re-dashboard-workspace">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={handleTabSelect}
          isOnline={isOnline}
          isWsConnected={isWsConnected}
          isSimulationRunning={isOnline && !telemetry.clock.is_paused}
          currentUserRole={currentUser.role}
          databaseStatus={databaseStatus}
        />

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-3.5 space-y-3.5 bg-[#0F1115]">
          {/* DASHBOARD VIEW */}
          {activeTab === 'dashboard' && (
            <div className="space-y-3.5 max-w-[1720px] mx-auto re-dashboard-page">
              {/* Row 1: KPI Cards Strip */}
              <KpiCards
                robots={telemetry.robots}
                tasks={telemetry.tasks}
                faults={telemetry.faults}
                resilienceState={telemetry.resilience.current_state}
                metrics={telemetry.metrics}
                isOnline={isOnline}
              />

              {/* Row 2: Central Simulation Map (Left) + Right Status Panels */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
                {/* Central Simulation Map (approx 7.8/12 cols) */}
                <div className="lg:col-span-8 flex flex-col">
                  <SimulationMap
                    world={telemetry.world}
                    robots={telemetry.robots}
                    tasks={telemetry.tasks}
                    selectedRobotId={selectedRobotId}
                    onSelectRobot={setSelectedRobotId}
                    onSelectTask={(tid) => {
                      const t = telemetry.tasks.find((x) => x.task_id === tid);
                      if (t) setSelectedTask(t);
                    }}
                  />
                </div>

                {/* Right Stack: Robot Status & Current Tasks (approx 4.2/12 cols) */}
                <div className="lg:col-span-4 flex flex-col gap-3.5">
                  <RobotStatusPanel
                    robots={telemetry.robots}
                    tasks={telemetry.tasks}
                    selectedRobotId={selectedRobotId}
                    onSelectRobot={(id) => setSelectedRobotId(id)}
                    onViewAll={() => setActiveTab('fleet')}
                  />

                  <CurrentTasksPanel
                    tasks={telemetry.tasks}
                    robots={telemetry.robots}
                    onOpenDispatcher={() => setIsDispatcherOpen(true)}
                    onSelectTask={(task) => setSelectedTask(task)}
                  />
                </div>
              </div>

              {/* Row 3: Bottom Panels (Resilience State Machine | Incident Timeline | Fault Injection) */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                {/* Resilience State Machine */}
                <div>
                  <ResilienceStateMachine
                    currentState={telemetry.resilience.current_state}
                    incidents={telemetry.incidents}
                  />
                </div>

                {/* Incident Timeline */}
                <div>
                  <IncidentTimelinePanel incidents={telemetry.incidents} />
                </div>

                {/* Fault Injection */}
                <div>
                  <FaultInjectionPanel
                    activeFaults={telemetry.faults}
                    robots={telemetry.robots}
                    currentUserRole={currentUser.role}
                    onInjectFault={handleInjectFault}
                    onClearFault={handleClearFault}
                    onClearAll={handleClearAllFaults}
                  />
                </div>
              </div>
            </div>
          )}

          {/* SIMULATION FULL VIEW */}
          {activeTab === 'simulation' && (
            <div className="h-[calc(100vh-85px)] flex flex-col gap-4">
              <SimulationMap
                world={telemetry.world}
                robots={telemetry.robots}
                tasks={telemetry.tasks}
                selectedRobotId={selectedRobotId}
                onSelectRobot={setSelectedRobotId}
              />
            </div>
          )}

          {/* FLEET VIEW */}
          {activeTab === 'fleet' && (
            <div className="space-y-4 max-w-6xl mx-auto">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-[#E5E7EB]">Fleet Overview & Telemetry</h2>
                  <p className="text-xs text-[#9CA3AF]">Detailed telemetry stream for all deployed warehouse robots</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {telemetry.robots.map((robot) => (
                  <div
                    key={robot.robot_id}
                    onClick={() => setSelectedRobotId(robot.robot_id)}
                    className="bg-[#151A21] border border-[#29323D] rounded-xl p-4 space-y-3 cursor-pointer hover:border-[#1683E8] transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-base font-bold text-[#E5E7EB]">{robot.robot_id}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 uppercase">
                        {robot.state}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                      <div className="bg-[#0F1115] p-2 rounded border border-[#29323D]">
                        <span className="text-[10px] text-[#6B7280] block">Position</span>
                        [{robot.position[0]}, {robot.position[1]}]
                      </div>
                      <div className="bg-[#0F1115] p-2 rounded border border-[#29323D]">
                        <span className="text-[10px] text-[#6B7280] block">Battery</span>
                        {Math.round(robot.battery)}%
                      </div>
                    </div>
                    <div className="text-xs text-[#9CA3AF]">
                      Task: <strong className="text-[#E5E7EB] font-mono">{robot.current_task || 'None'}</strong>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TASKS VIEW */}
          {activeTab === 'tasks' && (
            <div className="space-y-4 max-w-6xl mx-auto">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-[#E5E7EB]">Task Dispatcher & Tracking</h2>
                  <p className="text-xs text-[#9CA3AF]">Manage warehouse delivery jobs, assign priority levels and track progress</p>
                </div>
                <button
                  onClick={() => setIsDispatcherOpen(true)}
                  className="px-3 py-1.5 bg-[#1683E8] hover:bg-[#2B95F5] text-white rounded-lg text-xs font-semibold cursor-pointer shadow-sm"
                >
                  + Dispatch New Task
                </button>
              </div>
              <CurrentTasksPanel
                tasks={telemetry.tasks}
                robots={telemetry.robots}
                onOpenDispatcher={() => setIsDispatcherOpen(true)}
                onSelectTask={(t) => setSelectedTask(t)}
              />
            </div>
          )}

          {/* FAULT INJECTION VIEW */}
          {activeTab === 'faults' && (
            <div className="space-y-4 max-w-4xl mx-auto">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-[#E5E7EB]">Chaos Engineering & Fault Injection Testbed</h2>
                  <p className="text-xs text-[#9CA3AF]">Inject hardware anomalies, network degradation, and environmental obstacles</p>
                </div>
              </div>
              <FaultInjectionPanel
                activeFaults={telemetry.faults}
                robots={telemetry.robots}
                currentUserRole={currentUser.role}
                onInjectFault={handleInjectFault}
                onClearFault={handleClearFault}
                onClearAll={handleClearAllFaults}
              />
            </div>
          )}

          {/* INCIDENTS VIEW */}
          {activeTab === 'incidents' && (
            <div className="space-y-4 max-w-5xl mx-auto">
              <h2 className="text-lg font-bold text-[#E5E7EB]">Incident Audit Log</h2>
              <IncidentTimelinePanel incidents={telemetry.incidents} />
            </div>
          )}

          {/* RECOVERY VIEW */}
          {activeTab === 'recovery' && (
            <div className="space-y-4 max-w-5xl mx-auto">
              <h2 className="text-lg font-bold text-[#E5E7EB]">Resilience & Recovery State Analysis</h2>
              <ResilienceStateMachine
                currentState={telemetry.resilience.current_state}
                incidents={telemetry.incidents}
              />
            </div>
          )}

          {/* EXPERIMENTS VIEW */}
          {activeTab === 'experiments' && (
            <div className="space-y-4 max-w-5xl mx-auto">
              <ExperimentsRunner
                onRunScenario={handleRunScenario}
                currentUserRole={currentUser.role}
                currentRunningScenario={null}
              />
            </div>
          )}

          {/* METRICS VIEW */}
          {activeTab === 'metrics' && (
            <div className="space-y-4 max-w-6xl mx-auto">
              <MetricsDashboard
                metrics={telemetry.metrics}
                robots={telemetry.robots}
                tasks={telemetry.tasks}
                simTime={telemetry.clock.current_time}
              />
            </div>
          )}

          {/* BASELINE COMPARISON VIEW */}
          {activeTab === 'baseline' && (
            <div className="space-y-4 max-w-5xl mx-auto">
              <BaselineComparison currentMetrics={telemetry.metrics} />
            </div>
          )}

          {/* NETWORK VIEW */}
          {activeTab === 'network' && (
            <div className="space-y-4 max-w-5xl mx-auto">
              <NetworkTopologyView
                robots={telemetry.robots}
                network={telemetry.network}
              />
            </div>
          )}

          {/* DATABASE VIEW */}
          {activeTab === 'database' && (
            <div className="space-y-4 max-w-6xl mx-auto">
              <DatabaseDashboard
                currentUserRole={currentUser.role}
                isOnline={isOnline}
                onNotification={(msg, type) => showNotification(msg, type)}
              />
            </div>
          )}

          {/* SETTINGS / BACKUP VIEW */}
          {activeTab === 'admin-users' && roleAllows(currentUser.role, 'user_admin') && (
            <AdminConsole section="users" />
          )}

          {activeTab === 'admin-audit' && roleAllows(currentUser.role, 'audit_read') && (
            <AdminConsole section="audit" />
          )}

          {activeTab === 'settings' && (
            <div className="space-y-4 max-w-5xl mx-auto">
              <BackupManager
                telemetry={telemetry}
                onRestoreSnapshot={handleRestoreSnapshot}
                currentUserRole={currentUser.role}
                isOnline={isOnline}
              />
            </div>
          )}
        </main>

      </div>

      {/* Robot Detail Drawer (Slide-out) */}
      <RobotDetailDrawer
        robot={selectedRobot}
        currentUserRole={currentUser.role}
        onClose={() => setSelectedRobotId(null)}
        onAction={handleRobotAction}
      />

      {/* Task Detail Drawer (Slide-out) */}
      <TaskDetailDrawer
        task={selectedTask}
        robots={telemetry.robots}
        currentUserRole={currentUser.role}
        onClose={() => setSelectedTask(null)}
        onReassignTask={async (taskId) => {
          if (!requirePermission('task_dispatch')) return;
          try {
            const res = await apiService.apiFetch(`/api/tasks/${taskId}/reassign`, { method: 'POST' });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
              throw new Error(data.detail || data.error || `HTTP ${res.status}`);
            }
            showNotification(`Task ${taskId} reassigned from ${data.previous_robot} to ${data.new_robot}`, 'success');
            setSelectedTask(null);
          } catch (err: any) {
            console.error(`[Task Reassign: ${taskId}] Error:`, err);
            showNotification(`Task reassignment failed: ${err.message}`, 'error');
          }
        }}
        onAssignTask={async (taskId, robotId) => {
          if (!requirePermission('task_dispatch')) return;
          try {
            const res = await apiService.apiFetch(`/api/tasks/${taskId}/assign`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ robot_id: robotId }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
              throw new Error(data.detail || data.error || `HTTP ${res.status}`);
            }
            showNotification(`Task ${taskId} assigned to ${robotId}`, 'success');
            setSelectedTask(null);
          } catch (err: any) {
            showNotification(`Task assignment failed: ${err.message}`, 'error');
          }
        }}
        onCancelTask={async (taskId) => {
          if (!requirePermission('task_dispatch')) return;
          try {
            const res = await apiService.apiFetch(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
            if (!res.ok) {
              const err = await res.json().catch(() => ({}));
              throw new Error(err.detail || err.error || `HTTP ${res.status}`);
            }
            showNotification(`Task ${taskId} cancelled`, 'warning');
            setSelectedTask(null);
          } catch (err: any) {
            showNotification(`Task cancellation failed: ${err.message}`, 'error');
          }
        }}
      />

      {/* Task Dispatcher Modal */}
      {isDispatcherOpen && (
        <TaskDispatcherModal
          tasks={telemetry.tasks}
          onDispatchTask={handleDispatchTask}
          currentUserRole={currentUser.role}
          pickupStations={telemetry.world.pickup_stations}
          deliveryStations={telemetry.world.delivery_stations}
        />
      )}

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        timeScale={telemetry.clock.time_scale}
        onSave={handleSaveSettings}
      />
    </div>
  );
}
