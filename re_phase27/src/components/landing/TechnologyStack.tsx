import React from 'react';
import { Cpu, Database, FlaskConical, Globe2, RadioTower, ServerCog } from 'lucide-react';
import { SectionHeading } from './LandingPrimitives';
const stack=[['ROS 2','Robot Middleware',RadioTower],['Gazebo','3D Simulation',Globe2],['Python','Core Simulation',Cpu],['FastAPI','Backend REST & WS',ServerCog],['React','Frontend Dashboard',Globe2],['SQLite','Data Storage',Database]] as const;
export const TechnologyStack=()=> <section id="technology" className="landing-section landing-section-alt"><div className="landing-container"><SectionHeading title="Technology Stack" description="Built on robust, industry-standard robotics and software technologies"/><div className="landing-tech-grid">{stack.map(([name,desc,Icon])=><div className="landing-tech-card" key={name}><Icon/><b>{name}</b><span>{desc}</span></div>)}</div></div></section>;
