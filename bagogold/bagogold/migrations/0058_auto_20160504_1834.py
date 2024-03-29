# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-04 21:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0057_auto_20160504_1814'),
    ]

    operations = [
        migrations.AddField(
            model_name='acao',
            name='tipo',
            field=models.CharField(default='ON', max_length=5, verbose_name='Tipo de a\xe7\xe3o'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='acao',
            unique_together=set([('ticker', 'empresa', 'tipo')]),
        ),
    ]
