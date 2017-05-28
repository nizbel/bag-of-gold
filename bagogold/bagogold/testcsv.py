# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, OperacaoAcao, Provento, AcaoProvento
from bagogold.bagogold.models.fii import FII, HistoricoFII
from decimal import Decimal
from django.contrib.auth.models import User
import csv
import datetime
import re


def testcsv():
 
    f = open('bagogold/tradeSheet.csv', 'r')
    reader = csv.reader(f, delimiter=',')
    for row in reader:  
        if (row[0] != ''):
            acao = Acao.objects.get(ticker=row[0])
             
            # Operação consolidada?
            operacao_consolidada=False
            if (row[9] == 'Consolidado'):
                operacao_consolidada=True
             
            # Data da operação
            data = None
            if len(row[8]) == 7:
                data = datetime.datetime(int(row[8][3:]), int(row[8][1:3]), int(row[8][0]))
                print(data)
            elif len(row[8]) == 8:
                data = datetime.datetime(int(row[8][4:]), int(row[8][2:4]), int(row[8][0:2]))
                print(data)
                 
            # Não é proventos
            if (row[4] == '0'):
                if (row[2] == '0'):
                    # venda
                    operacaoAcao = OperacaoAcao(acao=acao, tipo_operacao='V', quantidade=int(row[1]),
                                                preco_unitario=Decimal(row[3]), corretagem=Decimal(10),
                                                emolumentos=(Decimal(row[5].strip('R$')) - 10), 
                                                consolidada=operacao_consolidada, data=data)
                    print(operacaoAcao)
                    operacaoAcao.save()
                 
                else:
                    # compra
                    operacaoAcao = OperacaoAcao(acao=acao, tipo_operacao='C', quantidade=int(row[1]),
                                                preco_unitario=Decimal(row[2]), corretagem=Decimal(10),
                                                emolumentos=(Decimal(row[5].strip('R$')) - 10), 
                                                consolidada=operacao_consolidada, data=data)
                    print(operacaoAcao)
                    operacaoAcao.save()
        print(row)
    f.close()

def testHistFII():

    f = open('bagogold/bbpo11.csv', 'r')
    reader = csv.reader(f, delimiter=';')
    for row in reader:  
        if (row[0] != '' and row[0] != 'Data'):
            fii = FII.objects.get(ticker='BBPO11')
            data = datetime.datetime(int(row[0][6:]), int(row[0][3:5]), int(row[0][0:2]))
            preco=Decimal(row[1].replace(',','.'))
            historico_fii = HistoricoFII(fii=fii, data=data, preco_unitario=preco)
            print(historico_fii)
            historico_fii.save()
            
    f.close()
    
def copiarBaseReal():

    f = open('bagogold/baseReal.csv', 'r')
    reader = csv.reader(f, delimiter=';')
    for row in reader:  
        data = datetime.datetime(int(row[3][0:4]), int(row[3][5:7]), int(row[3][8:]))
        tipoCV = 'C'
        if float(row[1]) < 0:
            tipoCV = 'V'
            row[1] = float(row[1]) * -1
        acao = Acao.objects.get(ticker=row[4])
        # Calcular corretagem e emolumentos a partir do total e da tabela da Bovespa
#         De R$ 0,01 a R$ 135,07         R$ 2,70  0,00 %
#         De R$ 135,08 a R$ 498,62       R$ 0,00  2,00 %
#         De R$ 498,63 a R$ 1.514,69     R$ 2,49  1,50 %
#         De R$ 1.514,70 a R$ 3.029,38   R$ 10,06 1,00 %
#         A partir de R$ 3.029,39        R$ 25,21 0,50 %
        corretagem = float(row[2])
#         print 'Corretagem tabela: %s' % (corretagem)
        if corretagem > 0:
            if corretagem > 20:
                emolumentos = corretagem - 20
                corretagem = 20
            elif corretagem > 10 and corretagem < 10.99:
                emolumentos = corretagem - 10
                corretagem = 10
            else:
                emolumentos = float(int(float(row[1]) * float(row[0]) * 0.0325)) / 100
                corretagem -= emolumentos
        else:
            emolumentos = 0
            
#         print '%s + %s = %s' % (emolumentos, corretagem, corretagem + emolumentos)
                           
        
        operacao_acao = OperacaoAcao(data=data, preco_unitario=float(row[1]), destinacao='B', corretagem=corretagem, emolumentos=emolumentos, 
                                     quantidade=int(row[0]), consolidada=True, tipo_operacao=tipoCV, acao=acao)
        operacao_acao.save()
            
    f.close()

def copiarBaseProventos():
    f = open('bagogold/proventos.csv', 'r')
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        print row
        provento = Provento()
        provento.acao = Acao.objects.get(ticker=row[0])
        provento.valor_unitario = Decimal(row[1])
        provento.data_ex = datetime.date(int(row[2][0:4]), int(row[2][5:7]), int(row[2][8:]))
        provento.data_pagamento = datetime.date(int(row[3][0:4]), int(row[3][5:7]), int(row[3][8:]))
        if row[4] == '1':
            provento.tipo_provento = 'D'
            provento.save()
        elif row[4] == '2':
            provento.tipo_provento = 'J'
            provento.save()
        elif row[4] == '3':
            provento.tipo_provento = 'A'
            provento.save()
            provento_em_acoes = AcaoProvento()
            provento_em_acoes.acao_recebida = Acao.objects.get(ticker=row[7])
            if Decimal(row[5]) != 0:
                provento_em_acoes.data_pagamento_frac = datetime.date(int(row[6][0:4]), int(row[6][5:7]), int(row[6][8:]))
                provento_em_acoes.valor_calculo_frac = Decimal(row[5])
            provento_em_acoes.provento = provento   
            provento_em_acoes.save()
        
    f.close()