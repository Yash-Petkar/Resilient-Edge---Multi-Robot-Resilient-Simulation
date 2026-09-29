import React, { useState } from 'react';
import { ArrowRight, Menu, X } from 'lucide-react';

const links = [['Home','home'],['Features','features'],['Simulation','simulation'],['Telemetry','telemetry'],['Use Cases','use-cases'],['Technology','technology'],['About','about']];

export const Navbar = () => {
  const [open, setOpen] = useState(false);
  const goAccess = () => { window.history.pushState({}, '', '/access'); window.dispatchEvent(new PopStateEvent('popstate')); };
  return <header className="landing-navbar"><div className="landing-container landing-nav-inner">
    <a className="landing-brand" href="#home" onClick={() => setOpen(false)}><span className="landing-brand-mark">RE</span><span><strong>Resilient<span>Edge</span></strong><small>Autonomous Robotics Platform</small></span></a>
    <nav className="landing-nav-links">{links.map(([label,id]) => <a key={id} href={`#${id}`}>{label}</a>)}</nav>
    <div className="landing-nav-actions"><button className="landing-btn landing-btn-secondary landing-demo-btn" onClick={() => document.getElementById('simulation')?.scrollIntoView({behavior:'smooth'})}>View Demo</button><button className="landing-btn landing-btn-primary" onClick={goAccess}>Access System <ArrowRight size={15}/></button><button className="landing-menu" onClick={() => setOpen(v=>!v)} aria-label="Toggle menu">{open ? <X/> : <Menu/>}</button></div>
  </div>{open && <nav className="landing-mobile-nav">{links.map(([label,id]) => <a key={id} href={`#${id}`} onClick={() => setOpen(false)}>{label}</a>)}<button className="landing-btn landing-btn-primary" onClick={goAccess}>Access System <ArrowRight size={15}/></button></nav>}</header>;
};
