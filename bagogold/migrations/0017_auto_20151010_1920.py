# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0016_auto_20151010_1902'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicotitulo',
            name='titulo',
            field=models.ForeignKey(to='bagogold.Titulo', unique_for_date=b'data'),
        ),
        migrations.AlterField(
            model_name='titulo',
            name='tipo',
            field=models.CharField(max_length=20, verbose_name='Tipo do t\xedtulo', unique_for_date=b'data_vencimento'),
        ),
    ]
