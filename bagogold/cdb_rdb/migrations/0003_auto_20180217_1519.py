# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-02-17 17:19
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0170_auto_20180213_0151'),
        ('cdb_rdb', '0002_historicovencimentocdb_rdb'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckpointCDB_RDB',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('qtd_restante', models.DecimalField(decimal_places=2, max_digits=11, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Quantidade restante da opera\xe7\xe3o')),
                ('qtd_atualizada', models.DecimalField(decimal_places=8, max_digits=17, validators=[django.core.validators.MinValueValidator(Decimal('1E-8'))], verbose_name='Quantidade atualizada da opera\xe7\xe3o')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor')),
            ],
        ),
        migrations.RenameField(
            model_name='operacaocdb_rdb',
            old_name='investimento',
            new_name='cdb_rdb',
        ),
        migrations.AddField(
            model_name='checkpointcdb_rdb',
            name='operacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cdb_rdb.OperacaoCDB_RDB'),
        ),
    ]