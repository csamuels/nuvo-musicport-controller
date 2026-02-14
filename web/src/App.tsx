import { useNuVo } from './hooks/useNuVo';
import { ZoneCard } from './components/ZoneCard';
import { SystemControls } from './components/SystemControls';
import './App.css';

function App() {
  const {
    zones,
    sources,
    loading,
    error,
    powerOn,
    powerOff,
    setVolume,
    toggleMute,
    setSource,
    togglePartyMode,
    allOff,
    refresh,
  } = useNuVo();

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

      <div className="zones-grid">
        {zones.map((zone) => (
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

      <footer className="app-footer">
        <span className="status-indicator"></span>
        Connected
      </footer>
    </div>
  );
}

export default App;
