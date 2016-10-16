# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC, \
    TransferenciaEntreDivisoes, DivisaoOperacaoAcao
from bagogold.bagogold.models.lc import OperacaoVendaLetraCredito
from django import forms
from django.forms import widgets

OPCOES_INVESTIMENTO = (('', 'Fonte externa'), ('B', 'Buy and Hold'), ('C', 'CDB/RDB'), ('D', 'Tesouro Direto'), ('F', 'Fundo de Inv. Imobiliário'), ('I', 'Fundo de Investimento'),
                       ('L', 'Letras de Crédito'), ('T', 'Trading'))
    
class DivisaoForm(forms.ModelForm):

    class Meta:
        model = Divisao
        fields = ('nome', 'valor_objetivo')
        
    def clean(self):
        data = super(DivisaoForm, self).clean()
        if data.get('valor_objetivo') is None:
            data['valor_objetivo'] = 0

        return data
    
# Inline FormSet para operações em ações 
class DivisaoOperacaoAcaoFormSet(forms.models.BaseInlineFormSet):
    class Meta:
        fields = ('nome', 'valor_objetivo')
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoAcaoFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            
    def add_fields(self, form, index):
        super(DivisaoOperacaoAcaoFormSet, self).add_fields(form, index)
        form.fields['qtd_proventos_utilizada'] = forms.DecimalField(max_digits=11, decimal_places=2)
        form.fields['qtd_proventos_utilizada'].label = 'Quantidade de proventos utilizada'
        form.fields['qtd_proventos_utilizada'].required = False
        
        if 'divisao' in form.initial:
            divisao_operacao = DivisaoOperacaoAcao.objects.get(divisao=form.initial['divisao'], operacao=self.instance)
            if hasattr(divisao_operacao, 'usoproventosoperacaoacao'):
                form.fields['qtd_proventos_utilizada'].initial = divisao_operacao.usoproventosoperacaoacao.qtd_utilizada
        
        # Alterar ordem do checkbox de exclusão, mandando-o pro final
        if 'DELETE' in form.fields.keys():
            botao_delete = form.fields['DELETE']
            del form.fields['DELETE']
            form.fields['DELETE'] = botao_delete
    
    def clean(self):
        print 'clean final'
        qtd_total_div = 0
        qtd_total_prov = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    print 'Testando form', form_divisao.cleaned_data
                    
                    # Verificar se foram escolhidas 2 divisões iguais
                    if form_divisao.cleaned_data['divisao'].id in divisoes_utilizadas:
                        raise forms.ValidationError('Divisão %s escolhida mais de uma vez' % (form_divisao.cleaned_data['divisao']))
                    else:
                        if self.investidor != form_divisao.cleaned_data['divisao'].investidor:
                            raise forms.ValidationError('Divisão não pertence ao investidor')
                        divisoes_utilizadas[form_divisao.cleaned_data['divisao'].id] = form_divisao.cleaned_data['divisao']
                    
                    # Verificar quantidade das divisões
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
                    # Verificar quantidade de proventos utilizada das divisões
                    div_qtd_prov = form_divisao.cleaned_data['qtd_proventos_utilizada']
                    if div_qtd_prov == None:
                        pass
                    elif div_qtd_prov >= 0:
                        qtd_total_prov += div_qtd_prov
                    else:
                        raise forms.ValidationError('Quantidade de proventos utilizada da divisão %s é inválida, não pode ser negativa' % (contador_forms))
                    
            else:
                print 'Invalid'
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')
        
        if qtd_total_prov > (self.instance.quantidade * self.instance.preco_unitario + self.instance.corretagem + self.instance.emolumentos):
            raise forms.ValidationError('Quantidade de proventos utilizada é maior do que o total gasto')
                    
                    
# Inline FormSet para operações em fundos de investimento imobiliário
class DivisaoOperacaoFIIFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoFIIFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar se foram escolhidas 2 divisões iguais
                    if form_divisao.cleaned_data['divisao'].id in divisoes_utilizadas:
                        raise forms.ValidationError('Divisão %s escolhida mais de uma vez' % (form_divisao.cleaned_data['divisao']))
                    else:
                        if self.investidor != form_divisao.cleaned_data['divisao'].investidor:
                            raise forms.ValidationError('Divisão não pertence ao investidor')
                        divisoes_utilizadas[form_divisao.cleaned_data['divisao'].id] = form_divisao.cleaned_data['divisao']
                        
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')

# Inline FormSet para operações em letras de crédito
class DivisaoOperacaoLCFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.operacao_compra = kwargs.pop('operacao_compra', None)
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoLCFormSet, self).__init__(*args, **kwargs)
    
        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar se foram escolhidas 2 divisões iguais
                    if form_divisao.cleaned_data['divisao'].id in divisoes_utilizadas:
                        raise forms.ValidationError('Divisão %s escolhida mais de uma vez' % (form_divisao.cleaned_data['divisao']))
                    else:
                        if self.investidor != form_divisao.cleaned_data['divisao'].investidor:
                            raise forms.ValidationError('Divisão não pertence ao investidor')
                        divisoes_utilizadas[form_divisao.cleaned_data['divisao'].id] = form_divisao.cleaned_data['divisao']
                        
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
                    # Verificar em caso de venda
                    if self.instance.tipo_operacao == 'V':
                        if DivisaoOperacaoLC.objects.get(divisao=form_divisao.cleaned_data['divisao'], operacao=self.operacao_compra).quantidade < div_qtd:
                            raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s' % (form_divisao.cleaned_data['divisao']))
                        
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')

# Inline FormSet para operações em CDB
class DivisaoOperacaoCDB_RDBFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.operacao_compra = kwargs.pop('operacao_compra', None)
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoCDB_RDBFormSet, self).__init__(*args, **kwargs)
        
        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
    
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar se foram escolhidas 2 divisões iguais
                    if form_divisao.cleaned_data['divisao'].id in divisoes_utilizadas:
                        raise forms.ValidationError('Divisão %s escolhida mais de uma vez' % (form_divisao.cleaned_data['divisao']))
                    else:
                        if self.investidor != form_divisao.cleaned_data['divisao'].investidor:
                            raise forms.ValidationError('Divisão não pertence ao investidor')
                        divisoes_utilizadas[form_divisao.cleaned_data['divisao'].id] = form_divisao.cleaned_data['divisao']
                        
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                    
                    # Verificar em caso de venda
                    if self.instance.tipo_operacao == 'V':
                        if DivisaoOperacaoCDB.objects.get(divisao=form_divisao.cleaned_data['divisao'], operacao=self.operacao_compra).quantidade < div_qtd:
                            raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s' % (form_divisao.cleaned_data['divisao']))
                        
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')
                            
# Inline FormSet para operações em CDB
class DivisaoOperacaoFundoInvestimentoFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoFundoInvestimentoFormSet, self).__init__(*args, **kwargs)
        
        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
    
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar se foram escolhidas 2 divisões iguais
                    if form_divisao.cleaned_data['divisao'].id in divisoes_utilizadas:
                        raise forms.ValidationError('Divisão %s escolhida mais de uma vez' % (form_divisao.cleaned_data['divisao']))
                    else:
                        if self.investidor != form_divisao.cleaned_data['divisao'].investidor:
                            raise forms.ValidationError('Divisão não pertence ao investidor')
                        divisoes_utilizadas[form_divisao.cleaned_data['divisao'].id] = form_divisao.cleaned_data['divisao']
                        
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
        if self.instance.quantidade_cotas < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')
                            
# Inline FormSet para operações em tesouro direto
class DivisaoOperacaoTDFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoTDFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    # Verificar se foram escolhidas 2 divisões iguais
                    if form_divisao.cleaned_data['divisao'].id in divisoes_utilizadas:
                        raise forms.ValidationError('Divisão %s escolhida mais de uma vez' % (form_divisao.cleaned_data['divisao']))
                    else:
                        if self.investidor != form_divisao.cleaned_data['divisao'].investidor:
                            raise forms.ValidationError('Divisão não pertence ao investidor')
                        divisoes_utilizadas[form_divisao.cleaned_data['divisao'].id] = form_divisao.cleaned_data['divisao']
                        
                    # Verificar quantidade
                    div_qtd = form_divisao.cleaned_data['quantidade']
                    if div_qtd != None and div_qtd > 0:
                        qtd_total_div += div_qtd
                    else:
                        raise forms.ValidationError('Quantidade da divisão %s é inválida, quantidade deve ser maior que 0' % (contador_forms))
                
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')

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
        if data.get('divisao_cedente') == None and data.get('investimento_origem') != '':
            raise forms.ValidationError('Conta cedente vazia não pode ter investimento definido')
        if data.get('divisao_recebedora') == None and data.get('investimento_destino') != '':
            raise forms.ValidationError('Conta recebedora vazia não pode ter investimento definido')
        
        return data
