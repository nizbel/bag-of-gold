# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-05 02:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fundo_investimento', '0005_auto_20170613_0021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicovalorcotas',
            name='valor_cota',
            field=models.DecimalField(decimal_places=15, max_digits=31, verbose_name='Valor da cota'),
        ),
    ]