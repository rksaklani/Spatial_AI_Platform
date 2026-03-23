"""
Server-Side Rendering API

Provides endpoints for server-side rendering:
- Device capability detection
- Rendering session management
- Frame streaming
- Adaptive rendering mode
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from typing import Optional, Tuple
from pydantic import BaseModel, Field
import asyncio
import structlog

from api.deps import get_current_user, get_db
from models.user import UserInDB
from services.server_renderer import get_server_renderer, DeviceCapability

logger = structlog.get_logger()
router = APIRouter(prefix="/render", tags=["server-render"])


class DeviceCapabilityRequest(BaseModel):
    """Device capability information from client."""
    user_agent: str
    webgl2: bool = False
    webgpu: bool = False
    gpu_vendor: Optional[str] = None
    gpu_renderer: Optional[str] = None
    max_texture_size: int = 0


class DeviceCapabilityResponse(BaseModel):
    """Device capability assessment."""
    has_webgl2: bool
    has_webgpu: bool
    estimated_performance: str
    is_sufficient: bool
    recommendation: str


class CreateSessionRequest(BaseModel):
    """Request to create rendering session."""
    scene_id: str
    resolution_width: int = Field(1920, ge=640, le=3840)
    resolution_height: int = Field(1080, ge=480, le=2160)


class CreateSessionResponse(BaseModel):
    """Rendering session created."""
    session_id: str
    websocket_url: str


class UpdateCameraRequest(BaseModel):
    """Update camera parameters."""
    position: Tuple[float, float, float]
    target: Tuple[float, float, float]
    fov: float = Field(60.0, ge=30, le=120)


class RenderStatsResponse(BaseModel):
    """Rendering statistics."""
    active_sessions: int
    total_sessions: int
    max_sessions: int
    total_frames_rendered: int
    avg_render_time_ms: float
    avg_fps: float


@router.post("/detect-capability", response_model=DeviceCapabilityResponse)
async def detect_device_capability(
    request: DeviceCapabilityRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Detect client device capability and recommend rendering mode.
    
    Analyzes client GPU and browser capabilities to determine if
    client-side rendering is sufficient or if server-side rendering
    should be used.
    """
    renderer = get_server_renderer()
    
    webgl_info = {
        "webgl2": request.webgl2,
        "webgpu": request.webgpu,
        "vendor": request.gpu_vendor,
        "renderer": request.gpu_renderer,
        "max_texture_size": request.max_texture_size,
    }
    
    capability = await renderer.detect_device_capability(
        user_agent=request.user_agent,
        webgl_info=webgl_info,
    )
    
    # Generate recommendation
    if capability.is_sufficient():
        recommendation = "client-side"
    else:
        recommendation = "server-side"
    
    return DeviceCapabilityResponse(
        has_webgl2=capability.has_webgl2,
        has_webgpu=capability.has_webgpu,
        estimated_performance=capability.estimated_performance,
        is_sufficient=capability.is_sufficient(),
        recommendation=recommendation,
    )


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_render_session(
    request: CreateSessionRequest,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Create a new server-side rendering session.
    
    Allocates GPU resources for rendering and returns a WebSocket URL
    for frame streaming.
    """
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({
        "_id": request.scene_id,
        "organization_id": current_user.organization_id,
    })
    
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    renderer = get_server_renderer()
    
    session = await renderer.create_session(
        scene_id=request.scene_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        resolution=(request.resolution_width, request.resolution_height),
    )
    
    if not session:
        raise HTTPException(
            status_code=503,
            detail="Server rendering capacity reached. Please try again later.",
        )
    
    # Generate WebSocket URL
    websocket_url = f"/api/v1/render/sessions/{session.session_id}/stream"
    
    return CreateSessionResponse(
        session_id=session.session_id,
        websocket_url=websocket_url,
    )


@router.post("/sessions/{session_id}/camera")
async def update_session_camera(
    session_id: str,
    request: UpdateCameraRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update camera parameters for a rendering session.
    
    The next rendered frame will use the updated camera position.
    """
    renderer = get_server_renderer()
    
    success = await renderer.update_camera(
        session_id=session_id,
        position=request.position,
        target=request.target,
        fov=request.fov,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or inactive")
    
    return {"status": "updated"}


@router.delete("/sessions/{session_id}")
async def close_render_session(
    session_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Close a rendering session and release GPU resources.
    """
    renderer = get_server_renderer()
    
    success = await renderer.close_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "closed"}


@router.get("/sessions/{session_id}/frame")
async def get_rendered_frame(
    session_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get a single rendered frame as JPEG.
    
    This is a polling-based alternative to WebSocket streaming.
    For real-time streaming, use the WebSocket endpoint instead.
    """
    renderer = get_server_renderer()
    
    frame_data = await renderer.render_frame(session_id)
    
    if not frame_data:
        raise HTTPException(status_code=404, detail="Session not found or inactive")
    
    return Response(
        content=frame_data,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.websocket("/sessions/{session_id}/stream")
async def stream_rendered_frames(
    websocket: WebSocket,
    session_id: str,
):
    """
    Stream rendered frames via WebSocket.
    
    Streams frames at 30 FPS. Client sends camera updates via WebSocket,
    server responds with rendered frames.
    
    Message format:
    - Client -> Server: JSON with camera parameters
    - Server -> Client: Binary JPEG frame data
    """
    await websocket.accept()
    
    renderer = get_server_renderer()
    
    try:
        # Verify session exists
        session = renderer.sessions.get(session_id)
        if not session or not session.active:
            await websocket.close(code=1008, reason="Session not found")
            return
        
        logger.info("websocket_stream_started", session_id=session_id)
        
        # Start streaming loop
        frame_interval = 1.0 / session.target_fps  # 30 FPS = 0.033s
        
        while True:
            try:
                # Check for camera updates from client (non-blocking)
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=0.001,
                    )
                    
                    # Update camera if provided
                    if "camera" in message:
                        camera = message["camera"]
                        await renderer.update_camera(
                            session_id=session_id,
                            position=tuple(camera["position"]),
                            target=tuple(camera["target"]),
                            fov=camera.get("fov", 60.0),
                        )
                except asyncio.TimeoutError:
                    pass  # No message, continue rendering
                
                # Render frame
                frame_data = await renderer.render_frame(session_id)
                
                if not frame_data:
                    break
                
                # Send frame to client
                await websocket.send_bytes(frame_data)
                
                # Maintain target FPS
                await asyncio.sleep(frame_interval)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("websocket_stream_error", error=str(e), session_id=session_id)
                break
        
    finally:
        # Clean up session
        await renderer.close_session(session_id)
        logger.info("websocket_stream_ended", session_id=session_id)


@router.get("/stats", response_model=RenderStatsResponse)
async def get_render_stats(
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get server rendering statistics.
    
    Requires admin privileges.
    """
    # TODO: Add admin check
    
    renderer = get_server_renderer()
    stats = renderer.get_session_stats()
    
    return RenderStatsResponse(**stats)
