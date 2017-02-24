$(document).ready(function() {
	form_count = $("input[name=divisaooperacaodebenture_set-TOTAL_FORMS]").val();
    // get extra form count so we know what index to use for the next item.
     $("#add-another").click(function() {
         divisao_id = parseInt(form_count) + 1;
         titulo = $("<h3 class='font-yellow-crusta' align='center'><strong>Divisão " + divisao_id + "</strong></h3><br/>");
         row = $('#divisao-0').clone();
         row.attr('id', 'divisao-' + form_count);
         $(row).find("*").each(function() { 
        	 $.each(this.attributes, function() {
        		 this.value = this.value.replace('_set-0', '_set-' + form_count);
        	 });
         });
         
         $("#forms").append(titulo);
         $("#forms").append(row);
         // build divisao and append it to our forms container
         
         if ($("#id_divisaooperacaodebenture_set-0-id").length > 0) {
	         id = $("#id_divisaooperacaodebenture_set-0-id").clone();
	         id.attr("name", "divisaooperacaodebenture_set-" + form_count + "-id");
	         id.attr('id', "id_divisaooperacaodebenture_set-" + form_count + "-id");
	         $("#forms").append(id);
         }

         if ($("#id_divisaooperacaodebenture_set-0-operacao").length > 0) {
	         operacao = $("#id_divisaooperacaodebenture_set-0-operacao").clone();
	         operacao.attr("name", "divisaooperacaodebenture_set-" + form_count + "-operacao");
	         operacao.attr('id', "id_divisaooperacaodebenture_set-" + form_count + "-operacao");
	         $("#forms").append(operacao);
         }
    
         form_count ++;
         $("[name=divisaooperacaodebenture_set-TOTAL_FORMS]").val(form_count);
         // increment form count so our view knows to populate 
         // that many fields for validation
         row.find('.bootstrap-select').replaceWith(function() { return $('select', this); });
         row.find('select').selectpicker('refresh');
         var campo_quantidade = row.find('.bootstrap-touchspin input').detach();
         row.find('.bootstrap-touchspin').empty().append(campo_quantidade);
         row.find("input[name$='-quantidade']").TouchSpin({
             min: 0,
             max: 1000000000,
             step: 1,
             maxboostedstep: 100,
             postfix: 'títulos'
         });
     });
});
