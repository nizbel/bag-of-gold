# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0007_auto_20150925_2048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operacaocompravenda',
            name='day_trade',
            field=models.NullBooleanField(verbose_name='\xc9 day trade?'),
        ),
    ]
