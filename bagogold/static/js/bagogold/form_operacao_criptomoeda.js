$(document).ready(function() {
    form_count = $("input[name=divisaooperacaocriptomoeda_set-TOTAL_FORMS]").val();
    // get extra form count so we know what index to use for the next item.
    $("#add-another").click(function() {
        divisao_id = parseInt(form_count) + 1;
        titulo = $("<div class='col-md-12'><h3 class='font-yellow-crusta' align='center'><strong>Divisão " + divisao_id + "</strong></h3><br/></div>");
        row = $('#divisao-0').clone();
        row.attr('id', 'divisao-' + form_count);
        $(row).find("*").each(function() { 
       	 if ($(this).is('input')) {
       		 $(this).val('');
       	 }
       	 if ($(this).is('option')) {
       		 $(this).removeAttr('selected');
       	 }
       	 $.each(this.attributes, function() {
       		 this.value = this.value.replace('_set-0', '_set-' + form_count);
       	 });
        });
        
        $("#forms").append(titulo);
        $("#forms").append(row);
        // build divisao and append it to our forms container

        // increment form count so our view knows to populate 
        // that many fields for validation
        form_count ++;
        $("[name=divisaooperacaocriptomoeda_set-TOTAL_FORMS]").val(form_count);
        // ready bootstrap elements
        row.find('.bootstrap-select').replaceWith(function() { return $('select', this); });
        row.find('select').selectpicker('refresh');
        row.find('.bootstrap-touchspin').find('*').not('input').remove();
    	var escolhida = $('#id_criptomoeda option:selected').text().split(' ')[0];
        row.find("input[name$='-quantidade']").TouchSpin({
       	 	initval: 0,
    		min: 0,
    		max: 1000000000,
    		step: 0.000000000000001,
    		decimals: 15,
    		maxboostedstep: 100,
    		postfix: escolhida
        });
    });
    
    // Pegar moeda utilizada escolhida atualmente
    if ($('#id_moeda_utilizada').val() == '') {
	    $("input[name='valor']").TouchSpin({
			min: 0.000000000001,
			max: 1000000000,
			step: 0.000000000001,
			decimals: 12,
			maxboostedstep: 100,
			prefix: 'R$'
		});
    } else {
        var utilizada_escolhida = $('#id_moeda_utilizada option:selected').text().split(' ')[0];
        $("input[name='valor']").TouchSpin({
			min: 0.000000000001,
			max: 1000000000,
			step: 0.000000000001,
			decimals: 12,
			maxboostedstep: 100,
			postfix: utilizada_escolhida
		});
    }
    
    // Pegar criptomoeda escolhida atualmente
    var escolhida = $('#id_criptomoeda option:selected').text().split(' ')[0];
	$("input[name='quantidade']").TouchSpin({
		min: 0.000000000001,
		max: 1000000000,
		step: 0.000000000001,
		decimals: 12,
		maxboostedstep: 100,
		postfix: escolhida
	});
	$("input[name$='-quantidade']").TouchSpin({
		min: 0,
		max: 1000000000,
		step: 0.000000000001,
		decimals: 12,
		maxboostedstep: 100,
		postfix: escolhida
	});
	
	// Preparar moeda da taxa
	var valor_criptomoeda = $('#id_criptomoeda').val();
	var valor_moeda_utilizada = $('#id_moeda_utilizada').val();
	$("#id_taxa_moeda option").each(function() {
		if ($(this).val() != valor_moeda_utilizada && $(this).val() != valor_criptomoeda) {
            $(this).attr('disabled', 'disabled');
		} else {
            $(this).removeAttr('disabled');
		}
	});
	if ($('#id_taxa_moeda option:selected:disabled').length > 0) {
        $("#id_taxa_moeda").val($("#id_taxa_moeda option:enabled:first").val());
   	}
   	$('#id_taxa_moeda').selectpicker('refresh');
   	$('#id_taxa_moeda').trigger('change');
	
	// Pegar moeda da taxa escolhida atualmente
	if ($('#id_taxa_moeda').val() == '') {
	    $("input[name='taxa']").TouchSpin({
			min: 0.000000000001,
			max: 1000000000,
			step: 0.000000000001,
			decimals: 12,
			maxboostedstep: 100,
			prefix: 'R$'
		});
    } else {
        var escolhida_taxa = $('#id_taxa_moeda option:selected').text().split(' ')[0];
        $("input[name='taxa']").TouchSpin({
    		min: 0,
    		max: 1000000000,
    		step: 0.000000000001,
    		decimals: 12,
    		maxboostedstep: 100,
    		postfix: escolhida_taxa
    	});
    }
	
    $('.date-picker').datepicker({
        language: 'pt-BR'
    });
	
    $('#id_moeda_utilizada').change(function() {
    	if ($(this).val() == '') {
	    	$('#id_valor').parent().find('.bootstrap-touchspin-prefix').show();
	    	$('#id_valor').parent().find('.bootstrap-touchspin-postfix').hide();
    	}
    	else {
        	var escolhida = $('#id_moeda_utilizada option:selected').text().split(' ')[0];
        	$('#id_valor').parent().find('.bootstrap-touchspin-prefix').hide();
	    	$('#id_valor').parent().find('.bootstrap-touchspin-postfix').text(escolhida);
	    	$('#id_valor').parent().find('.bootstrap-touchspin-postfix').show();
    	}
    	
    	// Altera opções de moeda da taxa de acordo com escolha das moedas envolvidas na operação
    	var valor_criptomoeda = $('#id_criptomoeda').val();
    	$("#id_taxa_moeda option").each(function() {
    		if ($(this).val() != $('#id_moeda_utilizada').val() && $(this).val() != valor_criptomoeda) {
                $(this).attr('disabled', 'disabled');
    		} else {
                $(this).removeAttr('disabled');
    		}
    	});
    	if ($('#id_taxa_moeda option:selected:disabled').length > 0) {
    	   $("#id_taxa_moeda").val($('#id_moeda_utilizada').val());
       	}
       	$('#id_taxa_moeda').selectpicker('refresh');
       	$('#id_taxa_moeda').trigger('change');
    });
    
    $('#id_criptomoeda').change(function() {
    	var escolhida = $('#id_criptomoeda option:selected').text().split(' ')[0];
    	$("input[name='quantidade']").parent().find('.bootstrap-touchspin-postfix').text(escolhida);
    	$("input[name$='-quantidade']").parent().find('.bootstrap-touchspin-postfix').text(escolhida);
    	
    	// Altera opções de moeda da taxa de acordo com escolha das moedas envolvidas na operação
    	var valor_moeda_utilizada = $('#id_moeda_utilizada').val();
    	$("#id_taxa_moeda option").each(function() {
    		if ($(this).val() != $('#id_criptomoeda').val() && $(this).val() != valor_moeda_utilizada) {
                $(this).attr('disabled', 'disabled');
    		} else {
                $(this).removeAttr('disabled');
    		}
    	});
    	if ($('#id_taxa_moeda option:selected:disabled').length > 0) {
    	   $("#id_taxa_moeda").val($('#id_criptomoeda').val());
       	}
       	$('#id_taxa_moeda').selectpicker('refresh');
       	$('#id_taxa_moeda').trigger('change');
    });
    
    $('#id_taxa_moeda').change(function() {
    	if ($(this).val() == '') {
	    	$('#id_taxa').parent().find('.bootstrap-touchspin-prefix').show();
	    	$('#id_taxa').parent().find('.bootstrap-touchspin-postfix').hide();
    	}
    	else {
        	var escolhida = $('#id_taxa_moeda option:selected').text().split(' ')[0];
        	$('#id_taxa').parent().find('.bootstrap-touchspin-prefix').hide();
	    	$('#id_taxa').parent().find('.bootstrap-touchspin-postfix').text(escolhida);
	    	$('#id_taxa').parent().find('.bootstrap-touchspin-postfix').show();
    	}
    });
});
