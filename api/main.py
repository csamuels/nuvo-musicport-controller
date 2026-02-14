"""FastAPI application for NuVo MusicPort control."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nuvo_sdk import NuVoClient
from .config import settings
from .dependencies import set_client, get_client_or_none
from .routes import zones, sources, control, websocket
from .services.websocket_manager import websocket_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles:
    - NuVo client connection on startup
    - Event subscription for WebSocket broadcasting
    - Client disconnection on shutdown
    """
    # Startup
    print(f"Connecting to NuVo device at {settings.nuvo_host}:{settings.nuvo_port}...")

    client = NuVoClient(settings.nuvo_host, settings.nuvo_port)

    try:
        await client.connect()
        print("Connected to NuVo device")

        # Subscribe to events for WebSocket broadcasting
        def on_state_change(event):
            """Broadcast state changes to WebSocket clients."""
            # Schedule broadcast in event loop
            import asyncio

            loop = asyncio.get_event_loop()
            loop.create_task(websocket_manager.broadcast(event))

        client.subscribe(on_state_change)
        print("Subscribed to state change events")

        # Store client globally
        await set_client(client)

        yield

    finally:
        # Shutdown
        print("Disconnecting from NuVo device...")
        client_instance = await get_client_or_none()
        if client_instance:
            await client_instance.disconnect()
        print("Disconnected")


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
