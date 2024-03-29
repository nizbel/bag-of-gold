# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-21 18:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0041_auto_20160321_1502'),
    ]

    operations = [
        migrations.CreateModel(
            name='DivisaoOperacaoFII',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.IntegerField(verbose_name=b'Quantidade')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao')),
                ('operacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.OperacaoFII')),
            ],
        ),
        migrations.CreateModel(
            name='DivisaoOperacaoTD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=2, max_digits=7, verbose_name='Quantidade')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao')),
                ('operacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.OperacaoTitulo')),
            ],
        ),
        migrations.AddField(
            model_name='divisaooperacaoacoes',
            name='quantidade',
            field=models.IntegerField(default=0, verbose_name=b'Quantidade'),
            preserve_default=False,
        ),
    ]
