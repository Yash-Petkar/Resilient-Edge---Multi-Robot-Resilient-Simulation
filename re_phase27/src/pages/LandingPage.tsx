import React from 'react';
import { Navbar } from '../components/landing/Navbar';
import { Hero } from '../components/landing/Hero';
import { MetricsBar } from '../components/landing/MetricsBar';
import { Features } from '../components/landing/Features';
import { SimulationPreview } from '../components/landing/SimulationPreview';
import { TelemetryPreview } from '../components/landing/TelemetryPreview';
import { TaskAllocation } from '../components/landing/TaskAllocation';
import { FaultRecovery } from '../components/landing/FaultRecovery';
import { NetworkSimulation } from '../components/landing/NetworkSimulation';
import { TechnologyStack } from '../components/landing/TechnologyStack';
import { UseCases } from '../components/landing/UseCases';
import { PlatformShowcase } from '../components/landing/PlatformShowcase';
import { FinalCTA } from '../components/landing/FinalCTA';
import { Footer } from '../components/landing/Footer';
import '../styles/landing.css';

export default function LandingPage() {
  return <div className="landing-page"><Navbar/><main><Hero/><MetricsBar/><Features/><SimulationPreview/><TelemetryPreview/><TaskAllocation/><FaultRecovery/><NetworkSimulation/><TechnologyStack/><UseCases/><PlatformShowcase/><FinalCTA/></main><Footer/></div>;
}
