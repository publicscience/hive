require(['config'], function() {
    'use strict';

    require([
            'jquery',
            'mentions'
    ], function($) {
        // Deleting things.
        $('[data-method=delete]').on('click', function(e) {
            e.preventDefault();

            var link = $(this),
                url = $(this).attr('href');
            if (confirm('Are you sure you want to delete this?')) {
                $.ajax(url, {
                    type: 'DELETE',
                    success: function() {
                        link.closest('.js-parent').remove();
                    }
                });
            }

            return false;
        });

        // Closing & opening issues.
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

        // Editing.
        $('[data-action=edit]').on('click', function(e) {
            e.preventDefault();
            var parent = $(this).closest('js-parent'),
                editable = parent.find('.js-editable'),
                raw = editable.data('raw');

            return false;
        });

        $('textarea.mention').mentionsInput({
            onDataRequest: function(mode, query, callback) {
                $.ajax('/users.json', {
                    data: {
                        query: query
                    },
                    success: function(data) {
                        callback.call(this, data['users']);
                    }
                });
            }
        });

        $('.js-preprocess input[type=submit]').on('click', function(e) {
            $('textarea.mention').each(function() {
                $(this).mentionsInput('val', function(text) {
                    $('textarea.mention-target').val(text);
                });
            });
        });

        $('.js-lightboxable').on('click', function() {
            var full_url = $(this).data('full');
            $('.overlay').fadeIn();
            $('.lightbox').html('<img src="'+full_url+'">');
        });

        $('.overlay').on('click', function() {
            $(this).fadeOut();
        });
    });

});
