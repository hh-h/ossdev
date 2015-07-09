/*global displayNotification, Status */
$(function() {
    'use strict';
    $('#login-button').on('click', function(e) {
        e.preventDefault();
        var user = $('#username').val();
        var pwd = $('#password').val();
        if (!user || !pwd) {
            displayNotification('Не указан логин или пароль!', 'error');
            return;
        }
        var xhr = $.ajax({
            type: 'POST',
            url: '/',
            data: $('#login-form').serialize(),
            dataType: 'json'
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул никаких данных!', 'error');
                return;
            }
            $('#password').val('');
            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Какая-то ошибка!';
                    displayNotification(msg, 'error');
                    break;
                case Status.WRONG_PW:
                    displayNotification('Неправильный логин или пароль!', 'error');
                    break;
                case Status.ERRSYMBOLS:
                    displayNotification('Недопустимые символы в логине или пароле!', 'error');
                    break;
                case Status.SUCCESS:
                    window.location = '/main';
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при попытке авторизации!', 'error');
        });
    });
});
