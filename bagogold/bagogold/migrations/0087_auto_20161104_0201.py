# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-11-04 04:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0086_pendenciadocumentoprovento_tipo'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvestidorLeituraDocumento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decisao', models.CharField(max_length=1, verbose_name='Decis\xe3o')),
                ('documento', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='bagogold.DocumentoProventoBovespa')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor')),
            ],
        ),
        migrations.CreateModel(
            name='InvestidorResponsavelPendencia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor')),
                ('pendencia', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='bagogold.PendenciaDocumentoProvento')),
            ],
        ),
        migrations.CreateModel(
            name='InvestidorValidacaoDocumento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('documento', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='bagogold.DocumentoProventoBovespa')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='investidorvalidacaodocumento',
            unique_together=set([('documento', 'investidor')]),
        ),
        migrations.AlterUniqueTogether(
            name='investidorresponsavelpendencia',
            unique_together=set([('pendencia', 'investidor')]),
        ),
        migrations.AlterUniqueTogether(
            name='investidorleituradocumento',
            unique_together=set([('documento', 'investidor')]),
        ),
    ]
