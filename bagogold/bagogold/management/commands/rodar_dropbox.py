from django.core.management.base import BaseCommand
import subprocess32 as subprocess
import time


class Command(BaseCommand):
    help = 'Roda Dropbox para testes com a aparencia do Metronic'

    def handle(self, *args, **options):
        subprocess.call(['/home/bagofgold/bin/dropbox.py', 'start'])
        time.sleep(20)
        subprocess.call(['/home/bagofgold/bin/dropbox.py', 'stop'])