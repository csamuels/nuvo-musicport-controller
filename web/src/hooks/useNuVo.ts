import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { useWebSocket } from './useWebSocket';
import type { Zone, Source, StateChangeEvent } from '../types/nuvo';

interface UseNuVoOptions {
  apiBaseUrl?: string;
}

export function useNuVo(options?: UseNuVoOptions) {
  const [zones, setZones] = useState<Zone[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deviceIP, setDeviceIP] = useState<string | null>(null);

  // Debug: log when zones change
  useEffect(() => {
    console.log('Zones state updated:', zones.length, 'zones');
    if (zones.length > 0) {
      console.log('First zone in state:', zones[0]);
    }
  }, [zones]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('Loading zones and sources...');
      const [zonesData, sourcesData, healthData] = await Promise.all([
        api.getZones(),
        api.getSources(),
        api.getHealth(),
      ]);

      console.log('Zones loaded:', zonesData);
      console.log('First zone volume:', zonesData[0]?.volume);
      console.log('First zone party_mode:', zonesData[0]?.party_mode);
      console.log('Device IP:', healthData.device);

      setZones(zonesData);
      setSources(sourcesData);
      setDeviceIP(healthData.device);

      console.log('State updated with', zonesData.length, 'zones');
    } catch (err) {
      console.error('Error loading data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleStateChange = useCallback((event: StateChangeEvent) => {
    console.log('State change:', event);

    setZones((prevZones) =>
      prevZones.map((zone) => {
        if (zone.zone_id === event.target) {
          const updated = { ...zone };

          switch (event.property) {
            case 'Volume':
              updated.volume = parseInt(event.value);
              break;
            case 'PowerOn':
              updated.is_on = event.value === 'True';
              break;
            case 'Mute':
              updated.mute = event.value === 'True';
              break;
            case 'SourceId':
              updated.source_id = parseInt(event.value);
              break;
            case 'SourceName':
              updated.source_name = event.value;
              break;
            case 'PartyMode':
              updated.party_mode = event.value;
              break;
          }

          return updated;
        }
        return zone;
      })
    );
  }, []);

  // Set base URL before loading data
  useEffect(() => {
    console.log('API Base URL option:', options?.apiBaseUrl);
    if (options?.apiBaseUrl) {
      console.log('Setting API base URL:', options.apiBaseUrl);
      api.setBaseUrl(options.apiBaseUrl);
    } else {
      console.log('No API base URL provided, using default');
    }
    loadData();
  }, [options?.apiBaseUrl, loadData]);

  useWebSocket(handleStateChange);

  const controls = {
    powerOn: (zoneNumber: number) => api.powerOn(zoneNumber),
    powerOff: (zoneNumber: number) => api.powerOff(zoneNumber),
    setVolume: (zoneNumber: number, volume: number) => api.setVolume(zoneNumber, volume),
    toggleMute: (zoneNumber: number) => api.toggleMute(zoneNumber),
    setSource: (zoneNumber: number, sourceGuid: string) => api.setSource(zoneNumber, sourceGuid),
    togglePartyMode: () => api.togglePartyMode(),
    allOff: () => api.allOff(),
    refresh: loadData,
  };

  return {
    zones,
    sources,
    loading,
    error,
    deviceIP,
    ...controls,
  };
}
