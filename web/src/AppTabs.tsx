import { useState } from 'react';
import { useNuVo } from './hooks/useNuVo';
import { MessageBanner } from './components/MessageBanner';
import { ControlTab } from './components/tabs/ControlTab';
import { ConfigTab } from './components/tabs/ConfigTab';
import './AppTabs.css';

interface AppTabsProps {
  apiBaseUrl?: string;
}

type TabType = 'control' | 'config';

function AppTabs({ apiBaseUrl }: AppTabsProps) {
  const [activeTab, setActiveTab] = useState<TabType>('control');

  const nuvoData = useNuVo({ apiBaseUrl });

  const {
    zones,
    sources,
    loading,
    error,
    deviceIP,
    powerOn,
    powerOff,
    setVolume,
    toggleMute,
    setSource,
    togglePartyMode,
    allOff,
    refresh,
  } = nuvoData;

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Connecting to NuVo MusicPort...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <button onClick={refresh}>Retry</button>
      </div>
    );
  }

  return (
    <div className="app-tabs">
      <header className="app-header">
        <h1>🎵 NuVo MusicPort</h1>
        <div className="tab-buttons">
          <button
            className={`tab-button ${activeTab === 'control' ? 'active' : ''}`}
            onClick={() => setActiveTab('control')}
          >
            Control
          </button>
          <button
            className={`tab-button ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            Config
          </button>
        </div>
      </header>

      <MessageBanner />

      <main className="tab-content">
        {activeTab === 'control' && (
          <ControlTab
            apiBaseUrl={apiBaseUrl}
            zones={zones}
            sources={sources}
            deviceIP={deviceIP}
            powerOn={powerOn}
            powerOff={powerOff}
            setVolume={setVolume}
            toggleMute={toggleMute}
            setSource={setSource}
            togglePartyMode={togglePartyMode}
            allOff={allOff}
            refresh={refresh}
          />
        )}
        {activeTab === 'config' && (
          <ConfigTab apiBaseUrl={apiBaseUrl} deviceIP={deviceIP} />
        )}
      </main>

      <footer className="app-footer">
        <span className="status-indicator"></span>
        Connected to MusicPort at {deviceIP || 'loading...'}
      </footer>
    </div>
  );
}

export default AppTabs;
