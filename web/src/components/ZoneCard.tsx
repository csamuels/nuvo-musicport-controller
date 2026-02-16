import type { Zone, Source } from '../types/nuvo';

interface ZoneCardProps {
  zone: Zone;
  sources: Source[];
  onPowerToggle: (zoneNumber: number, isOn: boolean) => void;
  onVolumeChange: (zoneNumber: number, volume: number) => void;
  onMuteToggle: (zoneNumber: number) => void;
  onSourceChange: (zoneNumber: number, sourceGuid: string) => void;
}

export function ZoneCard({
  zone,
  sources,
  onPowerToggle,
  onVolumeChange,
  onMuteToggle,
  onSourceChange,
}: ZoneCardProps) {
  const handlePowerClick = () => {
    onPowerToggle(zone.zone_number, !zone.is_on);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onVolumeChange(zone.zone_number, parseInt(e.target.value));
  };

  const handleSourceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onSourceChange(zone.zone_number, e.target.value);
  };

  return (
    <div className="zone-card">
      <div className="zone-header">
        <div className="zone-info">
          <h3>{zone.name}</h3>
          {zone.source_name && (
            <span className="source-label">{zone.source_name}</span>
          )}
        </div>
        <button
          className={`power-button ${zone.is_on ? 'on' : 'off'}`}
          onClick={handlePowerClick}
        >
          {zone.is_on ? '⏻ ON' : '⏻ OFF'}
        </button>
      </div>

      {zone.is_on && (
        <>
          <div className="volume-control">
            <button
              className="mute-button"
              onClick={() => onMuteToggle(zone.zone_number)}
            >
              {zone.mute ? '🔇' : '🔊'}
            </button>
            <input
              type="range"
              min={zone.min_volume}
              max={zone.max_volume}
              value={zone.volume}
              onChange={handleVolumeChange}
              className="volume-slider"
              disabled={zone.mute}
            />
            <span className="volume-label">{zone.volume}</span>
          </div>

          <div className="source-select">
            <label>Source:</label>
            <select
              value={zone.source_id > 0 ? sources.find(s => s.source_id === zone.source_id)?.guid : ''}
              onChange={handleSourceChange}
            >
              <option value="">Select source...</option>
              {sources.map((source) => (
                <option key={source.guid} value={source.guid}>
                  {source.name} {source.is_smart && '⭐'}
                </option>
              ))}
            </select>
          </div>
        </>
      )}

      {zone.party_mode !== 'Off' && (
        <div className="party-mode-badge">
          🎉 Party Mode {zone.party_mode === 'Host' ? '(Host)' : '(Slave)'}
        </div>
      )}
    </div>
  );
}
