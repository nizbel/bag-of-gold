$(document).ready(function() {
	$('#summernote').summernote({lang: "pt-BR"});
        //API:
        //var sHTML = $('#summernote_1').code(); // get code
        //$('#summernote_1').destroy(); // destroy
	
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
});