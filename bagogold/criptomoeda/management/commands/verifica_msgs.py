# -*- coding: utf-8 -*-
from bagogold.criptomoeda.models import ValorDiarioCriptomoeda, Bot
from bagogold.criptomoeda.utils import buscar_valor_criptomoedas_atual
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from operator import attrgetter
from random import randint
from twx.botapi import TelegramBot, ReplyKeyboardMarkup, ReplyKeyboardHide
import datetime
import re
import time
import urllib

class Command(BaseCommand):
    help = 'Verifica mensagens'
    
    def handle(self, *args, **options):
        inicio = datetime.datetime.now()
            
        """
        Setup the bot
        """
        bot_principal, criado = Bot.objects.get_or_create(id=1, defaults={'ultima_msg_lida': 0})
        
        bot = TelegramBot('348104532:AAHUfG8ASUkmCJAot267wLEmCQdQtB9dfvc')
        bot.update_bot_info().wait()
        
        fim = inicio
        
        while (fim - inicio) < datetime.timedelta(seconds=1):
            inicio_msg = datetime.datetime.now()
#         while True:
            updates = bot.get_updates(offset=bot_principal.ultima_msg_lida).wait()
            if not updates:
                updates = list()
            for update in updates:
#                 print update
                chat_id = update.message.sender.id
                if update.message.text != None:
                    bot.send_message(chat_id, u'%s' % ('\n'.join(['%s: *%s %s*' % (valor.criptomoeda, valor.valor.quantize(Decimal('0.01')), valor.moeda) \
                                                                  for valor in ValorDiarioCriptomoeda.objects.all()])), parse_mode='Markdown')
                
                bot_principal.ultima_msg_lida = update.update_id + 1
                bot_principal.save()
            
            # Enviar automaticamente dessa forma por enquanto
#             bot.send_message(150143379, u'%s' % ('\n'.join(['(%s)%s: *$%s*' % (valor.data_hora.strftime('%H:%M'), valor.criptomoeda, valor.valor.quantize(Decimal('0.01'))) for valor in \
#                                                           ValorDiarioCriptomoeda.objects.all().order_by('criptomoeda__ticker')])), parse_mode='Markdown')
            
            valor_atual = dict(ValorDiarioCriptomoeda.objects.filter(criptomoeda__ticker__in=['XZC', 'DCR', 'ZEC', 'XMR'], moeda='BRL') \
                .values_list('criptomoeda__ticker', 'valor'))
            for ticker, valor in valor_atual.items():
                if ticker == 'XZC':
#                     valor_atual[ticker] = (valor * Decimal('157.9233536') * Decimal('0.97')).quantize(Decimal('0.01'))
                    valor_atual[ticker] = (valor * Decimal('0') * Decimal('0.97')).quantize(Decimal('0.01'))
                elif ticker == 'DCR':
#                     valor_atual[ticker] = (valor * Decimal('50.16053218') * Decimal('0.97')).quantize(Decimal('0.01'))
                    valor_atual[ticker] = (valor * Decimal('109.66648258') * Decimal('0.97')).quantize(Decimal('0.01'))
                elif ticker == 'ZEC':
#                     valor_atual[ticker] = (valor * Decimal('7.23106982') * Decimal('0.97')).quantize(Decimal('0.01'))
                    valor_atual[ticker] = (valor * Decimal('0') * Decimal('0.97')).quantize(Decimal('0.01'))
                elif ticker == 'XMR':
#                     valor_atual[ticker] = (valor * Decimal('14.95360846') * Decimal('0.97')).quantize(Decimal('0.01'))
                    valor_atual[ticker] = (valor * Decimal('34.43321466') * Decimal('0.97')).quantize(Decimal('0.01'))

            # Enviar mensagem com valor atual dos investimentos
            bot.send_message(150143379, u'%s\nTotal: *R$ %s*' % ('\n'.join([u'%s: *R$ %s* (%s%%)' % (ticker, valor, ((valor-12000)/Decimal('60')).quantize(Decimal('0.01'))) for ticker, valor in valor_atual.items()]),
                                                                 sum(valor_atual.values())), parse_mode='Markdown')
            
            tempo_decorrido = datetime.datetime.now() - inicio_msg
            if tempo_decorrido.seconds < 3:
                time.sleep(3 - tempo_decorrido.seconds)
            fim = datetime.datetime.now()
        
