require(['config'], function() {
    'use strict';

    require([
            'jquery',
            'mentions'
    ], function($) {

        var mentionsInputOptions = {
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
        }
        $('textarea.mention').mentionsInput(mentionsInputOptions);

        // Preprocess mention-enabled forms.
        function preprocess(form) {
            form.find('textarea.mention').each(function() {
                $(this).mentionsInput('val', function(text) {
                    form.find('textarea.mention-target').val(text);
                });
            });
            return form;
        }

        // Deleting things.
        $(document.body).on('click', '[data-method=delete]', function(e) {
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
                    // Cheating :)
                    window.location.reload()
                }
            });
            return false;
        });

        // Editing.
        $(document.body).on('click', '[data-action=edit]', function(e) {
            e.preventDefault();
            var parent = $(this).closest('.js-parent'),
                editable = parent.find('.js-editable'),
                raw = editable.data('raw'),
                form = $('<form class="js-preprocess">\
                            <div><textarea class="mention">'+raw+'</textarea></div>\
                            <textarea name="body" class="mention-target"></textarea>\
                            <ul class="form--attachments">\
                            <li><h6>New Attachments</h6></li>\
                            <li class="input"><input type="file" name="file0"></li>\
                            </ul>\
                        </form>'),
                stashed = $('<div class="stashed" style="display:none;">'+editable.html()+'</div>'),
                actions = parent.find('[class*=actions]').first(),
                url = $(this).attr('href');

            actions.html('\
               <li><a href="'+url+'" data-action="cancel">cancel</a></li>\
               <li><a href="'+url+'" data-action="update">update</a></li>\
               ');

            editable.empty();
            editable.append(form);
            editable.append(stashed);
            form.find('textarea.mention')
                .mentionsInput(mentionsInputOptions)
                .focus();

            return false;
        });
        $(document.body).on('click', '[data-action=cancel]', function(e) {
            e.preventDefault();
            var parent = $(this).closest('.js-parent'),
                editable = parent.find('.js-editable'),
                stashed = parent.find('.stashed'),
                actions = parent.find('[class*=actions]').first(),
                url = $(this).attr('href');

            actions.html('\
               <li><a href="'+url+'" data-action="edit">edit</a></li>\
               <li><a href="'+url+'" data-method="delete">delete</a></li>\
               ');

            editable.html(stashed.html());
            return false;
        });

        $(document.body).on('click', '[data-action=update]', function(e) {
            e.preventDefault();

            var parent = $(this).closest('.js-parent'),
                editable = parent.find('.js-editable'),
                actions = parent.find('[class*=actions]').first(),
                form = preprocess(editable.find('form'))[0],
                url = $(this).attr('href'),
                formData = new FormData(form);

            $.ajax(url, {
                method: 'PUT',
                beforeSend: function(xhr) {
                },
                data: formData,
                success: function(data) {
                    parent.html($(data['html']).html());
                },
                cache: false,
                contentType: false,
                processData: false
            });

            actions.html('\
               <li><a href="'+url+'" data-action="edit">edit</a></li>\
               <li><a href="'+url+'" data-method="delete">delete</a></li>\
               ');

            return false;
        });

        $(document.body).on('click', '.js-preprocess input[type=submit]', function() {
            var form = $(this).closest('.js-preprocess');
            preprocess(form);
        });

        $(document.body).on('click', '.js-lightboxable', function() {
            var full_url = $(this).data('full');
            $('.overlay').fadeIn();
            $('.lightbox').html('<img src="'+full_url+'">');
        });

        $('.overlay').on('click', function() {
            $(this).fadeOut();
        });

        $(document.body).on('change', '.form--attachments input[type=file]', function() {
            if ( $(this).val() ) {
                var el = $(this).closest('.input'),
                    idx = el.index();
                if ( el.find('.js-clear-input').length === 0 ) {
                    el.append('<a class="js-clear-input" href="#">delete</a>');
                }
                $(this).closest('.form--attachments').append('<li class="input"><input type="file" name="file'+idx.toString()+'"></li>');
            }
        });

        $(document.body).on('click', '.js-clear-input', function(e) {
            e.preventDefault();
            $(this).closest('.input').find('input').val('');
            $(this).remove();
            return false;
        });
    });

});
