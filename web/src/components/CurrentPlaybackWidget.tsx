import { useState, useEffect } from 'react';
import { Zone, Source } from '../types/nuvo';
import { useStatus } from '../contexts/StatusContext';
import './CurrentPlaybackWidget.css';

interface CurrentPlaybackWidgetProps {
  apiUrl?: string;
  zones: Zone[];
  sources: Source[];
}

interface NowPlayingInfo {
  zone?: Zone;
  source?: Source;
  title?: string;
  artist?: string;
  album?: string;
}

export function CurrentPlaybackWidget({ apiUrl = '', zones, sources }: CurrentPlaybackWidgetProps) {
  const [nowPlaying, setNowPlaying] = useState<NowPlayingInfo>({});
  const { showStatus } = useStatus();

  useEffect(() => {
    // Find the active zone (first powered-on zone or party mode host)
    const partyHost = zones.find(z => z.party_mode === 'Host');
    const activeZone = partyHost || zones.find(z => z.power);

    if (activeZone) {
      const activeSource = sources.find(s => s.guid === activeZone.source_guid);
      setNowPlaying({
        zone: activeZone,
        source: activeSource,
      });

      // Fetch now playing info from API if available
      fetchNowPlaying();
    } else {
      setNowPlaying({});
    }
  }, [zones, sources]);

  const fetchNowPlaying = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/control/now-playing`);
      if (response.ok) {
        const data = await response.json();
        setNowPlaying(prev => ({
          ...prev,
          title: data.title,
          artist: data.artist,
          album: data.album,
        }));
      }
    } catch (err) {
      // Silently fail - not critical
    }
  };

  const handlePlaybackControl = async (action: 'play' | 'pause' | 'next' | 'prev') => {
    showStatus(`${action.charAt(0).toUpperCase() + action.slice(1)} playback...`, 'loading');
    // TODO: Implement playback control API calls
  };

  const getSourceDisplay = () => {
    if (!nowPlaying.source) return 'No active source';

    // Sources 5 and 6 are external
    if (nowPlaying.source.source_id === 5 || nowPlaying.source.source_id === 6) {
      return `${nowPlaying.source.name} (External Source)`;
    }

    return nowPlaying.source.name;
  };

  if (!nowPlaying.zone) {
    return (
      <div className="current-playback-widget inactive">
        <div className="playback-status">No zones active</div>
      </div>
    );
  }

  return (
    <div className="current-playback-widget">
      <div className="playback-info">
        <div className="playback-zone">
          <strong>{nowPlaying.zone.name}</strong>
          {nowPlaying.zone.party_mode === 'Host' && <span className="party-badge">Party Mode</span>}
        </div>
        <div className="playback-source">{getSourceDisplay()}</div>
        {nowPlaying.title && (
          <div className="playback-track">
            <div className="track-title">{nowPlaying.title}</div>
            {nowPlaying.artist && <div className="track-artist">{nowPlaying.artist}</div>}
            {nowPlaying.album && <div className="track-album">{nowPlaying.album}</div>}
          </div>
        )}
      </div>

      <div className="playback-controls">
        <button
          className="playback-btn"
          onClick={() => handlePlaybackControl('prev')}
          title="Previous"
        >
          ⏮
        </button>
        <button
          className="playback-btn play-pause"
          onClick={() => handlePlaybackControl('play')}
          title="Play/Pause"
        >
          ⏯
        </button>
        <button
          className="playback-btn"
          onClick={() => handlePlaybackControl('next')}
          title="Next"
        >
          ⏭
        </button>
      </div>
    </div>
  );
}
