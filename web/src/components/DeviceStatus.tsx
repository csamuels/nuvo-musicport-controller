import { useEffect, useState } from 'react';
import './DeviceStatus.css';

interface DeviceStatus {
  product: string;
  branding: string;
  label: string;
  build: string;
  total_storage: string;
  available_storage: string;
  amazon_cloud_status: string;
  time_stamp: string;
}

interface DeviceStatusProps {
  apiUrl: string;
}

export function DeviceStatus({ apiUrl }: DeviceStatusProps) {
  const [status, setStatus] = useState<DeviceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/device/status`);
        if (!response.ok) throw new Error('Failed to fetch device status');
        const data = await response.json();
        setStatus(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  if (loading) {
    return (
      <div className="device-status-card">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading device info...</p>
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="device-status-card error">
        <p>⚠️ Failed to load device status: {error}</p>
      </div>
    );
  }

  const storageUsed = parseFloat(status.total_storage) - parseFloat(status.available_storage);
  const storagePercent = (storageUsed / parseFloat(status.total_storage)) * 100;
  const storageLow = parseFloat(status.available_storage) < 10;

  return (
    <div className="device-status-card">
      <div className="device-status-header">
        <h3>ℹ️ Device Information</h3>
      </div>

      <div className="device-status-grid">
        {/* Product Info */}
        <div className="status-item">
          <span className="status-label">Product</span>
          <span className="status-value">
            {status.branding} ({status.product})
          </span>
        </div>

        {/* Version */}
        <div className="status-item">
          <span className="status-label">Version</span>
          <span className="status-value">{status.label}</span>
          <span className="status-detail">Build: {status.build}</span>
        </div>

        {/* Storage */}
        <div className="status-item full-width">
          <span className="status-label">💾 Storage</span>
          <div className="storage-info">
            <span className="status-value">
              {storageUsed.toFixed(2)} GB used / {status.total_storage} total
            </span>
            <span className={`storage-badge ${storageLow ? 'warning' : 'success'}`}>
              {status.available_storage} GB free
            </span>
            <span className="status-detail">
              ({storagePercent.toFixed(1)}% used)
            </span>
          </div>
        </div>

        {/* Cloud Status */}
        {status.amazon_cloud_status && (
          <div className="status-item full-width">
            <span className="status-label">☁️ Cloud Status</span>
            <span className="status-value">{status.amazon_cloud_status}</span>
          </div>
        )}

        {/* Last Update */}
        <div className="status-item full-width">
          <span className="status-detail">Last system update: {status.time_stamp}</span>
        </div>
      </div>
    </div>
  );
}
