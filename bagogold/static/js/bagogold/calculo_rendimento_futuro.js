$( document ).ready(function() {
	// Inputs para cálculo de patrimônio futuro
	$("#aporte_mensal_patr_fut").TouchSpin({
        min: 0.01,
        max: 1000000,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        prefix: 'R$'
    });

    $("#num_meses_patr_fut").TouchSpin({
        min: 1,
        max: 600,
        step: 1,
        maxboostedstep: 100,
        postfix: 'meses'
    });

    $("#taxa_anual_patr_fut").TouchSpin({
        min: 0.01,
        max: 100,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        postfix: '% ao ano'
    });

    // Inputs para cálculo de período para patrimônio
    $("#aporte_mensal_tempo_patr").TouchSpin({
        min: 0.01,
        max: 1000000,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        prefix: 'R$'
    });

    $("#patrimonio_tempo_patr").TouchSpin({
        min: 0.01,
        max: 10000000,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        prefix: 'R$'
    });

    $("#taxa_anual_tempo_patr").TouchSpin({
        min: 0.01,
        max: 100,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        postfix: '% ao ano'
    });
    
    // Inputs para cálculo de período para rendimento
    $("#aporte_mensal_tempo_rend").TouchSpin({
        min: 0.01,
        max: 1000000,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        prefix: 'R$'
    });

    $("#rendimento_tempo_rend").TouchSpin({
        min: 0.01,
        max: 100000,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        prefix: 'R$',
        postfix: 'ao mês'
    });

    $("#taxa_anual_tempo_rend").TouchSpin({
        min: 0.01,
        max: 100,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        postfix: '% ao ano'
    });
    
 // Inputs para cálculo de período para percentual do salário
    $("#perc_inv_tempo_rend_perc").TouchSpin({
        min: 1,
        max: 100,
        step: 1,
        maxboostedstep: 100,
        postfix: '% do salário'
    });

    $("#perc_tempo_rend_perc").TouchSpin({
        min: 1,
        max: 1000,
        step: 1,
        maxboostedstep: 100,
        postfix: '% do salário ao mês'
    });

    $("#taxa_anual_tempo_rend_perc").TouchSpin({
        min: 0.01,
        max: 100,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        postfix: '% ao ano'
    });
});

function formatar_mil(string_numerica) {
	string_numerica += '';
    var partes = string_numerica.split(',');
    var parte1 = partes[0];
    var parte2 = partes.length > 1 ? ',' + partes[1] : '';
    var regex = /(\d+)(\d{3})/;
    while (regex.test(parte1)) {
        parte1 = parte1.replace(regex, '$1' + '.' + '$2');
    }
    return parte1 + parte2;
}

function calcular_patrimonio_futuro() {
	if ($('#div_patr_fut').hasClass('hidden')) {
		$('#div_patr_fut').removeClass('hidden');
	}
	$('#div_patr_fut_comp').hide();
	if ($('#div_patr_fut_comp').hasClass('hidden')) {
		$('#div_patr_fut_comp').removeClass('hidden');
	}
	
    App.blockUI({
        target: '#portlet_patrimonio_futuro',
        iconOnly: true,
        overlayColor: 'none'
    });
    var aporte_mensal = parseFloat($('#aporte_mensal_patr_fut').val().replace(/\./g, '').replace(',', '.'));
    var num_meses = parseInt($('#num_meses_patr_fut').val());
    var taxa_anual = parseFloat($('#taxa_anual_patr_fut').val().replace(/\./g, '').replace(',', '.'));
    var taxa_mensal = Math.pow((1 + taxa_anual/100), (1.0/12)) - 1;
    
    var patrimonio = aporte_mensal * ((1 - Math.pow((1 + taxa_mensal), (num_meses+1))) / (1 - (1 + taxa_mensal)) - 1);

    $('#resultado_patrimonio_futuro').attr('data-value', formatar_mil(patrimonio.toFixed(2).replace('.', ',')));
    $('#resultado_patrimonio_futuro').counterUp({
        delay: 20,
        time: 400
    });

    var rendimento_apos_meses = taxa_mensal * patrimonio;

    $('#resultado_rendimento_futuro').attr('data-value', formatar_mil(rendimento_apos_meses.toFixed(2).replace('.', ',')));
    $('#resultado_rendimento_futuro').counterUp({
        delay: 20,
        time: 400
    });

    App.unblockUI('#portlet_patrimonio_futuro');
    
    // Carregar comparativos
    setTimeout(function() {
    	var valor_patr_fut_comp = (aporte_mensal * 0.1).toFixed(2);
    	
    	// Verificar se aumento no aporte é de pelo menos 1 centavo
    	if (valor_patr_fut_comp == '0.00') {
    		return;
    	}
    	
    	$('#valor_patr_fut_comp').html(formatar_mil(valor_patr_fut_comp.replace('.', ',')));
	    var aporte_mensal_comp = aporte_mensal + parseFloat(valor_patr_fut_comp);
	    
	    var patrimonio_comp = aporte_mensal_comp * ((1 - Math.pow((1 + taxa_mensal), (num_meses+1))) / (1 - (1 + taxa_mensal)) - 1);
	
	    $('#resultado_patrimonio_futuro_comp').attr('data-value', formatar_mil(patrimonio_comp.toFixed(2).replace('.', ',')));
	    $('#resultado_patrimonio_futuro_comp').counterUp({
	        delay: 20,
	        time: 400
	    });
	    
	    var rendimento_apos_meses_comp = taxa_mensal * patrimonio_comp;
	
	    $('#resultado_rendimento_futuro_comp').attr('data-value', formatar_mil(rendimento_apos_meses_comp.toFixed(2).replace('.', ',')));
	    $('#resultado_rendimento_futuro_comp').counterUp({
	        delay: 20,
	        time: 400
	    });

	    $('#div_patr_fut_comp').show();
    }, 500);
}

function getBaseLog(x, y) {
    return Math.log(y) / Math.log(x);
}

function calcular_periodo_para_patrimonio() {
	if ($('#div_tempo_patr').hasClass('hidden')) {
		$('#div_tempo_patr').removeClass('hidden');
	}

	App.blockUI({
        target: '#portlet_tempo_patrimonio',
        iconOnly: true,
        overlayColor: 'none'
    });
    var aporte_mensal = parseFloat($('#aporte_mensal_tempo_patr').val().replace(/\./g, '').replace(',', '.'));
    var patrimonio_desejado = parseFloat($('#patrimonio_tempo_patr').val().replace(/\./g, '').replace(',', '.'));
    var taxa_anual = parseFloat($('#taxa_anual_tempo_patr').val().replace(/\./g, '').replace(',', '.'));
    var taxa_mensal = Math.pow((1 + taxa_anual/100), (1.0/12)) - 1;

    var tempo_necessario_rendimento_mensal = getBaseLog(1 + taxa_mensal, -1 * (-1 + patrimonio_desejado * (1 - (1 + taxa_mensal)) / (aporte_mensal))) - 1;

    $('#resultado_tempo_patrimonio').attr('data-value', formatar_mil(tempo_necessario_rendimento_mensal.toFixed(1).replace('.', ',')));
    $('#resultado_tempo_patrimonio').counterUp({
        delay: 20,
        time: 400
    });

    App.unblockUI('#portlet_tempo_patrimonio');
}

function calcular_periodo_para_rendimento() {
	if ($('#div_tempo_rend').hasClass('hidden')) {
		$('#div_tempo_rend').removeClass('hidden');
	}

    App.blockUI({
        target: '#portlet_tempo_resultado',
        iconOnly: true,
        overlayColor: 'none'
    });
    var aporte_mensal = parseFloat($('#aporte_mensal_tempo_rend').val().replace(/\./g, '').replace(',', '.'));
    var rendimento_mensal_desejado = parseFloat($('#rendimento_tempo_rend').val().replace(/\./g, '').replace(',', '.'));
    var taxa_anual = parseFloat($('#taxa_anual_tempo_rend').val().replace(/\./g, '').replace(',', '.'));
    var taxa_mensal = Math.pow((1 + taxa_anual/100), (1.0/12)) - 1;
    
    var tempo_necessario_rendimento_mensal = getBaseLog(1 + taxa_mensal, -1 * (-1 + rendimento_mensal_desejado / taxa_mensal * (1 - (1 + taxa_mensal)) / (aporte_mensal))) - 1;

    $('#resultado_tempo_rendimento').attr('data-value', formatar_mil(tempo_necessario_rendimento_mensal.toFixed(1).replace('.', ',')));
    $('#resultado_tempo_rendimento').counterUp({
        delay: 20,
        time: 400
    });

    App.unblockUI('#portlet_tempo_resultado');
}

function calcular_periodo_para_rendimento_perc() {
	if ($('#div_tempo_rend_perc').hasClass('hidden')) {
		$('#div_tempo_rend_perc').removeClass('hidden');
	}

    App.blockUI({
        target: '#portlet_tempo_resultado_perc',
        iconOnly: true,
        overlayColor: 'none'
    });
    var perc_investido = parseFloat($('#perc_inv_tempo_rend_perc').val().replace(/\./g, '').replace(',', '.'));
    var perc_desejado = parseFloat($('#perc_tempo_rend_perc').val().replace(/\./g, '').replace(',', '.'));
    var taxa_anual = parseFloat($('#taxa_anual_tempo_rend_perc').val().replace(/\./g, '').replace(',', '.'));
    var taxa_mensal = Math.pow((1 + taxa_anual/100), (1.0/12)) - 1;
    
    var tempo_necessario_rendimento_mensal_perc = getBaseLog(1 + taxa_mensal, -1 * (-1 + perc_desejado / taxa_mensal * (1 - (1 + taxa_mensal)) / (perc_investido))) - 1;

    $('#resultado_tempo_rendimento_perc').attr('data-value', formatar_mil(tempo_necessario_rendimento_mensal_perc.toFixed(1).replace('.', ',')));
    $('#resultado_tempo_rendimento_perc').counterUp({
        delay: 20,
        time: 400
    });

    App.unblockUI('#portlet_tempo_resultado_perc');
}