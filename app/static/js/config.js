requirejs.config({
    baseUrl: '/js',
    paths: {
        jquery: '//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min',
        requirejs: 'vendor/bower/requirejs/require',
        underscore: 'vendor/bower/underscore/underscore-min',
        elastic: 'vendor/jquery.elastic',
        mentions: 'vendor/jquery.mentionsInput'
    },
    shim: {
        underscore: {
            exports: '_'
        },
        elastic: {
            deps: ['jquery'],
            exports: 'elastic'
        },
        mentions: {
            deps: ['jquery', 'underscore', 'elastic'],
            exports: 'mentions'
        }
    }
});
