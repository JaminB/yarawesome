from django.core.management.base import BaseCommand
from celery import Celery


class Command(BaseCommand):
    help = "Start the Celery worker"

    def handle(self, *args, **options):
        celery_app = Celery("yarawesome")
        celery_app.config_from_object("django.conf:settings", namespace="CELERY")
        celery_app.worker_main(["worker", "--loglevel=info"])
