/**
 * Main app with auto-discovery
 */

import { useServerDiscovery } from './hooks/useServerDiscovery';
import { ServerSelector } from './components/ServerSelector';
import App from './App';
import './App.css';

function AppWithDiscovery() {
  const { serverUrl, discovering, selectServer } = useServerDiscovery();

  // Show server selector if no server selected
  if (!serverUrl) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>🎵 NuVo MusicPort</h1>
          <p className="subtitle">Multi-Room Audio Control</p>
        </header>
        <ServerSelector onServerSelected={selectServer} />
      </div>
    );
  }

  // Show main app when server is selected
  return <App apiBaseUrl={serverUrl} />;
}

export default AppWithDiscovery;
