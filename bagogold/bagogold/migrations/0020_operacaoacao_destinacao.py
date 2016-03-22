# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0019_auto_20151013_0839'),
    ]

    operations = [
        migrations.AddField(
            model_name='operacaoacao',
            name='destinacao',
            field=models.CharField(default='T', max_length=1, verbose_name='Destina\xe7\xe3o'),
            preserve_default=False,
        ),
    ]
