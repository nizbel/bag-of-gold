$(document).ready(function() {
	//for every field change
    $('#id_preco_unitario').change(function() {
        var preco = $('#id_preco_unitario').val().replace(/,/g, '.');
        
        var selected = $("input[type='radio'][name='radioDT']:checked");
        if (selected.length > 0 && selected.val() == "1") {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.025 / 100;
        } else {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.0325 / 100;
        }
        $('#id_emolumentos').val((Math.floor(emolumentos*100)/100).toFixed(2).replace('.', ','));
    });
    
    $('#id_quantidade').change(function() {
        var preco = $('#id_preco_unitario').val().replace(/,/g, '.');
        
        var selected = $("input[type='radio'][name='radioDT']:checked");
        if (selected.length > 0 && selected.val() == "1") {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.025 / 100;
        } else {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.0325 / 100;
        }
        $('#id_emolumentos').val((Math.floor(emolumentos*100)/100).toFixed(2).replace('.', ','));
    });
    
	$("input[name='radioDT']").click(function () {
		var preco = $('#id_preco_unitario').val().replace(/,/g, '.');
        
        var selected = $("input[type='radio'][name='radioDT']:checked");
        if (selected.length > 0 && selected.val() == "1") {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.025 / 100;
        } else {
            var emolumentos = (preco * $('#id_quantidade').val()) * 0.0325 / 100;
        }
        $('#id_emolumentos').val((Math.floor(emolumentos*100)/100).toFixed(2).replace('.', ','));
	});
});