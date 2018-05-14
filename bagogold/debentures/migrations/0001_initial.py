# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-05-14 02:55
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bagogold', '0188_auto_20180513_2355'),
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
            ],
        ),
        migrations.CreateModel(
            name='Debenture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=10, verbose_name='C\xf3digo')),
                ('indice', models.PositiveSmallIntegerField(choices=[(1, b'Prefixado'), (2, b'IPCA'), (3, b'DI'), (4, b'IGP-M'), (5, b'SELIC')], verbose_name='\xcdndice')),
                ('porcentagem', models.DecimalField(decimal_places=3, default=Decimal('100'), max_digits=6, verbose_name='Porcentagem sobre \xedndice')),
                ('data_emissao', models.DateField(verbose_name='Data de emiss\xe3o')),
                ('valor_emissao', models.DecimalField(decimal_places=8, max_digits=17, verbose_name='Valor nominal na emiss\xe3o')),
                ('data_inicio_rendimento', models.DateField(verbose_name='Data de in\xedcio do rendimento')),
                ('data_vencimento', models.DateField(blank=True, null=True, verbose_name='Data de vencimento')),
                ('data_fim', models.DateField(blank=True, null=True, verbose_name='Data de fim')),
                ('incentivada', models.BooleanField(verbose_name='\xc9 incentivada?')),
                ('padrao_snd', models.BooleanField(verbose_name='\xc9 padr\xe3o SND?')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoValorDebenture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_nominal', models.DecimalField(decimal_places=6, max_digits=15, verbose_name='Valor nominal')),
                ('juros', models.DecimalField(decimal_places=6, max_digits=15, verbose_name='Juros')),
                ('premio', models.DecimalField(decimal_places=6, max_digits=15, verbose_name='Pr\xeamio')),
                ('data', models.DateField(verbose_name='Data')),
                ('debenture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='debentures.Debenture')),
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
                ('debenture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='debentures.Debenture')),
            ],
        ),
        migrations.CreateModel(
            name='OperacaoDebenture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preco_unitario', models.DecimalField(decimal_places=8, max_digits=15, verbose_name='Pre\xe7o unit\xe1rio')),
                ('quantidade', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Quantidade')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('taxa', models.DecimalField(decimal_places=2, max_digits=11, verbose_name='Taxa')),
                ('tipo_operacao', models.CharField(max_length=1, verbose_name='Tipo de opera\xe7\xe3o')),
                ('debenture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='debentures.Debenture')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor')),
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
                ('debenture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='debentures.Debenture')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='debenture',
            unique_together=set([('codigo',)]),
        ),
        migrations.AddField(
            model_name='amortizacaodebenture',
            name='debenture',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='debentures.Debenture'),
        ),
    ]