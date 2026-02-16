/**
 * Hook for server discovery and selection
 */

import { useState, useEffect } from 'react';

interface DiscoveredServer {
  ip: string;
  hostname: string | null;
  responds_to_mrad: boolean;
  device_info: string | null;
}

export function useServerDiscovery() {
  const [serverUrl, setServerUrl] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState(true);
  const [servers, setServers] = useState<DiscoveredServer[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if server URL is stored in localStorage
    const stored = localStorage.getItem('nuvo_server_url');
    if (stored) {
      setServerUrl(stored);
      setDiscovering(false);
      return;
    }

    // Otherwise, discover servers
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

      const devices: DiscoveredServer[] = await response.json();

      // Filter to NuVo devices
      const nuvoServers = devices.filter(d => d.responds_to_mrad);
      setServers(nuvoServers);

      // Auto-select if only one
      if (nuvoServers.length === 1) {
        const url = `http://${nuvoServers[0].ip}:8000`;
        selectServer(url);
      } else if (nuvoServers.length === 0) {
        setError('No NuVo devices found. Please enter IP manually.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Discovery failed');
    } finally {
      setDiscovering(false);
    }
  };

  const selectServer = (url: string) => {
    setServerUrl(url);
    localStorage.setItem('nuvo_server_url', url);
  };

  const clearServer = () => {
    setServerUrl(null);
    localStorage.removeItem('nuvo_server_url');
    discoverServers();
  };

  return {
    serverUrl,
    discovering,
    servers,
    error,
    discoverServers,
    selectServer,
    clearServer,
  };
}
