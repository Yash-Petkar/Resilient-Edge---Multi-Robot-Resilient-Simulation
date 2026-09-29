import React from 'react';
import { Boxes, GitBranch, HeartPulse, Network, Radio, Scaling } from 'lucide-react';
import { SectionHeading } from './LandingPrimitives';
const features = [
 ['Multi-Robot Simulation','Realistic 2D/3D environments with ROS 2 + Gazebo integration for physics-aware dynamics.',Boxes],
 ['Resilient Task Allocation','Intelligent task assignment with auction mechanics, dynamic reassignment, and conflict handling.',GitBranch],
 ['Fault Detection & Recovery','Automatic fault detection with immediate task reassignment and recovery workflows.',HeartPulse],
 ['Network Simulation','Test latency degradation, packet loss, bandwidth constraints, partitions, and mesh disconnects.',Network],
 ['Real-time Telemetry','Live monitoring and operational analytics with high-frequency dashboard telemetry.',Radio],
 ['Scalable & Flexible','Extensible architecture for custom robots, sensors, environments, and experiments.',Scaling],
] as const;
export const Features = () => <section id="features" className="landing-section"><div className="landing-container"><SectionHeading title="Key Features" description="Powerful capabilities for resilient multi-robot operations"/><div className="landing-feature-grid">{features.map(([title,text,Icon])=><article className="landing-feature-card" key={title}><span><Icon size={19}/></span><h3>{title}</h3><p>{text}</p></article>)}</div></div></section>;
