$(document).ready(function() {
	$('#form_inserir_transf_cripto_lote').submit(function(){
		var erro = false;
		try {
		    var transferencias = $('#id_transferencias_lote').val().split('\n');

		    var resultado = formatar(transferencias);
		    erro = !resultado[0];
		    $('#id_transferencias_lote').val(resultado[1]);
		} catch (e) {
			erro = true;
		}
		if (erro) {
	    	return false;
		}
	});
});

function formatar(lista_strings) {
	// Remover linhas vazias
	for (var i = lista_strings.length-1; i >= 0; i--) {
		if (lista_strings[i] == "") {
			lista_strings.splice(i, 1);
		}
	}
	
	var sucesso = true;
	var erros = [];
	
	for (var i = 0; i < lista_strings.length; i++) {
		var campos = lista_strings[i].split(";")
		if (campos.length < 6) {
			erros.push('\nLinha ' + (i+1) + ': está com menos campos que o padrão');
			continue;
		}
		else if (campos.length > 6) {
			erros.push('\nLinha ' + (i+1) + ': está com mais campos que o padrão');
			continue;
		}
		
		// Testar campo com moedas
		var padrao_par_moeda = /[\w\d]+/;
		campos[0] = campos[0].toUpperCase();
		if (!padrao_par_moeda.test(campos[0])) {
			erros.push('\nLinha ' + (i+1) + ': campo MOEDA está vazio');
		}
		
		// Formatar valores númericos
		campos[1] = campos[1].replace(/[^\d,]/g, '');
		campos[5] = campos[5].replace(/[^\d,]/g, '');
		
		// Verificar quantidade de casas decimais
		var padrao_max_decimais = /,\d{12}\d+/;
		if (padrao_max_decimais.test(campos[1])) {
			erros.push('\nLinha ' + (i+1) + ': quantidade está com mais de 12 casas decimais');
		}
		if (padrao_max_decimais.test(campos[5])) {
			erros.push('\nLinha ' + (i+1) + ': taxa está com mais de 12 casas decimais');
		}
		
		// Testar origem e destino
		if (campos[2].length > 50) {
			erros.push('\nLinha ' + (i+1) + ': descrição de origem deve ter no máximo 50 caracteres');
		}
		if (campos[3].length > 50) {
			erros.push('\nLinha ' + (i+1) + ': descrição de destino deve ter no máximo 50 caracteres');
		}
		
		// Testar data
		var padrao_data = /\d{1,2}[,\.\-\/]\d{1,2}[,\.\-\/]\d\d\d\d/;
		if (!padrao_data.test(campos[4])) {
			erros.push('\nLinha ' + (i+1) + ': data deve estar no formato DD/MM/YYYY');
		} else {
			campos[4] = campos[4].replace(/\D/g, '/');
		}
		
		
		lista_strings[i] = campos.join(";");
	}
	
	if (erros.length > 0) {
		sucesso = false;
		alert(erros);
	}
	
	return [sucesso, lista_strings.join("\n")];
}
