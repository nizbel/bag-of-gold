# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-24 03:11
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0154_selicproventoacaodescritodocbovespa'),
        ('criptomoeda', '0006_auto_20170823_0335'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transferenciacriptomoeda',
            name='criptomoeda',
        ),
        migrations.RemoveField(
            model_name='transferenciacriptomoeda',
            name='valor',
        ),
        migrations.AddField(
            model_name='transferenciacriptomoeda',
            name='investidor',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transferenciacriptomoeda',
            name='moeda',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.Criptomoeda'),
        ),
        migrations.AddField(
            model_name='transferenciacriptomoeda',
            name='quantidade',
            field=models.DecimalField(decimal_places=12, default=0, max_digits=21, validators=[django.core.validators.MinValueValidator(Decimal('1E-12'))], verbose_name='Quantidade transferida'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transferenciacriptomoeda',
            name='taxa',
            field=models.DecimalField(decimal_places=12, default=0, max_digits=21, validators=[django.core.validators.MinValueValidator(Decimal('1E-12'))], verbose_name='Taxa da transfer\xeancia'),
            preserve_default=False,
        ),
    ]
