import { useState, useEffect } from 'react';
import { Zone } from '../types/nuvo';
import { useStatus } from '../contexts/StatusContext';
import './RadioStationPlayer.css';

interface RadioStation {
  id: string;
  call_sign: string;
  name: string;
  description: string;
  genre: string;
  provider: string;
}

interface RadioStationPlayerProps {
  apiUrl?: string;
  zones: Zone[];
}

export function RadioStationPlayer({ apiUrl = '', zones }: RadioStationPlayerProps) {
  const [stations, setStations] = useState<RadioStation[]>([]);
  const [loading, setLoading] = useState(false);
  const [playingStationId, setPlayingStationId] = useState<string | null>(null);
  const [selectedGenre, setSelectedGenre] = useState<string>('all');
  const { showStatus, clearStatus } = useStatus();

  useEffect(() => {
    loadStations();
  }, []);

  const loadStations = async () => {
    try {
      setLoading(true);
      // Get TuneIn radio stations from music server browse
      const response = await fetch(`${apiUrl}/api/music-servers/browse`);
      if (!response.ok) throw new Error('Failed to load stations');
      const data = await response.json();

      // Parse station data
      const tuneinStations = data.map((item: any) => {
        const title = item.title;

        // Extract call sign and genre
        const callSign = title.split('(')[0].trim();
        const genreMatch = title.match(/\(([^)]+)\)/);
        const genre = genreMatch ? genreMatch[1] : 'Other';

        return {
          id: item.guid,
          call_sign: callSign,
          name: title,
          description: item.metadata?.desc || '',
          genre: genre,
          provider: 'TuneIn'
        };
      });

      setStations(tuneinStations);
    } catch (err) {
      console.error('Failed to load radio stations:', err);
      showStatus('Failed to load radio stations', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePlayStation = async (station: RadioStation) => {
    if (playingStationId) return;

    setPlayingStationId(station.id);
    const loadingId = showStatus(`Starting TuneIn station ${station.call_sign}...`, 'loading');

    try {
      const response = await fetch(`${apiUrl}/api/tunein/play`, {
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

      showStatus(`Now playing ${station.call_sign} in Party Mode`, 'success');
    } catch (err) {
      clearStatus(loadingId);
      showStatus('Network error - failed to connect', 'error', 8000);
    } finally {
      setTimeout(() => setPlayingStationId(null), 3000);
    }
  };

  // Extract unique genres
  const genres = ['all', ...new Set(stations.map(s => s.genre))].sort();

  // Filter stations by genre
  const filteredStations = selectedGenre === 'all'
    ? stations
    : stations.filter(s => s.genre === selectedGenre);

  if (loading) {
    return <div className="radio-loading">Loading radio stations...</div>;
  }

  if (stations.length === 0) {
    return (
      <div className="radio-player">
        <p className="radio-description">No TuneIn stations available. Add stations in the Config tab.</p>
      </div>
    );
  }

  return (
    <div className="radio-player">
      <div className="radio-filters">
        <label>Filter by Genre:</label>
        <select value={selectedGenre} onChange={(e) => setSelectedGenre(e.target.value)}>
          {genres.map(genre => (
            <option key={genre} value={genre}>
              {genre === 'all' ? 'All Genres' : genre}
            </option>
          ))}
        </select>
        <span className="station-count">({filteredStations.length} stations)</span>
      </div>

      <div className="stations-grid-compact">
        {filteredStations.map((station) => {
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
