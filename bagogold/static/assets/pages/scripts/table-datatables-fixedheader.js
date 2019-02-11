var TableDatatablesFixedHeader = function () {

    var initTable1 = function () {
        var table = $('.table-header-fixed');

        var fixedHeaderOffset = 0;
        if (App.getViewPort().width < App.getResponsiveBreakpoint('md')) {
			if ($('.page-header').hasClass('page-header-fixed-mobile')) {
			fixedHeaderOffset = $('.page-header').outerHeight(true);
			}
		} else if ($('body').hasClass('page-header-menu-fixed')) { // admin 3 fixed header menu mode
		fixedHeaderOffset = $('.page-header-menu').outerHeight(true);
		} else if ($('body').hasClass('page-header-top-fixed')) { // admin 3 fixed header top mode
		fixedHeaderOffset = $('.page-header-top').outerHeight(true);
		} else if ($('.page-header').hasClass('navbar-fixed-top')) {
		fixedHeaderOffset = $('.page-header').outerHeight(true);
		} else if ($('body').hasClass('page-header-fixed')) {
		fixedHeaderOffset = 64; // admin 5 fixed height
		}

        var oTable = table.filter(function() {
        	return (! $.fn.DataTable.isDataTable($(this)) && ! ($(this).hasClass('fixedHeader-floating') || $(this).hasClass('fixedHeader-locked')));
        	}).dataTable({

            // Internationalisation. For more info refer to http://datatables.net/manual/i18n
            "language": {
                "aria": {
                    "sortAscending": ": activate to sort column ascending",
                    "sortDescending": ": activate to sort column descending"
                },
                "emptyTable": "Nenhum dado disponível",
                "info": "Mostrando _START_ a _END_ de _TOTAL_ itens",
                "infoEmpty": "Nenhum resultado encontrado",
                "infoFiltered": "(total de _MAX_ itens )",
                "lengthMenu": "_MENU_ itens",
                "search": "Busca:",
                "zeroRecords": "Nenhum registro correspondente encontrado"
            },

            // Or you can use remote translation file
            //"language": {
            //   url: '//cdn.datatables.net/plug-ins/3cfcc339e89/i18n/Portuguese.json'
            //},

            // setup rowreorder extension: http://datatables.net/extensions/fixedheader/
            fixedHeader: {
                header: true,
                headerOffset: fixedHeaderOffset
            },

            "order": [
                [0, 'asc']
            ],
            
            "lengthMenu": [
                [5, 10, 15, 20, -1],
                [5, 10, 15, 20, "Todos"] // change per page values here
            ],
            // set the initial value
            "pageLength": 20,
            
            // Uncomment below line("dom" parameter) to fix the dropdown overflow issue in the datatable cells. The default datatable layout
            // setup uses scrollable div(table-scrollable) with overflow:auto to enable vertical scroll(see: assets/global/plugins/datatables/plugins/bootstrap/dataTables.bootstrap.js). 
            // So when dropdowns used the scrollable div should be removed. 
            //"dom": "<'row' <'col-md-12'T>><'row'<'col-md-6 col-sm-12'l><'col-md-6 col-sm-12'f>r>t<'row'<'col-md-5 col-sm-12'i><'col-md-7 col-sm-12'p>>",
      });
    }

    return {

        //main function to initiate the module
        init: function () {

            if (!jQuery().dataTable) {
                return;
            }

            initTable1();
        }

    };

}();

jQuery(document).ready(function() {
    TableDatatablesFixedHeader.init();
});