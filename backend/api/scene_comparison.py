"""
Scene comparison API endpoints (placeholder).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/scene-comparison", tags=["Scene Comparison"])


@router.get("/")
async def placeholder():
    """Placeholder endpoint."""
    return {"message": "Scene comparison endpoints coming soon"}
