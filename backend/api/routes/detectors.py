# GET /api/detectors — lists all registered detectors and their live stats.

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import require_auth

router = APIRouter()


@router.get('/api/detectors', tags=['Detectors'])
async def list_detectors(_auth=Depends(require_auth)):
    """List all registered detectors with their status and detection counts."""
    try:
        from backend.main import detection_engine
        detectors = [
            {
                'name': d.name,
                'category': (
                    d.category.value if hasattr(d.category, 'value') else str(d.category)
                ),
                'description': getattr(d, 'description', ''),
                'enabled': d.enabled,
                'detection_count': d.detection_count,
                'version': getattr(d, 'version', '1.0'),
            }
            for d in detection_engine.detectors
        ]
    except Exception:
        detectors = []

    return {'detectors': detectors, 'total': len(detectors)}


@router.get('/api/detectors/{detector_name}', tags=['Detectors'])
async def get_detector(detector_name: str, _auth=Depends(require_auth)):
    """Get info on one specific detector by name."""
    try:
        from backend.main import detection_engine
        for d in detection_engine.detectors:
            if d.name == detector_name:
                return {
                    'name': d.name,
                    'category': (
                        d.category.value if hasattr(d.category, 'value') else str(d.category)
                    ),
                    'description': getattr(d, 'description', ''),
                    'enabled': d.enabled,
                    'detection_count': d.detection_count,
                    'version': getattr(d, 'version', '1.0'),
                }
    except Exception:
        pass
    raise HTTPException(status_code=404, detail='Detector not found')
