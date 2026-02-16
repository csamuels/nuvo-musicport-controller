import { useState, useEffect } from 'react';
import { Zone } from '../types/nuvo';
import { useStatus } from '../contexts/StatusContext';
import './MusicAlbumBrowser.css';

interface Album {
  guid: string;
  title: string;
  artist: string;
  year?: string;
  genre?: string;
  track_count: number;
  art_url?: string;
}

interface MusicAlbumBrowserProps {
  apiUrl?: string;
  zones: Zone[];
}

export function MusicAlbumBrowser({ apiUrl = '', zones }: MusicAlbumBrowserProps) {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'artist' | 'genre' | 'year'>('all');
  const [filterValue, setFilterValue] = useState<string>('');
  const [showZoneModal, setShowZoneModal] = useState(false);
  const [selectedAlbum, setSelectedAlbum] = useState<Album | null>(null);
  const { showStatus } = useStatus();

  useEffect(() => {
    loadAlbums();
  }, []);

  const loadAlbums = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/api/library/albums`);
      if (!response.ok) throw new Error('Failed to load albums');
      const data = await response.json();
      setAlbums(data);
    } catch (err) {
      console.error('Failed to load albums:', err);
      showStatus('Failed to load music library', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAlbumClick = (album: Album) => {
    // Check if any zone is selected
    const activeZone = zones.find(z => z.power);
    if (!activeZone) {
      // No active zone, show modal
      setSelectedAlbum(album);
      setShowZoneModal(true);
    } else {
      // Play on active zone
      playAlbum(album, activeZone.zone_number, false);
    }
  };

  const playAlbum = async (album: Album, zoneNumber?: number, partyMode: boolean = false) => {
    const target = partyMode ? 'Party Mode' : `Zone ${zoneNumber}`;
    showStatus(`Playing album '${album.title}' in ${target}...`, 'loading');

    try {
      const response = await fetch(`${apiUrl}/api/library/play/album`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          album_guid: album.guid,
          zone_number: zoneNumber,
          party_mode: partyMode
        })
      });

      if (!response.ok) {
        throw new Error('Failed to play album');
      }

      showStatus(`Now playing '${album.title}' by ${album.artist}`, 'success');
      setShowZoneModal(false);
      setSelectedAlbum(null);
    } catch (err) {
      showStatus('Failed to play album', 'error');
    }
  };

  // Get unique filter values
  const getFilterOptions = () => {
    switch (selectedFilter) {
      case 'artist':
        return [...new Set(albums.map(a => a.artist))].sort();
      case 'genre':
        return [...new Set(albums.map(a => a.genre).filter(Boolean))].sort();
      case 'year':
        return [...new Set(albums.map(a => a.year).filter(Boolean))].sort().reverse();
      default:
        return [];
    }
  };

  // Filter albums
  const filteredAlbums = filterValue
    ? albums.filter(album => {
        switch (selectedFilter) {
          case 'artist':
            return album.artist === filterValue;
          case 'genre':
            return album.genre === filterValue;
          case 'year':
            return album.year === filterValue;
          default:
            return true;
        }
      })
    : albums;

  if (loading) {
    return <div className="music-loading">Loading music library...</div>;
  }

  if (albums.length === 0) {
    return (
      <div className="music-browser">
        <p className="music-description">No albums found in music library</p>
      </div>
    );
  }

  return (
    <div className="music-browser">
      <div className="music-filters">
        <select value={selectedFilter} onChange={(e) => {
          setSelectedFilter(e.target.value as any);
          setFilterValue('');
        }}>
          <option value="all">All Albums</option>
          <option value="artist">By Artist</option>
          <option value="genre">By Genre</option>
          <option value="year">By Year</option>
        </select>

        {selectedFilter !== 'all' && (
          <select value={filterValue} onChange={(e) => setFilterValue(e.target.value)}>
            <option value="">All {selectedFilter}s</option>
            {getFilterOptions().map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        )}

        <span className="album-count">({filteredAlbums.length} albums)</span>
      </div>

      <div className="albums-grid">
        {filteredAlbums.map((album) => (
          <div
            key={album.guid}
            className="album-card"
            onClick={() => handleAlbumClick(album)}
          >
            {album.art_url ? (
              <img src={album.art_url} alt={album.title} className="album-art" />
            ) : (
              <div className="album-art-placeholder">💿</div>
            )}
            <div className="album-info">
              <div className="album-title">{album.title}</div>
              <div className="album-artist">{album.artist}</div>
              {album.year && <div className="album-year">{album.year}</div>}
            </div>
          </div>
        ))}
      </div>

      {/* Zone Selection Modal */}
      {showZoneModal && selectedAlbum && (
        <div className="zone-modal" onClick={() => setShowZoneModal(false)}>
          <div className="zone-modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Select Playback Location</h3>
            <p>Where would you like to play '{selectedAlbum.title}'?</p>

            <div className="zone-options">
              <button
                className="zone-option party-mode"
                onClick={() => playAlbum(selectedAlbum, undefined, true)}
              >
                🎉 Party Mode (All Zones)
              </button>

              {zones.map((zone) => (
                <button
                  key={zone.guid}
                  className="zone-option"
                  onClick={() => playAlbum(selectedAlbum, zone.zone_number, false)}
                >
                  {zone.name}
                </button>
              ))}
            </div>

            <button className="cancel-btn" onClick={() => setShowZoneModal(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
