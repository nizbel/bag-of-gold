# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-04 02:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0054_provento_observacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='codigo_cvm',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name=b'C\xc3\xb3digo CVM'),
        ),
        migrations.AddField(
            model_name='transferenciaentredivisoes',
            name='investimento_destino',
            field=models.CharField(blank=True, max_length=1, null=True, verbose_name=b'Investimento de destino'),
        ),
        migrations.AddField(
            model_name='transferenciaentredivisoes',
            name='investimento_origem',
            field=models.CharField(blank=True, max_length=1, null=True, verbose_name=b'Investimento de origem'),
        ),
    ]
