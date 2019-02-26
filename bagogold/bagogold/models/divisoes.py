# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.aggregates import Sum, Count
from django.db.models.expressions import Case, When, F
from django.db.models.fields import DecimalField

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.outros_investimentos.models import Amortizacao, Rendimento


class Divisao (models.Model):
    INVESTIMENTO_ACOES_CODIGO = 'A'
    INVESTIMENTO_CDB_RDB_CODIGO = 'C'
    INVESTIMENTO_CRI_CRA_CODIGO = 'R'
    INVESTIMENTO_CRIPTOMOEDAS_CODIGO = 'M'
    INVESTIMENTO_DEBENTURES_CODIGO = 'D'
    INVESTIMENTO_FII_CODIGO = 'F'
    INVESTIMENTO_FUNDO_INV_CODIGO = 'I'
    INVESTIMENTO_LCI_LCA_CODIGO = 'L'
    INVESTIMENTO_LETRAS_CAMBIO_CODIGO = 'A'
    INVESTIMENTO_OUTROS_INV_CODIGO = 'O'
    INVESTIMENTO_TESOURO_DIRETO_CODIGO = 'T'
    
    INVESTIMENTO_ACOES_DESCRICAO = u'Ações'
    INVESTIMENTO_CDB_RDB_DESCRICAO = 'CDB/RDB'
    INVESTIMENTO_CRI_CRA_DESCRICAO = 'CRI/CRA'
    INVESTIMENTO_CRIPTOMOEDAS_DESCRICAO = 'Criptomoedas'
    INVESTIMENTO_DEBENTURES_DESCRICAO = u'Debêntures'
    INVESTIMENTO_FII_DESCRICAO = 'FII'
    INVESTIMENTO_FUNDO_INV_DESCRICAO = 'Fundos de Investimento'
    INVESTIMENTO_LCI_LCA_DESCRICAO = 'LCI/LCA'
    INVESTIMENTO_LETRAS_CAMBIO_DESCRICAO = u'Letras de Câmbio'
    INVESTIMENTO_OUTROS_INV_DESCRICAO = 'Outros Investimentos'
    INVESTIMENTO_TESOURO_DIRETO_DESCRICAO = 'Tesouro Direto'
    
    INVESTIMENTOS_DISPONIVEIS_TIMELINE = {
        INVESTIMENTO_LETRAS_CAMBIO_CODIGO: INVESTIMENTO_LETRAS_CAMBIO_DESCRICAO,
        INVESTIMENTO_CDB_RDB_CODIGO: INVESTIMENTO_CDB_RDB_DESCRICAO,
        INVESTIMENTO_LCI_LCA_CODIGO: INVESTIMENTO_LCI_LCA_DESCRICAO,
        INVESTIMENTO_CRIPTOMOEDAS_CODIGO: INVESTIMENTO_CRIPTOMOEDAS_DESCRICAO,
        INVESTIMENTO_TESOURO_DIRETO_CODIGO: INVESTIMENTO_TESOURO_DIRETO_DESCRICAO
    }
    
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
        possui_operacoes = (DivisaoOperacaoAcao.objects.filter(divisao=self).count() + DivisaoOperacaoCDB_RDB.objects.filter(divisao=self).count() + DivisaoOperacaoFII.objects.filter(divisao=self).count() \
            + DivisaoOperacaoFundoInvestimento.objects.filter(divisao=self).count() + DivisaoOperacaoLCI_LCA.objects.filter(divisao=self).count() + DivisaoOperacaoTD.objects.filter(divisao=self).count() \
            + DivisaoOperacaoCriptomoeda.objects.filter(divisao=self).count() + DivisaoOperacaoDebenture.objects.filter(divisao=self).count() + DivisaoOperacaoCRI_CRA.objects.filter(divisao=self).count() \
            + DivisaoInvestimento.objects.filter(divisao=self).count() + DivisaoOperacaoLetraCambio.objects.filter(divisao=self).count()) > 0
        
        return possui_operacoes
    
    def buscar_data_primeira_operacao(self):
        datas_primeira_operacao = list()
        
        # Preencher com as primeiras datas de operação para cada investimento
        if DivisaoOperacaoAcao.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoAcao.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoOperacaoCDB_RDB.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoCDB_RDB.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoOperacaoCriptomoeda.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoCriptomoeda.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoOperacaoFII.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoFII.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoOperacaoLCI_LCA.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoLCI_LCA.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoOperacaoDebenture.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoDebenture.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoOperacaoFundoInvestimento.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoFundoInvestimento.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoOperacaoCRI_CRA.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoCRI_CRA.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoOperacaoTD.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoOperacaoTD.objects.filter(divisao=self).order_by('operacao__data')[0].operacao.data)
        if DivisaoInvestimento.objects.filter(divisao=self).exists():
            datas_primeira_operacao.append(DivisaoInvestimento.objects.filter(divisao=self).order_by('investimento__data')[0].investimento.data)
        
        if len(datas_primeira_operacao) == 0:
            return None
        
        return min(datas_primeira_operacao)
    
    def saldo_acoes_bh(self, data=datetime.date.today()):
        from bagogold.bagogold.models.acoes import UsoProventosOperacaoAcao
        from bagogold.bagogold.utils.acoes import \
            calcular_poupanca_prov_acao_ate_dia_por_divisao
        """
        Calcula o saldo de operações de ações Buy and Hold de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self, operacao__destinacao='B', operacao__data__lte=data).select_related('operacao'):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
        
        saldo += UsoProventosOperacaoAcao.objects.filter(divisao_operacao__divisao=self).aggregate(qtd_total=Sum('qtd_utilizada'))['qtd_total'] or 0
        
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
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self, operacao__destinacao='T', operacao__data__lte=data).select_related('operacao'):
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
        from bagogold.bagogold.utils.taxas_indexacao import calcular_valor_atualizado_com_taxas_di, \
            calcular_valor_atualizado_com_taxa_prefixado
        from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo, calcular_iof_e_ir_longo_prazo
        from bagogold.cdb_rdb.models import CDB_RDB
        """
        Calcula o saldo de operações de CDB/RDB de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        historico_di = HistoricoTaxaDI.objects.all()
        # Computar compras
        saldo -= (DivisaoOperacaoCDB_RDB.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='C').aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        for venda_divisao in DivisaoOperacaoCDB_RDB.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='V') \
            .annotate(tipo_rendimento=F('operacao__cdb_rdb__tipo_rendimento')).select_related('operacao__cdb_rdb'):
            # Para venda, calcular valor do cdb/rdb no dia da venda
            valor_venda = venda_divisao.quantidade
             
            # Calcular o valor atualizado
            if venda_divisao.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
                # DI
                dias_de_rendimento = historico_di.filter(data__gte=venda_divisao.operacao.operacao_compra_relacionada().data, data__lt=venda_divisao.operacao.data)
                taxas_dos_dias = dict(dias_de_rendimento.values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
                valor_venda = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor_venda, venda_divisao.operacao.porcentagem())
                valor_venda -= sum(calcular_iof_e_ir_longo_prazo(valor_venda - venda_divisao.quantidade, 
                                                              (venda_divisao.operacao.data - venda_divisao.operacao.operacao_compra_relacionada().data).days))
            elif venda_divisao.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
                # Prefixado
                # Calcular quantidade dias para valorização
                qtd_dias = qtd_dias_uteis_no_periodo(venda_divisao.operacao.operacao_compra_relacionada().data, venda_divisao.operacao.data)
                valor_venda = calcular_valor_atualizado_com_taxa_prefixado(valor_venda, venda_divisao.operacao.porcentagem(), qtd_dias)
                valor_venda -= sum(calcular_iof_e_ir_longo_prazo(valor_venda - venda_divisao.quantidade, 
                                                              (venda_divisao.operacao.data - venda_divisao.operacao.operacao_compra_relacionada().data).days))
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
        
        # Transferências de criptomoedas
        saldo -= DivisaoTransferenciaCriptomoeda.objects.filter(divisao=self, transferencia__data__lte=data, transferencia__moeda__isnull=True) \
                    .aggregate(total_taxas=Sum('transferencia__taxa'))['total_taxas'] or 0
        
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
        from bagogold.fii.utils import \
            calcular_poupanca_prov_fii_ate_dia_por_divisao
        """
        Calcula o saldo de operações de FII de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoFII.objects.filter(divisao=self, operacao__data__lte=data).select_related('operacao'):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos - operacao.qtd_proventos_utilizada()) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
        
        # Proventos
        saldo += calcular_poupanca_prov_fii_ate_dia_por_divisao(self, data)    
        
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FII, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FII, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_fundo_investimento(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de fundo de investimento de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoFundoInvestimento.objects.filter(divisao=self, operacao__data__lte=data).annotate(tipo_operacao=F('operacao__tipo_operacao')):
            if operacao_divisao.tipo_operacao == 'C':
                saldo -= operacao_divisao.quantidade 
            elif operacao_divisao.tipo_operacao == 'V':
                saldo += operacao_divisao.quantidade
                
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FUNDO_INV, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FUNDO_INV, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_lc(self, data=datetime.date.today()):
        from bagogold.bagogold.utils.taxas_indexacao import calcular_valor_atualizado_com_taxas_di, \
            calcular_valor_atualizado_com_taxa_prefixado
        from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo, calcular_iof_e_ir_longo_prazo
        
        from bagogold.lc.models import LetraCambio
        """
        Calcula o saldo de operações de Letra de Câmbio de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        historico_di = HistoricoTaxaDI.objects.all()
        
        # Computar compras
        saldo -= (DivisaoOperacaoLetraCambio.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='C').aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        for venda_divisao in DivisaoOperacaoLetraCambio.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='V') \
            .annotate(tipo_rendimento=F('operacao__lc__tipo_rendimento')).select_related('operacao', 'operacao__lc'):
            # Para venda, calcular valor do cdb/rdb no dia da venda
            valor_venda = venda_divisao.quantidade
             
            # Calcular o valor atualizado
            if venda_divisao.tipo_rendimento == LetraCambio.LC_DI:
                # DI
                dias_de_rendimento = historico_di.filter(data__gte=venda_divisao.operacao.operacao_compra_relacionada().data, data__lt=venda_divisao.operacao.data)
                taxas_dos_dias = dict(dias_de_rendimento.values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
                valor_venda = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor_venda, venda_divisao.operacao.porcentagem())
                valor_venda -= sum(calcular_iof_e_ir_longo_prazo(valor_venda - venda_divisao.quantidade, 
                                                              (venda_divisao.operacao.data - venda_divisao.operacao.operacao_compra_relacionada().data).days))
            elif venda_divisao.tipo_rendimento == LetraCambio.LC_PREFIXADO:
                # Prefixado
                # Calcular quantidade dias para valorização
                qtd_dias = qtd_dias_uteis_no_periodo(venda_divisao.operacao.operacao_compra_relacionada().data, venda_divisao.operacao.data)
                valor_venda = calcular_valor_atualizado_com_taxa_prefixado(valor_venda, venda_divisao.operacao.porcentagem(), qtd_dias)
                valor_venda -= sum(calcular_iof_e_ir_longo_prazo(valor_venda - venda_divisao.quantidade, 
                                                              (venda_divisao.operacao.data - venda_divisao.operacao.operacao_compra_relacionada().data).days))
            
            # Arredondar
            str_auxiliar = str(valor_venda.quantize(Decimal('.0001')))
            valor_venda = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            saldo += valor_venda
        
        # Transferências
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LC, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LC, data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_lci_lca(self, data=datetime.date.today()):
        from bagogold.bagogold.utils.taxas_indexacao import calcular_valor_atualizado_com_taxas_di
        """
        Calcula o saldo de operações de Letra de Crédito de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        historico_di = HistoricoTaxaDI.objects.all()
        
        # Computar compras
        saldo -= (DivisaoOperacaoLCI_LCA.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='C').aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        for venda_divisao in DivisaoOperacaoLCI_LCA.objects.filter(divisao=self, operacao__data__lte=data, operacao__tipo_operacao='V').select_related('operacao', 'operacao__letra_credito'):
            # Para venda, calcular valor do cdb/rdb no dia da venda
            valor_venda = venda_divisao.quantidade
             
            # Calcular o valor atualizado
            dias_de_rendimento = historico_di.filter(data__gte=venda_divisao.operacao.operacao_compra_relacionada().data, data__lt=venda_divisao.operacao.data)
            taxas_dos_dias = dict(dias_de_rendimento.values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            valor_venda = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor_venda, venda_divisao.operacao.porcentagem())
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
        for operacao_divisao in DivisaoOperacaoTD.objects.filter(divisao=self, operacao__data__lte=data).select_related('operacao'):
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
        # Letra de Câmbio
        saldo += self.saldo_lc(data=data)
        # Letra de Crédito
        saldo += self.saldo_lci_lca(data=data)
        # Outros investimentos
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
    
class DivisaoOperacaoLetraCambio (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('lc.OperacaoLetraCambio')
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
    
    def divisao_operacao_compra_relacionada(self):
        from bagogold.lc.models import OperacaoVendaLetraCambio
        if self.operacao.tipo_operacao == 'V':
            return DivisaoOperacaoLetraCambio.objects.get(operacao=OperacaoVendaLetraCambio.objects.get(operacao_venda=self.operacao).operacao_compra, divisao_id=self.divisao_id)
        else:
            return None
    
    def qtd_disponivel_venda_na_data(self, data, desconsiderar_operacao=None):
        from bagogold.lc.models import OperacaoVendaLetraCambio
        if self.operacao.tipo_operacao != 'C':
            raise ValueError('Operação deve ser de compra')
        vendas = OperacaoVendaLetraCambio.objects.filter(operacao_compra=self.operacao_id, operacao_venda__data__lte=data).exclude(operacao_venda=desconsiderar_operacao).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in DivisaoOperacaoLetraCambio.objects.filter(operacao__id__in=vendas, divisao_id=self.divisao_id):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
class CheckpointDivisaoLetraCambio (models.Model):
    ano = models.SmallIntegerField(u'Ano')
    divisao_operacao = models.ForeignKey('DivisaoOperacaoLetraCambio', limit_choices_to={'operacao__tipo_operacao': 'C'})
    qtd_restante = models.DecimalField(u'Quantidade restante da operação', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    qtd_atualizada = models.DecimalField(u'Quantidade atualizada da operação', max_digits=17, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    
    class Meta:
        unique_together=('divisao_operacao', 'ano')
        
class DivisaoOperacaoLCI_LCA (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    operacao = models.ForeignKey('lci_lca.OperacaoLetraCredito')
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
    
    def divisao_operacao_compra_relacionada(self):
        from bagogold.lci_lca.models import OperacaoVendaLetraCredito
        if self.operacao.tipo_operacao == 'V':
            return DivisaoOperacaoLCI_LCA.objects.get(operacao=OperacaoVendaLetraCredito.objects.get(operacao_venda=self.operacao).operacao_compra, divisao_id=self.divisao_id)
        else:
            return None
    
    def qtd_disponivel_venda_na_data(self, data, desconsiderar_operacao=None):
        from bagogold.lci_lca.models import OperacaoVendaLetraCredito
        if self.operacao.tipo_operacao != 'C':
            raise ValueError('Operação deve ser de compra')
        vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra=self.operacao, operacao_venda__data__lte=data).exclude(operacao_venda=desconsiderar_operacao).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in DivisaoOperacaoLCI_LCA.objects.filter(operacao__id__in=vendas, divisao_id=self.divisao_id):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
class CheckpointDivisaoLCI_LCA (models.Model):
    ano = models.SmallIntegerField(u'Ano')
    divisao_operacao = models.ForeignKey('DivisaoOperacaoLCI_LCA', limit_choices_to={'operacao__tipo_operacao': 'C'})
    qtd_restante = models.DecimalField(u'Quantidade restante da operação', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    qtd_atualizada = models.DecimalField(u'Quantidade atualizada da operação', max_digits=17, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    
    class Meta:
        unique_together=('divisao_operacao', 'ano')
    
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
    
    def divisao_operacao_compra_relacionada(self):
        from bagogold.cdb_rdb.models import OperacaoVendaCDB_RDB
        if self.operacao.tipo_operacao == 'V':
            return DivisaoOperacaoCDB_RDB.objects.get(operacao=OperacaoVendaCDB_RDB.objects.get(operacao_venda=self.operacao).operacao_compra, divisao_id=self.divisao_id)
        else:
            return None
    
    def qtd_disponivel_venda_na_data(self, data, desconsiderar_operacao=None):
        from bagogold.cdb_rdb.models import OperacaoVendaCDB_RDB
        if self.operacao.tipo_operacao != 'C':
            raise ValueError('Operação deve ser de compra')
        vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=self.operacao, operacao_venda__data__lte=data).exclude(operacao_venda=desconsiderar_operacao).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in DivisaoOperacaoCDB_RDB.objects.filter(operacao__id__in=vendas, divisao_id=self.divisao_id):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
class CheckpointDivisaoCDB_RDB (models.Model):
    ano = models.SmallIntegerField(u'Ano')
    divisao_operacao = models.ForeignKey('DivisaoOperacaoCDB_RDB', limit_choices_to={'operacao__tipo_operacao': 'C'})
    qtd_restante = models.DecimalField(u'Quantidade restante da operação', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    qtd_atualizada = models.DecimalField(u'Quantidade atualizada da operação', max_digits=17, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    
    class Meta:
        unique_together=('divisao_operacao', 'ano')
    
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
    
class DivisaoForkCriptomoeda (models.Model):
    divisao = models.ForeignKey('Divisao', verbose_name=u'Divisão')
    fork = models.ForeignKey('criptomoeda.Fork')
    """
    Guarda a quantidade do fork que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade', max_digits=21, decimal_places=12)
    
    class Meta:
        unique_together=('divisao', 'fork')
        
    def __unicode__(self):
        return self.divisao.nome + ': %s %s de fork de %s' % (str(self.quantidade), self.fork.moeda_recebida.ticker, self.fork.moeda_origem.ticker)
    
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
    operacao = models.ForeignKey('debentures.OperacaoDebenture')
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
    operacao = models.ForeignKey('tesouro_direto.OperacaoTitulo')
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
    operacao = models.ForeignKey('fii.OperacaoFII')
    """
    Guarda a quantidade de FIIs que pertence a divisão
    """
    quantidade = models.IntegerField('Quantidade', validators=[MinValueValidator(1)])
    
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
    fii = models.ForeignKey('fii.FII')
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
    TIPO_INVESTIMENTO_LC = 'A'
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
                                  (TIPO_INVESTIMENTO_LC, 'Letra de Câmbio'), 
                                  (TIPO_INVESTIMENTO_LCI_LCA, 'LCI/LCA'), 
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
    B = Buy and Hold; C = CDB/RDB; D = Tesouro Direto; E = Debênture; F = FII; I = Fundo de investimento;
    L = Letra de Crédito; M = Criptomoeda;  O = Outros investimentos; R = CRI/CRA; T = Trading; N = Não alocado
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
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LC:
            return 'Letra de Câmbio'
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
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LC:
            return 'Letra de Câmbio'
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