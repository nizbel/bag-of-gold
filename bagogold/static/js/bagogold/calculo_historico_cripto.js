// Apontar qual coluna será usada para buscar o tempo no cryptocompare e qual coluna possui valores
function calcular_patrimonio_em_reais(patrimonio, colTempoCalc, colValores, preencherAteIndice) {
	var def = $.Deferred();
	
	if (patrimonio.length == 0) {
		def.resolve({patrimonio: []});
		return def.promise();
	}
	var tickers = [];
    
	var colValorSomado = patrimonio[0].length;
	
    // Busca os tickers
	for (var data = 0; data < patrimonio.length; data++) {
		// Prepara o patrimonio calculado
		patrimonio[data].push(parseFloat(0));
	    loop_ticker: for (var key_data in patrimonio[data][colValores]) {
	    	if (patrimonio[data][colValores].hasOwnProperty(key_data)) {
	    		for (var i = 0; i < tickers.length; i++) {
    	    		if (tickers[i] == key_data) {
    	    			continue loop_ticker;
    	    		}
	    		}
                tickers.push(key_data);
	    	}
	    }
	}
	
	var requests = [];
	
    // Busca valores historicos para preencher no patrimonio calculado
	for (var i = 0; i < tickers.length; i++) {
    	var ticker_atual = tickers[i];
    	
    	requests.push($.get('https://min-api.cryptocompare.com/data/histoday?fsym=' + ticker_atual + '&tsym=BRL&allData=true'));
    }
    
    // Testar indice maximo de preenchimento para evitar erros
    if (preencherAteIndice == null || preencherAteIndice < 0 || preencherAteIndice > patrimonio.length) {
    	preencherAteIndice = patrimonio.length;
    }
    
	$.when.apply(null,requests).then(function(){
	    // in javascript arguments  exposed by default and can be treated like array
	    $.each(arguments, function(index, responseData){
            var status = responseData[1], response = responseData[0];
            if(status === 'success'){
            	var ticker_atual = tickers[index];
                // Guarda o índice da última data encontrada
                var ultima_data = 0;
                // Desconsiderar data atual de patrimônio
                loop_data_pat: for (var data = 0; data < preencherAteIndice; data++) {
                    for (var key_data in patrimonio[data][colValores]) {
                        // Verifica cada ticker nas datas para passar valor para patrimonio calculado
                        if (key_data == ticker_atual) {
                            // Data possui ticker, pesquisar no response a data para pegar valor de fechamento
                            for (var info_hist = ultima_data; info_hist < response.Data.length; info_hist++) {
                                if (response.Data[info_hist].time == patrimonio[data][colTempoCalc]) {
                                    patrimonio[data][colValorSomado] += patrimonio[data][colValores][key_data] * response.Data[info_hist].close;
                                    ultima_data = info_hist;
                                    continue loop_data_pat;
                                }
                            }
                        }
                    }
                }
            }          
	    });
	    
	    def.resolve({patrimonio: patrimonio});
	});
    return def.promise();
}