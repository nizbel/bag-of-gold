$(document).ready(function() {
	form_count = $("input[name=divisaooperacaotd_set-TOTAL_FORMS]").val();
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
         $("[name=divisaooperacaotd_set-TOTAL_FORMS]").val(form_count);
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
             postfix: 'títulos'
         });
     });
     
     $( "#id_data" ).change(function() {
 		var dataEscolhida = $(this).val();
 		if (dataEscolhida == null || dataEscolhida == '') {
 			return;
 		}
 		var tipoOperacao = $('#id_tipo_operacao').val();
 		$.ajax({
 			url : "{% url 'td:buscar_titulos_validos_na_data' %}", // the endpoint
 			type : "GET", // http method
 			data: {dataEscolhida: dataEscolhida, tipoOperacao: tipoOperacao},
 			
 			// handle a successful response
 			success : function(lista_titulos_validos) {
 				$("#id_titulo option").each(function() {
 					if ($.inArray(parseInt(this.value), lista_titulos_validos) > -1) {
 						$("#id_titulo option[value=" + this.value + "]").show();
 					} else {
 						$("#id_titulo option[value=" + this.value + "]").hide();
 					}
 				});
 			}, 
 				
 			// handle a non-successful response
 			error : function(xhr,errmsg,err) {
 				console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
 			}
 		});
 	});
 	
 	$( "#id_tipo_operacao" ).change(function() {
 		var dataEscolhida = $('#id_data').val();
 		if (dataEscolhida == null || dataEscolhida == '') {
 			return;
 		}
 		var tipoOperacao = $(this).val();
 		$.ajax({
 			url : "{% url 'td:buscar_titulos_validos_na_data' %}", // the endpoint
 			type : "GET", // http method
 			data: {dataEscolhida: dataEscolhida, tipoOperacao: tipoOperacao},
 			
 			// handle a successful response
 			success : function(lista_titulos_validos) {
 				$("#id_titulo option").each(function() {
 					if ($.inArray(parseInt(this.value), lista_titulos_validos) > -1) {
 						$("#id_titulo option[value=" + this.value + "]").show();
 					} else {
 						$("#id_titulo option[value=" + this.value + "]").hide();
 					}
 				});
 			}, 
 				
 			// handle a non-successful response
 			error : function(xhr,errmsg,err) {
 				console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
 			}
 		});
 	});
 	$("input[name='preco_unitario']").TouchSpin({
 		min: 0,
 		max: 1000000000,
 		step: 0.01,
 		decimals: 2,
 		maxboostedstep: 100,
 		prefix: 'R$'
 	});
 	$("input[name='quantidade']").TouchSpin({
 		min: 0,
 		max: 1000000000,
        step: 0.01,
        decimals: 2,
 		maxboostedstep: 100,
        postfix: 'títulos'
 	});
 	$("input[name='taxa_bvmf']").TouchSpin({
 		min: 0,
 		max: 1000000000,
 		step: 0.01,
 		decimals: 2,
 		maxboostedstep: 100,
 		prefix: 'R$'
 	});
 	$("input[name='taxa_custodia']").TouchSpin({
 		min: 0,
 		max: 1000000000,
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
        postfix: 'títulos'
 	});
 	$('.date-picker').datepicker({
 		language: 'pt-BR'
 	});
});
