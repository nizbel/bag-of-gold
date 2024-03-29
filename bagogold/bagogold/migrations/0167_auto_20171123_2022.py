# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-11-23 22:22
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0166_auto_20171119_0132'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckpointDivisaoFII',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('quantidade', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Quantidade no ano')),
                ('preco_medio', models.DecimalField(decimal_places=4, max_digits=11, verbose_name='Pre\xe7o m\xe9dio')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao', verbose_name='Divis\xe3o')),
                ('fii', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.FII')),
            ],
        ),
        migrations.CreateModel(
            name='CheckpointDivisaoProventosFII',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('valor', models.DecimalField(decimal_places=16, max_digits=22, verbose_name='Valor da poupan\xe7a de proventos')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao', verbose_name='Divis\xe3o')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='checkpointdivisaoproventosfii',
            unique_together=set([('ano', 'divisao')]),
        ),
        migrations.AlterUniqueTogether(
            name='checkpointdivisaofii',
            unique_together=set([('fii', 'ano', 'divisao')]),
        ),
    ]
