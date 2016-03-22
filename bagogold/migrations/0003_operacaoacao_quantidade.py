# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0002_auto_20150626_2230'),
    ]

    operations = [
        migrations.AddField(
            model_name='operacaoacao',
            name='quantidade',
            field=models.IntegerField(default=0, verbose_name=b'Quantidade'),
            preserve_default=False,
        ),
    ]
