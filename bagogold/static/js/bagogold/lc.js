$(document).ready(function() {
	form_count = $("input[name=divisaooperacaolc_set-TOTAL_FORMS]").val();
    // get extra form count so we know what index to use for the next item.
     $("#add-another").click(function() {
         divisao_id = parseInt(form_count) + 1;
         titulo = $("<h3>Divisão " + divisao_id + "</h3>");
         
         label_divisao = $("<label for=id_divisaooperacaolc_set-" + form_count + "-divisao>Divisão:</label>");
         divisao = $("#id_divisaooperacaolc_set-0-divisao").clone();
         divisao.attr("name", "divisaooperacaolc_set-" + form_count + "-divisao");
         divisao.attr('id', "id_divisaooperacaolc_set-" + form_count + "-divisao");
         divisao.removeAttr('value');
         par_divisao = $('<p></p>');
         par_divisao.append(label_divisao);
         par_divisao.append(divisao);
         

         label_quantidade = $("<label for=id_divisaooperacaolc_set-" + form_count + "-quantidade>Quantidade:</label>");
         quantidade = $("#id_divisaooperacaolc_set-0-quantidade").clone();
         quantidade.attr("name", "divisaooperacaolc_set-" + form_count + "-quantidade");
         quantidade.attr('id', "id_divisaooperacaolc_set-" + form_count + "-quantidade");
         quantidade.removeAttr('value');
         par_quantidade = $('<p></p>');
         par_quantidade.append(label_quantidade);
         par_quantidade.append(quantidade);
         
         id = $("#id_divisaooperacaolc_set-0-id").clone();
         id.attr("name", "divisaooperacaolc_set-" + form_count + "-id");
         id.attr('id', "id_divisaooperacaolc_set-" + form_count + "-id");
         id.removeAttr('value');
         par_id = $('<p></p>');
         par_id.append(id);

         operacao = $("#id_divisaooperacaolc_set-0-operacao").clone();
         operacao.attr("name", "divisaooperacaolc_set-" + form_count + "-operacao");
         operacao.attr('id', "id_divisaooperacaolc_set-" + form_count + "-operacao");
         par_operacao = $('<p></p>');
         par_operacao.append(operacao);
      
         $("#forms").append(titulo);
         $("#forms").append(par_divisao);
         $("#forms").append(par_quantidade);
         $("#forms").append(par_id);
         $("#forms").append(par_operacao);
         // build divisao and append it to our forms container
    
         form_count ++;
         $("[name=divisaooperacaolc_set-TOTAL_FORMS]").val(form_count);
         // increment form count so our view knows to populate 
         // that many fields for validation
     })
	
	
	if ($('#id_tipo_operacao').val() == 'C') {
        $("#id_operacao_compra").parent().hide();
        $("#id_letra_credito").parent().show();
    } else {
        $("#id_operacao_compra").parent().show();
        $("#id_letra_credito").parent().hide();
    }
	
	// Adiciona alterações para o form dependendo do tipo de operação
	$("#id_tipo_operacao").change(function() {
	   if ($(this).val() == 'C') {
		   $("#id_operacao_compra").parent().hide();
		   $("#id_letra_credito").parent().show();
	   } else {
        $("#id_operacao_compra").parent().show();
        $("#id_letra_credito").parent().hide();
	   }
	})
});
