import os
import shutil
from celery import shared_task


@shared_task
def import_binary_file(binary_file_path: str) -> None:
    pass
