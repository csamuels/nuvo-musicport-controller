import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { useWebSocket } from './useWebSocket';
import type { Zone, Source, StateChangeEvent } from '../types/nuvo';

export function useNuVo() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [zonesData, sourcesData] = await Promise.all([
        api.getZones(),
        api.getSources(),
      ]);
      setZones(zonesData);
      setSources(sourcesData);
    } catch (err) {
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

  useWebSocket(handleStateChange);

  useEffect(() => {
    loadData();
  }, [loadData]);

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
    ...controls,
  };
}
