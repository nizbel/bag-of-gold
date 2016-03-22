# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0015_historicotitulo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='titulo',
            name='tipo',
            field=models.CharField(max_length=20, verbose_name='Tipo do t\xedtulo'),
        ),
    ]
