# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-03-21 03:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0142_auto_20170321_0023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='divisaooperacaolc',
            name='quantidade',
            field=models.DecimalField(decimal_places=2, max_digits=11, verbose_name=b'Quantidade'),
        ),
    ]
