# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-26 19:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0191_auto_20180826_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicoinvestidorleituradocumento',
            name='proventos_criados',
            field=models.SmallIntegerField(default=0, verbose_name='Proventos criados'),
            preserve_default=False,
        ),
    ]
