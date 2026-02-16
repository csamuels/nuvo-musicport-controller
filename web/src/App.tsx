import { useNuVo } from './hooks/useNuVo';
import { ZoneCard } from './components/ZoneCard';
import { SystemControls } from './components/SystemControls';
import { DeviceStatus } from './components/DeviceStatus';
import { RadioStations } from './components/RadioStations';
import { MusicServerBrowser } from './components/MusicServerBrowser';
import { CredentialsManager } from './components/CredentialsManager';
import { StatusBar } from './components/StatusBar';
import { StatusProvider } from './contexts/StatusContext';
import { config } from './services/config';
import './App.css';

interface AppProps {
  apiBaseUrl?: string;
}

function App({ apiBaseUrl }: AppProps) {
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
  } = useNuVo({ apiBaseUrl });

  const handlePowerToggle = async (zoneNumber: number, shouldBeOn: boolean) => {
    try {
      if (shouldBeOn) {
        await powerOn(zoneNumber);
      } else {
        await powerOff(zoneNumber);
      }
    } catch (err) {
      console.error('Failed to toggle power:', err);
    }
  };

  const handleVolumeChange = async (zoneNumber: number, volume: number) => {
    try {
      await setVolume(zoneNumber, volume);
    } catch (err) {
      console.error('Failed to set volume:', err);
    }
  };

  const handleMuteToggle = async (zoneNumber: number) => {
    try {
      await toggleMute(zoneNumber);
    } catch (err) {
      console.error('Failed to toggle mute:', err);
    }
  };

  const handleSourceChange = async (zoneNumber: number, sourceGuid: string) => {
    try {
      await setSource(zoneNumber, sourceGuid);
    } catch (err) {
      console.error('Failed to change source:', err);
    }
  };

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

  // Determine if party mode is active and which zone is the host
  const partyModeActive = zones.some(z => z.party_mode === 'Host' || z.party_mode === 'Slave');
  const hostZone = zones.find(z => z.party_mode === 'Host');

  // Filter zones: in party mode, show only the host zone
  const displayZones = partyModeActive && hostZone ? [hostZone] : zones;

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎵 NuVo MusicPort</h1>
        <p className="subtitle">{zones.length} Zones • {sources.length} Sources</p>
      </header>

      <SystemControls
        onPartyModeToggle={togglePartyMode}
        onAllOff={allOff}
        onRefresh={refresh}
      />

      <div style={{ margin: '1rem' }}>
        <DeviceStatus apiUrl={apiBaseUrl || 'http://localhost:8000'} />
      </div>

      <RadioStations apiUrl={apiBaseUrl} />

      {partyModeActive && (
        <div className="party-mode-banner">
          🎉 Party Mode Active - Controlling all zones from {hostZone?.name}
        </div>
      )}

      <div className="zones-grid">
        {displayZones.map((zone) => (
          <ZoneCard
            key={zone.guid}
            zone={zone}
            sources={sources}
            onPowerToggle={handlePowerToggle}
            onVolumeChange={handleVolumeChange}
            onMuteToggle={handleMuteToggle}
            onSourceChange={handleSourceChange}
          />
        ))}
      </div>

      <MusicServerBrowser apiUrl={apiBaseUrl} />

      <CredentialsManager apiUrl={apiBaseUrl} />

      <footer className="app-footer">
        <span className="status-indicator"></span>
        Connected to MusicPort at {deviceIP || 'loading...'}
      </footer>

      <StatusBar />
    </div>
  );
}

export default App;
