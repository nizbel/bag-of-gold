# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0009_fii_operacaofii_proventofii'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proventofii',
            name='acao',
        ),
        migrations.RemoveField(
            model_name='proventofii',
            name='tipo_provento',
        ),
        migrations.AddField(
            model_name='proventofii',
            name='fii',
            field=models.ForeignKey(default=None, to='bagogold.FII'),
            preserve_default=False,
        ),
    ]
