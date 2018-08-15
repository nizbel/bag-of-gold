# -*- encoding: utf-8 -*-
from django.core.management.base import BaseCommand

from conf.conf import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY


class Command(BaseCommand):
    help = 'Prepara utilização da AWS'

    def handle(self, *args, **options):
        arquivo = file('credentials', 'w+')

        arquivo.write('[default]')
        arquivo.write('aws_access_key_id=' + AWS_ACCESS_KEY_ID)
        arquivo.write('aws_secret_access_key=' + AWS_SECRET_ACCESS_KEY)
    
        arquivo.close()
