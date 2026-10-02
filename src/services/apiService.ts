import { resolveDemoMode } from '../config/demoMode';

export type UserRole = 'ADMIN' | 'OPERATOR' | 'OBSERVER' | 'VIEWER';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  avatar_url?: string;
}

export interface DatabaseStatus {
  provider: 'local' | 'error';
  connected: boolean;
  database: 'local' | 'unknown';
  status: 'online' | 'offline' | 'error';
  storage_mode?: string;
  last_success_at?: number | null;
  last_error?: string | null;
}

const TOKEN_KEY = 'resilientedge.access_token';

// Production: set VITE_API_BASE_URL to the public FastAPI origin.
// Local development: leave it empty and the existing Node proxy handles /api/*.
const API_BASE_URL = String(import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '');

function resolveApiUrl(input: RequestInfo | URL): RequestInfo | URL {
  if (!API_BASE_URL) return input;
  if (input instanceof URL) return new URL(input.toString(), API_BASE_URL);
  if (typeof input === 'string') {
    if (/^https?:\/\//i.test(input)) return input;
    return `${API_BASE_URL}${input.startsWith('/') ? input : `/${input}`}`;
  }
  return input;
}

class ApiService {
  private currentUser: UserProfile = {
    id: '', email: '', full_name: '', role: 'OBSERVER',
  };
  private databaseStatus: DatabaseStatus = {
    provider: 'local', connected: false, database: 'unknown', status: 'offline',
  };
  private backendDemoMode: boolean | null = null;

  public isAuthConfigured(): boolean { return true; }

  /** Single authoritative frontend switch. Never hard-code demo mode. */
  public isDemoMode(): boolean {
    return resolveDemoMode(import.meta.env.VITE_DEMO_MODE);
  }

  /** Returns a human-readable deployment mismatch, if backend health has reported its mode. */
  public getModeMismatch(): string | null {
    if (this.backendDemoMode === null) return null;
    if (this.isDemoMode() === this.backendDemoMode) return null;
    return `Configuration mismatch: frontend VITE_DEMO_MODE=${this.isDemoMode()} but backend DEMO_MODE=${this.backendDemoMode}.`;
  }

  public getDemoRole(): UserRole | null {
    const role = localStorage.getItem('resilientedge.demo_role');
    return role === 'ADMIN' || role === 'OPERATOR' || role === 'OBSERVER' || role === 'VIEWER' ? role : null;
  }

  public setDemoRole(role: UserRole) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('resilientedge.refresh_token');
    localStorage.setItem('resilientedge.demo_role', role);
    this.currentUser = {
      id: `demo-${role.toLowerCase()}`,
      email: 'demo@resilientedge.local',
      full_name: `Demo ${role === 'ADMIN' ? 'Administrator' : role.charAt(0) + role.slice(1).toLowerCase()}`,
      role,
    };
  }

  public clearDemoRole() {
    localStorage.removeItem('resilientedge.demo_role');
    this.currentUser = { id: '', email: '', full_name: '', role: 'OBSERVER' };
  }

  public getCurrentUser(): UserProfile { return this.currentUser; }

  public getAccessToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  public getSession() {
    const token = this.getAccessToken();
    return token ? { access_token: token } : null;
  }

  public async signIn(email: string, password: string) {
    const response = await fetch(resolveApiUrl('/api/auth/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || 'Authentication failed');
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem('resilientedge.refresh_token', data.refresh_token);
    this.currentUser = data.user;
    return { access_token: data.access_token, user: data.user };
  }

  public async signOut() {
    try { await this.apiFetch('/api/auth/logout', { method: 'POST' }); } finally {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem('resilientedge.refresh_token');
      this.currentUser = { id: '', email: '', full_name: '', role: 'OBSERVER' };
    }
  }

  public async restoreSession(): Promise<UserProfile | null> {
    if (!this.getAccessToken()) return null;
    let response = await fetch(resolveApiUrl('/api/auth/me'), { headers: { Authorization: `Bearer ${this.getAccessToken()}` } });
    if (response.status === 401) {
      const refreshToken = localStorage.getItem('resilientedge.refresh_token');
      if (refreshToken) {
        const refreshed = await fetch(resolveApiUrl('/api/auth/refresh'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) });
        if (refreshed.ok) {
          const data = await refreshed.json();
          localStorage.setItem(TOKEN_KEY, data.access_token);
          localStorage.setItem('resilientedge.refresh_token', data.refresh_token);
          response = await fetch(resolveApiUrl('/api/auth/me'), { headers: { Authorization: `Bearer ${data.access_token}` } });
        }
      }
    }
    if (!response.ok) { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem('resilientedge.refresh_token'); return null; }
    const user = await response.json(); this.currentUser = user; return user;
  }

  public onAuthStateChange(_callback: (session: any) => void) {
    // Local JWT auth has no external auth event stream. Auth is restored explicitly on startup.
    return { data: { subscription: { unsubscribe() {} } } };
  }

  public async apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
    const makeRequest = () => {
      const headers = new Headers(init.headers || {});
      const token = this.getAccessToken();
      if (token) headers.set('Authorization', `Bearer ${token}`);
      else if (this.isDemoMode()) {
        const demoRole = this.getDemoRole();
        if (demoRole) headers.set('X-Demo-Role', demoRole);
      }
      return fetch(resolveApiUrl(input), { ...init, headers });
    };
    let response = await makeRequest();
    if (response.status === 401 && !String(input).includes('/api/auth/')) {
      const refreshToken = localStorage.getItem('resilientedge.refresh_token');
      if (refreshToken) {
        const refreshed = await fetch(resolveApiUrl('/api/auth/refresh'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) });
        if (refreshed.ok) {
          const data = await refreshed.json();
          localStorage.setItem(TOKEN_KEY, data.access_token);
          localStorage.setItem('resilientedge.refresh_token', data.refresh_token);
          response = await makeRequest();
        }
      }
    }
    if (response.status === 401 && !String(input).includes('/api/auth/login')) {
      localStorage.removeItem(TOKEN_KEY); localStorage.removeItem('resilientedge.refresh_token');
      this.currentUser = { id: '', email: '', full_name: '', role: 'OBSERVER' };
    }
    return response;
  }

  public async checkConnection(): Promise<boolean> {
    try {
      const response = await this.apiFetch('/api/health', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const health = await response.json();
      this.backendDemoMode = Boolean(health.demo_mode);
      this.databaseStatus = {
        provider: health.database === 'sqlite' ? 'local' : 'error',
        connected: health.database === 'sqlite' && health.database_status === 'online',
        database: health.database === 'sqlite' ? 'local' : 'unknown',
        status: health.database === 'sqlite' && health.database_status === 'online' ? 'online' : 'error',
        storage_mode: health.storage_mode,
        last_success_at: health.persistence?.last_success_at ?? null,
        last_error: health.persistence?.last_error ?? null,
      };
      return this.databaseStatus.connected;
    } catch (err: any) {
      this.databaseStatus = { provider: 'error', connected: false, database: 'unknown', status: 'offline', last_error: err?.message || 'Backend unavailable' };
      return false;
    }
  }

  public getStatus() {
    const label = this.databaseStatus.connected
      ? 'LOCAL DATABASE ONLINE'
      : this.databaseStatus.status === 'error'
        ? 'DATABASE ERROR'
        : 'LOCAL DATABASE OFFLINE';
    return {
      isConfigured: true,
      isConnected: this.databaseStatus.connected,
      database: this.databaseStatus.database,
      databaseHealth: this.databaseStatus.status,
      queueLength: 0,
      currentUser: this.currentUser,
      statusLabel: label,
    };
  }

  public setCurrentUserRole(role: UserRole) { this.currentUser = { ...this.currentUser, role }; }
  public canMutate(): boolean { return this.currentUser.role === 'ADMIN' || this.currentUser.role === 'OPERATOR'; }
  public canAdminister(): boolean { return this.currentUser.role === 'ADMIN'; }

  public async fetchDatabaseStats() {
    const res = await this.apiFetch('/api/database/stats');
    if (!res.ok) throw new Error(`Database stats failed (${res.status})`);
    return res.json();
  }
}

export const apiService = new ApiService();
