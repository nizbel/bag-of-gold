$(document).ready(function() {
    //for every field change
    $('#id_preco_unitario').blur(function() {
        var preco = $('#id_preco_unitario').val().replace(/,/g, '.');
        
        var selected = $("input[type='radio'][name='radioDT']:checked");
        if (selected.length > 0 && selected.val() == "0") {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.0325 / 100;
        } else {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.025 / 100;
        }
        
        $('#id_emolumentos').val(Math.floor(emolumentos*100)/100);
    });
    
    $('#id_quantidade').blur(function() {
        var preco = $('#id_preco_unitario').val().replace(/,/g, '.');
        
        var selected = $("input[type='radio'][name='radioDT']:checked");
        if (selected.length > 0 && selected.val() == "0") {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.0325 / 100;
        } else {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.025 / 100;
        }
        $('#id_emolumentos').val(Math.floor(emolumentos*100)/100);
    });
    
    form_count = $("input[name=divisaooperacaoacao_set-TOTAL_FORMS]").val();
    // get extra form count so we know what index to use for the next item.
     $("#add-another").click(function() {
         divisao_id = parseInt(form_count) + 1;
         titulo = $("<h3>Divisão " + divisao_id + "</h3>");
         
         label_divisao = $("<label for=id_divisaooperacaoacao_set-" + form_count + "-divisao>Divisão:</label>");
         divisao = $("#id_divisaooperacaoacao_set-0-divisao").clone();
         divisao.attr("name", "divisaooperacaoacao_set-" + form_count + "-divisao");
         divisao.attr('id', "id_divisaooperacaoacao_set-" + form_count + "-divisao");
         divisao.removeAttr('value');
         par_divisao = $('<p></p>');
         par_divisao.append(label_divisao);
         par_divisao.append(divisao);
         
         label_quantidade = $("<label for=id_divisaooperacaoacao_set-" + form_count + "-quantidade>Quantidade:</label>");
         quantidade = $("#id_divisaooperacaoacao_set-0-quantidade").clone();
         quantidade.attr("name", "divisaooperacaoacao_set-" + form_count + "-quantidade");
         quantidade.attr('id', "id_divisaooperacaoacao_set-" + form_count + "-quantidade");
         quantidade.removeAttr('value');
         par_quantidade = $('<p></p>');
         par_quantidade.append(label_quantidade);
         par_quantidade.append(quantidade);
         
         label_qtd_proventos_utilizada = $("<label for=id_divisaooperacaoacao_set-" + form_count + "-qtd_proventos_utilizada>Quantidade de proventos utilizada:</label>");
         qtd_proventos_utilizada = $("#id_divisaooperacaoacao_set-0-qtd_proventos_utilizada").clone();
         qtd_proventos_utilizada.attr("name", "divisaooperacaoacao_set-" + form_count + "-qtd_proventos_utilizada");
         qtd_proventos_utilizada.attr('id', "id_divisaooperacaoacao_set-" + form_count + "-qtd_proventos_utilizada");
         qtd_proventos_utilizada.removeAttr('value');
         par_qtd_proventos_utilizada = $('<p></p>');
         par_qtd_proventos_utilizada.append(label_qtd_proventos_utilizada);
         par_qtd_proventos_utilizada.append(qtd_proventos_utilizada);
         
         id = $("#id_divisaooperacaoacao_set-0-id").clone();
         id.attr("name", "divisaooperacaoacao_set-" + form_count + "-id");
         id.attr('id', "id_divisaooperacaoacao_set-" + form_count + "-id");
         id.removeAttr('value');
         par_id = $('<p></p>');
         par_id.append(id);
    
         operacao = $("#id_divisaooperacaoacao_set-0-operacao").clone();
         operacao.attr("name", "divisaooperacaoacao_set-" + form_count + "-operacao");
         operacao.attr('id', "id_divisaooperacaoacao_set-" + form_count + "-operacao");
         par_operacao = $('<p></p>');
         par_operacao.append(operacao);
      
         $("#forms").append(titulo);
         $("#forms").append(par_divisao);
         $("#forms").append(par_quantidade);
         $("#forms").append(par_qtd_proventos_utilizada);
         $("#forms").append(par_id);
         $("#forms").append(par_operacao);
         // build divisao and append it to our forms container
    
         form_count ++;
         $("[name=divisaooperacaoacao_set-TOTAL_FORMS]").val(form_count);
         // increment form count so our view knows to populate 
         // that many fields for validation
     })
});
