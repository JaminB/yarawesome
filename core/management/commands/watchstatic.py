import os
import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from django.apps import apps


class StaticChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        for app_config in apps.get_app_configs():
            if event.src_path.startswith(app_config.path + "/static"):
                print("Static files modified. Running collectstatic...")
                call_command("collectstatic", interactive=False)


class Command(BaseCommand):
    help = "Watch static files for changes across all installed apps and run collectstatic when necessary."

    def handle(self, *args, **options):
        event_handler = StaticChangeHandler()
        observer = Observer()
        for app_config in apps.get_app_configs():
            if os.path.exists(app_config.path + "/static"):
                observer.schedule(
                    event_handler, path=app_config.path + "/static", recursive=True
                )
        observer.start()
        print("Watching for changes in static files across all apps...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
