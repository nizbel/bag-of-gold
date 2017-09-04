# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-23 06:35
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('criptomoeda', '0005_auto_20170823_0217'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransferenciaCriptomoeda',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(verbose_name='Data')),
                ('valor', models.DecimalField(decimal_places=12, max_digits=21, validators=[django.core.validators.MinValueValidator(Decimal('1E-12'))], verbose_name='Valor da transfer\xeancia')),
                ('origem', models.CharField(max_length=50, verbose_name='Local de origem')),
                ('destino', models.CharField(max_length=50, verbose_name='Local de destino')),
                ('criptomoeda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.Criptomoeda')),
            ],
        ),
        migrations.AlterField(
            model_name='historicovalorcriptomoeda',
            name='valor',
            field=models.DecimalField(decimal_places=12, max_digits=21, verbose_name='Valor'),
        ),
    ]