$(document).ready(function() {
	$('#form_inserir_op_cripto_lote').submit(function(){
		var erro = false;
		try {
		    var operacoes = $('#id_operacoes_lote').val().split('\n');
		    
		    var resultado = formatar(operacoes);
		    console.log(resultado);
		    erro = !resultado[0];
		    $('#id_operacoes_lote').val(resultado[1]);
		} catch (e) {
			erro = true;
			console.log(e);
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
		if (campos.length < 7) {
			erros.push('\nLinha ' + (i+1) + ': está com menos campos que o padrão');
			continue;
		}
		else if (campos.length > 7) {
			erros.push('\nLinha ' + (i+1) + ': está com mais campos que o padrão');
			continue;
		}
		
		// Testar campo com moedas
		var padrao_par_moeda = /[\w\d]+\/[\w\d]+/;
		campos[0] = campos[0].toUpperCase();
		if (!padrao_par_moeda.test(campos[0])) {
			erros.push('\nLinha ' + (i+1) + ': par MOEDA/MOEDA_UTILIZADA está formatado incorretamente');
		}
		
		// Formatar valores númericos
		campos[1] = campos[1].replace(/[^\d,]/g, '');
		campos[2] = campos[2].replace(/[^\d,]/g, '');
		campos[5] = campos[5].replace(/[^\d,]/g, '');
		
		// Verificar quantidade de casas decimais
		var padrao_max_decimais = /,\d{12}\d+/;
		if (padrao_max_decimais.test(campos[1])) {
			erros.push('\nLinha ' + (i+1) + ': quantidade está com mais de 12 casas decimais');
		}
		if (padrao_max_decimais.test(campos[2])) {
			erros.push('\nLinha ' + (i+1) + ': preço unitário está com mais de 12 casas decimais');
		}
		if (padrao_max_decimais.test(campos[5])) {
			erros.push('\nLinha ' + (i+1) + ': taxa está com mais de 12 casas decimais');
		}
		
		// Testar tipo de operação
		campos[4] = campos[4].toUpperCase();
		if (campos[4] != "C" && campos[4] != "V") {
			erros.push('\nLinha ' + (i+1) + ': tipo de operação deve ser C ou V');
		}
		
		// Testar data
		var padrao_data = /\d{1,2}[,\.\-\/]\d{1,2}[,\.\-\/]\d\d\d\d/;
		if (!padrao_data.test(campos[3])) {
			erros.push('\nLinha ' + (i+1) + ': data deve estar no formato DD/MM/YYYY');
		} else {
			campos[3] = campos[3].replace(/\D/g, '/');
		}
		
		// Verificar moeda da taxa
		campos[6] = campos[6].toUpperCase();
		if (campos[6] != campos[0].split('/')[0] && campos[6] != campos[0].split('/')[1]) {
			erros.push('\nLinha ' + (i+1) + ': moeda para taxa deve estar no par do primeiro campo');
		}
		
		lista_strings[i] = campos.join(";");
	}
	
	if (erros.length > 0) {
		sucesso = false;
		alert(erros);
	}
	
	return [sucesso, lista_strings.join("\n")];
}
