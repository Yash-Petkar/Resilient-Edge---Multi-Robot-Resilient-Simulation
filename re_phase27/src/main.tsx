import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import LandingPage from './pages/LandingPage';
import AccessPage from './pages/AccessPage';
import './index.css';

const root = createRoot(document.getElementById('root')!);

const renderRoute = () => {
  const path = window.location.pathname;
  root.render(
    <StrictMode>
      {path === '/' ? <LandingPage /> : path === '/access' ? <AccessPage /> : <App />}
    </StrictMode>,
  );
};

renderRoute();
window.addEventListener('popstate', renderRoute);
