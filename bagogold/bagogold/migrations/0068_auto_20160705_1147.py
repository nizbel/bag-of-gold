# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-07-05 14:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0067_auto_20160702_2348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='investidor',
            name='corretagem_padrao',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Corretagem padr\xe3o'),
        ),
        migrations.AlterField(
            model_name='investidor',
            name='tipo_corretagem',
            field=models.CharField(default=b'F', max_length=1, verbose_name='Tipo de corretagem'),
        ),
    ]
