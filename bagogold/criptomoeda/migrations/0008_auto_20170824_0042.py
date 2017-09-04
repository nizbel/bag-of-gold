# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-24 03:42
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('criptomoeda', '0007_auto_20170824_0011'),
    ]

    operations = [
        migrations.AddField(
            model_name='operacaocriptomoeda',
            name='moeda_taxa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='moeda_taxa', to='criptomoeda.Criptomoeda'),
        ),
        migrations.AlterField(
            model_name='operacaocriptomoeda',
            name='valor',
            field=models.DecimalField(decimal_places=12, max_digits=21, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Taxa da opera\xe7\xe3o'),
        ),
        migrations.AlterField(
            model_name='operacaocriptomoedataxa',
            name='moeda',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.Criptomoeda'),
        ),
        migrations.AlterField(
            model_name='operacaocriptomoedataxa',
            name='valor',
            field=models.DecimalField(decimal_places=12, max_digits=21, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Taxa da opera\xe7\xe3o'),
        ),
        migrations.AlterField(
            model_name='transferenciacriptomoeda',
            name='moeda',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.Criptomoeda'),
        ),
    ]