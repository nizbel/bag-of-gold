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
});