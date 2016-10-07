# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from decimal import Decimal
from ftplib import FTP
from urllib2 import Request, urlopen, URLError, HTTPError
import datetime


def buscar_valores_diarios():
    ftp = FTP('ftp.cetip.com.br')
    ftp.login()
    ftp.cwd('MediaCDI')
    linhas = []
    ftp.retrlines('NLST', linhas.append)
    for nome in linhas:
        # Verifica se são os .txt do CDI
        if '.txt' in nome:
            # Testa se data do arquivo é maior do que a última data registrada
            data = datetime.date(int(nome[0:4]), int(nome[4:6]), int(nome[6:8]))
            data_ultimo_registro = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
            if data > data_ultimo_registro:
                taxa = []
                ftp.retrlines('RETR ' + nome, taxa.append)
#                 print '%s: %s' % (data, Decimal(taxa[0]) / 100)
                historico = HistoricoTaxaDI(data = data, taxa = Decimal(taxa[0]) / 100)
                historico.save()