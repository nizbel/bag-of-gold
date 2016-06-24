# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC, \
    TransferenciaEntreDivisoes
from bagogold.bagogold.models.lc import OperacaoVendaLetraCredito
from django import forms
from django.forms import widgets

OPCOES_INVESTIMENTO = ((None, ''), ('B', 'Buy and Hold'), ('C', 'CDB/RDB'), ('D', 'Tesouro Direto'), ('F', 'Fundo de Inv. Imobiliário'), ('L', 'Letras de Crédito'),
                       ('T', 'Trading'))
    
class DivisaoForm(forms.ModelForm):

    class Meta:
        model = Divisao
        fields = ('nome', 'valor_objetivo')
        
    def clean(self):
        data = super(DivisaoForm, self).clean()
        if data.get('valor_objetivo') is None:
            data['valor_objetivo'] = 0

        return data
    
# Inline FormSet para operações em ações (B&H)
class DivisaoOperacaoAcaoFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes = list()
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
                    if self.instance.quantidade < qtd_total_div:
                        raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')

# Inline FormSet para operações em fundos de investimento imobiliário
class DivisaoOperacaoFIIFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes = list()
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
                    if self.instance.quantidade < qtd_total_div:
                        raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')

# Inline FormSet para operações em letras de crédito
class DivisaoOperacaoLCFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.operacao_compra = kwargs.pop('operacao_compra', None)
        super(DivisaoOperacaoLCFormSet, self).__init__(*args, **kwargs)
    
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes = list()
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
                    if self.instance.quantidade < qtd_total_div:
                        raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
                    
                    # Verificar em caso de venda
                    if self.instance.tipo_operacao == 'V':
                        # Caso de venda total da letra de crédito
                        if self.instance.quantidade < self.operacao_compra.quantidade:
                            if DivisaoOperacaoLC.objects.get(divisao=form_divisao.cleaned_data['divisao'], operacao=self.operacao_compra).quantidade < div_qtd:
                                raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s' % (form_divisao.cleaned_data['divisao']))

# Inline FormSet para operações em CDB
class DivisaoOperacaoCDB_RDBFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.operacao_compra = kwargs.pop('operacao_compra', None)
        super(DivisaoOperacaoCDB_RDBFormSet, self).__init__(*args, **kwargs)
    
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes = list()
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
                    if self.instance.quantidade < qtd_total_div:
                        raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
                    
                    # Verificar em caso de venda
                    if self.instance.tipo_operacao == 'V':
                        # Caso de venda total do CDB
                        if self.instance.quantidade < self.operacao_compra.quantidade:
                            if DivisaoOperacaoCDB.objects.get(divisao=form_divisao.cleaned_data['divisao'], operacao=self.operacao_compra).quantidade < div_qtd:
                                raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s' % (form_divisao.cleaned_data['divisao']))
                            
# Inline FormSet para operações em tesouro direto
class DivisaoOperacaoTDFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes = list()
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
                    if self.instance.quantidade < qtd_total_div:
                        raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')

class TransferenciaEntreDivisoesForm(forms.ModelForm):
    class Meta:
        model = TransferenciaEntreDivisoes
        fields = ('divisao_cedente', 'investimento_origem', 'divisao_recebedora', 'investimento_destino', 'data', 'quantidade')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'investimento_origem': widgets.Select(choices=OPCOES_INVESTIMENTO),
                 'investimento_destino': widgets.Select(choices=OPCOES_INVESTIMENTO),}
        
    def clean_quantidade(self):
        quantidade = self.cleaned_data['quantidade']
        if quantidade <= 0:
            raise forms.ValidationError('Quantidade deve ser maior que 0')
        return quantidade
    
    def clean(self):
        data = super(TransferenciaEntreDivisoesForm, self).clean()
        if data.get('divisao_cedente') == None and data.get('divisao_recebedora') == None:
            raise forms.ValidationError('Conta cedente e recebedora não podem ser vazias')
        if data.get('divisao_cedente') == None and data.get('investimento_origem') != None:
            raise forms.ValidationError('Conta vazia não pode ter investimento definido')
        if data.get('divisao_recebedora') == None and data.get('investimento_destino') != None:
            raise forms.ValidationError('Conta vazia não pode ter investimento definido')
        
        return data
