export interface Zone {
  guid: string;
  name: string;
  zone_id: string;
  zone_number: number;
  is_on: boolean;
  volume: number;
  mute: boolean;
  source_id: number;
  source_name: string;
  party_mode: string;
  max_volume: number;
  min_volume: number;
}

export interface Source {
  guid: string;
  name: string;
  source_id: number;
  is_smart: boolean;
  is_network: boolean;
  zone_count: number;
}

export interface SystemStatus {
  device_type: string;
  firmware_version: string;
  all_mute: boolean;
  all_off: boolean;
  active_zone: string;
  active_source: string;
  zones: Zone[];
  sources: Source[];
}

export interface StateChangeEvent {
  type: 'state_change';
  target: string;
  property: string;
  value: string;
  timestamp: number;
}
