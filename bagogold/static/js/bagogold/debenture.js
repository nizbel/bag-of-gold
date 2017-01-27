$(document).ready(function() {
	form_count = $("input[name=divisaooperacaodebenture_set-TOTAL_FORMS]").val();
    // get extra form count so we know what index to use for the next item.
     $("#add-another").click(function() {
         divisao_id = parseInt(form_count) + 1;
         titulo = $("<h3 class='font-yellow-crusta' align='center'><strong>Divisão " + divisao_id + "</strong></h3><br/>");
         row = $('#divisao-0').clone();
         
         $("#forms").append(titulo);
         $("#forms").append(row);
         // build divisao and append it to our forms container
         
//         label_divisao = $("<label for=id_divisaooperacaodebenture_set-" + form_count + "-divisao>Divisão:</label>");
//         divisao = $("#id_divisaooperacaodebenture_set-0-divisao").clone();
//         divisao.attr("name", "divisaooperacaodebenture_set-" + form_count + "-divisao");
//         divisao.attr('id', "id_divisaooperacaodebenture_set-" + form_count + "-divisao");
//         divisao.removeAttr('value');
//         par_divisao = $('<p></p>');
//         par_divisao.append(label_divisao);
//         par_divisao.append(divisao);
//         
//
//         label_quantidade = $("<label for=id_divisaooperacaodebenture_set-" + form_count + "-quantidade>Quantidade:</label>");
//         quantidade = $("#id_divisaooperacaodebenture_set-0-quantidade").clone();
//         quantidade.attr("name", "divisaooperacaodebenture_set-" + form_count + "-quantidade");
//         quantidade.attr('id', "id_divisaooperacaodebenture_set-" + form_count + "-quantidade");
//         quantidade.removeAttr('value');
//         par_quantidade = $('<p></p>');
//         par_quantidade.append(label_quantidade);
//         par_quantidade.append(quantidade);
         
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
     });
});
