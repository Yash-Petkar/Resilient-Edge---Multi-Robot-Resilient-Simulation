import React, { useEffect, useState } from 'react';
import { ShieldCheck, Users, ScrollText, RefreshCw, Save } from 'lucide-react';
import { UserRole } from '../../types';
import { apiService } from '../../services/apiService';

interface AdminUser { id: string; email: string; full_name: string | null; role: UserRole; created_at?: string; updated_at?: string; }
interface AuditLog { log_id: string; user_id: string | null; user_role: string | null; action: string; entity_type: string | null; entity_id: string | null; metadata: Record<string, unknown> | null; created_at: string; }

const roles: UserRole[] = ['ADMIN', 'OPERATOR', 'OBSERVER', 'VIEWER'];
const label = (role: UserRole) => role === 'ADMIN' ? 'Administrator' : role === 'OPERATOR' ? 'Operator' : role === 'OBSERVER' ? 'Observer' : 'Viewer';

export const AdminConsole: React.FC<{ section?: 'users' | 'audit' }> = ({ section = 'users' }) => {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      if (section === 'users') {
        const u = await apiService.apiFetch('/api/admin/users');
        if (!u.ok) throw new Error('Users request failed (' + u.status + ')');
        setUsers((await u.json()).users || []);
      }
      const a = await apiService.apiFetch('/api/admin/audit');
      if (!a.ok) throw new Error('Audit request failed (' + a.status + ')');
      setLogs((await a.json()).logs || []);
    } catch (e: any) { setError(e.message || 'Unable to load administration data'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const changeRole = async (user: AdminUser, role: UserRole) => {
    if (role === user.role) return;
    setSaving(user.id); setError(null);
    try {
      const response = await apiService.apiFetch(`/api/admin/users/${encodeURIComponent(user.id)}/role`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || `Role update failed (${response.status})`);
      setUsers((current) => current.map((item) => item.id === user.id ? { ...item, role } : item));
      await load();
    } catch (e: any) { setError(e.message || 'Role update failed'); }
    finally { setSaving(null); }
  };

  return <div className="max-w-[1500px] mx-auto space-y-4">
    <div className="flex items-center justify-between"><div><div className="text-[10px] uppercase tracking-widest text-[#64748B]">Administration</div><h1 className="text-xl font-semibold mt-1">{section === 'users' ? 'Users & Roles' : 'Audit Log'}</h1></div><button onClick={load} disabled={loading} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[#29323D] bg-[#151A21] text-xs hover:bg-[#1B222B] disabled:opacity-50"><RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh</button></div>
    {error && <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 text-[#FCA5A5] text-xs px-3 py-2.5">{error}</div>}
    {section === 'users' ? <div className="rounded-xl border border-[#29323D] bg-[#0B1016] overflow-hidden"><div className="px-4 py-3 border-b border-[#29323D] flex items-center gap-2"><Users className="w-4 h-4 text-[#4DB4FF]" /><span className="text-xs font-semibold">Accounts</span></div><div className="overflow-x-auto"><table className="w-full text-xs"><thead className="bg-[#0F1115] text-[#64748B]"><tr><th className="text-left px-4 py-3">Name</th><th className="text-left px-4 py-3">Email</th><th className="text-left px-4 py-3">Role</th><th className="text-left px-4 py-3">Created</th></tr></thead><tbody>{users.map((user) => <tr key={user.id} className="border-t border-[#29323D]"><td className="px-4 py-3 text-[#E5E7EB]">{user.full_name || 'Unnamed user'}</td><td className="px-4 py-3 text-[#94A3B8]">{user.email}</td><td className="px-4 py-3"><select value={user.role} disabled={saving === user.id} onChange={(e) => changeRole(user, e.target.value as UserRole)} className="bg-[#151A21] border border-[#29323D] rounded-md px-2 py-1.5 text-xs text-[#E5E7EB] outline-none focus:border-[#1683E8]">{roles.map((role) => <option key={role} value={role}>{label(role)}</option>)}</select>{saving === user.id && <Save className="inline ml-2 w-3 h-3 text-[#4DB4FF] animate-pulse" />}</td><td className="px-4 py-3 text-[#64748B]">{user.created_at ? new Date(user.created_at).toLocaleString() : '—'}</td></tr>)}</tbody></table></div></div> : <div className="rounded-xl border border-[#29323D] bg-[#0B1016] overflow-hidden"><div className="px-4 py-3 border-b border-[#29323D] flex items-center gap-2"><ScrollText className="w-4 h-4 text-[#4DB4FF]" /><span className="text-xs font-semibold">Security & Operations Audit</span></div><div className="divide-y divide-[#29323D]">{logs.map((log) => <div key={log.log_id} className="px-4 py-3 flex items-start gap-3"><ShieldCheck className="w-4 h-4 mt-0.5 text-[#64748B]" /><div className="min-w-0"><div className="text-xs font-semibold text-[#E5E7EB]">{log.action}</div><div className="text-[11px] text-[#64748B] mt-1">{log.entity_type || 'system'} {log.entity_id ? `• ${log.entity_id}` : ''} • {new Date(log.created_at).toLocaleString()}</div></div></div>)}{!logs.length && <div className="px-4 py-8 text-center text-xs text-[#64748B]">No audit entries returned.</div>}</div></div>}
  </div>;
};
