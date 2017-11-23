# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.outros_investimentos.models import Amortizacao, Rendimento
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.aggregates import Sum, Count
from django.db.models.expressions import Case, When, F
from django.db.models.fields import DecimalField
import datetime

class Divisao (models.Model):
    nome = models.CharField(u'Nome da divisão', max_length=50)
    valor_objetivo = models.DecimalField(u'Objetivo', max_digits=11, decimal_places=2, blank=True, default=0)
    investidor = models.ForeignKey('Investidor')
    
    def __unicode__(self):
        return self.nome
    
    def objetivo_indefinido(self):
        return (self.valor_objetivo == 0)
    
    def divisao_principal(self):
        return self.investidor.divisaoprincipal.divisao.id == self.id

    def possui_operacoes_registradas(self):
        possui_operacoes = (DivisaoOperacaoAcao.objects.filter(divisao=self).count() + DivisaoOperacaoCDB_RDB.objects.filter(divisao=self).count() + DivisaoOperacaoFII.objects.filter(divisao=self).count() + \
            DivisaoOperacaoFundoInvestimento.objects.filter(divisao=self).count() + DivisaoOperacaoLC.objects.filter(divisao=self).count() + DivisaoOperacaoTD.objects.filter(divisao=self).count()) > 0
        
        return possui_operacoes
    
    def saldo_acoes_bh(self, data=datetime.date.today()):
        from bagogold.bagogold.utils.acoes import \
            calcular_poupanca_prov_acao_ate_dia_por_divisao
        """
        Calcula o saldo de operações de ações Buy and Hold de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self, operacao__destinacao='B', operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos - operacao.qtd_proventos_utilizada()) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
        
        # Proventos
        saldo += calcular_poupanca_prov_acao_ate_dia_por_divisao(data, self)        
        
        # Transferências
            
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_BUY_AND_HOLD, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_BUY_AND_HOLD, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
        return saldo
    
    def saldo_acoes_trade(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de ações para trade de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self, operacao__destinacao='T', operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
                
        # Transferências

        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TRADING, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TRADING, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
        return saldo
    
    def saldo_cdb_rdb(self, data=datetime.date.today()):
        from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas_di, \
            calcular_valor_atualizado_com_taxa_prefixado
        from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo
        from bagogold.cdb_rdb.models import CDB_RDB
        """
        Calcula o saldo de operações de CDB/RDB de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        historico_di = HistoricoTaxaDI.objects.all()
        # Computar compras
        saldo -= (DivisaoOperacaoCDB_RDB.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='C').aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        for venda_divisao in DivisaoOperacaoCDB_RDB.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='V'):
            # Para venda, calcular valor do cdb/rdb no dia da venda
            valor_venda = venda_divisao.quantidade
            taxa = venda_divisao.operacao.porcentagem()
             
            # Calcular o valor atualizado
            if venda_divisao.operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
                # DI
                dias_de_rendimento = historico_di.filter(data__gte=venda_divisao.operacao.operacao_compra_relacionada().data, data__lt=venda_divisao.operacao.data)
                taxas_dos_dias = dict(dias_de_rendimento.values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
                valor_venda = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor_venda, taxa)
            elif venda_divisao.operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
                # Prefixado
                # Calcular quantidade dias para valorização
                qtd_dias = qtd_dias_uteis_no_periodo(venda_divisao.operacao.operacao_compra_relacionada().data, venda_divisao.operacao.data)
                valor_venda = calcular_valor_atualizado_com_taxa_prefixado(valor_venda, taxa, qtd_dias)
            # Arredondar
            str_auxiliar = str(valor_venda.quantize(Decimal('.0001')))
            valor_venda = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            saldo += valor_venda
            
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_cri_cra(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de CRI/CRA de uma divisão (dinheiro livre)
        """
        saldo = DivisaoOperacaoCRI_CRA.objects.filter(divisao=self, operacao__data__lte=data) \
        .annotate(total=Case(When(operacao__tipo_operacao='C', then=-1 * (F('quantidade') * F('operacao__preco_unitario') + F('operacao__taxa') * (F('quantidade') / F('operacao__quantidade')))),
                            When(operacao__tipo_operacao='V', then=F('quantidade') * F('operacao__preco_unitario') - F('operacao__taxa') * (F('quantidade') / F('operacao__quantidade'))),
                            output_field=DecimalField())).aggregate(soma_total=Sum('total'))['soma_total'] or Decimal(0)

        # TODO adicionar remunerações
        
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRI_CRA, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRI_CRA, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
        return saldo
    
    def saldo_criptomoeda(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações em Criptomoedas de uma divisão (dinheiro livre)
        """
        # Pegar operações que não tenham criptomoeda como moeda utilizada, apenas reais
        # Operações sem taxa
        saldo = DivisaoOperacaoCriptomoeda.objects.filter(divisao=self, operacao__data__lte=data, operacao__operacaocriptomoedamoeda__isnull=True,
                                                          operacao__operacaocriptomoedataxa__isnull=True) \
        .annotate(total=Case(When(operacao__tipo_operacao='C', then=-1 * (F('quantidade') * F('operacao__preco_unitario'))),
                            When(operacao__tipo_operacao='V', then=F('quantidade') * F('operacao__preco_unitario')),
                            output_field=DecimalField())).aggregate(soma_total=Sum('total'))['soma_total'] or Decimal(0)
                            
        # Operações com taxa
        saldo += DivisaoOperacaoCriptomoeda.objects.filter(divisao=self, operacao__data__lte=data, operacao__operacaocriptomoedamoeda__isnull=True,
                                                          operacao__operacaocriptomoedataxa__isnull=False) \
        .annotate(total=Case(When(operacao__tipo_operacao='C', \
                                  # Para compras, verificar se taxa está na moeda comprada ou na utilizada
                  then=Case(When(operacao__operacaocriptomoedataxa__moeda=F('operacao__criptomoeda'),
                                 then=(F('quantidade') + F('operacao__operacaocriptomoedataxa__valor') * (F('quantidade') / F('operacao__quantidade'))) * F('operacao__preco_unitario') *-1),
                            When(operacao__operacaocriptomoedataxa__moeda=F('operacao__operacaocriptomoedamoeda__criptomoeda'), 
                                then=F('quantidade') * F('operacao__preco_unitario') *-1 - F('operacao__operacaocriptomoedataxa__valor')* (F('quantidade') / F('operacao__quantidade'))))),
                             When(operacao__tipo_operacao='V', \
                                  # Para vendas, verificar se taxa está na moeda comprada ou na utilizada
                  then=Case(When(operacao__operacaocriptomoedataxa__moeda=F('operacao__criptomoeda'),
                                 then=(F('quantidade') - F('operacao__operacaocriptomoedataxa__valor') * (F('quantidade') / F('operacao__quantidade'))) * F('operacao__preco_unitario')),
                            When(operacao__operacaocriptomoedataxa__moeda=F('operacao__operacaocriptomoedamoeda__criptomoeda'), 
                                then=F('quantidade') * F('operacao__preco_unitario') - F('operacao__operacaocriptomoedataxa__valor') * (F('quantidade') / F('operacao__quantidade'))))),
                            output_field=DecimalField())).aggregate(soma_total=Sum('total'))['soma_total'] or Decimal(0)
                            
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRIPTOMOEDA, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRIPTOMOEDA, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
        return saldo
    
    def saldo_debentures(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de Debêntures de uma divisão (dinheiro livre)
        """
        saldo = DivisaoOperacaoDebenture.objects.filter(divisao=self, operacao__data__lte=data) \
        .annotate(total=Case(When(operacao__tipo_operacao='C', then=-1 * (F('quantidade') * F('operacao__preco_unitario') + F('operacao__taxa') * (F('quantidade') / F('operacao__quantidade')))),
                            When(operacao__tipo_operacao='V', then=F('quantidade') * F('operacao__preco_unitario') - F('operacao__taxa') * (F('quantidade') / F('operacao__quantidade'))),
                            output_field=DecimalField())).aggregate(soma_total=Sum('total'))['soma_total'] or Decimal(0)
        
        # TODO adicionar pagamentos
                        
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_DEBENTURE, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_DEBENTURE, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
        return saldo
    
    def saldo_fii(self, data=datetime.date.today()):
        from bagogold.bagogold.utils.fii import \
            calcular_poupanca_prov_fii_ate_dia_por_divisao
        """
        Calcula o saldo de operações de FII de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoFII.objects.filter(divisao=self, operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos - operacao.qtd_proventos_utilizada()) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
        
        # Proventos
        saldo += calcular_poupanca_prov_fii_ate_dia_por_divisao(data, self)    
        
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FII, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FII, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_fundo_investimento(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de fundo de investimento de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoFundoInvestimento.objects.filter(divisao=self, operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= operacao_divisao.quantidade 
            elif operacao.tipo_operacao == 'V':
                saldo += operacao_divisao.quantidade
                
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FUNDO_INV, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FUNDO_INV, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_lc(self, data=datetime.date.today()):
        from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas_di
        """
        Calcula o saldo de operações de Letra de Crédito de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        historico_di = HistoricoTaxaDI.objects.all()
        
        # Computar compras
        saldo -= (DivisaoOperacaoLC.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='C').aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        for venda_divisao in DivisaoOperacaoLC.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='V'):
            # Para venda, calcular valor do cdb/rdb no dia da venda
            valor_venda = venda_divisao.quantidade
            taxa = venda_divisao.operacao.porcentagem_di()
             
            # Calcular o valor atualizado
            dias_de_rendimento = historico_di.filter(data__gte=venda_divisao.operacao.operacao_compra_relacionada().data, data__lt=venda_divisao.operacao.data)
            taxas_dos_dias = dict(dias_de_rendimento.values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            valor_venda = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor_venda, taxa)
            # Arredondar
            str_auxiliar = str(valor_venda.quantize(Decimal('.0001')))
            valor_venda = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            saldo += valor_venda
        
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LCI_LCA, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LCI_LCA, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_outros_invest(self, data=datetime.date.today()):
        """
        Calcula o saldo de outros investimentos de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
#         saldo -= (DivisaoInvestimento.objects.filter(divisao=self, investimento__data_lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        investimentos = DivisaoInvestimento.objects.filter(divisao=self, investimento__data__lte=data, 
                                                            investimento__data_encerramento__isnull=True) \
                    .annotate(qtd_total=F('investimento__quantidade')).values_list('investimento__id', 'quantidade', 'qtd_total')
    
        dict_divisao = {investimento[0]: investimento[1] for investimento in investimentos}
        # Quantidades totais investidas pela divisão
        saldo -= sum(dict_divisao.values())
        
        dict_investimentos = {investimento[0]: investimento[2] for investimento in investimentos}
    
        amortizacoes = dict(Amortizacao.objects.filter(data__lte=data, investimento__in=dict_investimentos.keys()) \
                            .values('investimento__id').annotate(total_amortizado=Sum('valor')).values_list('investimento__id', 'total_amortizado'))
        saldo += sum({ k: (amortizacoes.get(k, 0) * dict_divisao.get(k, 0) / dict_investimentos.get(k, 0)).quantize(Decimal('0.01')) \
                             for k in set(dict_investimentos) | set(amortizacoes) | set(dict_divisao) \
                             if (amortizacoes.get(k, 0) * dict_divisao.get(k, 0) / dict_investimentos.get(k, 0)).quantize(Decimal('0.01')) > 0 }.values())
        
        rendimentos = dict(Rendimento.objects.filter(data__lte=data, investimento__in=dict_investimentos.keys()) \
                            .values('investimento__id').annotate(total_rendimentos=Sum('valor')).values_list('investimento__id', 'total_rendimentos'))
        saldo += sum({ k: (rendimentos.get(k, 0) * dict_divisao.get(k, 0) / dict_investimentos.get(k, 0)).quantize(Decimal('0.01')) \
                             for k in set(dict_investimentos) | set(rendimentos) | set(dict_divisao) \
                             if (rendimentos.get(k, 0) * dict_divisao.get(k, 0) / dict_investimentos.get(k, 0)).quantize(Decimal('0.01')) > 0 }.values())
        
#         qtd_investimentos = { k: (dict_divisao.get(k, 0) - (amortizacoes.get(k, 0) * dict_divisao.get(k, 0) / dict_investimentos.get(k, 0))).quantize(Decimal('0.01')) \
#                              for k in set(dict_investimentos) | set(amortizacoes) | set(dict_divisao) \
#                              if (dict_divisao.get(k, 0) - (amortizacoes.get(k, 0) * dict_divisao.get(k, 0) / dict_investimentos.get(k, 0))).quantize(Decimal('0.01')) > 0 }
        
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_OUTROS_INVEST, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_OUTROS_INVEST, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)

        return saldo
    
    def saldo_td(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de Tesouro Direto de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoTD.objects.filter(divisao=self, operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.taxa_custodia + operacao.taxa_bvmf) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.taxa_custodia + operacao.taxa_bvmf) * operacao_divisao.percentual_divisao())
                
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TESOURO_DIRETO, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TESOURO_DIRETO, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        # Arredondar
        saldo = saldo.quantize(Decimal('.01'))
        
        return saldo
    
    
    def saldo(self, data=datetime.date.today()):
        """
        Calcula o saldo total restante de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        # Ações
        # Buy and hold
        saldo += self.saldo_acoes_bh(data=data)
        # Trades
        saldo += self.saldo_acoes_trade(data=data)
        # CDB/RDB
        saldo += self.saldo_cdb_rdb(data=data)
        # CRI/CRA
        saldo += self.saldo_cri_cra(data=data)
        # Debêntures
        saldo += self.saldo_debentures(data=data)
        # FII
        saldo += self.saldo_fii(data=data)
        # Fundo de investimento
        saldo += self.saldo_fundo_investimento(data=data)
        # LC
        saldo += self.saldo_lc(data=data)
        # Outros investimetnos
        saldo += self.saldo_outros_invest(data=data)
        # TD
        saldo += self.saldo_td(data=data)
        
        return saldo
    
class DivisaoPrincipal (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    investidor = models.OneToOneField('Investidor', on_delete=models.CASCADE, primary_key=True)

class DivisaoInvestimento (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    investimento = models.OneToOneField('outros_investimentos.Investimento')
    """
    Guarda a quantidade do investimento que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade', max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'investimento')
        
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.investimento)
    
    """
    Calcula o percentual do investimento que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.investimento.quantidade
    
class DivisaoOperacaoLC (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('OperacaoLetraCredito')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoCDB_RDB (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('cdb_rdb.OperacaoCDB_RDB')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoCriptomoeda (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('criptomoeda.OperacaoCriptomoeda')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=21, decimal_places=12)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoTransferenciaCriptomoeda (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    transferencia = models.ForeignKey('criptomoeda.TransferenciaCriptomoeda')
    """
    Guarda a quantidade da transferência que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=21, decimal_places=12)
    
    class Meta:
        unique_together=('divisao', 'transferencia')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.transferencia)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoCRI_CRA (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('cri_cra.OperacaoCRI_CRA')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=11, decimal_places=2)
     
    class Meta:
        unique_together=('divisao', 'operacao')
     
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
     
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoDebenture (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('OperacaoDebenture')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoFundoInvestimento (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('fundo_investimento.OperacaoFundoInvestimento')
    """
    Guarda a quantidade do valor da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoAcao (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('OperacaoAcao')
    """
    Guarda a quantidade de ações que pertence a divisão
    """
    quantidade = models.IntegerField('Quantidade')
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return Decimal(self.quantidade) / self.operacao.quantidade
    
class DivisaoOperacaoTD (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('OperacaoTitulo')
    """
    Guarda a quantidade de títulos que pertence a divisão
    """
    quantidade = models.DecimalField(u'Quantidade', max_digits=7, decimal_places=2) 
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
        
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoFII (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('OperacaoFII')
    """
    Guarda a quantidade de FIIs que pertence a divisão
    """
    quantidade = models.IntegerField('Quantidade')
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
        
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return Decimal(self.quantidade) / self.operacao.quantidade
    
class CheckpointDivisaoFII (models.Model):
    ano = models.SmallIntegerField(u'Ano')
    fii = models.ForeignKey('FII')
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    quantidade = models.IntegerField(u'Quantidade no ano', validators=[MinValueValidator(0)])
    preco_medio = models.DecimalField(u'Preço médio', max_digits=11, decimal_places=4)
    
    class Meta:
        unique_together=('fii', 'ano', 'divisao')
    
class CheckpointDivisaoProventosFII (models.Model):
    ano = models.SmallIntegerField(u'Ano')
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    valor = models.DecimalField(u'Valor da poupança de proventos', max_digits=22, decimal_places=16)
        
    class Meta:
        unique_together=('ano', 'divisao')
    
    
class TransferenciaEntreDivisoes(models.Model):
    TIPO_INVESTIMENTO_BUY_AND_HOLD = 'B'
    TIPO_INVESTIMENTO_CDB_RDB = 'C'
    TIPO_INVESTIMENTO_TESOURO_DIRETO = 'D'
    TIPO_INVESTIMENTO_DEBENTURE = 'E'
    TIPO_INVESTIMENTO_FII = 'F'
    TIPO_INVESTIMENTO_FUNDO_INV = 'I'
    TIPO_INVESTIMENTO_LCI_LCA = 'L'
    TIPO_INVESTIMENTO_CRIPTOMOEDA = 'M'
    TIPO_INVESTIMENTO_OUTROS_INVEST = 'O'
    TIPO_INVESTIMENTO_CRI_CRA = 'R'
    TIPO_INVESTIMENTO_TRADING = 'T'
    
    ESCOLHAS_TIPO_INVESTIMENTO = (('', 'Fonte externa'), 
                                  (TIPO_INVESTIMENTO_BUY_AND_HOLD, 'Buy and Hold'), 
                                  (TIPO_INVESTIMENTO_CDB_RDB, 'CDB/RDB'), 
                                  (TIPO_INVESTIMENTO_TESOURO_DIRETO, 'Tesouro Direto'), 
                                  (TIPO_INVESTIMENTO_DEBENTURE, 'Debênture'),
                                  (TIPO_INVESTIMENTO_FII, 'Fundo de Inv. Imobiliário'), 
                                  (TIPO_INVESTIMENTO_FUNDO_INV, 'Fundo de Investimento'),
                                  (TIPO_INVESTIMENTO_LCI_LCA, 'Letras de Crédito'), 
                                  (TIPO_INVESTIMENTO_CRIPTOMOEDA, 'Criptomoeda'),
                                  (TIPO_INVESTIMENTO_CRI_CRA, 'CRI/CRA'), 
                                  (TIPO_INVESTIMENTO_TRADING, 'Trading'),
                                  (TIPO_INVESTIMENTO_OUTROS_INVEST, 'Outros investimentos'))
    
    """
    Transferências em dinheiro entre as divisões, cedente ou recebedor nulos significa que
    é uma transferência de dinheiro de/para meio externo
    """
    divisao_cedente = models.ForeignKey('Divisao', verbose_name=u'Divisão cedente', blank=True, null=True, related_name='divisao_cedente')
    divisao_recebedora = models.ForeignKey('Divisao', verbose_name=u'Divisão recebedora', blank=True, null=True, related_name='divisao_recebedora')
    data = models.DateField(u'Data da transferência', blank=True, null=True)
    """
    B = Buy and Hold; C = CDB/RDB; D = Tesouro Direto; E = Debênture; F = FII; 
    I = Fundo de investimento; L = Letra de Crédito; R = CRI/CRA; T = Trading; O = Outros investimentos; N = Não alocado
    """
    investimento_origem = models.CharField('Investimento de origem', blank=True, null=True, max_length=1)
    investimento_destino = models.CharField('Investimento de destino', blank=True, null=True, max_length=1)
    """
    Quantidade em R$
    """
    quantidade = models.DecimalField(u'Quantidade transferida', max_digits=11, decimal_places=2)
    descricao = models.CharField(u'Descrição', blank=True, null=True, max_length=150)
    
    def __unicode__(self):
        descricao = ('(' + self.descricao + ')') if self.descricao else ''
        nome_divisao_cedente = self.divisao_cedente.nome if self.divisao_cedente else 'Meio externo'
        nome_divisao_recebedora = self.divisao_recebedora.nome if self.divisao_recebedora else 'Meio externo'
        return 'R$' + str(self.quantidade) + ' de ' + nome_divisao_cedente + ' para ' + nome_divisao_recebedora + ' em ' + str(self.data) + ' ' + descricao
    
    def intradivisao(self):
        """
        Verifica se a transferência foi feita entre investimentos de uma mesma divisão
        """
        return self.divisao_cedente == self.divisao_recebedora
    
    def investimento_origem_completo(self):
        if self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_BUY_AND_HOLD:
            return 'Buy and Hold'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB:
            return 'CDB/RDB'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TESOURO_DIRETO:
            return 'Tesouro Direto'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_DEBENTURE:
            return 'Debênture'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FII:
            return 'FII'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FUNDO_INV:
            return 'Fundo de inv.'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LCI_LCA:
            return 'Letra de Crédito'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRIPTOMOEDA:
            return 'Criptomoeda'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRI_CRA:
            return 'CRI/CRA'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TRADING:
            return 'Trading'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_OUTROS_INVEST:
            return 'Outros investimentos'
        elif self.investimento_origem == 'N':
            return 'Não alocado'
    
    def investimento_destino_completo(self):
        if self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_BUY_AND_HOLD:
            return 'Buy and Hold'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB:
            return 'CDB/RDB'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TESOURO_DIRETO:
            return 'Tesouro Direto'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_DEBENTURE:
            return 'Debênture'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FII:
            return 'FII'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FUNDO_INV:
            return 'Fundo de inv.'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LCI_LCA:
            return 'Letra de Crédito'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRIPTOMOEDA:
            return 'Criptomoeda'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRI_CRA:
            return 'CRI/CRA'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TRADING:
            return 'Trading'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_OUTROS_INVEST:
            return 'Outros investimentos'
        elif self.investimento_destino == 'N':
            return 'Não alocado'
    
# class EntradaProgramada(models.Model):
#     divisao
#     investimento
#     quantidade
#     frequencia
#     data_inicio
#     data_fim