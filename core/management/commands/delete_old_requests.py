from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import BloodRequest

class Command(BaseCommand):
    help = 'Deletes blood requests older than 24 hours'

    def handle(self, *args, **kwargs):
        expired_time = timezone.now() - timedelta(hours=24)
        old_requests = BloodRequest.objects.filter(created_at__lt=expired_time)
        count = old_requests.count()
        old_requests.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} expired blood requests."))
