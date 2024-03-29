# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-03-17 05:19
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cri_cra', '0011_auto_20170312_1128'),
    ]

    operations = [
        migrations.AddField(
            model_name='cri_cra',
            name='data_inicio_rendimento',
            field=models.DateField(default=datetime.date(2016, 10, 27), verbose_name='Data de in\xedcio do rendimento'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cri_cra',
            name='tipo_indexacao',
            field=models.PositiveSmallIntegerField(choices=[(1, b'DI'), (2, b'Prefixado'), (3, b'IPCA'), (4, b'Selic')], verbose_name='Tipo de indexa\xe7\xe3o'),
        ),
    ]
