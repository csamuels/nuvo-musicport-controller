/**
 * Server selection component with auto-discovery
 */

import { useState, useEffect } from 'react';

interface Server {
  ip: string;
  hostname: string | null;
  device_info: string | null;
}

interface ServerSelectorProps {
  onServerSelected: (serverUrl: string) => void;
}

export function ServerSelector({ onServerSelected }: ServerSelectorProps) {
  const [discovering, setDiscovering] = useState(true);
  const [servers, setServers] = useState<Server[]>([]);
  const [selectedServer, setSelectedServer] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    discoverServers();
  }, []);

  const discoverServers = async () => {
    setDiscovering(true);
    setError(null);

    try {
      const response = await fetch('/api/discovery');
      if (!response.ok) {
        throw new Error('Discovery failed');
      }

      const devices = await response.json();

      // Filter to only devices with MRAD port
      const nuvoServers = devices.filter((d: any) => d.responds_to_mrad);

      setServers(nuvoServers);

      // Auto-select if only one server found
      if (nuvoServers.length === 1) {
        const serverUrl = `http://${nuvoServers[0].ip}:8000`;
        setSelectedServer(serverUrl);
        onServerSelected(serverUrl);
      } else if (nuvoServers.length === 0) {
        setError('No NuVo MusicPort devices found on network');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Discovery failed');
    } finally {
      setDiscovering(false);
    }
  };

  const handleServerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const serverUrl = e.target.value;
    setSelectedServer(serverUrl);
    onServerSelected(serverUrl);
  };

  const handleManualEntry = () => {
    const ip = prompt('Enter NuVo MusicPort IP address:', '10.0.0.45');
    if (ip) {
      const serverUrl = `http://${ip}:8000`;
      setSelectedServer(serverUrl);
      onServerSelected(serverUrl);
    }
  };

  if (discovering) {
    return (
      <div className="server-selector">
        <div className="discovery-status">
          <div className="spinner-small"></div>
          <p>Discovering NuVo devices on network...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="server-selector">
        <div className="error-box">
          <p>{error}</p>
          <div className="button-group">
            <button onClick={discoverServers}>Try Again</button>
            <button onClick={handleManualEntry}>Enter Manually</button>
          </div>
        </div>
      </div>
    );
  }

  if (servers.length === 1) {
    // Auto-selected - show confirmation
    const server = servers[0];
    return (
      <div className="server-selector">
        <div className="server-connected">
          <h3>✓ Connected to NuVo MusicPort</h3>
          <p className="server-ip">{server.ip}</p>
          {server.hostname && <p className="server-name">{server.hostname}</p>}
          <button className="link-button" onClick={discoverServers}>
            Scan Again
          </button>
        </div>
      </div>
    );
  }

  // Multiple servers - show dropdown
  return (
    <div className="server-selector">
      <div className="server-picker">
        <h3>Select NuVo MusicPort Server</h3>
        <p className="subtitle">Found {servers.length} devices on network</p>

        <select
          value={selectedServer}
          onChange={handleServerChange}
          className="server-dropdown"
        >
          <option value="">Select a server...</option>
          {servers.map((server) => (
            <option key={server.ip} value={`http://${server.ip}:8000`}>
              {server.ip}
              {server.hostname && ` (${server.hostname})`}
            </option>
          ))}
        </select>

        <div className="button-group">
          <button onClick={discoverServers}>Scan Again</button>
          <button onClick={handleManualEntry}>Enter Manually</button>
        </div>
      </div>
    </div>
  );
}
