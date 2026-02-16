import { Zone, Source } from '../../types/nuvo';
import { CurrentPlaybackWidget } from '../CurrentPlaybackWidget';
import { ZoneCard } from '../ZoneCard';
import { RadioStationPlayer } from '../RadioStationPlayer';
import { MusicAlbumBrowser } from '../MusicAlbumBrowser';
import { SystemControls } from '../SystemControls';
import './ControlTab.css';

interface ControlTabProps {
  apiBaseUrl?: string;
  zones: Zone[];
  sources: Source[];
  deviceIP: string;
  powerOn: (zoneNumber: number) => Promise<void>;
  powerOff: (zoneNumber: number) => Promise<void>;
  setVolume: (zoneNumber: number, volume: number) => Promise<void>;
  toggleMute: (zoneNumber: number) => Promise<void>;
  setSource: (zoneNumber: number, sourceGuid: string) => Promise<void>;
  togglePartyMode: () => Promise<void>;
  allOff: () => Promise<void>;
  refresh: () => Promise<void>;
}

export function ControlTab({
  apiBaseUrl,
  zones,
  sources,
  powerOn,
  powerOff,
  setVolume,
  toggleMute,
  setSource,
  togglePartyMode,
  allOff,
  refresh,
}: ControlTabProps) {
  // Determine if party mode is active
  const partyModeActive = zones.some(z => z.party_mode === 'Host' || z.party_mode === 'Slave');
  const hostZone = zones.find(z => z.party_mode === 'Host');

  // Filter zones: in party mode, show only the host zone
  const displayZones = partyModeActive && hostZone ? [hostZone] : zones;

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

  return (
    <div className="control-tab">
      {/* Current Playback Status & Controls */}
      <CurrentPlaybackWidget
        apiUrl={apiBaseUrl}
        zones={zones}
        sources={sources}
      />

      {/* System Controls */}
      <SystemControls
        onPartyModeToggle={togglePartyMode}
        onAllOff={allOff}
        onRefresh={refresh}
      />

      {partyModeActive && (
        <div className="party-mode-banner">
          🎉 Party Mode Active - Controlling all zones from {hostZone?.name}
        </div>
      )}

      {/* Zone Cards */}
      <div className="zones-section">
        <h3>Zones</h3>
        <div className="zones-grid-compact">
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
      </div>

      {/* Radio Stations */}
      <div className="radio-section">
        <h3>📻 Radio Stations</h3>
        <RadioStationPlayer apiUrl={apiBaseUrl} zones={zones} />
      </div>

      {/* Music Albums */}
      <div className="music-section">
        <h3>💿 Music Library</h3>
        <MusicAlbumBrowser apiUrl={apiBaseUrl} zones={zones} />
      </div>
    </div>
  );
}
