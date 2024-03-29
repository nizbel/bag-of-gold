# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-02-03 04:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0127_auto_20170203_0207'),
    ]

    operations = [
        migrations.CreateModel(
            name='AmortizacaoDebenture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taxa', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Taxa')),
                ('periodo', models.IntegerField(verbose_name='Per\xedodo')),
                ('unidade_periodo', models.CharField(max_length=10, verbose_name='Unidade do per\xedodo')),
                ('carencia', models.DateField(blank=True, null=True, verbose_name='Car\xeancia')),
                ('tipo', models.PositiveSmallIntegerField(choices=[(0, 'Indefinido'), (1, 'Percentual fixo sobre o valor nominal atualizado em per\xedodos n\xe3o uniformes'), (2, 'Percentual fixo sobre o valor nominal atualizado em per\xedodos uniformes'), (3, 'Percentual fixo sobre o valor nominal de emiss\xe3o em per\xedodos n\xe3o uniformes'), (4, 'Percentual fixo sobre o valor nominal de emiss\xe3o em per\xedodos uniformes'), (5, 'Percentual vari\xe1vel sobre o valor nominal atualizado em per\xedodos n\xe3o uniformes'), (6, 'Percentual vari\xe1vel sobre o valor nominal atualizado em per\xedodos uniformes'), (7, 'Percentual vari\xe1vel sobre o valor nominal de emiss\xe3o em per\xedodos n\xe3o uniformes'), (8, 'Percentual vari\xe1vel sobre o valor nominal de emiss\xe3o em per\xedodos uniformes')], verbose_name='Tipo de amortiza\xe7\xe3o')),
                ('data', models.DateField(verbose_name='Data')),
                ('debenture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Debenture')),
            ],
        ),
        migrations.CreateModel(
            name='JurosDebenture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taxa', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Taxa')),
                ('periodo', models.IntegerField(verbose_name='Per\xedodo')),
                ('unidade_periodo', models.CharField(max_length=10, verbose_name='Unidade do per\xedodo')),
                ('carencia', models.DateField(blank=True, null=True, verbose_name='Car\xeancia')),
                ('data', models.DateField(verbose_name='Data')),
                ('debenture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Debenture')),
            ],
        ),
        migrations.CreateModel(
            name='PremioDebenture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taxa', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Taxa')),
                ('periodo', models.IntegerField(verbose_name='Per\xedodo')),
                ('unidade_periodo', models.CharField(max_length=10, verbose_name='Unidade do per\xedodo')),
                ('carencia', models.DateField(blank=True, null=True, verbose_name='Car\xeancia')),
                ('data', models.DateField(verbose_name='Data')),
                ('debenture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Debenture')),
            ],
        ),
    ]
