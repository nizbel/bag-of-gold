/**
 Core layout handlers and component wrappers
 **/

// BEGIN: Layout Brand
var LayoutBrand = function () {

	return {
		//main function to initiate the module
		init: function () {
			$('body').on('click', '.c-hor-nav-toggler', function () {
				var target = $(this).data('target');
				$(target).toggleClass("c-shown");
			});
		}

	};
}();
// END

// BEGIN: Layout Header
var LayoutHeader = function () {
	var offset = parseInt($('.c-layout-header').attr('data-minimize-offset') > 0 ? parseInt($('.c-layout-header').attr('data-minimize-offset')) : 0);
	var _handleHeaderOnScroll = function () {
		if ($(window).scrollTop() > offset) {
			$("body").addClass("c-page-on-scroll");
		} else {
			$("body").removeClass("c-page-on-scroll");
		}
	}

	var _handleTopbarCollapse = function () {
		$('.c-layout-header .c-topbar-toggler').on('click', function (e) {
			$('.c-layout-header-topbar-collapse').toggleClass("c-topbar-expanded");
		});
	}

	return {
		//main function to initiate the module
		init: function () {
			if ($('body').hasClass('c-layout-header-fixed-non-minimized')) {
				return;
			}

			_handleHeaderOnScroll();
			_handleTopbarCollapse();

			$(window).scroll(function () {
				_handleHeaderOnScroll();
			});
		}
	};
}();
// END

// BEGIN: Layout Mega Menu
var LayoutMegaMenu = function () {

	return {
		//main function to initiate the module
		init: function () {
			$('.c-mega-menu').on('click', '.c-toggler', function (e) {
				if (App.getViewPort().width < App.getBreakpoint('md')) {
					e.preventDefault();
					if ($(this).closest("li").hasClass('c-open')) {
						$(this).closest("li").removeClass('c-open');
					} else {
						$(this).closest("li").addClass('c-open');
					}
				}
			});

			$('.c-layout-header .c-hor-nav-toggler:not(.c-quick-sidebar-toggler)').on('click', function () {
				$('.c-layout-header').toggleClass('c-mega-menu-shown');

				if ($('body').hasClass('c-layout-header-mobile-fixed')) {
					var height = App.getViewPort().height - $('.c-layout-header').outerHeight(true) - 60;
					$('.c-mega-menu').css('max-height', height);
				}
			});
		}
	};
}();
// END

// BEGIN: Layout Go To Top
var LayoutGo2Top = function () {

	var handle = function () {
		var currentWindowPosition = $(window).scrollTop(); // current vertical position
		if (currentWindowPosition > 300) {
			$(".c-layout-go2top").show();
		} else {
			$(".c-layout-go2top").hide();
		}
	};

	return {

		//main function to initiate the module
		init: function () {

			handle(); // call headerFix() when the page was loaded

			if (navigator.userAgent.match(/iPhone|iPad|iPod/i)) {
				$(window).bind("touchend touchcancel touchleave", function (e) {
					handle();
				});
			} else {
				$(window).scroll(function () {
					handle();
				});
			}

			$(".c-layout-go2top").on('click', function (e) {
				e.preventDefault();
				$("html, body").animate({
					scrollTop: 0
				}, 600);
			});
		}

	};
}();
// END: Layout Go To Top

// BEGIN: Onepage Nav
var LayoutOnepageNav = function () {

	var handle = function () {
		var offset;
		var scrollspy;
		var speed;
		var nav;

		$('body').addClass('c-page-on-scroll');
		offset = $('.c-layout-header-onepage').outerHeight(true);
		$('body').removeClass('c-page-on-scroll');

		if ($('.c-mega-menu-onepage-dots').size() > 0) {
			if ($('.c-onepage-dots-nav').size() > 0) {
				$('.c-onepage-dots-nav').css('margin-top', -($('.c-onepage-dots-nav').outerHeight(true) / 2));
			}
			scrollspy = $('body').scrollspy({
				target: '.c-mega-menu-onepage-dots',
				offset: offset
			});
			speed = parseInt($('.c-mega-menu-onepage-dots').attr('data-onepage-animation-speed'));
		} else {
			scrollspy = $('body').scrollspy({
				target: '.c-mega-menu-onepage',
				offset: offset
			});
			speed = parseInt($('.c-mega-menu-onepage').attr('data-onepage-animation-speed'));
		}

		scrollspy.on('activate.bs.scrollspy', function () {
			$(this).find('.c-onepage-link.c-active').removeClass('c-active');
			$(this).find('.c-onepage-link.active').addClass('c-active');
		});

		$('.c-onepage-link > a').on('click', function (e) {
			var section = $(this).attr('href');
			var top = 0;

			if (section !== "#home") {
				top = $(section).offset().top - offset + 1;
			}

			$('html, body').stop().animate({
				scrollTop: top,
			}, speed, 'easeInExpo');

			e.preventDefault();

			if (App.getViewPort().width < App.getBreakpoint('md')) {
				$('.c-hor-nav-toggler').click();
			}
		});
	};

	return {

		//main function to initiate the module
		init: function () {
			handle(); // call headerFix() when the page was loaded
		}

	};
}();
// END: Onepage Nav

// BEGIN: OwlCarousel
var ContentOwlcarousel = function () {

	var _initInstances = function () {
		$("[data-slider='owl'] .owl-carousel").each(function () {

			var parent = $(this);

			var items;
			var itemsDesktop;
			var itemsDesktopSmall;
			var itemsTablet;
			var itemsTabletSmall;
			var itemsMobile;

			var rtl_mode = (parent.data('rtl') !== undefined) ? parent.data('rtl') : false ; 
			var items_loop = (parent.data('loop') !== undefined) ? parent.data('loop') : true ; 
			var items_nav_dots = (parent.attr('data-navigation-dots') !== undefined) ? parent.data('navigation-dots') : true ; 
			var items_nav_label = (parent.attr('data-navigation-label') !== undefined) ? parent.data('navigation-label') : false ; 

			if (parent.data("single-item") == true) {
				items = 1;
				itemsDesktop = 1;
				itemsDesktopSmall = 1;
				itemsTablet = 1;
				itemsTabletSmall = 1;
				itemsMobile = 1;
			} else {
				items = parent.data('items');
				itemsDesktop = parent.data('desktop-items') ? parent.data('desktop-items') : items;
				itemsDesktopSmall = parent.data('desktop-small-items') ? parent.data('desktop-small-items') : 3;
				itemsTablet = parent.data('tablet-items') ? parent.data('tablet-items') : 2;
				itemsMobile = parent.data('mobile-items') ? parent.data('mobile-items') : 1;
			}

			parent.owlCarousel({

				rtl: rtl_mode,
				loop: items_loop,
				items: items,
				responsive: {
					0:{
						items: itemsMobile
					},
					480:{
						items: itemsMobile
					},
					768:{
						items: itemsTablet
					},
					980:{
						items: itemsDesktopSmall
					},
					1200:{
						items: itemsDesktop
					}
				},

				dots: items_nav_dots,
				nav: items_nav_label,
				navText: false,
				autoplay: (parent.data("auto-play")) ? parent.data("auto-play") : true,
				autoplayTimeout: (parent.data('slide-speed')) ? parent.data('slide-speed') : 5000,
				autoplayHoverPause: (parent.data('auto-play-hover-pause')) ? parent.data('auto-play-hover-pause') : false,
			});
		});
	};

	return {

		//main function to initiate the module
		init: function () {

			_initInstances();
		}

	};
}();
// END: OwlCarousel

/*
// BEGIN: CounterUp
var ContentCounterUp = function () {

	var _initInstances = function () {

		// init counter up
		$("[data-counter='counterup']").counterUp({
			delay: 10,
			time: 1000
		});
	};

	return {

		//main function to initiate the module
		init: function () {
			_initInstances();
		}

	};
}();
// END: CounterUp
*/

// BEGIN : SCROLL TO VIEW DETECTION
function isScrolledIntoView(elem)
{
    var $elem = $(elem);
    var $window = $(window);

    var docViewTop = $window.scrollTop();
    var docViewBottom = docViewTop + $window.height();

    var elemTop = $elem.offset().top;
    var elemBottom = elemTop + $elem.height();

    return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
}
// END : SCROLL TO VIEW FUNCTION

/*
// BEGIN : PROGRESS BAR 
var LayoutProgressBar = function ($) {

    return {
        init: function () {
        	var id_count = 0; // init progress bar id number
        	$('.c-progress-bar-line').each(function(){
        		id_count++; // progress bar id running number
        		// build progress bar class selector with running id number
        		var this_id = $(this).attr('data-id', id_count);
        		var this_bar = '.c-progress-bar-line[data-id="'+id_count+'"]';

        		// build progress bar object key
        		var progress_data = $(this).data('progress-bar');
				progress_data = progress_data.toLowerCase().replace(/\b[a-z]/g, function(letter) {
				    return letter.toUpperCase();
				});
				if(progress_data == 'Semicircle') { progress_data = 'SemiCircle'; }

				// grab options
				var bar_color = $(this).css('border-top-color'); // color	
				var this_animation = $(this).data('animation'); // animation type : linear, easeIn, easeOut, easeInOut, bounce
				var stroke_width = $(this).data('stroke-width'); // stroke width
				var bar_duration = $(this).data('duration'); // duration
				var trail_width = $(this).data('trail-width'); // trail width
				var trail_color = $(this).data('trail-color'); // trail color
				var bar_progress = $(this).data('progress'); // progress value
				var font_color = $(this).css('color'); // progress font color

				// set default data if options is null / undefinded
				if (bar_color == 'rgb(92, 104, 115)'){ bar_color = '#32c5d2'; } // set default color 
				if (trail_color == ''){ trail_color = '#5c6873'; }
				if (trail_width == ''){ trail_width = '0'; }
				if (bar_progress == ""){ bar_progress = '1'; }
				if (stroke_width == ""){ stroke_width = '3'; }
				if (this_animation == ""){ this_animation = 'easeInOut'; }
				if (bar_duration == ""){ bar_duration = '1500'; }
	         

	         	// set progress bar
	         	var bar = new ProgressBar[progress_data](this_bar, {
		            strokeWidth: stroke_width,
		            easing: this_animation,
		            duration: bar_duration,
		            color: bar_color,
		            trailWidth: trail_width,
		            trailColor: trail_color,
		            svgStyle: null,		            
	            	step: function (state, bar) {
						bar.setText(Math.round(bar.value() * 100) + '%');
					},									   
					text: {
						style: {
							color: font_color,
						}
					},
		        });

	         	// init animation when progress bar in view without scroll
	         	var check_scroll = isScrolledIntoView(this_bar); // check if progress bar is in view - return true / false
			    if (check_scroll == true){
		        	bar.animate(bar_progress);  // Number from 0.0 to 1.0
		        }
		        
	         	// start progress bar animation upon scroll view
		        $(window).scroll(function (event) {
				    var check_scroll = isScrolledIntoView(this_bar); // check if progress bar is in view - return true / false
				    if (check_scroll == true){
			        	bar.animate(bar_progress);  // Number from 0.0 to 1.0
			        }
				});
				

        	});

        	
         
           
        }
    }
}(jQuery);
// END : PROGRESS BAR
*/

// Main theme initialization
$(document).ready(function () {
	// init layout handlers
	LayoutBrand.init();
	LayoutMegaMenu.init();
	LayoutGo2Top.init();
	LayoutOnepageNav.init();
//	LayoutProgressBar.init();
	LayoutHeader.init();

	// init plugin wrappers
	ContentOwlcarousel.init();
//	ContentCounterUp.init();
});

