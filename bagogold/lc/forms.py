# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.lc.models import LetraCambio, OperacaoLetraCambio, \
    HistoricoPorcentagemLetraCambio, HistoricoCarenciaLetraCambio, OperacaoVendaLetraCambio, \
    HistoricoVencimentoLetraCambio
from django import forms
from django.forms import widgets
import datetime


ESCOLHAS_TIPO_RENDIMENTO=((1, 'Prefixado'), 
                            (2, 'Pós-fixado'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class LetraCambioForm(LocalizedModelForm):
    class Meta:
        model = LetraCambio
        fields = ('nome', 'tipo_rendimento')
        widgets={'tipo_rendimento': widgets.Select(choices=ESCOLHAS_TIPO_RENDIMENTO),}

class OperacaoLetraCambioForm(LocalizedModelForm):
    # Campo verificado apenas no caso de venda de operação de letra de cambio
    operacao_compra = forms.ModelChoiceField(label='Operação de compra', queryset=OperacaoLetraCambio.objects.filter(tipo_operacao='C'), required=False)
    
    class Meta:
        model = OperacaoLetraCambio
        fields = ('tipo_operacao', 'quantidade', 'data', 'operacao_compra',
                  'lc')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        labels = {'lc': u'Letra de Câmbio'}
        
    class Media:
        js = ('js/bagogold/form_operacao_lc.min.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoLetraCambioForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['lc'].required = False
        self.fields['lc'].queryset = LetraCambio.objects.filter(investidor=self.investidor)
        self.fields['operacao_compra'].queryset = OperacaoLetraCambio.objects.filter(tipo_operacao='C', investidor=self.investidor)
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
                if self.cleaned_data['data'] < operacao_compra.data_carencia():
                    raise forms.ValidationError('Data da venda deve ser posterior ao período de carência (%s)' % 
                                                (operacao_compra.data_carencia().strftime("%d/%m/%Y")))
                elif self.cleaned_data['data'] > operacao_compra.data_vencimento():
                    raise forms.ValidationError('Data da venda não pode ser após o período de vencimento (%s)' %
                                                (operacao_compra.data_vencimento().strftime("%d/%m/%Y")))
            # Testar quantidade
            quantidade = self.cleaned_data['quantidade']
            registros_desconsiderar = list()
            if self.instance.id != None:
                registros_desconsiderar.append(self.instance.id)
            if quantidade > operacao_compra.qtd_disponivel_venda(desconsiderar_vendas=registros_desconsiderar):
                raise forms.ValidationError('Não é possível vender mais do que o disponível na operação de compra')
            return operacao_compra
        return None

    def clean_lc(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            if self.cleaned_data.get('operacao_compra'):
                lc = self.cleaned_data.get('operacao_compra').lc
                return lc
        else:
            lc = self.cleaned_data.get('lc')
            if lc is None:
                raise forms.ValidationError('Insira CDB válido')
            return lc
        return None
    
    def clean(self):
        data = super(OperacaoLetraCambioForm, self).clean()
        # Testa se não se trata de uma edição de compra para venda
        if data.get('tipo_operacao') == 'V' and self.instance.tipo_operacao == 'C':
            # Verificar se já há vendas registradas para essa compra, se sim, lançar erro
            if OperacaoVendaLetraCambio.objects.filter(operacao_compra=self.instance):
                raise forms.ValidationError('Não é possível alterar tipo de operação pois já há vendas registradas para essa compra')

class HistoricoPorcentagemLetraCambioForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoPorcentagemLetraCambio
        fields = ('porcentagem', 'data', 'lc')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels={'lc': 'Letra de Câmbio'}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.lc = kwargs.pop('lc')
        except:
            self.lc = None
        super(HistoricoPorcentagemLetraCambioForm, self).__init__(*args, **kwargs)
        if self.lc:
            self.fields['lc'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_lc(self):
        lc = self.cleaned_data['lc']
        if lc.investidor != self.investidor:
            raise forms.ValidationError('Letra de Câmbio inválida')
        if hasattr(self.instance, 'lc') and lc != self.instance.lc:
            raise forms.ValidationError('Letra de Câmbio não deve ser alterada')
        return lc
        
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
        cleaned_data = super(HistoricoPorcentagemLetraCambioForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoPorcentagemLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de porcentagem para essa data')
        return cleaned_data
        
class HistoricoCarenciaLetraCambioForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoCarenciaLetraCambio
        fields = ('carencia', 'data', 'lc')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'carencia': 'Período de carência',
                  'lc': 'Letra de Câmbio'}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.lc = kwargs.pop('lc')
        except:
            self.lc = None
        super(HistoricoCarenciaLetraCambioForm, self).__init__(*args, **kwargs)
        if self.lc:
            self.fields['lc'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_carencia(self):
        carencia = self.cleaned_data['carencia']
        if carencia <= 0:
            raise forms.ValidationError('Carência deve ser de pelo menos 1 dia')
        return carencia
    
    def clean_lc(self):
        lc = self.cleaned_data['lc']
        if lc.investidor != self.investidor:
            raise forms.ValidationError('Letra de Câmbio inválida')
        if hasattr(self.instance, 'lc') and lc != self.instance.lc:
            raise forms.ValidationError('Letra de Câmbio não deve ser alterada')
        return lc
    
    def clean_data(self):
        data = self.cleaned_data['data']
        # Verifica se o registro é da data incial, e se foi feita alteração
        if self.inicial and data:
            raise forms.ValidationError('Data inicial não pode ser alterada')
        elif not self.inicial and not data:
            raise forms.ValidationError('Data é obrigatória')
        return data
    
    def clean(self):
        cleaned_data = super(HistoricoCarenciaLetraCambioForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de carência para essa data')
        
        # Testes para datas iniciais
        if self.inicial:
            # Verificar vencimento inicial e todos os vencimentos até próxima alteração de carência
            vencimento_inicial = HistoricoVencimentoLetraCambio.objects.get(lc=cleaned_data.get('lc'), data__isnull=True).vencimento
            if vencimento_inicial < cleaned_data.get('carencia'):
                raise forms.ValidationError('Carência inicial está maior do que período de vencimento inicial')
            elif HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__isnull=False).exists():
                # Verificar alterações de vencimento entre a vencimento carência e a próxima alteração
                proxima_carencia = HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__isnull=False).order_by('data')[0]
                for vencimento_periodo in HistoricoVencimentoLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__lt=proxima_carencia.data):
                    if vencimento_periodo.vencimento > cleaned_data.get('carencia'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (vencimento_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de vencimento a partir da data dessa alteração de carência
                for vencimento_periodo in HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc')):
                    if vencimento_periodo.vencimento > cleaned_data.get('carencia'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (vencimento_periodo.data.strftime('%d/%m/%Y')))
            
            
        else:
            # Verificar vencimento vigente, e alterações de vencimento ao longo do período que a nova carência estiver vigente
            vencimento_vigente = cleaned_data.get('lc').vencimento_na_data(cleaned_data.get('data'))
            if vencimento_vigente < cleaned_data.get('carencia'):
                raise forms.ValidationError('Vencimento na data de início está menor do que o período de carência')
            # Testar se período de carência será maior que algum período de vencimento vigente
            if HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__gt=cleaned_data.get('data')).exists():
                # Verificar alterações de vencimento entre a data dessa alteração de carência e a próxima
                proxima_carencia = HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__gt=cleaned_data.get('data')).order_by('data')[0]
                for vencimento_periodo in HistoricoVencimentoLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__range=[cleaned_data.get('data') + datetime.timedelta(days=1), 
                                                                                                                   proxima_carencia.data - datetime.timedelta(days=1)]):
                    if vencimento_periodo.vencimento < cleaned_data.get('carencia'):
                        raise forms.ValidationError('Vencimento vigente em %s está menor do que o período de carência' % (vencimento_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de vencimento a partir da data dessa alteração de carência
                for vencimento_periodo in HistoricoVencimentoLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__gt=cleaned_data.get('data')):
                    if vencimento_periodo.vencimento < cleaned_data.get('carencia'):
                        raise forms.ValidationError('Vencimento vigente em %s está menor do que o período de carência' % (vencimento_periodo.data.strftime('%d/%m/%Y')))
                
        return cleaned_data
    
class HistoricoVencimentoLetraCambioForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoVencimentoLetraCambio
        fields = ('vencimento', 'data', 'lc')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'vencimento': 'Período de vencimento',
                  'lc': 'Letra de Câmbio'}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.lc = kwargs.pop('lc')
        except:
            self.lc = None
        super(HistoricoVencimentoLetraCambioForm, self).__init__(*args, **kwargs)
        if self.lc:
            self.fields['lc'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_vencimento(self):
        vencimento = self.cleaned_data['vencimento']
        if vencimento <= 0:
            raise forms.ValidationError('Período de vencimento deve ser de pelo menos 1 dia')
        return vencimento
    
    def clean_lc(self):
        lc = self.cleaned_data['lc']
        if lc.investidor != self.investidor:
            raise forms.ValidationError('Letra de Câmbio inválida')
        if hasattr(self.instance, 'lc') and lc != self.instance.lc:
            raise forms.ValidationError('Letra de Câmbio não deve ser alterada')
        return lc
    
    def clean_data(self):
        data = self.cleaned_data['data']
        # Verifica se o registro é da data incial, e se foi feita alteração
        if self.inicial and data:
            raise forms.ValidationError('Data inicial não pode ser alterada')
        elif not self.inicial and not data:
            raise forms.ValidationError('Data é obrigatória')
        return data
    
    def clean(self):
        cleaned_data = super(HistoricoVencimentoLetraCambioForm, self).clean()
        cleaned_data.get('lc')
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoVencimentoLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de vencimento para essa data')
        
        # Testes para datas iniciais
        if self.inicial:
            # Verificar carência inicial e todas as carências até próxima alteração de vencimento
            carencia_inicial = HistoricoCarenciaLetraCambio.objects.get(lc=cleaned_data.get('lc'), data__isnull=True).carencia
            if carencia_inicial > cleaned_data.get('vencimento'):
                raise forms.ValidationError('Carência inicial está maior do que período de vencimento inicial')
            elif HistoricoVencimentoLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__isnull=False).exists():
                # Verificar alterações de carência entre o vencimento inicial e a próxima alteração
                proximo_vencimento = HistoricoVencimentoLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__isnull=False).order_by('data')[0]
                for carencia_periodo in HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__lt=proximo_vencimento.data):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de carência a partir da data dessa alteração de vencimento
                for carencia_periodo in HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc')):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            
        # Testes para datas não iniciais
        else:
            # Verificar carência vigente, e alterações de carência ao longo do período que esse novo vencimento estiver vigente
            carencia_vigente = cleaned_data.get('lc').carencia_na_data(cleaned_data.get('data'))
            if carencia_vigente > cleaned_data.get('vencimento'):
                raise forms.ValidationError('Carência na data de início está maior do que o período de vencimento')
            # Testar se período de vencimento será menor que algum período de carência vigente
            if HistoricoVencimentoLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__gt=cleaned_data.get('data')).exists():
                # Verificar alterações de carência entre a data dessa alteração de vencimento e a próxima
                proximo_vencimento = HistoricoVencimentoLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__gt=cleaned_data.get('data')).order_by('data')[0]
                for carencia_periodo in HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__range=[cleaned_data.get('data') + datetime.timedelta(days=1), 
                                                                                                                   proximo_vencimento.data - datetime.timedelta(days=1)]):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de carência a partir da data dessa alteração de vencimento
                for carencia_periodo in HistoricoCarenciaLetraCambio.objects.filter(lc=cleaned_data.get('lc'), data__gt=cleaned_data.get('data')):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
        
                
        return cleaned_data