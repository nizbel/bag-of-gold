# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0012_historicofii'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicofii',
            name='fii',
            field=models.ForeignKey(to='bagogold.FII', unique_for_date=b'data'),
        ),
    ]
