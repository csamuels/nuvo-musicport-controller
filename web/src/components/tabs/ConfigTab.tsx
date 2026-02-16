import { DeviceStatus } from '../DeviceStatus';
import { RadioStationManager } from '../RadioStationManager';
import { CredentialsManager } from '../CredentialsManager';
import './ConfigTab.css';

interface ConfigTabProps {
  apiBaseUrl?: string;
  deviceIP: string;
}

export function ConfigTab({ apiBaseUrl, deviceIP }: ConfigTabProps) {
  return (
    <div className="config-tab">
      {/* Device & Network Settings */}
      <div className="device-settings-section">
        <h3>Device Settings</h3>
        <DeviceStatus apiUrl={apiBaseUrl || 'http://localhost:8000'} />
      </div>

      {/* Radio Station Management */}
      <div className="radio-management-section">
        <h3>📻 TuneIn Radio Station Management</h3>
        <RadioStationManager apiUrl={apiBaseUrl} />
      </div>

      {/* Credentials */}
      <div className="credentials-section">
        <h3>Service Credentials</h3>
        <CredentialsManager apiUrl={apiBaseUrl} />
      </div>
    </div>
  );
}
