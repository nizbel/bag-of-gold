$(document).ready(function() {
	// Remuneração
	form_count_remuneracao = $("input[name=dataremuneracaocri_cra_set-TOTAL_FORMS]").val();
    // get extra form count so we know what index to use for the next item.
     $("#add_data_remuneracao").click(function() {
         remuneracao_id = parseInt(form_count_remuneracao) + 1;
         row = $('#remuneracao-0').clone();
         row.attr('id', 'remuneracao-' + form_count_remuneracao);
         $(row).find("*").each(function() { 
        	 if ($(this).is('input')) {
        		 $(this).val('');
        	 }
        	 $.each(this.attributes, function() {
        		 this.value = this.value.replace('_set-0', '_set-' + form_count_remuneracao);
        	 });
         });
         
         $("#remuneracoes").append(row);
         // build data and append it to container
         
         row.find('#label_data_remuneracao_set-' + form_count_remuneracao).text(row.find('#label_data_remuneracao_set-' + form_count_remuneracao).text().replace('1', remuneracao_id));
         
         // increment form count so our view knows to populate 
         // that many fields for validation
         form_count_remuneracao ++;
         $("[name=dataremuneracaocri_cra_set-TOTAL_FORMS]").val(form_count_remuneracao);
         // ready bootstrap elements
         row.find('.date-picker').datepicker({
             todayHighlight: true,
             language: 'pt-BR'
         });
     });
     
     // Amortização
     form_count_amortizacao = $("input[name=dataamortizacaocri_cra_set-TOTAL_FORMS]").val();
     // get extra form count so we know what index to use for the next item.
      $("#add_data_amortizacao").click(function() {
          amortizacao_id = parseInt(form_count_amortizacao) + 1;
          row = $('#amortizacao-0').clone();
          row.attr('id', 'amortizacao-' + form_count_amortizacao);
          $(row).find("*").each(function() { 
         	 $.each(this.attributes, function() {
         		 this.value = this.value.replace('_set-0', '_set-' + form_count_amortizacao);
         	 });
          });
          
          $("#amortizacoes").append(row);
          // build data and append it to container
          
          row.find('#label_data_amortizacao_set-' + form_count_amortizacao).text(row.find('#label_data_amortizacao_set-' + form_count_amortizacao).text().replace('1', amortizacao_id));
          
          if ($("#id_dataamortizacaocri_cra_set-0-id").length > 0) {
 	         id = $("#id_dataamortizacaocri_cra_set-0-id").clone();
 	         id.attr("name", "dataamortizacaocri_cra_set-" + form_count_amortizacao + "-id");
 	         id.attr('id', "id_dataamortizacaocri_cra_set-" + form_count_amortizacao + "-id");
 	         $("#remuneracoes").append(id);
          }

          if ($("#id_dataamortizacaocri_cra_set-0-cri_cra").length > 0) {
 	         cri_cra = $("#id_dataamortizacaocri_cra_set-0-cri_cra").clone();
 	         cri_cra.attr("name", "dataamortizacaocri_cra_set-" + form_count_amortizacao + "-cri_cra");
 	         cri_cra.attr('id', "id_dataamortizacaocri_cra_set-" + form_count_amortizacao + "-cri_cra");
 	         $("#remuneracoes").append(operacao);
          }

          // increment form count so our view knows to populate 
          // that many fields for validation
          form_count_amortizacao ++;
          $("[name=dataamortizacaocri_cra_set-TOTAL_FORMS]").val(form_count_amortizacao);
          // ready bootstrap elements
          row.find('.date-picker').datepicker({
              todayHighlight: true,
              language: 'pt-BR'
          });
          var campo_percentual= row.find('.bootstrap-touchspin input').detach();
          row.find('.bootstrap-touchspin').empty().append(campo_percentual);
          row.find("input[name$='-percentual']").TouchSpin({
        	  initval: 0,
              min: 0,
              max: 100,
              step: 0.0001,
              decimals: 4,
              maxboostedstep: 100,
              postfix: '%'
          });
      });
});
