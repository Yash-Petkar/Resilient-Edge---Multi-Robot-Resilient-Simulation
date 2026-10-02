import React, { useEffect, useState } from 'react';
import { Activity, ArrowLeft, ArrowRight, Eye, ShieldCheck } from 'lucide-react';
import { apiService } from '../services/apiService';
import { UserRole } from '../types';
import '../styles/access.css';

const ROLES: Array<{
  role: UserRole;
  title: string;
  description: string;
  capabilities: string[];
  Icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
}> = [
  {
    role: 'ADMIN',
    title: 'Admin',
    description: 'Full control of the ResilientEdge platform, simulation, recovery, and configuration.',
    capabilities: ['Fleet control', 'Task dispatch', 'Fault injection', 'Recovery', 'Experiments', 'Settings'],
    Icon: ShieldCheck,
  },
  {
    role: 'OBSERVER',
    title: 'Observer',
    description: 'Read-only access to fleet state, telemetry, incidents, network health, and experiment results.',
    capabilities: ['Dashboard', 'Fleet monitoring', 'Telemetry', 'Incidents', 'Metrics', 'Network status'],
    Icon: Eye,
  },
];

export default function AccessPage() {
  const [selectedRole, setSelectedRole] = useState<UserRole>('ADMIN');
  const [configurationError, setConfigurationError] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let active = true;
    const check = async () => {
      await apiService.checkConnection();
      if (!active) return;
      setConfigurationError(apiService.getModeMismatch());
      setChecking(false);
    };
    check();
    return () => { active = false; };
  }, []);

  const enter = () => {
    if (configurationError || checking) return;
    apiService.setDemoRole(selectedRole);
    window.history.pushState({}, '', '/app');
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  const goBack = () => {
    window.history.pushState({}, '', '/');
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  return (
    <div className="access-page">
      <div className="access-grid" />
      <header className="access-header">
        <button type="button" className="access-brand" onClick={goBack} aria-label="Return to ResilientEdge home">
          <span className="access-brand-mark">RE</span>
          <span>
            <strong>Resilient<span>Edge</span></strong>
            <small>Autonomous Robotics Platform</small>
          </span>
        </button>
        <button type="button" className="access-back" onClick={goBack}>
          <ArrowLeft size={15} /> Back to platform
        </button>
      </header>

      <main className="access-main">
        <div className="access-kicker"><Activity size={14} /> DIRECT DEMO ACCESS</div>
        <h1>Select your access mode</h1>
        <p className="access-lead">
          No username or password is required for this local/demo deployment. Select the workspace you want to enter.
        </p>

        {configurationError && (
          <div className="access-error" role="alert">
            <strong>Demo access is unavailable.</strong>
            <span>{configurationError}</span>
            <small>Set DEMO_MODE=true and VITE_DEMO_MODE=true for the direct Admin/Observer flow.</small>
          </div>
        )}

        <section className="access-role-grid" aria-label="Access modes">
          {ROLES.map(({ role, title, description, capabilities, Icon }) => {
            const selected = selectedRole === role;
            return (
              <button
                key={role}
                type="button"
                className={`access-role-card ${selected ? 'selected' : ''}`}
                onClick={() => setSelectedRole(role)}
                aria-pressed={selected}
              >
                <div className="access-role-top">
                  <span className="access-role-icon"><Icon size={25} strokeWidth={1.8} /></span>
                  {selected && <span className="access-selected">Selected</span>}
                </div>
                <h2>{title}</h2>
                <p>{description}</p>
                <div className="access-capabilities">
                  {capabilities.map((item) => <span key={item}>{item}</span>)}
                </div>
                <span className="access-role-arrow"><ArrowRight size={18} /></span>
              </button>
            );
          })}
        </section>

        <button type="button" className="access-enter" onClick={enter} disabled={checking || Boolean(configurationError)}>
          {checking ? 'Checking platform…' : `Continue as ${selectedRole === 'ADMIN' ? 'Admin' : 'Observer'}`}
          <ArrowRight size={17} />
        </button>

        <div className="access-note">
          <span className="access-status-dot" /> Backend RBAC remains enforced for the selected demo role.
        </div>
      </main>
    </div>
  );
}
