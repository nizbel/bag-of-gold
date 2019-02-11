$(document).ready(function() {
	$('#summernote').summernote({lang: "pt-BR"});
	
	// Carregar multiselect
    var btn_class = $('#id_tags').attr('class');
    var width = ($('#id_tags').data('width')) ? $('#id_tags').data('width') : '' ;
    var height = ($('#id_tags').data('height')) ? $('#id_tags').data('height') : '' ;
    var filter = ($('#id_tags').data('filter')) ? $('#id_tags').data('filter') : false ;
	$('#id_tags').multiselect({
        enableFiltering: filter,
        filterPlaceholder: 'Insira o nome da tag',
        enableCaseInsensitiveFiltering: true,
        buttonWidth: width,
        maxHeight: height,
        buttonClass: btn_class,
        numberDisplayed: 10
    });   
	
	$('#post_form').submit(function() {
		$('#id_conteudo').val($('#summernote').summernote('code'));
	});
    
    // Aplicar maxlength
    $("#id_titulo").maxlength({alwaysShow: true});
    $("#id_chamada_facebook").maxlength({alwaysShow: true});
});