# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0026_auto_20151028_0100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provento',
            name='tipo_provento',
            field=models.CharField(max_length=1, verbose_name='Tipo de provento'),
        ),
    ]
