# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.cdb_rdb.models import CDB_RDB, OperacaoCDB_RDB, \
    HistoricoPorcentagemCDB_RDB, HistoricoCarenciaCDB_RDB, OperacaoVendaCDB_RDB, \
    HistoricoVencimentoCDB_RDB
from django import forms
from django.forms import widgets
import datetime


ESCOLHAS_CDB_RDB=(('C', 'CDB'), 
                  ('R', 'RDB'))

ESCOLHAS_TIPO_RENDIMENTO=((1, 'Prefixado'), 
                            (2, 'Pós-fixado'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class CDB_RDBForm(LocalizedModelForm):
    class Meta:
        model = CDB_RDB
        fields = ('nome', 'tipo', 'tipo_rendimento')
        widgets={'tipo': widgets.Select(choices=ESCOLHAS_CDB_RDB),
                 'tipo_rendimento': widgets.Select(choices=ESCOLHAS_TIPO_RENDIMENTO),}

class OperacaoCDB_RDBForm(LocalizedModelForm):
    # Campo verificado apenas no caso de venda de operação de cdb/rdb
    operacao_compra = forms.ModelChoiceField(label='Operação de compra', queryset=OperacaoCDB_RDB.objects.filter(tipo_operacao='C'), required=False)
    
    class Meta:
        model = OperacaoCDB_RDB
        fields = ('tipo_operacao', 'quantidade', 'data', 'operacao_compra',
                  'investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/form_operacao_cdb_rdb.min.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoCDB_RDBForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['investimento'].required = False
        self.fields['investimento'].queryset = CDB_RDB.objects.filter(investidor=self.investidor)
        self.fields['operacao_compra'].queryset = OperacaoCDB_RDB.objects.filter(tipo_operacao='C', investidor=self.investidor)
        # Remover operações que já tenham sido totalmente vendidas e a própria operação
        operacoes_compra_invalidas = [operacao_compra_invalida.id for operacao_compra_invalida in self.fields['operacao_compra'].queryset if operacao_compra_invalida.qtd_disponivel_venda() == 0] + \
            ([self.instance.id] if self.instance.id != None else [])
        # Manter operação de compra atual, caso seja edição de venda
        if self.instance.operacao_compra_relacionada() and self.instance.operacao_compra_relacionada().id in operacoes_compra_invalidas:
            operacoes_compra_invalidas.remove(self.instance.operacao_compra_relacionada().id)
        self.fields['operacao_compra'].queryset = self.fields['operacao_compra'].queryset.exclude(id__in=operacoes_compra_invalidas)
    
    def clean_operacao_compra(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            operacao_compra = self.cleaned_data.get('operacao_compra')
            # Testar se operacao_compra é válido
            if operacao_compra is None:
                raise forms.ValidationError('Selecione operação de compra válida')
            # Testar data, deve ser posterior a operação de compra relacionada
            if 'data' not in self.cleaned_data or self.cleaned_data['data'] == None:
                return None
            else:
                if self.cleaned_data["data"] < operacao_compra.data + datetime.timedelta(days=operacao_compra.carencia()):
                    raise forms.ValidationError('Data da venda deve ser posterior ao período de carência (%s)' % 
                                                ((operacao_compra.data + datetime.timedelta(days=operacao_compra.carencia())).strftime("%d/%m/%Y")))
            # Testar quantidade
            quantidade = self.cleaned_data['quantidade']
            registros_desconsiderar = list()
            if self.instance.id != None:
                registros_desconsiderar.append(self.instance.id)
            if quantidade > operacao_compra.qtd_disponivel_venda(desconsiderar_vendas=registros_desconsiderar):
                raise forms.ValidationError('Não é possível vender mais do que o disponível na operação de compra')
            return operacao_compra
        return None

    def clean_investimento(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            if self.cleaned_data.get('operacao_compra'):
                cdb_rdb = self.cleaned_data.get('operacao_compra').investimento
                return cdb_rdb
        else:
            cdb = self.cleaned_data.get('investimento')
            if cdb is None:
                raise forms.ValidationError('Insira CDB válido')
            return cdb
        return None
    
    def clean(self):
        data = super(OperacaoCDB_RDBForm, self).clean()
        # Testa se não se trata de uma edição de compra para venda
        if data.get('tipo_operacao') == 'V' and self.instance.tipo_operacao == 'C':
            # Verificar se já há vendas registradas para essa compra, se sim, lançar erro
            if OperacaoVendaCDB_RDB.objects.filter(operacao_compra=self.instance):
                raise forms.ValidationError('Não é possível alterar tipo de operação pois já há vendas registradas para essa compra')

class HistoricoPorcentagemCDB_RDBForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoPorcentagemCDB_RDB
        fields = ('porcentagem', 'data', 'cdb_rdb')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels={'cdb_rdb': 'CDB/RDB'}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.cdb_rdb = kwargs.pop('cdb_rdb')
        except:
            self.cdb_rdb = None
        super(HistoricoPorcentagemCDB_RDBForm, self).__init__(*args, **kwargs)
        if self.cdb_rdb:
            self.fields['cdb_rdb'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_cdb_rdb(self):
        cdb_rdb = self.cleaned_data['cdb_rdb']
        if cdb_rdb.investidor != self.investidor:
            raise forms.ValidationError('CDB/RDB inválido')
        if hasattr(self.instance, 'cdb_rdb') and cdb_rdb != self.instance.cdb_rdb:
            raise forms.ValidationError('CDB/RDB não deve ser alterado')
        return cdb_rdb
        
    def clean_data(self):
        data = self.cleaned_data['data']
        # Verifica se o registro é da data incial, e se foi feita alteração
        if self.inicial and data:
            raise forms.ValidationError('Data inicial não pode ser alterada')
        elif not self.inicial and not data:
            raise forms.ValidationError('Data é obrigatória')
        return data
    
    def clean_porcentagem(self):
        porcentagem = self.cleaned_data['porcentagem']
        if porcentagem <= 0:
            raise forms.ValidationError('Porcentagem deve ser maior que zero')
        return porcentagem
    
    def clean(self):
        cleaned_data = super(HistoricoPorcentagemCDB_RDBForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de porcentagem para essa data')
        return cleaned_data
        
class HistoricoCarenciaCDB_RDBForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoCarenciaCDB_RDB
        fields = ('carencia', 'data', 'cdb_rdb')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'carencia': 'Período de carência',
                  'cdb_rdb': 'CDB/RDB'}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.cdb_rdb = kwargs.pop('cdb_rdb')
        except:
            self.cdb_rdb = None
        super(HistoricoCarenciaCDB_RDBForm, self).__init__(*args, **kwargs)
        if self.cdb_rdb:
            self.fields['cdb_rdb'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_carencia(self):
        carencia = self.cleaned_data['carencia']
        if carencia <= 0:
            raise forms.ValidationError('Carência deve ser de pelo menos 1 dia')
        return carencia
    
    def clean_cdb_rdb(self):
        cdb_rdb = self.cleaned_data['cdb_rdb']
        if cdb_rdb.investidor != self.investidor:
            raise forms.ValidationError('CDB/RDB inválido')
        if hasattr(self.instance, 'cdb_rdb') and cdb_rdb != self.instance.cdb_rdb:
            raise forms.ValidationError('CDB/RDB não deve ser alterado')
        return cdb_rdb
    
    def clean_data(self):
        data = self.cleaned_data['data']
        # Verifica se o registro é da data incial, e se foi feita alteração
        if self.inicial and data:
            raise forms.ValidationError('Data inicial não pode ser alterada')
        elif not self.inicial and not data:
            raise forms.ValidationError('Data é obrigatória')
        return data
    
    def clean(self):
        cleaned_data = super(HistoricoCarenciaCDB_RDBForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de carência para essa data')
        
        # Testes para datas iniciais
        if self.inicial:
            # Verificar vencimento inicial e todos os vencimentos até próxima alteração de carência
            vencimento_inicial = HistoricoVencimentoCDB_RDB.objects.get(cdb_rdb=cleaned_data.get('cdb_rdb'), data__isnull=True).vencimento
            if vencimento_inicial < cleaned_data.get('carencia'):
                raise forms.ValidationError('Carência inicial está maior do que período de vencimento inicial')
            elif HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__isnull=False).exists():
                # Verificar alterações de vencimento entre a vencimento carência e a próxima alteração
                proxima_carencia = HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__isnull=False).order_by('data')[0]
                for vencimento_periodo in HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__lt=proxima_carencia.data):
                    if vencimento_periodo.vencimento > cleaned_data.get('carencia'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (vencimento_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de vencimento a partir da data dessa alteração de carência
                for vencimento_periodo in HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb')):
                    if vencimento_periodo.vencimento > cleaned_data.get('carencia'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (vencimento_periodo.data.strftime('%d/%m/%Y')))
            
            
        else:
            # Verificar vencimento vigente, e alterações de vencimento ao longo do período que a nova carência estiver vigente
            vencimento_vigente = cleaned_data.get('cdb_rdb').vencimento_na_data(cleaned_data.get('data'))
            if vencimento_vigente < cleaned_data.get('carencia'):
                raise forms.ValidationError('Vencimento na data de início está menor do que o período de carência')
            # Testar se período de carência será maior que algum período de vencimento vigente
            if HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__gt=cleaned_data.get('data')).exists():
                # Verificar alterações de vencimento entre a data dessa alteração de carência e a próxima
                proxima_carencia = HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__gt=cleaned_data.get('data')).order_by('data')[0]
                for vencimento_periodo in HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__range=[cleaned_data.get('data') + datetime.timedelta(days=1), 
                                                                                                                   proxima_carencia.data - datetime.timedelta(days=1)]):
                    if vencimento_periodo.vencimento < cleaned_data.get('carencia'):
                        raise forms.ValidationError('Vencimento vigente em %s está menor do que o período de carência' % (vencimento_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de vencimento a partir da data dessa alteração de carência
                for vencimento_periodo in HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__gt=cleaned_data.get('data')):
                    if vencimento_periodo.vencimento < cleaned_data.get('carencia'):
                        raise forms.ValidationError('Vencimento vigente em %s está menor do que o período de carência' % (vencimento_periodo.data.strftime('%d/%m/%Y')))
                
        return cleaned_data
    
class HistoricoVencimentoCDB_RDBForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoVencimentoCDB_RDB
        fields = ('vencimento', 'data', 'cdb_rdb')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'vencimento': 'Período de vencimento',
                  'cdb_rdb': 'CDB/RDB'}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.cdb_rdb = kwargs.pop('cdb_rdb')
        except:
            self.cdb_rdb = None
        super(HistoricoVencimentoCDB_RDBForm, self).__init__(*args, **kwargs)
        if self.cdb_rdb:
            self.fields['cdb_rdb'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_vencimento(self):
        vencimento = self.cleaned_data['vencimento']
        if vencimento <= 0:
            raise forms.ValidationError('Período de vencimento deve ser de pelo menos 1 dia')
        return vencimento
    
    def clean_cdb_rdb(self):
        cdb_rdb = self.cleaned_data['cdb_rdb']
        if cdb_rdb.investidor != self.investidor:
            raise forms.ValidationError('CDB/RDB inválido')
        if hasattr(self.instance, 'cdb_rdb') and cdb_rdb != self.instance.cdb_rdb:
            raise forms.ValidationError('CDB/RDB não deve ser alterado')
        return cdb_rdb
    
    def clean_data(self):
        data = self.cleaned_data['data']
        # Verifica se o registro é da data incial, e se foi feita alteração
        if self.inicial and data:
            raise forms.ValidationError('Data inicial não pode ser alterada')
        elif not self.inicial and not data:
            raise forms.ValidationError('Data é obrigatória')
        return data
    
    def clean(self):
        cleaned_data = super(HistoricoVencimentoCDB_RDBForm, self).clean()
        cleaned_data.get('cdb_rdb')
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de vencimento para essa data')
        
        # Testes para datas iniciais
        if self.inicial:
            # Verificar carência inicial e todas as carências até próxima alteração de vencimento
            carencia_inicial = HistoricoCarenciaCDB_RDB.objects.get(cdb_rdb=cleaned_data.get('cdb_rdb'), data__isnull=True).carencia
            if carencia_inicial > cleaned_data.get('vencimento'):
                raise forms.ValidationError('Carência inicial está maior do que período de vencimento inicial')
            elif HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__isnull=False).exists():
                # Verificar alterações de carência entre o vencimento inicial e a próxima alteração
                proximo_vencimento = HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__isnull=False).order_by('data')[0]
                for carencia_periodo in HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__lt=proximo_vencimento.data):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de carência a partir da data dessa alteração de vencimento
                for carencia_periodo in HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb')):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            
        # Testes para datas não iniciais
        else:
            # Verificar carência vigente, e alterações de carência ao longo do período que esse novo vencimento estiver vigente
            carencia_vigente = cleaned_data.get('cdb_rdb').carencia_na_data(cleaned_data.get('data'))
            if carencia_vigente > cleaned_data.get('vencimento'):
                raise forms.ValidationError('Carência na data de início está maior do que o período de vencimento')
            # Testar se período de vencimento será menor que algum período de carência vigente
            if HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__gt=cleaned_data.get('data')).exists():
                # Verificar alterações de carência entre a data dessa alteração de vencimento e a próxima
                proximo_vencimento = HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__gt=cleaned_data.get('data')).order_by('data')[0]
                for carencia_periodo in HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__range=[cleaned_data.get('data') + datetime.timedelta(days=1), 
                                                                                                                   proximo_vencimento.data - datetime.timedelta(days=1)]):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de carência a partir da data dessa alteração de vencimento
                for carencia_periodo in HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cleaned_data.get('cdb_rdb'), data__gt=cleaned_data.get('data')):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
        
                
        return cleaned_data