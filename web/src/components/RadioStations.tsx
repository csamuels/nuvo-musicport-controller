import { useState, useEffect } from 'react';
import { useStatus } from '../contexts/StatusContext';
import './RadioStations.css';

interface RadioStation {
  id: string;
  call_sign: string;
  name: string;
  description: string;
  genre: string;
  provider: string;
}

interface RadioStationsProps {
  apiUrl?: string;
}

export function RadioStations({ apiUrl = '' }: RadioStationsProps) {
  const [stations, setStations] = useState<RadioStation[]>([]);
  const [loading, setLoading] = useState(false);
  const [playingStationId, setPlayingStationId] = useState<string | null>(null);
  const { showStatus, clearStatus } = useStatus();

  const baseUrl = apiUrl || '';

  useEffect(() => {
    loadStations();
  }, []);

  const loadStations = async () => {
    try {
      setLoading(true);
      // Get Pandora radio stations from Music Server
      const response = await fetch(`${baseUrl}/api/music-servers/browse`);
      if (!response.ok) throw new Error('Failed to load stations');
      const data = await response.json();

      // Parse station data
      const mcsStations = data.map((item: any) => {
        const title = item.title;

        // Extract call sign (e.g., "89.1 - WFDU" from "89.1 - WFDU (Eclectic Music)")
        const callSign = title.split('(')[0].trim();

        // Extract genre from parentheses (e.g., "Eclectic Music" from "89.1 - WFDU (Eclectic Music)")
        const genreMatch = title.match(/\(([^)]+)\)/);
        const genre = genreMatch ? genreMatch[1] : '';

        return {
          id: item.guid,
          call_sign: callSign,
          name: title,
          description: item.metadata?.desc || '',
          genre: genre,
          provider: 'Pandora'
        };
      });

      setStations(mcsStations);
    } catch (err) {
      console.error('Failed to load radio stations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayStation = async (station: RadioStation) => {
    if (playingStationId) return;

    setPlayingStationId(station.id);
    const loadingId = showStatus(`Starting ${station.call_sign}...`, 'loading');

    try {
      const response = await fetch(`${baseUrl}/api/pandora/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          station_name: station.name,
          music_server_instance: 'Music_Server_A'
        })
      });

      clearStatus(loadingId);

      if (!response.ok) {
        const data = await response.json();
        const msg = data.detail || 'Failed to play station';
        showStatus(msg.includes('503') ? 'Music server reconnecting...' : `Error: ${msg}`, 'error', 8000);
        return;
      }

      showStatus(`Now playing ${station.call_sign}`, 'success');
    } catch (err) {
      clearStatus(loadingId);
      showStatus('Network error - failed to connect', 'error', 8000);
    } finally {
      setTimeout(() => setPlayingStationId(null), 3000);
    }
  };

  if (loading) {
    return (
      <div className="radio-stations">
        <div className="radio-loading">Loading radio stations...</div>
      </div>
    );
  }

  if (stations.length === 0) {
    return (
      <div className="radio-stations">
        <div className="radio-header">
          <h2>📻 Radio Stations</h2>
          <p className="radio-description">No stations available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="radio-stations">
      <div className="radio-header">
        <h2>📻 Pandora Radio Stations ({stations.length})</h2>
        <p className="radio-description">
          Click to play in party mode on all zones
        </p>
      </div>

      <div className="stations-grid-compact">
        {stations.map((station) => {
          const isThisStationLoading = playingStationId === station.id;
          const isAnyStationLoading = playingStationId !== null;

          return (
            <div
              key={station.id}
              className={`station-card-compact ${isThisStationLoading ? 'loading' : ''}`}
              onClick={() => !isAnyStationLoading && handlePlayStation(station)}
              style={{
                cursor: isAnyStationLoading ? 'wait' : 'pointer',
                opacity: isAnyStationLoading && !isThisStationLoading ? 0.5 : 1
              }}
            >
              <div className="station-provider-badge">
                {station.provider}
              </div>

              <div className="station-call-sign-compact">
                {station.call_sign}
              </div>

              {station.genre && (
                <div className="station-genre-compact">
                  {station.genre}
                </div>
              )}

              {isThisStationLoading && (
                <div className="station-loading-indicator">⟳</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
