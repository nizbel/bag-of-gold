# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-29 05:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0182_auto_20180429_0215'),
        ('criptomoeda', '0015_fork'),
    ]

    operations = [
        migrations.AddField(
            model_name='fork',
            name='investidor',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor'),
            preserve_default=False,
        ),
    ]
