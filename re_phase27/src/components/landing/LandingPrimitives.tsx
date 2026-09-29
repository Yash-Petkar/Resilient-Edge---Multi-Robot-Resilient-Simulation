import React from 'react';
import { ArrowRight, CheckCircle2, CircleAlert, Network, Play, Radio, RotateCcw, ShieldCheck, Square, Wifi, Zap } from 'lucide-react';

export const DemoBadge = ({ children = 'Demo Data' }: { children?: React.ReactNode }) => (
  <span className="landing-demo-badge">{children}</span>
);

export const SectionHeading = ({ eyebrow, title, description, id }: { eyebrow?: string; title: string; description?: string; id?: string }) => (
  <div id={id} className="landing-section-heading">
    {eyebrow && <div className="landing-eyebrow">{eyebrow}</div>}
    <h2>{title}</h2>
    {description && <p>{description}</p>}
  </div>
);

export const MiniChart = ({ kind = 'line' }: { kind?: 'line' | 'bars' | 'network' }) => {
  if (kind === 'network') {
    return <div className="landing-mini-network"><span>R-01</span><i /><span>R-02</span><i /><span>R-03</span><i /><span>R-04</span></div>;
  }
  if (kind === 'bars') return <div className="landing-bars">{[48, 72, 58, 84, 65, 91, 74].map((h, i) => <span key={i} style={{ height: `${h}%` }} />)}</div>;
  return <div className="landing-sparkline"><svg viewBox="0 0 300 80" preserveAspectRatio="none"><path d="M0 55 C25 48,35 60,55 50 S90 45,110 52 S145 35,165 44 S195 28,215 38 S250 25,270 34 S290 18,300 24" fill="none" stroke="currentColor" strokeWidth="3" /></svg></div>;
};

export const StatusPill = ({ tone = 'success', children }: { tone?: 'success' | 'warning' | 'error' | 'info'; children: React.ReactNode }) => (
  <span className={`landing-status landing-status-${tone}`}><span />{children}</span>
);

export const RobotPreview = ({ id, state, battery, task, position, tone }: { id: string; state: string; battery: number; task: string; position: string; tone: 'success' | 'warning' | 'error' }) => (
  <div className="landing-robot-card">
    <div className="landing-robot-card-head"><strong>{id}</strong><StatusPill tone={tone}>{state}</StatusPill></div>
    <div className="landing-robot-icon"><span className="landing-wheel left" /><span className="landing-wheel right" /><span className="landing-rover-body" /><span className="landing-rover-sensor" /></div>
    <div className="landing-robot-meta"><span>Battery</span><b>{battery}%</b></div>
    <div className="landing-progress"><i style={{ width: `${battery}%` }} /></div>
    <div className="landing-robot-meta"><span>Task</span><b>{task}</b></div>
    <div className="landing-robot-meta"><span>Position</span><code>{position}</code></div>
  </div>
);

export const DashboardPreview = () => (
  <div className="landing-dashboard-preview">
    <div className="landing-preview-toolbar"><span /><span /><span /><b>RESILIENTEDGE / CONTROL</b><em>LIVE DEMO</em></div>
    <div className="landing-preview-body">
      <aside><div className="landing-preview-logo">RE</div>{['Dashboard','Robots','Telemetry','Tasks','Network','Recovery'].map((x, i) => <span className={i === 0 ? 'active' : ''} key={x}>{x}</span>)}</aside>
      <main>
        <div className="landing-preview-title"><div><b>Fleet Overview</b><small>Illustrative telemetry workspace</small></div><StatusPill>System Online</StatusPill></div>
        <div className="landing-preview-kpis"><div><small>Total Robots</small><b>3</b><span>All connected</span></div><div><small>Active Tasks</small><b>12</b><span>8 running</span></div><div><small>Network Health</small><b>98.7%</b><span>Nominal</span></div></div>
        <div className="landing-preview-grid"><div className="landing-preview-map"><div className="map-grid" /><span className="map-robot r1">R-01</span><span className="map-robot r2">R-02</span><span className="map-robot r3">R-03</span><svg viewBox="0 0 500 230"><path d="M50 180 C130 130,120 70,220 105 S300 180,380 110 S420 70,470 40" fill="none" stroke="#2563EB" strokeWidth="3" strokeDasharray="8 7" /></svg></div><div className="landing-preview-events"><b>System Events</b><div><CheckCircle2 /> Task reassigned successfully</div><div><CircleAlert /> Network latency elevated</div><div><Radio /> Telemetry stream synchronized</div><div><ShieldCheck /> Recovery completed</div></div></div>
      </main>
    </div>
  </div>
);

export const ControlRow = ({ label, active = true }: { label: string; active?: boolean }) => <div className="landing-control-row"><span>{label}</span><b className={active ? 'on' : ''}>{active ? 'ON' : 'OFF'}</b></div>;

export const ArrowLink = ({ children }: { children: React.ReactNode }) => <span className="landing-arrow-link">{children}<ArrowRight size={15} /></span>;

export const PreviewLegend = ({ children }: { children: React.ReactNode }) => <div className="landing-preview-legend">{children}</div>;
