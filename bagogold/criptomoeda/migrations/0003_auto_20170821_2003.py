# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-21 23:03
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('criptomoeda', '0002_auto_20170818_1510'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperacaoCriptomoedaTaxa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor', models.DecimalField(decimal_places=12, max_digits=21, verbose_name='Taxa da opera\xe7\xe3o')),
                ('moeda', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.Criptomoeda')),
            ],
        ),
        migrations.RemoveField(
            model_name='operacaocriptomoeda',
            name='taxa',
        ),
        migrations.AlterField(
            model_name='operacaocriptomoeda',
            name='valor',
            field=models.DecimalField(decimal_places=12, max_digits=21, validators=[django.core.validators.MinValueValidator(Decimal('1E-12'))], verbose_name='Valor unit\xe1rio'),
        ),
        migrations.AddField(
            model_name='operacaocriptomoedataxa',
            name='operacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.OperacaoCriptomoeda'),
        ),
    ]
