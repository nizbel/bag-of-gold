# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-21 21:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0061_auto_20160620_2008'),
    ]

    operations = [
        migrations.CreateModel(
            name='DivisaoOperacaoCDB',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=2, max_digits=11, verbose_name=b'Quantidade')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao')),
                ('operacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.OperacaoCDB')),
            ],
        ),
        migrations.CreateModel(
            name='DivisaoOperacaoRDB',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=2, max_digits=11, verbose_name=b'Quantidade')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao')),
                ('operacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.OperacaoRDB')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='divisaooperacaordb',
            unique_together=set([('divisao', 'operacao')]),
        ),
        migrations.AlterUniqueTogether(
            name='divisaooperacaocdb',
            unique_together=set([('divisao', 'operacao')]),
        ),
    ]
