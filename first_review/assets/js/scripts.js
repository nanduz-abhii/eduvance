/*
Author       : Themesvila
Template Name: Edumon
Version      : 1.0
*/


(function($) {
	'use strict';


		/*PRELOADER JS*/
		
		$(window).on('load', function() { 
			$('.preloader').fadeOut();
			$('.preloader').delay(350).fadeOut('slow'); 
		}); 
				
		/*END PRELOADER JS*/
		
		jQuery(document).ready(function($) {

			/*Counter */
			$('.counter-item .cnumb').counterUp({
				delay: 10,
				time: 1000
			});
			
			/* Active Menu */
			$(".mobile_menu").simpleMobileMenu({			
				"menuStyle": "slide"
			});
			
		});
		
		
		/*Start Search Box JS*/
		$(".search-btn").click(function(){
			$(".search_box").addClass("active");
			$(this).css("display", "none");
			$(".search-data").fadeIn(500);
			$(".close-btn").fadeIn(500);
			$(".search-data .line").addClass("active");
			setTimeout(function(){
			 $("input").focus();
			 $(".search-data label").fadeIn(500);
			 $(".search-data span").fadeIn(500);
			}, 800);
		});

		$(".close-btn").click(function(){
			$(".search_box").removeClass("active");
			$(".search-btn").fadeIn(800);
			$(".search-data").fadeOut(500);
			$(".close-btn").fadeOut(500);
			$(".search-data .line").removeClass("active");
			$("input").val("");
			$(".search-data label").fadeOut(500);
			$(".search-data span").fadeOut(500);
		});		
		/*End Search Box JS*/
		
		/*START Mini Cart JS*/
		
		$('.mcart_open').on('click', function(){
			var menu = $(this).attr('data-menu');

			$(menu).toggleClass('min_cart_active');
			

		});

		$('.min_cart_wrapper').on('click', function(event){	
			if ( $(event.target).hasClass('min_cart_wrapper') ) {
				 $('.min_cart_active').removeClass('min_cart_active');
			}
		});
	
		$('.cart_close').on('click', function(event){	
			$('.min_cart_active').removeClass('min_cart_active');			
		});

  	
		/*END Mini Cart JS*/
		
		/* Image Popup */
		 $('.popbtn').magnificPopup({
			 type:'image',
			 gallery:{
				enabled:true
			  }
		});		
		
		 /*START Portfolio*/	
		$('.courses-slider').owlCarousel({
			items : 3,
			autoplay: true,
			center: true,
			loop: true,
			navText: ["<i class='bx bx-chevrons-left'></i>" ,"<i class='bx bx-chevrons-right'></i>"],
			nav: true,
			dots: false,
			margin: 30,
			responsive:{
				0:{
					items:1,
					
				},
				575:{
					items:1,
					
				},
				768:{
					items:2,
					
				},
				1000:{
					items:3,
			
				},
				1200:{
					items:3,
			
				}
			}
		});
		
		/*END Portfolio*/
		
		/*START PARTNER LOGO*/
		$('.partners').owlCarousel({
			margin: 60,
			autoPlay: 5000, //Set AutoPlay to 3 seconds
			items : 6,			
			nav: false,
			dots: false,
			loop: true,
			responsive:{
				0:{
					items:2,
					
				},
				575:{
					items:3,
					
				},
				768:{
					items:4,
					
				},
				1000:{
					items:5,
			
				},
				1200:{
					items:6,
			
				}
			}
		});
		/*END PARTNER LOGO*/
		
		 /*START Testimonials*/	
		$('.review-slider').owlCarousel({
			items : 3,
			autoplay: true,
			center: true,
			loop: true,
			navText: ["<i class='bx bx-chevrons-left'></i>" ,"<i class='bx bx-chevrons-right'></i>"],
			nav: true,
			dots: true,
			margin: 35,
			responsive:{
				0:{
					items:1,
					
				},
				575:{
					items:1,
					
				},
				768:{
					items:2,
					
				},
				1000:{
					items:3,
			
				},
				1200:{
					items:3,
			
				}
			}
		});
		
		/*END Testimonials*/

		/*Start MouseMove*/
		document.addEventListener("mousemove", parallax);
		function parallax(event) {
		  this.querySelectorAll(".eitem").forEach((shift) => {
			const position = shift.getAttribute("value");
			const x = (window.innerWidth - event.pageX * position) / 90;
			const y = (window.innerHeight - event.pageY * position) / 90;

			shift.style.transform = `translateX(${x}px) translateY(${y}px)`;
		  });
		}
		/*End MouseMove*/
		
		/* WOW */
		new WOW().init();

})(jQuery);
