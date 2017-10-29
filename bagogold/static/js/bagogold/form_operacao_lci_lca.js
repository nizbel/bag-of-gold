$(document).ready(function() {
	form_count = $("input[name=divisaooperacaolc_set-TOTAL_FORMS]").val();
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
         $("[name=divisaooperacaolc_set-TOTAL_FORMS]").val(form_count);
         // ready bootstrap elements
         row.find('.bootstrap-select').replaceWith(function() { return $('select', this); });
         row.find('select').selectpicker('refresh');
         row.find('.bootstrap-touchspin').find('*').not('input').remove();
         row.find("input[name$='-quantidade']").TouchSpin({
        	 initval: 0,
             min: 0,
             max: 1000000000,
             step: 0.01,
             decimals: 2,
             maxboostedstep: 100,
             prefix: 'R$'
         });
     });

     // Preparar campos
 	$("input[name='quantidade']").TouchSpin({
 		initval: 0.01,
 		min: 0.01,
 		max: 999999999,
        step: 0.01,
        decimals: 2,
        maxboostedstep: 100,
        prefix: 'R$'
 	});
 	$("input[name$='-quantidade']").TouchSpin({
 		min: 0,
 		max: 1000000000,
 		step: 0.01,
 		decimals: 2,
 		maxboostedstep: 100,
 		prefix: 'R$'
 	});
 	$('.date-picker').datepicker({
 	   language: 'pt-BR'
 	}).on('changeDate', function(e) {
 		verificarVendasPossiveis($(this).find('input').val());
 	});
     $("select[id$='-divisao']").selectpicker('refresh');
     $("#id_tipo_operacao").selectpicker('refresh');

     if ($('#id_tipo_operacao').parent().find('button').attr('title') == 'Venda') {
        $("#grupo_operacao_compra").removeClass('hidden');
        $("#grupo_investimento").addClass('hidden');
    } else {
        $("#grupo_operacao_compra").addClass('hidden');
        $("#grupo_investimento").removeClass('hidden');
    }
	
	// Adiciona alterações para o form dependendo do tipo de operação
	$("#id_tipo_operacao").change(function() {
	   if ($(this).val() == 'C') {
		   $("#grupo_operacao_compra").addClass('hidden');
		   $("#grupo_investimento").removeClass('hidden');
	   } else {
        $("#grupo_operacao_compra").removeClass('hidden');
        $("#grupo_investimento").addClass('hidden');
	   }
	});
});
