import os
from yarawesome import settings

os.makedirs(f"{settings.MEDIA_ROOT}/uploads/", exist_ok=True)
os.makedirs(f"{settings.MEDIA_ROOT}/rule-uploads/", exist_ok=True)
