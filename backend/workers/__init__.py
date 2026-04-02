# Workers package
# Import all task modules so Celery can discover them

from workers import video_pipeline
from workers import import_pipeline
from workers import gaussian_splatting
from workers import scene_optimization
from workers import test_tasks

__all__ = [
    'video_pipeline',
    'import_pipeline',
    'gaussian_splatting',
    'scene_optimization',
    'test_tasks',
]
