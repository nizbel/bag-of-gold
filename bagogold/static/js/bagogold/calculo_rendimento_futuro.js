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
    var data_inicio = $(this).attr('data-inicial');
    var data_fim = $(this).attr('data-final');
    App.blockUI({
        target: '#portlet_tempo_resultado',
        iconOnly: true,
        overlayColor: 'none'
    });
    var aporte_mensal = 1000;
    var num_meses = 48;
    var taxa_anual = 7.5;
    var taxa_mensal = Math.pow((1 + taxa_anual/100), (1.0/12)) - 1;
    
    var rendimento_apos_meses = taxa_mensal * aporte_mensal * ((1 - Math.pow((1 + taxa_mensal), (num_meses+1))) / (1 - (1 + taxa_mensal)));
    
    var rendimento_mensal_desejado = 1000000 * taxa_mensal;
    var tempo_necessario_rendimento_mensal = getBaseLog(1 + taxa_mensal, -1 * (-1 + rendimento_mensal_desejado / taxa_mensal * (1 - (1 + taxa_mensal)) / (aporte_mensal))) - 1;

    $('#resultado_tempo_rendimento').attr('data-value', formatar_mil(tempo_necessario_rendimento_mensal.toFixed(1).replace('.', ',')));
    $('#resultado_tempo_rendimento').counterUp({
        delay: 20,
        time: 400
    });

    App.unblockUI('#portlet_tempo_resultado');
}