# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-01-17 04:21
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0113_debenture_padrao_snd'),
    ]

    operations = [
        migrations.CreateModel(
            name='AmortizacaoDebenture',
            fields=[
                ('debenture', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='bagogold.Debenture')),
                ('taxa', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Taxa')),
                ('periodo', models.IntegerField(verbose_name='Per\xedodo')),
                ('unidade_periodo', models.CharField(max_length=10, verbose_name='Unidade do per\xedodo')),
                ('carencia', models.DateField(verbose_name='Car\xeancia')),
                ('tipo', models.SmallIntegerField(verbose_name='Tipo de amortiza\xe7\xe3o')),
                ('data', models.DateField(verbose_name='Data')),
            ],
        ),
        migrations.CreateModel(
            name='JurosDebenture',
            fields=[
                ('debenture', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='bagogold.Debenture')),
                ('taxa', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Taxa')),
                ('periodo', models.IntegerField(verbose_name='Per\xedodo')),
                ('unidade_periodo', models.CharField(max_length=10, verbose_name='Unidade do per\xedodo')),
                ('carencia', models.DateField(verbose_name='Car\xeancia')),
                ('data', models.DateField(verbose_name='Data')),
            ],
        ),
        migrations.CreateModel(
            name='PremioDebenture',
            fields=[
                ('debenture', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='bagogold.Debenture')),
                ('taxa', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Taxa')),
                ('periodo', models.IntegerField(verbose_name='Per\xedodo')),
                ('unidade_periodo', models.CharField(max_length=10, verbose_name='Unidade do per\xedodo')),
                ('carencia', models.DateField(verbose_name='Car\xeancia')),
                ('data', models.DateField(verbose_name='Data')),
            ],
        ),
        migrations.RemoveField(
            model_name='debenture',
            name='juros_adicional',
        ),
        migrations.AlterField(
            model_name='debenture',
            name='porcentagem',
            field=models.DecimalField(decimal_places=3, default=Decimal('100'), max_digits=6, verbose_name='Porcentagem sobre indexa\xe7\xe3o'),
        ),
    ]
