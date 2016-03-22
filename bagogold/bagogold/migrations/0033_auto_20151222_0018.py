# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0032_auto_20151221_2252'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicotaxadi',
            name='taxa',
            field=models.DecimalField(unique_for_date=b'data', verbose_name='Rendimento anual', max_digits=5, decimal_places=2),
        ),
    ]
