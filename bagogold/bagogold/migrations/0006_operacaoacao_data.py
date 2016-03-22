# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0005_remove_operacaoacao_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='operacaoacao',
            name='data',
            field=models.DateField(default=None, verbose_name='Data', blank=True),
            preserve_default=False,
        ),
    ]
