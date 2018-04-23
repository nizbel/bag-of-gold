
function calcular_patrimonio_futuro() {
    var data_inicio = $(this).attr('data-inicial');
    var data_fim = $(this).attr('data-final');
    App.blockUI({
        target: '#portlet_patrimonio_futuro',
        iconOnly: true,
        overlayColor: 'none'
    });
    var aporte_mensal = 1000;
    var num_meses = 48;
    var taxa_anual = 7.5;
    var taxa_mensal = Math.pow((1 + taxa_anual/100), (1.0/12)) - 1;
    
    var patrimonio = aporte_mensal * ((1 - Math.pow((1 + taxa_mensal), (num_meses+1))) / (1 - (1 + taxa_mensal)));
    
    $('#resultado_patrimonio_futuro').attr('data-value', patrimonio.toFixed(2).replace('.', ',')).html('0');
    $('#resultado_patrimonio_futuro').counterUp({
        delay: 10,
        time: 1000
    });

    App.unblockUI('#portlet_patrimonio_futuro');
}

function calcular_renda_futura() {
    var data_inicio = $(this).attr('data-inicial');
    var data_fim = $(this).attr('data-final');
    App.blockUI({
        target: '#portlet_rendimento_futuro',
        iconOnly: true,
        overlayColor: 'none'
    });
    var aporte_mensal = 1000;
    var num_meses = 48;
    var taxa_anual = 7.5;
    var taxa_mensal = Math.pow((1 + taxa_anual/100), (1.0/12)) - 1;
    
    var rendimento_apos_meses = taxa_mensal * aporte_mensal * ((1 - Math.pow((1 + taxa_mensal), (num_meses+1))) / (1 - (1 + taxa_mensal)));
    
    $('#resultado_rendimento_futuro').attr('data-value', rendimento_apos_meses.toFixed(2).replace('.', ',')).html('0');
    $('#resultado_rendimento_futuro').counterUp({
        delay: 10,
        time: 1000
    });

    App.unblockUI('#portlet_rendimento_futuro');
}

function getBaseLog(x, y) {
    return Math.log(y) / Math.log(x);
}

function calcular_periodo_para_patrimonio() {
    var data_inicio = $(this).attr('data-inicial');
    var data_fim = $(this).attr('data-final');
    App.blockUI({
        target: '#portlet_tempo_patrimonio',
        iconOnly: true,
        overlayColor: 'none'
    });
    var aporte_mensal = 1000;
    var num_meses = 48;
    var taxa_anual = 7.5;
    var taxa_mensal = Math.pow((1 + taxa_anual/100), (1.0/12)) - 1;

    var rendimento_apos_meses = aporte_mensal * ((1 - Math.pow((1 + taxa_mensal), (num_meses+1))) / (1 - (1 + taxa_mensal)));
    
    var patrimonio_desejado = 1000000;
    var tempo_necessario_rendimento_mensal = getBaseLog(1 + taxa_mensal, -1 * (-1 + patrimonio_desejado * (1 - (1 + taxa_mensal)) / (aporte_mensal))) - 1;

    $('#resultado_tempo_patrimonio').attr('data-value', tempo_necessario_rendimento_mensal.toFixed(1).replace('.', ',')).html('0');
    $('#resultado_tempo_patrimonio').counterUp({
        delay: 10,
        time: 1000
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

    $('#resultado_tempo_rendimento').attr('data-value', tempo_necessario_rendimento_mensal.toFixed(1).replace('.', ',')).html('0');
    $('#resultado_tempo_rendimento').counterUp({
        delay: 10,
        time: 1000
    });

    App.unblockUI('#portlet_tempo_resultado');
}