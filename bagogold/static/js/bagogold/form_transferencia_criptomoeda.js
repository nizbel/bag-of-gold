$(document).ready(function() {
    form_count = $("input[name=divisaotransferenciacriptomoeda_set-TOTAL_FORMS]").val();
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
        $("[name=divisaotransferenciacriptomoeda_set-TOTAL_FORMS]").val(form_count);
        // ready bootstrap elements
        row.find('.bootstrap-select').replaceWith(function() { return $('select', this); });
        row.find('select').selectpicker('refresh');
        row.find('.bootstrap-touchspin').find('*').not('input').remove();
    	var escolhida = $('#id_moeda option:selected').text().split(' ')[0];
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
    
    // Pegar criptomoeda escolhida atualmente
    var escolhida = $('#id_moeda option:selected').text().split(' ')[0];
    $("input[name='taxa']").TouchSpin({
		min: 0,
		max: 1000000000,
		step: 0.000000000001,
		decimals: 12,
		maxboostedstep: 100,
		postfix: escolhida
	});
    
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
	
    $('.date-picker').datepicker({
        todayHighlight: true,
        language: 'pt-BR'
    });
	
    $('#id_moeda').change(function() {
    	var escolhida = $('#id_moeda option:selected').text().split(' ')[0];
    	$("input[name='quantidade']").parent().find('.bootstrap-touchspin-postfix').text(escolhida);
    	$("input[name$='-quantidade']").parent().find('.bootstrap-touchspin-postfix').text(escolhida);
    	$("input[name='taxa']").parent().find('.bootstrap-touchspin-postfix').text(escolhida);
    });
});
