require(['config'], function() {
    'use strict';

    require([
            'jquery',
            'modernizr'
    ], function($, ø) {
        // Do stuff.
        console.log('main.js has loaded.');
        console.log('running jQuery version ' + $().jquery + '.');
        console.log('running Modernizr version ' + ø._version + '.');

        $('[data-method=delete]').on('click', function(e) {
            e.preventDefault();

            var link = $(this),
                url = $(this).attr('href');
            if (confirm('Are you sure you want to delete this?')) {
                $.ajax(url, {
                    type: 'DELETE',
                    success: function() {
                        link.closest('.js-deletable').remove();
                    }
                });
            }

            return false;
        });

        $('[data-action=close], [data-action=open]').on('click', function(e) {
            e.preventDefault();
            var link = $(this),
                url = '/issues/' + $(this).data('id') + '/' + $(this).data('action');
            $.ajax(url, {
                type: 'PUT',
                success: function() {
                    window.location.reload()
                }
            });
            return false;
        });
    });

});
