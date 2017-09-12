# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, HistoricoAcao
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.tfs import preencher_historico_acao, buscar_historico, \
    preencher_historico_fii
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from django.core.management.base import BaseCommand
from threading import Thread
import datetime


class PreencheHistoricoAcaoThread(Thread):
    def __init__(self, tickers, data_inicial, data_final):
        self.tickers = tickers 
        self.data_inicial = data_inicial
        self.data_final = data_final
        super(PreencheHistoricoAcaoThread, self).__init__()

    def run(self):
        try:
            for index, ticker in enumerate(self.tickers):
#                 print 'Starting', ticker, '%s%%' % (format(float(index)/len(self.tickers)*100, '.2f'))
                preencher_historico_acao(ticker, buscar_historico(ticker, self.data_inicial, self.data_final))
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print ticker, "Thread:", message
            pass
        
class PreencheHistoricoFIIThread(Thread):
    def __init__(self, tickers, data_inicial, data_final):
        self.tickers = tickers 
        self.data_inicial = data_inicial
        self.data_final = data_final
        super(PreencheHistoricoFIIThread, self).__init__()

    def run(self):
        try:
            for index, ticker in enumerate(self.tickers):
#                 print 'Starting', ticker, '%s%%' % (format(float(index)/len(self.tickers)*100, '.2f'))
                preencher_historico_fii(ticker, buscar_historico(ticker, self.data_inicial, self.data_final))
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print ticker, "Thread:", message
            pass
                    

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs'

    def add_arguments(self, parser):
        parser.add_argument("-i", "--data_inicial", action="store", type=str, dest="data_inicial")
        parser.add_argument("-f", "--data_final", action="store", type=str, dest="data_final")

    def handle(self, *args, **options):
        # Preparar datas
        # Verificar formato da data inicial
        try:
            data_inicial = None if not options['data_inicial'] else datetime.datetime.strptime(options['data_inicial'], '%d-%m-%Y').date()
        except:
            print u'Data inicial deve estar no forma DD-MM-AAAA'
            return
        # Verificar formato da data final
        try:
            data_final = None if not options['data_final'] else datetime.datetime.strptime(options['data_final'], '%d-%m-%Y').date()
        except:
            print u'Data final deve estar no forma DD-MM-AAAA'
            return
        
        # Validar dados entrados
        if data_inicial and data_final:
            if data_final <= data_inicial:
                print u'Data final deve ser maior que data inicial'
                return
            elif (data_final - data_inicial).days > 730:
                print u'Período máximo entre datas é de 2 anos'
                return
        # Criar valores para dados não entrados
        elif data_final and not data_inicial:
            data_inicial = data_final - datetime.timedelta(days=180)
        elif data_inicial and not data_final:
            data_final = min(datetime.date.today(), data_inicial + datetime.timedelta(days=180))
        else:
            data_final = datetime.date.today()
            data_inicial = data_final - datetime.timedelta(days=180)

        #Ação
        if datetime.datetime.now().hour < 18:
            # Pegar fechamento do ultimo dia util
            ultimo_dia_util = datetime.date.today() - datetime.timedelta(days=1)
            while ultimo_dia_util.weekday() > 4 or verificar_feriado_bovespa(ultimo_dia_util):
                ultimo_dia_util = ultimo_dia_util - datetime.timedelta(days=1)
            acoes_sem_fechamento = HistoricoAcao.objects.filter(data=ultimo_dia_util).values_list('acao__ticker', flat=True)
            acoes = Acao.objects.all().exclude(ticker__in=acoes_sem_fechamento)
        else:
            # Pegar fechamento do dia
            acoes = Acao.objects.all()
        acoes = Acao.objects.filter(ticker='BBAS3')
        print acoes
        qtd_threads = 32
        qtd_por_thread = int(len(acoes)/qtd_threads)+1
        contador = 0
        threads = []
        while contador <= len(acoes):
            t = PreencheHistoricoAcaoThread(acoes[contador : min(contador+qtd_por_thread,len(acoes))], data_inicial, data_final)
            threads.append(t)
            t.start()
            contador += qtd_por_thread
        for t in threads:
            t.join()
             
        if 2 == 2:
            return    
        # FII
        fiis = FII.objects.all()
        qtd_por_thread = int(len(fiis)/qtd_threads)+1
        contador = 0
        threads = []
        while contador <= len(fiis):
            t = PreencheHistoricoFIIThread(fiis[contador : min(contador+qtd_por_thread,len(fiis))], data_inicial, data_final)
            threads.append(t)
            t.start()
            contador += qtd_por_thread
        for t in threads:
            t.join()

