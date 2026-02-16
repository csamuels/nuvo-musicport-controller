import { useState, useEffect } from 'react';
import './CredentialsManager.css';

interface Service {
  name: string;
  descrip: string;
  signup_url: string;
  service_message: string;
  is_excluded: boolean;
  limit_type: string;
  limit: number;
  supports_upload_download: boolean;
  supports_aux_radio: boolean;
  supports_lat_lon: boolean;
  supports_exclusion: boolean;
}

interface Account {
  account_id: string;
  username: string;
  status?: string;
}

interface AuxRadioStation {
  id: string;
  call_sign: string;
  name: string;
  description: string;
  stream_url: string;
  image_url: string;
}

interface RadioLookupResult {
  call_sign: string;
  name: string;
  description: string;
  stream_url: string;
  image_url: string;
}

interface CredentialsManagerProps {
  apiUrl?: string;
}

export function CredentialsManager({ apiUrl = '' }: CredentialsManagerProps) {
  const [services, setServices] = useState<Service[]>([]);
  const [accounts, setAccounts] = useState<Record<string, Account[]>>({});
  const [auxRadioStations, setAuxRadioStations] = useState<AuxRadioStation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingAccount, setEditingAccount] = useState<{
    service: Service;
    account?: Account;
    username: string;
    password: string;
    upload: boolean;
    download: boolean;
  } | null>(null);
  const [locationDialog, setLocationDialog] = useState<{
    latitude: string;
    longitude: string;
    loading: boolean;
  } | null>(null);
  const [editingStation, setEditingStation] = useState<{
    station?: AuxRadioStation;
    call_sign: string;
    name: string;
    description: string;
    stream_url: string;
    image_url: string;
    lookupResults: RadioLookupResult[];
    lookupLoading: boolean;
  } | null>(null);

  const baseUrl = apiUrl || '';

  useEffect(() => {
    loadServices();
    loadAuxRadioStations();
  }, []);

  const loadServices = async () => {
    try {
      setLoading(true);
      console.log('[CredentialsManager] Loading services...');

      const response = await fetch(`${baseUrl}/api/credentials/services`);
      console.log('[CredentialsManager] Services response:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('[CredentialsManager] Failed to load services:', errorData);
        throw new Error('Failed to load services');
      }

      const data = await response.json();
      console.log('[CredentialsManager] Services loaded:', data.length, 'services');
      setServices(data);

      // Load accounts for each service
      console.log('[CredentialsManager] Loading accounts for all services...');
      for (const service of data) {
        await loadAccounts(service.name);
      }
      console.log('[CredentialsManager] All accounts loaded');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load services';
      console.error('[CredentialsManager] Fatal error loading services:', {
        error: err,
        message: errorMsg,
        type: err instanceof Error ? err.constructor.name : typeof err
      });
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadAccounts = async (serviceName: string) => {
    try {
      console.log(`[CredentialsManager] Loading accounts for ${serviceName}...`);
      const url = `${baseUrl}/api/credentials/services/${serviceName}/accounts`;
      console.log(`[CredentialsManager] Fetching:`, url);

      const response = await fetch(url);
      console.log(`[CredentialsManager] ${serviceName} response:`, response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error(`[CredentialsManager] ${serviceName} API error:`, {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        });

        // Check if this is a device communication error
        if (response.status === 500) {
          console.warn(`[CredentialsManager] ${serviceName} - Server error (500)`);
          console.warn(`[CredentialsManager] This may indicate:`);
          console.warn(`  1. Device at 10.0.0.45 is not responding`);
          console.warn(`  2. Credentials endpoint path is incorrect`);
          console.warn(`  3. Device requires authentication`);
          console.warn(`[CredentialsManager] Error detail:`, errorData.detail);
        }

        throw new Error('Failed to load accounts');
      }

      const data = await response.json();
      console.log(`[CredentialsManager] ${serviceName} accounts data:`, data);

      // Parse HTML response to extract accounts
      // For now, we'll just store the HTML
      setAccounts(prev => ({
        ...prev,
        [serviceName]: [] // Would need to parse HTML to get actual accounts
      }));
    } catch (err) {
      console.error(`[CredentialsManager] Failed to load accounts for ${serviceName}:`, {
        error: err,
        message: err instanceof Error ? err.message : 'Unknown error',
        stack: err instanceof Error ? err.stack : undefined
      });

      // Don't throw - allow other services to load
      // Set empty array for this service
      setAccounts(prev => ({
        ...prev,
        [serviceName]: []
      }));
    }
  };

  const toggleExclude = async (service: Service) => {
    try {
      const response = await fetch(`${baseUrl}/api/credentials/services/exclude`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_name: service.name,
          excluded: !service.is_excluded
        })
      });

      if (!response.ok) throw new Error('Failed to update service');

      // Update local state
      setServices(prev => prev.map(s =>
        s.name === service.name ? { ...s, is_excluded: !s.is_excluded } : s
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update service');
    }
  };

  const openAddAccount = (service: Service) => {
    setEditingAccount({
      service,
      username: '',
      password: '',
      upload: service.supports_upload_download,
      download: service.supports_upload_download
    });
  };

  const openEditAccount = (service: Service, account: Account) => {
    setEditingAccount({
      service,
      account,
      username: account.username,
      password: '',
      upload: false,
      download: false
    });
  };

  const saveAccount = async () => {
    if (!editingAccount) return;

    try {
      const isEdit = !!editingAccount.account;
      const endpoint = isEdit ? 'accounts/edit' : 'accounts/add';

      const body = isEdit
        ? {
            account_id: editingAccount.account!.account_id,
            username: editingAccount.username,
            password: editingAccount.password,
            upload: editingAccount.upload,
            download: editingAccount.download
          }
        : {
            service_name: editingAccount.service.name,
            username: editingAccount.username,
            password: editingAccount.password,
            upload: editingAccount.upload,
            download: editingAccount.download
          };

      const response = await fetch(`${baseUrl}/api/credentials/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save account');
      }

      setEditingAccount(null);
      await loadAccounts(editingAccount.service.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save account');
    }
  };

  const deleteAccount = async (service: Service, accountId: string) => {
    if (!confirm('Are you sure you want to delete this account?')) return;

    try {
      const response = await fetch(`${baseUrl}/api/credentials/accounts/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: accountId })
      });

      if (!response.ok) throw new Error('Failed to delete account');

      await loadAccounts(service.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete account');
    }
  };

  const openLocationDialog = () => {
    setLocationDialog({ latitude: '', longitude: '', loading: false });
  };

  const getGeolocation = () => {
    if (!locationDialog) return;

    setLocationDialog({ ...locationDialog, loading: true });

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setLocationDialog({ ...locationDialog, loading: false });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocationDialog({
          latitude: position.coords.latitude.toFixed(6),
          longitude: position.coords.longitude.toFixed(6),
          loading: false
        });
      },
      (error) => {
        setError(`Failed to get location: ${error.message}`);
        setLocationDialog({ ...locationDialog, loading: false });
      }
    );
  };

  const saveLocation = async () => {
    if (!locationDialog) return;

    try {
      const response = await fetch(`${baseUrl}/api/credentials/location`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: parseFloat(locationDialog.latitude),
          longitude: parseFloat(locationDialog.longitude)
        })
      });

      if (!response.ok) throw new Error('Failed to save location');

      setLocationDialog(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save location');
    }
  };

  // Aux Radio Stations
  const loadAuxRadioStations = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/credentials/aux-radio/stations`);
      if (!response.ok) throw new Error('Failed to load stations');
      const data = await response.json();

      // Would need to parse HTML to extract stations
      // For now, set empty array
      setAuxRadioStations([]);
    } catch (err) {
      console.error('Failed to load aux radio stations:', err);
    }
  };

  const openAddStation = () => {
    setEditingStation({
      call_sign: '',
      name: '',
      description: '',
      stream_url: '',
      image_url: '',
      lookupResults: [],
      lookupLoading: false
    });
  };

  const openEditStation = (station: AuxRadioStation) => {
    setEditingStation({
      station,
      call_sign: station.call_sign,
      name: station.name,
      description: station.description,
      stream_url: station.stream_url,
      image_url: station.image_url,
      lookupResults: [],
      lookupLoading: false
    });
  };

  const lookupStation = async () => {
    if (!editingStation || !editingStation.call_sign) return;

    setEditingStation({ ...editingStation, lookupLoading: true, lookupResults: [] });

    try {
      const response = await fetch(`${baseUrl}/api/credentials/radio-lookup/${encodeURIComponent(editingStation.call_sign)}`);
      if (!response.ok) throw new Error('Failed to lookup station');
      const results = await response.json();

      setEditingStation({ ...editingStation, lookupResults: results, lookupLoading: false });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to lookup station');
      setEditingStation({ ...editingStation, lookupLoading: false });
    }
  };

  const applyLookupResult = (result: RadioLookupResult) => {
    if (!editingStation) return;

    setEditingStation({
      ...editingStation,
      call_sign: result.call_sign,
      name: result.name,
      description: result.description,
      stream_url: result.stream_url,
      image_url: result.image_url,
      lookupResults: []
    });
  };

  const saveStation = async () => {
    if (!editingStation) return;

    try {
      const isEdit = !!editingStation.station;
      const endpoint = isEdit ? 'aux-radio/edit' : 'aux-radio/add';

      const body = isEdit
        ? {
            station_id: editingStation.station!.id,
            call_sign: editingStation.call_sign,
            name: editingStation.name,
            description: editingStation.description,
            stream_url: editingStation.stream_url,
            image_url: editingStation.image_url
          }
        : {
            call_sign: editingStation.call_sign,
            name: editingStation.name,
            description: editingStation.description,
            stream_url: editingStation.stream_url,
            image_url: editingStation.image_url
          };

      const response = await fetch(`${baseUrl}/api/credentials/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save station');
      }

      setEditingStation(null);
      await loadAuxRadioStations();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save station');
    }
  };

  const deleteStation = async (stationId: string) => {
    if (!confirm('Are you sure you want to delete this station?')) return;

    try {
      const response = await fetch(`${baseUrl}/api/credentials/aux-radio/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ station_id: stationId })
      });

      if (!response.ok) throw new Error('Failed to delete station');

      await loadAuxRadioStations();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete station');
    }
  };

  if (loading && services.length === 0) {
    return (
      <div className="credentials-manager">
        <div className="credentials-loading">Loading services...</div>
      </div>
    );
  }

  return (
    <div className="credentials-manager">
      <div className="credentials-header">
        <h2>🔐 Streaming Service Credentials</h2>
        <p className="credentials-description">
          Enter your account information for available online music services
        </p>
      </div>

      {error && (
        <div className="credentials-error">
          ⚠️ {error}
          <button onClick={() => setError(null)} className="btn-dismiss">✕</button>
        </div>
      )}

      <div className="services-list">
        {services.map(service => (
          <div key={service.name} className="service-card">
            <div className="service-header">
              {service.supports_exclusion && (
                <label className="service-toggle">
                  <input
                    type="checkbox"
                    checked={!service.is_excluded}
                    onChange={() => toggleExclude(service)}
                  />
                  <span className="service-name">{service.descrip}</span>
                </label>
              )}
              {!service.supports_exclusion && (
                <span className="service-name">{service.descrip}</span>
              )}
            </div>

            {!service.is_excluded ? (
              <div className="service-content">
                <div className="service-message">
                  <a href={service.signup_url} target="_blank" rel="noopener noreferrer">
                    Click here to sign up
                  </a>
                  {' '}- {service.service_message}
                </div>

                <div className="accounts-section">
                  {accounts[service.name]?.length > 0 ? (
                    <div className="accounts-list">
                      {accounts[service.name].map(account => (
                        <div key={account.account_id} className="account-item">
                          <span className="account-username">{account.username}</span>
                          {account.status && (
                            <span className="account-status error">{account.status}</span>
                          )}
                          <div className="account-actions">
                            <button
                              onClick={() => openEditAccount(service, account)}
                              className="btn-icon"
                              title="Edit"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => deleteAccount(service, account.account_id)}
                              className="btn-icon"
                              title="Delete"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-accounts">
                      No credentials are currently configured.
                    </div>
                  )}

                  <button
                    onClick={() => openAddAccount(service)}
                    className="btn-add-account"
                  >
                    Add Account
                  </button>

                  {service.supports_lat_lon && (
                    <button
                      onClick={openLocationDialog}
                      className="btn-configure-location"
                    >
                      Configure Local Radio
                    </button>
                  )}

                  {service.supports_aux_radio && (
                    <div className="aux-radio-section">
                      <h4>Additional TuneIn Stations</h4>
                      <p className="aux-radio-description">
                        These additional stations will appear in the TuneIn Radio Local Radio Menu.
                      </p>

                      {auxRadioStations.length > 0 ? (
                        <div className="aux-radio-list">
                          {auxRadioStations.map(station => (
                            <div key={station.id} className="aux-radio-item">
                              <div className="aux-radio-info">
                                <span className="aux-radio-call-sign">{station.call_sign}</span>
                                <span className="aux-radio-name">{station.name}</span>
                              </div>
                              <div className="aux-radio-actions">
                                <button
                                  onClick={() => openEditStation(station)}
                                  className="btn-icon"
                                  title="Edit"
                                >
                                  ✏️
                                </button>
                                <button
                                  onClick={() => deleteStation(station.id)}
                                  className="btn-icon"
                                  title="Delete"
                                >
                                  🗑️
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="no-aux-radio">
                          No additional stations configured.
                        </div>
                      )}

                      <button
                        onClick={openAddStation}
                        className="btn-add-station"
                      >
                        Add Station
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="service-disabled">
                Currently disabled. Click the checkbox above to enable.
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Edit/Add Account Dialog */}
      {editingAccount && (
        <div className="dialog-overlay" onClick={() => setEditingAccount(null)}>
          <div className="dialog" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <h3>{editingAccount.account ? 'Edit' : 'Add'} {editingAccount.service.descrip} Account</h3>
              <button onClick={() => setEditingAccount(null)} className="btn-close">✕</button>
            </div>

            <div className="dialog-content">
              <div className="form-group">
                <label>Username / Email</label>
                <input
                  type="text"
                  value={editingAccount.username}
                  onChange={e => setEditingAccount({ ...editingAccount, username: e.target.value })}
                  className="input-text"
                  placeholder="Enter your username or email"
                />
              </div>

              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={editingAccount.password}
                  onChange={e => setEditingAccount({ ...editingAccount, password: e.target.value })}
                  className="input-text"
                  placeholder="Enter your password"
                />
              </div>

              {editingAccount.service.supports_upload_download && (
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={editingAccount.download}
                      onChange={e => setEditingAccount({ ...editingAccount, download: e.target.checked })}
                    />
                    Copy content from cloud to this server
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={editingAccount.upload}
                      onChange={e => setEditingAccount({ ...editingAccount, upload: e.target.checked })}
                    />
                    Copy content from server to cloud
                  </label>
                </div>
              )}
            </div>

            <div className="dialog-footer">
              <button onClick={saveAccount} className="btn-primary">Save</button>
              <button onClick={() => setEditingAccount(null)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Location Dialog */}
      {locationDialog && (
        <div className="dialog-overlay" onClick={() => setLocationDialog(null)}>
          <div className="dialog" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <h3>Configure Local Radio</h3>
              <button onClick={() => setLocationDialog(null)} className="btn-close">✕</button>
            </div>

            <div className="dialog-content">
              <p className="dialog-description">
                TuneIn Radio uses your location to find local radio stations. You can automatically detect your location or enter coordinates manually.
              </p>

              <button
                onClick={getGeolocation}
                className="btn-geolocation"
                disabled={locationDialog.loading}
              >
                {locationDialog.loading ? '📍 Getting location...' : '📍 Use My Current Location'}
              </button>

              <div className="form-group">
                <label>Latitude</label>
                <input
                  type="number"
                  step="0.000001"
                  value={locationDialog.latitude}
                  onChange={e => setLocationDialog({ ...locationDialog, latitude: e.target.value })}
                  className="input-text"
                  placeholder="e.g., 40.7128"
                />
              </div>

              <div className="form-group">
                <label>Longitude</label>
                <input
                  type="number"
                  step="0.000001"
                  value={locationDialog.longitude}
                  onChange={e => setLocationDialog({ ...locationDialog, longitude: e.target.value })}
                  className="input-text"
                  placeholder="e.g., -74.0060"
                />
              </div>

              <p className="dialog-hint">
                💡 Visit <a href="https://maps.google.com" target="_blank" rel="noopener noreferrer">maps.google.com</a>,
                right-click any location, and select "What's here?" to get coordinates.
              </p>
            </div>

            <div className="dialog-footer">
              <button onClick={saveLocation} className="btn-primary">Save</button>
              <button onClick={() => setLocationDialog(null)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Aux Radio Station Dialog */}
      {editingStation && (
        <div className="dialog-overlay" onClick={() => setEditingStation(null)}>
          <div className="dialog dialog-large" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <h3>{editingStation.station ? 'Edit' : 'Add'} Additional TuneIn Station</h3>
              <button onClick={() => setEditingStation(null)} className="btn-close">✕</button>
            </div>

            <div className="dialog-content">
              <div className="station-lookup">
                <div className="form-group">
                  <label>Call Sign (e.g., WNYC-FM)</label>
                  <div className="input-with-button">
                    <input
                      type="text"
                      value={editingStation.call_sign}
                      onChange={e => setEditingStation({ ...editingStation, call_sign: e.target.value })}
                      className="input-text"
                      placeholder="Enter call sign"
                      maxLength={10}
                    />
                    <button
                      onClick={lookupStation}
                      className="btn-lookup"
                      disabled={!editingStation.call_sign || editingStation.lookupLoading}
                    >
                      {editingStation.lookupLoading ? '🔍 Searching...' : '🔍 Lookup'}
                    </button>
                  </div>
                </div>

                {editingStation.lookupResults.length > 0 && (
                  <div className="lookup-results">
                    <p className="lookup-results-header">Select a station to auto-fill:</p>
                    {editingStation.lookupResults.map((result, idx) => (
                      <div
                        key={idx}
                        className="lookup-result-item"
                        onClick={() => applyLookupResult(result)}
                      >
                        <div className="lookup-result-info">
                          <div className="lookup-result-name">{result.name}</div>
                          <div className="lookup-result-desc">{result.description}</div>
                        </div>
                        <button className="btn-apply">Apply</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>Name (e.g., Public Radio)</label>
                <input
                  type="text"
                  value={editingStation.name}
                  onChange={e => setEditingStation({ ...editingStation, name: e.target.value })}
                  className="input-text"
                  placeholder="Station name"
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <input
                  type="text"
                  value={editingStation.description}
                  onChange={e => setEditingStation({ ...editingStation, description: e.target.value })}
                  className="input-text"
                  placeholder="Station description"
                />
              </div>

              <div className="form-group">
                <label>Stream URL</label>
                <input
                  type="text"
                  value={editingStation.stream_url}
                  onChange={e => setEditingStation({ ...editingStation, stream_url: e.target.value })}
                  className="input-text"
                  placeholder="https://..."
                />
              </div>

              <div className="form-group">
                <label>Image URL</label>
                <input
                  type="text"
                  value={editingStation.image_url}
                  onChange={e => setEditingStation({ ...editingStation, image_url: e.target.value })}
                  className="input-text"
                  placeholder="https://..."
                />
              </div>
            </div>

            <div className="dialog-footer">
              <button onClick={saveStation} className="btn-primary">Save</button>
              <button onClick={() => setEditingStation(null)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
