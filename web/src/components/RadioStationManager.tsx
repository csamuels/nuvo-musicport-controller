import { useState, useEffect } from 'react';
import { useStatus } from '../contexts/StatusContext';
import './RadioStationManager.css';

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

interface RadioStationManagerProps {
  apiUrl?: string;
}

export function RadioStationManager({ apiUrl = '' }: RadioStationManagerProps) {
  const [stations, setStations] = useState<AuxRadioStation[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchMode, setSearchMode] = useState<'callsign' | 'genre'>('callsign');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<RadioLookupResult[]>([]);
  const [selectedStation, setSelectedStation] = useState<RadioLookupResult | null>(null);
  const [testingStation, setTestingStation] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const { showStatus, clearStatus } = useStatus();

  useEffect(() => {
    loadStations();
  }, []);

  const loadStations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/api/credentials/aux-radio/stations`);
      if (!response.ok) throw new Error('Failed to load stations');
      const data = await response.json();
      setStations(data);
    } catch (err) {
      console.error('Failed to load stations:', err);
      showStatus('Failed to load aux radio stations', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    const loadingId = showStatus(`Searching for station: ${searchQuery}...`, 'loading');

    try {
      const response = await fetch(`${apiUrl}/api/credentials/radio-lookup/${encodeURIComponent(searchQuery)}`);
      clearStatus(loadingId);

      if (!response.ok) throw new Error('Failed to search');

      const results = await response.json();

      if (results.length === 0) {
        showStatus('No stations found matching your search', 'error');
        setSearchResults([]);
        return;
      }

      setSearchResults(results);
      showStatus(`Found ${results.length} stations`, 'success');
    } catch (err) {
      clearStatus(loadingId);
      showStatus('Search failed - check network connection', 'error');
    }
  };

  const handleTestStation = async (station: RadioLookupResult) => {
    setTestingStation(true);
    const loadingId = showStatus(`Testing station: ${station.call_sign}...`, 'loading');

    try {
      // Use the validate endpoint to test
      const response = await fetch(`${apiUrl}/api/tunein/validate-stations?quick_check=true`);
      clearStatus(loadingId);

      if (response.ok) {
        showStatus(`Station ${station.call_sign} is valid and ready to add`, 'success');
      } else {
        showStatus(`Warning: Could not validate station`, 'error');
      }
    } catch (err) {
      clearStatus(loadingId);
      showStatus('Test failed - but station may still work', 'error');
    } finally {
      setTestingStation(false);
    }
  };

  const handleAddStation = async () => {
    if (!selectedStation) return;

    const loadingId = showStatus(`Adding station: ${selectedStation.call_sign}...`, 'loading');

    try {
      const response = await fetch(`${apiUrl}/api/credentials/aux-radio/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selectedStation)
      });

      clearStatus(loadingId);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to add station');
      }

      showStatus(`Successfully added ${selectedStation.call_sign}`, 'success');
      setShowAddModal(false);
      setSearchQuery('');
      setSearchResults([]);
      setSelectedStation(null);
      loadStations();
    } catch (err: any) {
      clearStatus(loadingId);
      showStatus(`Failed to add station: ${err.message}`, 'error');
    }
  };

  const handleDeleteStation = async (stationId: string, callSign: string) => {
    const loadingId = showStatus(`Deleting station: ${callSign}...`, 'loading');

    try {
      const response = await fetch(`${apiUrl}/api/credentials/aux-radio/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ station_id: stationId })
      });

      clearStatus(loadingId);

      if (!response.ok) {
        throw new Error('Failed to delete station');
      }

      showStatus(`Successfully deleted ${callSign}`, 'success');
      setDeleteConfirm(null);
      loadStations();
    } catch (err) {
      clearStatus(loadingId);
      showStatus('Failed to delete station', 'error');
    }
  };

  if (loading) {
    return <div className="station-manager-loading">Loading stations...</div>;
  }

  return (
    <div className="station-manager">
      <div className="station-manager-header">
        <button className="add-station-btn" onClick={() => setShowAddModal(true)}>
          + Add Station
        </button>
        <span className="station-count">{stations.length} stations configured</span>
      </div>

      <div className="stations-grid">
        {stations.map((station) => (
          <div key={station.id} className="station-manager-card">
            <div className="station-info">
              <div className="station-call-sign">{station.call_sign}</div>
              <div className="station-name">{station.name}</div>
            </div>
            <div className="station-actions">
              {deleteConfirm === station.id ? (
                <div className="delete-confirm">
                  <span>Delete?</span>
                  <button
                    className="confirm-yes"
                    onClick={() => handleDeleteStation(station.id, station.call_sign)}
                  >
                    Yes
                  </button>
                  <button
                    className="confirm-no"
                    onClick={() => setDeleteConfirm(null)}
                  >
                    No
                  </button>
                </div>
              ) : (
                <button
                  className="delete-btn"
                  onClick={() => setDeleteConfirm(station.id)}
                  title="Delete station"
                >
                  🗑️
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {stations.length === 0 && (
        <div className="no-stations">
          <p>No auxiliary radio stations configured.</p>
          <p>Click "Add Station" to add your favorite stations.</p>
        </div>
      )}

      {/* Add Station Modal */}
      {showAddModal && (
        <div className="add-station-modal" onClick={() => setShowAddModal(false)}>
          <div className="add-station-content" onClick={(e) => e.stopPropagation()}>
            <h3>Add Radio Station</h3>

            <div className="search-mode-tabs">
              <button
                className={searchMode === 'callsign' ? 'active' : ''}
                onClick={() => setSearchMode('callsign')}
              >
                Search by Call Sign
              </button>
              <button
                className={searchMode === 'genre' ? 'active' : ''}
                onClick={() => setSearchMode('genre')}
              >
                Search by Genre
              </button>
            </div>

            <div className="search-box">
              <input
                type="text"
                placeholder={searchMode === 'callsign' ? 'Enter call sign (e.g., WFMU)' : 'Enter genre (e.g., Jazz, Rock)'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button onClick={handleSearch}>Search</button>
            </div>

            {searchResults.length > 0 && (
              <div className="search-results">
                <h4>Search Results ({searchResults.length})</h4>
                <div className="results-list">
                  {searchResults.map((result, index) => (
                    <div
                      key={index}
                      className={`result-item ${selectedStation === result ? 'selected' : ''}`}
                      onClick={() => setSelectedStation(result)}
                    >
                      <div className="result-info">
                        <div className="result-call-sign">{result.call_sign}</div>
                        <div className="result-description">{result.description}</div>
                      </div>
                      {selectedStation === result && (
                        <div className="result-actions">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleTestStation(result);
                            }}
                            disabled={testingStation}
                          >
                            {testingStation ? 'Testing...' : 'Test'}
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="modal-actions">
              <button
                className="add-btn"
                onClick={handleAddStation}
                disabled={!selectedStation}
              >
                Add Selected Station
              </button>
              <button className="cancel-btn" onClick={() => {
                setShowAddModal(false);
                setSearchQuery('');
                setSearchResults([]);
                setSelectedStation(null);
              }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
