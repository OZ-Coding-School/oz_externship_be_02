from celery import shared_task
from django.core.management import call_command


@shared_task
def run_crawler_v2() -> None:
    call_command("crawler_v2")
