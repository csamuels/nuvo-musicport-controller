# 🎵 NuVo MusicPort Control System

**Complete control solution for NuVo MusicPort multi-room audio systems**

[![Tests](https://github.com/your-repo/nuvo-musicport/workflows/Test/badge.svg)](https://github.com/your-repo/nuvo-musicport/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Modern, feature-rich control system built through reverse-engineering the NuVo MusicPort MRAD protocol. Provides Python SDK, REST API, React web UI, Alexa skill, and Home Assistant integration.

![NuVo MusicPort Architecture](docs/images/architecture.png)

## ✨ Features

- **🐍 Python SDK** - Async library for direct device control
- **🌐 REST API** - FastAPI server with OpenAPI docs
- **⚡ WebSocket** - Real-time state updates
- **📱 Web UI** - Beautiful React interface for phones/tablets
- **🗣️ Alexa** - Voice control integration
- **🏠 Home Assistant** - Smart home integration
- **🐳 Docker** - Easy deployment with docker-compose

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/your-repo/nuvo-musicport.git
cd nuvo-musicport

# Configure device IP
echo "NUVO_HOST=10.0.0.45" > .env

# Start services
docker-compose up -d

# Access web UI
open http://localhost:3000
```

### Option 2: Python

```bash
# Install SDK
pip install nuvo-sdk

# Use in Python
import asyncio
from nuvo_sdk import NuVoClient

async def main():
    async with NuVoClient("10.0.0.45") as client:
        zones = await client.get_zones()
        await client.set_volume(50, zone_number=1)

asyncio.run(main())
```

### Option 3: API Server

```bash
# Install dependencies
pip install -e .

# Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000

# View API docs
open http://localhost:8000/docs
```

## 📖 Documentation

- **[API Reference](docs/API.md)** - Complete REST API documentation
- **[SDK Guide](docs/SDK.md)** - Python library usage
- **[Web UI Setup](web/README.md)** - React interface installation
- **[Alexa Skill](docs/ALEXA.md)** - Voice control deployment
- **[Home Assistant](docs/HOME_ASSISTANT.md)** - Smart home integration
- **[Protocol](docs/PROTOCOL.md)** - MRAD protocol specification

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│  Clients: Web UI, Alexa, Home Assistant        │
└─────────────────────────────────────────────────┘
                    ↓ REST API + WebSocket
┌─────────────────────────────────────────────────┐
│  FastAPI Server (api/)                          │
│  - REST endpoints                               │
│  - WebSocket broadcasting                       │
│  - CORS & auth                                  │
└─────────────────────────────────────────────────┘
                    ↓ Python SDK
┌─────────────────────────────────────────────────┐
│  NuVo SDK (nuvo_sdk/)                          │
│  - Async TCP client                             │
│  - Protocol parser                              │
│  - Event subscription                           │
└─────────────────────────────────────────────────┘
                    ↓ MRAD Protocol (Port 5006)
┌─────────────────────────────────────────────────┐
│  NuVo MusicPort Device                          │
└─────────────────────────────────────────────────┘
```

## 📦 Project Structure

```
musicport/
├── nuvo_sdk/              # Python SDK
│   ├── client.py          # Async NuVo client
│   ├── protocol.py        # MRAD protocol parser
│   ├── models.py          # Data models
│   └── events.py          # Event subscription
├── api/                   # REST API server
│   ├── main.py            # FastAPI app
│   ├── routes/            # API endpoints
│   └── services/          # WebSocket manager
├── web/                   # React web UI
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   └── services/      # API client
│   └── package.json
├── alexa/                 # Alexa skill
│   ├── lambda_function.py # AWS Lambda handler
│   └── interaction_model.json
├── homeassistant/         # Home Assistant integration
│   └── custom_components/
│       └── nuvo_musicport/
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Usage examples
├── Dockerfile             # Container image
├── docker-compose.yml     # Multi-container setup
└── setup.py               # Package configuration
```

## 🎯 Supported Features

### Zone Control
- ✅ Power on/off (6 zones)
- ✅ Volume control (0-79)
- ✅ Mute toggle
- ✅ Source selection
- ✅ Real-time status updates

### System Control
- ✅ Party mode (all zones same source)
- ✅ All off command
- ✅ Source management (6 sources)
- ✅ Event subscription

### Integrations
- ✅ REST API with OpenAPI docs
- ✅ WebSocket real-time updates
- ✅ React web interface
- ✅ Alexa voice control
- ✅ Home Assistant entities

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests (requires device)
pytest tests/integration -v

# Run all tests with coverage
pytest --cov=nuvo_sdk --cov-report=html
```

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Reverse-engineered MRAD protocol through packet capture
- Built with FastAPI, React, and modern async Python
- Inspired by the need for better NuVo device control

## 🔗 Links

- **Documentation**: https://nuvo-musicport.readthedocs.io
- **Issues**: https://github.com/your-repo/nuvo-musicport/issues
- **PyPI**: https://pypi.org/project/nuvo-sdk
- **Docker Hub**: https://hub.docker.com/r/yourname/nuvo-musicport

## 📊 Status

| Component | Status | Coverage |
|-----------|--------|----------|
| Python SDK | ✅ Complete | 90%+ |
| REST API | ✅ Complete | 85%+ |
| Web UI | ✅ Complete | - |
| Alexa Skill | ✅ Complete | - |
| Home Assistant | ✅ Complete | - |
| Documentation | ✅ Complete | - |

---

**Made with ❤️ for the NuVo MusicPort community**
