import { useState, useEffect } from 'react';
import './MusicServerBrowser.css';

interface PickListItem {
  index: number;
  title: string;
  guid: string;
  item_type: string;
  metadata: Record<string, string>;
}

interface MusicServerStatus {
  server_name: string | null;
  instance_name: string | null;
  running: boolean;
  volume: number;
  mute: boolean;
  play_state: string;
  now_playing: Record<string, string>;
  supported_types: string[];
}

interface MusicServerBrowserProps {
  apiUrl?: string;
}

export function MusicServerBrowser({ apiUrl = '' }: MusicServerBrowserProps) {
  const [instances, setInstances] = useState<string[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<string>('');
  const [status, setStatus] = useState<MusicServerStatus | null>(null);
  const [browseItems, setBrowseItems] = useState<PickListItem[]>([]);
  const [searchFilter, setSearchFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mcsUnavailable, setMcsUnavailable] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const baseUrl = apiUrl || '';

  // Load instances on mount
  useEffect(() => {
    console.log('[MusicServerBrowser] Component mounted, loading instances...');
    loadInstances();
  }, []);

  // Load status when instance changes
  useEffect(() => {
    if (selectedInstance) {
      console.log('[MusicServerBrowser] Instance selected:', selectedInstance);
      loadStatus();
      loadBrowseItems();
    }
  }, [selectedInstance]);

  const loadInstances = async () => {
    try {
      console.log('[MusicServerBrowser] Fetching instances from:', `${baseUrl}/api/music-servers/instances`);
      const response = await fetch(`${baseUrl}/api/music-servers/instances`);

      console.log('[MusicServerBrowser] Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('[MusicServerBrowser] API Error Response:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        });

        // Check if this is an MCS connection error
        if (response.status === 500 &&
            (errorData.detail?.includes('forcibly closed') ||
             errorData.detail?.includes('connection') ||
             errorData.detail?.includes('10054'))) {
          setMcsUnavailable(true);
          console.warn('[MusicServerBrowser] MCS Service Unavailable - Connection Error:', errorData.detail);
          console.warn('[MusicServerBrowser] This usually means:');
          console.warn('  1. MCS client connection (port 5004) failed during API startup');
          console.warn('  2. The connection was dropped after initial connection');
          console.warn('  3. The MusicPort device MCS service is not responding');
          console.warn('[MusicServerBrowser] Try restarting the API server or check device connectivity');
          setError('MCS service unavailable - check console for details');
          return;
        }

        throw new Error(`HTTP ${response.status}: ${errorData.detail || response.statusText}`);
      }

      const data = await response.json();
      console.log('[MusicServerBrowser] Instances loaded successfully:', data);

      setInstances(data);
      setMcsUnavailable(false);
      setError(null);

      if (data.length > 0 && !selectedInstance) {
        console.log('[MusicServerBrowser] Auto-selecting first instance:', data[0]);
        setSelectedInstance(data[0]);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load instances';
      setError(errorMsg);
      console.error('[MusicServerBrowser] Fatal Error:', {
        error: err,
        message: errorMsg,
        type: err instanceof Error ? err.constructor.name : typeof err,
        stack: err instanceof Error ? err.stack : undefined
      });
    }
  };

  const selectInstance = async (instanceName: string) => {
    try {
      setLoading(true);
      const response = await fetch(`${baseUrl}/api/music-servers/instance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instance_name: instanceName }),
      });
      if (!response.ok) throw new Error('Failed to select instance');
      setSelectedInstance(instanceName);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to select instance');
    } finally {
      setLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      console.log('[MusicServerBrowser] Loading status...');
      const response = await fetch(`${baseUrl}/api/music-servers/status`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[MusicServerBrowser] Failed to load status:', response.status, errorData);
        throw new Error('Failed to load status');
      }
      const data = await response.json();
      console.log('[MusicServerBrowser] Status loaded:', data);
      setStatus(data);
    } catch (err) {
      console.error('[MusicServerBrowser] Status error:', err);
    }
  };

  const loadBrowseItems = async () => {
    try {
      setLoading(true);
      console.log('[MusicServerBrowser] Loading browse items...');
      const response = await fetch(`${baseUrl}/api/music-servers/browse`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[MusicServerBrowser] Failed to browse:', response.status, errorData);
        throw new Error('Failed to browse');
      }
      const data = await response.json();
      console.log('[MusicServerBrowser] Browse items loaded:', data.length, 'items');
      setBrowseItems(data);
      setError(null);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to browse';
      console.error('[MusicServerBrowser] Browse error:', err);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const selectItem = async (index: number) => {
    try {
      setLoading(true);
      const response = await fetch(`${baseUrl}/api/music-servers/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index }),
      });
      if (!response.ok) throw new Error('Failed to select item');

      // Reload browse list (might navigate into folder or start playing)
      await loadBrowseItems();
      await loadStatus();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to select');
    } finally {
      setLoading(false);
    }
  };

  const applyFilter = async () => {
    try {
      setLoading(true);
      // Default to radio filter (can be made configurable)
      const response = await fetch(`${baseUrl}/api/music-servers/filter/radio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filter_value: searchFilter }),
      });
      if (!response.ok) throw new Error('Failed to apply filter');

      await loadBrowseItems();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to filter');
    } finally {
      setLoading(false);
    }
  };

  const clearQueue = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/music-servers/queue/clear`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to clear queue');
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear queue');
    }
  };

  const handleRetry = () => {
    console.log('[MusicServerBrowser] Retry button clicked, attempt:', retryCount + 1);
    setRetryCount(retryCount + 1);
    setMcsUnavailable(false);
    setError(null);
    loadInstances();
  };

  if (instances.length === 0) {
    return (
      <div className="music-server-browser">
        <div className="browser-header">
          <h2>🎵 Music Servers</h2>
        </div>
        <div className="browser-content">
          {mcsUnavailable ? (
            <div className="mcs-unavailable">
              <p className="error-title">⚠️ MCS Service Unavailable</p>
              <p className="error-message">{error}</p>
              <div className="error-details">
                <p><strong>Possible causes:</strong></p>
                <ul>
                  <li>MCS client connection (port 5004) failed during startup</li>
                  <li>Connection to MusicPort device was dropped</li>
                  <li>Device MCS service is not responding</li>
                </ul>
                <p><strong>Solutions:</strong></p>
                <ul>
                  <li>Check console logs for detailed error information</li>
                  <li>Restart the API server to re-establish connection</li>
                  <li>Verify device at 10.0.0.45 is accessible</li>
                </ul>
              </div>
              <button onClick={handleRetry} className="btn-retry">
                🔄 Retry Connection (Attempt {retryCount + 1})
              </button>
            </div>
          ) : error ? (
            <div className="error-state">
              <p className="no-servers">❌ Error loading Music Servers</p>
              <p className="error-message">{error}</p>
              <p className="hint">Check console for details</p>
              <button onClick={handleRetry} className="btn-retry">
                🔄 Retry
              </button>
            </div>
          ) : (
            <div>
              <p className="no-servers">No Music Servers available</p>
              <p className="hint">Make sure MCS is connected on port 5004</p>
              <button onClick={handleRetry} className="btn-retry">
                🔄 Retry
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="music-server-browser">
      <div className="browser-header">
        <h2>🎵 Music Servers</h2>

        <select
          className="instance-select"
          value={selectedInstance}
          onChange={(e) => selectInstance(e.target.value)}
        >
          {instances.map((instance) => (
            <option key={instance} value={instance}>
              {instance.replace('Music_Server_', 'Server ')}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="browser-error">
          ⚠️ {error}
        </div>
      )}

      {status && (
        <div className="now-playing">
          <div className="now-playing-info">
            <span className="play-state">{status.play_state}</span>
            {status.now_playing.track && (
              <span className="track-info">
                {status.now_playing.track}
                {status.now_playing.artist && ` - ${status.now_playing.artist}`}
              </span>
            )}
            {status.now_playing.station && (
              <span className="station-info">📻 {status.now_playing.station}</span>
            )}
          </div>
          <div className="now-playing-controls">
            <button onClick={clearQueue} className="btn-small">Clear Queue</button>
          </div>
        </div>
      )}

      <div className="browser-search">
        <input
          type="text"
          placeholder="Search stations, artists, albums..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && applyFilter()}
          className="search-input"
        />
        <button onClick={applyFilter} className="btn-search">Search</button>
        <button
          onClick={() => {
            setSearchFilter('');
            applyFilter();
          }}
          className="btn-clear"
        >
          Clear
        </button>
      </div>

      <div className="browser-content">
        {loading && <div className="browser-loading">Loading...</div>}

        {!loading && browseItems.length === 0 && (
          <div className="no-items">
            <p>No items to display</p>
            <p className="hint">Select an instance and browse content</p>
          </div>
        )}

        {!loading && browseItems.length > 0 && (
          <div className="browse-list">
            {browseItems.map((item) => (
              <div
                key={item.index}
                className="browse-item"
                onClick={() => selectItem(item.index)}
              >
                <span className="item-icon">
                  {item.item_type === 'Station' && '📻'}
                  {item.item_type === 'Album' && '💿'}
                  {item.item_type === 'Playlist' && '📋'}
                  {item.item_type === 'Track' && '🎵'}
                  {item.item_type === 'Folder' && '📁'}
                  {!['Station', 'Album', 'Playlist', 'Track', 'Folder'].includes(item.item_type) && '▶️'}
                </span>
                <span className="item-title">{item.title}</span>
                <span className="item-type">{item.item_type}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {status?.supported_types && status.supported_types.length > 0 && (
        <div className="supported-types">
          <span>Supported:</span>
          {status.supported_types.slice(0, 6).map((type) => (
            <span key={type} className="type-badge">{type}</span>
          ))}
        </div>
      )}
    </div>
  );
}
