# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-24 04:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tesouro_direto', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operacaotitulo',
            name='investidor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor'),
        ),
    ]
