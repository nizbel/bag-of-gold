# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-01-17 02:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0112_auto_20170116_2229'),
    ]

    operations = [
        migrations.AddField(
            model_name='debenture',
            name='padrao_snd',
            field=models.BooleanField(default=False, verbose_name='\xc9 padr\xe3o SND?'),
            preserve_default=False,
        ),
    ]
