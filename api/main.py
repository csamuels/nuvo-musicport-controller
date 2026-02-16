"""FastAPI application for NuVo MusicPort control."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nuvo_sdk import NuVoClient
from nuvo_sdk.mcs_client_simple import SimpleMCSClient as MCSClient
from .config import settings
from .dependencies import set_client, get_client_or_none, set_mcs_client, get_mcs_client_or_none
from .routes import zones, sources, control, websocket, discovery, device, music_servers, credentials, tunein, local_music, station_validator, debug
from .services.websocket_manager import websocket_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles:
    - NuVo client connection on startup (gracefully handles offline device)
    - Event subscription for WebSocket broadcasting
    - Client disconnection on shutdown
    """
    # Startup
    print(f"Initializing NuVo clients for {settings.nuvo_host}...")

    client = NuVoClient(settings.nuvo_host, settings.nuvo_port)
    mcs_client = MCSClient(settings.nuvo_host, 5004)

    # Try to connect to MRAD (zone control)
    mrad_connected = False
    try:
        print(f"Connecting to NuVo device at {settings.nuvo_host}:{settings.nuvo_port}...")
        await client.connect()
        print("[OK] Connected to NuVo device (MRAD)")
        mrad_connected = True

        # Subscribe to events for WebSocket broadcasting
        def on_state_change(event):
            """Broadcast state changes to WebSocket clients."""
            import asyncio
            loop = asyncio.get_event_loop()
            loop.create_task(websocket_manager.broadcast(event))

        client.subscribe(on_state_change)
        print("[OK] Subscribed to state change events")

    except Exception as e:
        print(f"[WARN] Warning: Could not connect to NuVo device (MRAD): {e}")
        print("  API server will start, but device features will be unavailable until device comes online")

    # Store MRAD client globally (even if not connected - endpoints will handle reconnection)
    await set_client(client)

    # Try to connect to MCS (music server control)
    mcs_connected = False
    try:
        print(f"Connecting to Music Server at {settings.nuvo_host}:5004...")
        await mcs_client.connect()
        print("[OK] Connected to Music Server (MCS)")
        mcs_connected = True
    except Exception as e:
        print(f"[WARN] Warning: Could not connect to Music Server (MCS): {e}")
        print("  Music server features will be unavailable until device comes online")

    # Store MCS client globally (even if not connected - endpoints will handle reconnection)
    await set_mcs_client(mcs_client)

    # Summary
    if mrad_connected and mcs_connected:
        print("[OK] All systems ready")
    elif mrad_connected or mcs_connected:
        print("[WARN] API server started with partial connectivity")
    else:
        print("[WARN] API server started in offline mode - waiting for device")

    yield

    # Shutdown
    print("Shutting down NuVo clients...")

    client_instance = await get_client_or_none()
    if client_instance and client_instance._connected:
        try:
            await client_instance.disconnect()
            print("[OK] Disconnected from MRAD")
        except:
            pass

    mcs_instance = await get_mcs_client_or_none()
    if mcs_instance and mcs_instance._connected:
        try:
            await mcs_instance.disconnect()
            print("[OK] Disconnected from MCS")
        except:
            pass

    print("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="NuVo MusicPort API",
    description="REST API and WebSocket interface for NuVo MusicPort multi-room audio control",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(zones.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(control.router, prefix="/api")
app.include_router(discovery.router, prefix="/api")
app.include_router(device.router, prefix="/api")
app.include_router(music_servers.router, prefix="/api")
app.include_router(tunein.router, prefix="/api")
app.include_router(station_validator.router, prefix="/api")
app.include_router(local_music.router, prefix="/api")
app.include_router(credentials.router, prefix="/api/credentials", tags=["Credentials"])
app.include_router(debug.router, prefix="/api")
app.include_router(websocket.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NuVo MusicPort API",
        "version": "0.1.0",
        "docs": "/docs",
        "websocket": "/ws",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    client = await get_client_or_none()
    return {
        "status": "healthy" if client and client._connected else "disconnected",
        "device": settings.nuvo_host,
    }
