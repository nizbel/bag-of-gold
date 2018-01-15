$(document).ready(function() {
    $('.em-construcao').attr('data-original-title', 'Em construção').attr('data-placement', 'top').addClass('tooltips').removeClass('em-construcao');
});

// Clipboard.js
$('.mt-clipboard').each(function(){
	var clipboard = new Clipboard(this);	

	clipboard.on('success', function(e) {
	});
});