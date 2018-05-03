# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-29 05:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('criptomoeda', '0015_fork'),
        ('bagogold', '0181_auto_20180424_0230'),
    ]

    operations = [
        migrations.CreateModel(
            name='DivisaoForkCriptomoeda',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=12, max_digits=21, verbose_name=b'Quantidade')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao', verbose_name='Divis\xe3o')),
                ('fork', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.Fork')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='divisaoforkcriptomoeda',
            unique_together=set([('divisao', 'fork')]),
        ),
    ]