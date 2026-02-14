# NuVo MusicPort Web UI

Beautiful, mobile-responsive React interface for controlling your NuVo MusicPort system.

## Features

- ✅ **Real-time updates** via WebSocket
- ✅ **Zone cards** with power, volume, mute, source controls
- ✅ **System commands** - Party mode, All off
- ✅ **Mobile responsive** - Works on phones and tablets
- ✅ **Dark theme** - Modern, easy on the eyes
- ✅ **TypeScript** - Type-safe development

## Quick Start

```bash
# Install dependencies
cd web
npm install

# Start development server (requires API server running)
npm run dev

# Build for production
npm run build
```

The web UI will be available at `http://localhost:3000`

## Requirements

- Node.js 18+ and npm
- NuVo API server running at `http://localhost:8000`

## Architecture

- **React 18** with TypeScript
- **Vite** for fast development and builds
- **Native WebSocket** for real-time updates
- **CSS** for styling (no heavy frameworks)
- **Proxy** to API server (no CORS issues)

## Project Structure

```
web/
├── src/
│   ├── components/      # React components
│   │   ├── ZoneCard.tsx       # Zone control card
│   │   └── SystemControls.tsx # System buttons
│   ├── hooks/          # Custom React hooks
│   │   ├── useNuVo.ts        # Main state & controls
│   │   └── useWebSocket.ts   # WebSocket connection
│   ├── services/       # API client
│   │   └── api.ts            # REST API wrapper
│   ├── types/          # TypeScript types
│   │   └── nuvo.ts           # Data models
│   ├── App.tsx         # Main app component
│   ├── App.css         # Styles
│   └── main.tsx        # Entry point
├── index.html          # HTML template
├── package.json        # Dependencies
├── vite.config.ts      # Vite configuration
└── tsconfig.json       # TypeScript config
```

## Usage

The UI automatically connects to the API server and displays all zones. Controls are intuitive:

- **Power button** - Turn zones on/off
- **Volume slider** - Adjust volume (0-79)
- **Mute button** - Toggle mute
- **Source dropdown** - Select music source
- **Party Mode** - All zones play same source
- **All Off** - Turn off all zones

Changes are reflected in real-time across all connected clients!
