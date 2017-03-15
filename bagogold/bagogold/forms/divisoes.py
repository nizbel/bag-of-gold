# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC, \
    TransferenciaEntreDivisoes, DivisaoOperacaoAcao, DivisaoOperacaoFII, \
    DivisaoOperacaoCDB_RDB, DivisaoOperacaoTD
from bagogold.bagogold.models.lc import OperacaoVendaLetraCredito
from bagogold.bagogold.utils.fundo_investimento import \
    calcular_qtd_cotas_ate_dia_por_divisao
from bagogold.bagogold.utils.td import calcular_qtd_titulos_ate_dia_por_divisao
from bagogold.cri_cra.utils.utils import \
    qtd_cri_cra_ate_dia_para_divisao_para_certificado
from decimal import Decimal
from django import forms
from django.forms import widgets

class DivisaoForm(LocalizedModelForm):

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
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoAcaoFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            form.fields['quantidade'].initial = Decimal('0')
            form.fields['quantidade'].localize = True
            
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
        qtd_total_div = 0
        qtd_total_prov = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        divisao_a_excluir = False
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                # Verifica se pode passar pelo form, e se não está configurado para ser apagada
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    if ('DELETE' not in form_divisao.cleaned_data or not form_divisao.cleaned_data['DELETE']):
                        
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
                    
                    # Divisão será apagada
                    elif form_divisao.cleaned_data['DELETE']:
                        divisao_a_excluir = True

        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            if divisao_a_excluir:
                raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação. Repasse a quantidade da divisão excluída para a(s) remanescente(s)')
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')
        
        if qtd_total_prov > (self.instance.quantidade * self.instance.preco_unitario + self.instance.corretagem + self.instance.emolumentos):
            raise forms.ValidationError('Quantidade de proventos utilizada é maior do que o total gasto')
                    
            
# Inline FormSet para operações em debêntures
class DivisaoOperacaoDebentureFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoDebentureFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            form.fields['quantidade'].initial = Decimal('0')
            form.fields['quantidade'].localize = True
    
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        divisao_a_excluir = False
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    if ('DELETE' not in form_divisao.cleaned_data or not form_divisao.cleaned_data['DELETE']):
                        
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
                        
                    # Divisão será apagada
                    elif form_divisao.cleaned_data['DELETE']:
                        divisao_a_excluir = True
                        
        if self.instance.quantidade < qtd_total_div:
            print self.instance.preco_unitario
            print self.instance.quantidade
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            if divisao_a_excluir:
                raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação. Repasse a quantidade da divisão excluída para a(s) remanescente(s)')
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')
        
                
# Inline FormSet para operações em fundos de investimento imobiliário
class DivisaoOperacaoFIIFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoFIIFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            form.fields['quantidade'].initial = Decimal('0')
            form.fields['quantidade'].localize = True
    
    def add_fields(self, form, index):
        super(DivisaoOperacaoFIIFormSet, self).add_fields(form, index)
        form.fields['qtd_proventos_utilizada'] = forms.DecimalField(max_digits=11, decimal_places=2)
        form.fields['qtd_proventos_utilizada'].label = 'Quantidade de proventos utilizada'
        form.fields['qtd_proventos_utilizada'].required = False
        
        if 'divisao' in form.initial:
            divisao_operacao = DivisaoOperacaoFII.objects.get(divisao=form.initial['divisao'], operacao=self.instance)
            if hasattr(divisao_operacao, 'usoproventosoperacaofii'):
                form.fields['qtd_proventos_utilizada'].initial = divisao_operacao.usoproventosoperacaofii.qtd_utilizada
        
        # Alterar ordem do checkbox de exclusão, mandando-o pro final
        if 'DELETE' in form.fields.keys():
            botao_delete = form.fields['DELETE']
            del form.fields['DELETE']
            form.fields['DELETE'] = botao_delete
            
    def clean(self):
        qtd_total_div = 0
        qtd_total_prov = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        divisao_a_excluir = False
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    if ('DELETE' not in form_divisao.cleaned_data or not form_divisao.cleaned_data['DELETE']):
                        
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
                        
                        # Verificar quantidade de proventos utilizada das divisões
                        div_qtd_prov = form_divisao.cleaned_data['qtd_proventos_utilizada']
                        if div_qtd_prov == None:
                            pass
                        elif div_qtd_prov >= 0:
                            qtd_total_prov += div_qtd_prov
                        else:
                            raise forms.ValidationError('Quantidade de proventos utilizada da divisão %s é inválida, não pode ser negativa' % (contador_forms))
                
                    # Divisão será apagada
                    elif form_divisao.cleaned_data['DELETE']:
                        divisao_a_excluir = True
                        
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            if divisao_a_excluir:
                raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação. Repasse a quantidade da divisão excluída para a(s) remanescente(s)')
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')

# Inline FormSet para operações em letras de crédito
class DivisaoOperacaoLCFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.operacao_compra = kwargs.pop('operacao_compra', None)
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoLCFormSet, self).__init__(*args, **kwargs)
    
        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            form.fields['quantidade'].initial = Decimal('0')
            form.fields['quantidade'].localize = True
            
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        divisao_a_excluir = False
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    if ('DELETE' not in form_divisao.cleaned_data or not form_divisao.cleaned_data['DELETE']):
                        
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
                            if not DivisaoOperacaoLC.objects.filter(divisao=form_divisao.cleaned_data['divisao'], operacao=self.operacao_compra).exists():
                                raise forms.ValidationError('Venda para divisão %s não é permitida, não há alocação para a operação de compra selecionada' % (form_divisao.cleaned_data['divisao']))
                            if DivisaoOperacaoLC.objects.get(divisao=form_divisao.cleaned_data['divisao'], operacao=self.operacao_compra).quantidade < div_qtd:
                                raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s' % (form_divisao.cleaned_data['divisao']))
                        
                    # Divisão será apagada
                    elif form_divisao.cleaned_data['DELETE']:
                        divisao_a_excluir = True
                        
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            if divisao_a_excluir:
                raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação. Repasse a quantidade da divisão excluída para a(s) remanescente(s)')
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')

# Inline FormSet para operações em CDB/RDB
class DivisaoOperacaoCDB_RDBFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.operacao_compra = kwargs.pop('operacao_compra', None)
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoCDB_RDBFormSet, self).__init__(*args, **kwargs)
        
        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            form.fields['quantidade'].initial = Decimal('0')
            form.fields['quantidade'].localize = True
    
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        divisao_a_excluir = False
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    if ('DELETE' not in form_divisao.cleaned_data or not form_divisao.cleaned_data['DELETE']):
                        
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
                            if not DivisaoOperacaoCDB_RDB.objects.filter(divisao=form_divisao.cleaned_data['divisao'], operacao=self.operacao_compra).exists():
                                raise forms.ValidationError('Venda para divisão %s não é permitida, não há alocação para a operação de compra selecionada' % (form_divisao.cleaned_data['divisao']))
                            if DivisaoOperacaoCDB_RDB.objects.get(divisao=form_divisao.cleaned_data['divisao'], operacao=self.operacao_compra).quantidade < div_qtd:
                                raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s' % (form_divisao.cleaned_data['divisao']))
                        
                    # Divisão será apagada
                    elif form_divisao.cleaned_data['DELETE']:
                        divisao_a_excluir = True
                        
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            if divisao_a_excluir:
                raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação. Repasse a quantidade da divisão excluída para a(s) remanescente(s)')
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')
        
class DivisaoOperacaoCRI_CRAFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoCRI_CRAFormSet, self).__init__(*args, **kwargs)
        
        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            form.fields['quantidade'].initial = Decimal('0')
            form.fields['quantidade'].localize = True
    
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        divisao_a_excluir = False
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    if ('DELETE' not in form_divisao.cleaned_data or not form_divisao.cleaned_data['DELETE']):
                        
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
                        print self.instance.tipo_operacao
                        if self.instance.tipo_operacao == 'V':
                            if qtd_cri_cra_ate_dia_para_divisao_para_certificado(self.instance.data, form_divisao.cleaned_data['divisao'].id, self.instance.cri_cra.id) < div_qtd:
                                raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s' % (form_divisao.cleaned_data['divisao']))
                        
                    # Divisão será apagada
                    elif form_divisao.cleaned_data['DELETE']:
                        divisao_a_excluir = True

        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            if divisao_a_excluir:
                raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação. Repasse a quantidade da divisão excluída para a(s) remanescente(s)')
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')
                            
# Inline FormSet para operações em Fundo de Investimento
class DivisaoOperacaoFundoInvestimentoFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoFundoInvestimentoFormSet, self).__init__(*args, **kwargs)
        
        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            form.fields['quantidade'].initial = Decimal('0')
            form.fields['quantidade'].localize = True
    
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        divisao_a_excluir = False
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    if ('DELETE' not in form_divisao.cleaned_data or not form_divisao.cleaned_data['DELETE']):
                        
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
                            fundos_disponiveis = calcular_qtd_cotas_ate_dia_por_divisao(self.instance.data, form_divisao.cleaned_data['divisao'].id)
                            qtd_disponivel_divisao = fundos_disponiveis[form_divisao.cleaned_data['divisao'].id] if form_divisao.cleaned_data['divisao'] in fundos_disponiveis else 0 
                            if qtd_disponivel_divisao < div_qtd:
                                raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s, disponível: R$ %s' % (form_divisao.cleaned_data['divisao'], qtd_disponivel_divisao))
                        
                    # Divisão será apagada
                    elif form_divisao.cleaned_data['DELETE']:
                        divisao_a_excluir = True
                
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            if divisao_a_excluir:
                raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação. Repasse a quantidade da divisão excluída para a(s) remanescente(s)')
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')
                            
# Inline FormSet para operações em tesouro direto
class DivisaoOperacaoTDFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        super(DivisaoOperacaoTDFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)
            form.fields['quantidade'].initial = Decimal('0')
            form.fields['quantidade'].localize = True
            
    def clean(self):
        qtd_total_div = 0
        contador_forms = 0
        divisoes_utilizadas = {}
        divisao_a_excluir = False
        for form_divisao in self.forms:
            contador_forms += 1
            if form_divisao.is_valid():
#                 print form_divisao.cleaned_data.get('quantidade')
                if not (form_divisao.instance.id == None and not form_divisao.has_changed()):
                    if ('DELETE' not in form_divisao.cleaned_data or not form_divisao.cleaned_data['DELETE']):
                        
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
                            titulos_disponiveis = calcular_qtd_titulos_ate_dia_por_divisao(self.instance.data, form_divisao.cleaned_data['divisao'].id)
                            qtd_disponivel_divisao = titulos_disponiveis[self.instance.titulo.id] if self.instance.titulo.id in titulos_disponiveis else 0 
                            if qtd_disponivel_divisao < div_qtd:
                                raise forms.ValidationError('Venda de quantidade acima da disponível para divisão %s, disponível: %s' % (form_divisao.cleaned_data['divisao'], qtd_disponivel_divisao))
                        
                    # Divisão será apagada
                    elif form_divisao.cleaned_data['DELETE']:
                        divisao_a_excluir = True
                
        if self.instance.quantidade < qtd_total_div:
            raise forms.ValidationError('Quantidade total alocada para as divisões é maior que quantidade da operação')
        elif self.instance.quantidade > qtd_total_div:
            if divisao_a_excluir:
                raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação. Repasse a quantidade da divisão excluída para a(s) remanescente(s)')
            raise forms.ValidationError('Quantidade total alocada para as divisões é menor que quantidade da operação')

class TransferenciaEntreDivisoesForm(LocalizedModelForm):
    class Meta:
        model = TransferenciaEntreDivisoes
        fields = ('divisao_cedente', 'investimento_origem', 'divisao_recebedora', 'investimento_destino', 'data', 'quantidade', 'descricao')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'investimento_origem': widgets.Select(choices=TransferenciaEntreDivisoes.ESCOLHAS_TIPO_INVESTIMENTO),
                 'investimento_destino': widgets.Select(choices=TransferenciaEntreDivisoes.ESCOLHAS_TIPO_INVESTIMENTO),}
    
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(TransferenciaEntreDivisoesForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['divisao_cedente'].queryset = Divisao.objects.filter(investidor=self.investidor)
        self.fields['divisao_recebedora'].queryset = Divisao.objects.filter(investidor=self.investidor)
    
    def clean_quantidade(self):
        quantidade = self.cleaned_data['quantidade']
        if quantidade <= 0:
            raise forms.ValidationError('Quantidade deve ser maior que 0')
        return quantidade
    
    def clean(self):
        data = super(TransferenciaEntreDivisoesForm, self).clean()
        if data.get('divisao_cedente') == None and data.get('divisao_recebedora') == None:
            raise forms.ValidationError('Divisão cedente e recebedora não podem ser vazias')
        if data.get('divisao_cedente') == None and data.get('investimento_origem') != '':
            raise forms.ValidationError('Divisão cedente vazia não pode ter investimento definido')
        if data.get('divisao_recebedora') == None and data.get('investimento_destino') != '':
            raise forms.ValidationError('Divisão recebedora vazia não pode ter investimento definido')
        if data.get('divisao_cedente') != None and data.get('divisao_cedente').investidor != self.investidor:
            raise forms.ValidationError('Divisão cedente não permitida para o investidor')
        if data.get('divisao_recebedora') != None and data.get('divisao_recebedora').investidor != self.investidor:
            raise forms.ValidationError('Divisão recebedora não permitida para o investidor')
        
        return data
