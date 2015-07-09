/*global disableBtn, displayNotification,
$spinner, Status, $topadmPlaceHolder, topadmTemplate */
$(function() {
    'use strict';
// поиск свитча
    // нажатие энтер в инпуте поиска свитча
    $('#inp-topadm').keypress(function(e) {
        // 13 - enter
        if (e.which === 13) {
            var $btn = $('#topadm-button');
            e.preventDefault();
            if (!$btn.prop('disabled')) {
                $btn.trigger('click');
            }
        }
    });
    // кнопка поиска свитча
    $('#topadm-button').click(function(e) {
        e.preventDefault();
        var $btn = $(this);

        disableBtn($btn);

        var inp = $.trim($('#inp-topadm').val());
        if (!inp) {
            displayNotification('Для поиска укажите IP или Sysname свитча!', 'error');
            return;
        }
        $spinner.removeClass('hide');
        $('#topadm-content').empty();
        var xhr = $.ajax({
            type: 'GET',
            url: '/topology/switch',
            data: {
                inp : inp
            },
            dataType: 'json'
        })
        .done(function(data) {
            $spinner.addClass('hide');
            $topadmPlaceHolder.data('id', '');
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    displayNotification('Ошибка при получении топологии!', 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Нет доступа просматривать топологию!', 'error');
                    break;
                case Status.EMPTY:
                    displayNotification('Свитч не найден в базе!', 'info');
                    break;
                case Status.SUCCESS:
                    //console.log(data.data);
                    $topadmPlaceHolder.data('ip', data.data.ip);
                    $topadmPlaceHolder.html(topadmTemplate({object: data.data}));
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при получении топологии!', 'error');
            $spinner.addClass('hide');
        });
    });

// удаление порта со свитча из базы
    // при нажатии на крестик удаления порта
    $(document).on('click', '.topadm-delete-port', function(e) {
        e.preventDefault();
        var $modal = $('#modalDelLinkContainer');
        var $tr = $(this).closest('tr');
        var port = $.trim($tr.find('.topadm-portname').text());
        $('#topadm-port-to-del').text(port);
        $modal.modal({
            show: true,
            backdrop: 'static'
        });
    });
    // при подтверждении удаления порта
    $('#modalAcceptDeleteLink').on('click', function(e) {
        e.preventDefault();
        var ip = $topadmPlaceHolder.data('ip');
        var port = $('#topadm-port-to-del').text();
        var xhr = $.ajax({
            type: 'POST',
            url: '/topology/delete',
            data: {
                ip  : ip,
                port: port
            },
            dataType: 'json'
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при удаления порта!';
                    displayNotification(msg, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('У Вас не хватает прав!', 'error');
                    break;
                case Status.SUCCESS:
                    displayNotification('Порт успешно удален!', 'success');
                    $('#inp-topadm').val(ip);
                    $('#topadm-button').trigger('click');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при попытке удаления порта!', 'error');
        });
    });

// добавление нового линка свитчу
    // нажатие на кнопку "добавить линк"
    $(document).on('click', '#topadm-add-link-button', function(e) {
        e.preventDefault();
        var $modal = $('#modalAddLinkContainer');
        // спрячем элементы, которые надо показывать по очереди
        $modal.find('#topadmLinkToSwitchContainer,#topadmAddRemotePortNameContainer,#modalAcceptAddLink')
            .addClass('hide');
        // заполним селект выбора порта на этом свитче
        var ip = $topadmPlaceHolder.data('ip');
        var xhr = $.ajax({
            type: 'POST',
            url: '/topology/ports',
            data: {
                ip  : ip
            },
            dataType: 'json'
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при получении списка портов на свитче';
                    displayNotification(msg, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('У Вас не хватает прав!', 'error');
                    break;
                case Status.SUCCESS:
                    var $el = $('#topadmAddPortName');
                    $el.select2('val', '')
                        // removing all old options
                        .find('option')
                        .remove()
                        // fill with new options from db
                        .append($('<option></option>'));
                    // заполним select портами пришедшими из запроса
                    $.each(data.data, function(key, value) {
                        $el.append($('<option></option>')
                            .attr('value', value)
                            .text(value));
                    });
                    // покажем элемент в модальном окне
                    $('#topadmAddPortNameContainer').removeClass('hide');
                    // покажем само модальное окно
                    $modal.modal({
                        show: true,
                        backdrop: 'static'
                    });
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при получении списка портов на свитче!', 'error');
        });
    });
    // выбор порта на данном свитче
    $('#topadmAddPortName').on('select2-selecting', function() {
        // сотрем старое значение и покажем форму ввода IP удаленного свитча
        $('#inp-connect').val('');
        // спрячем элементы которые еще рано видеть
        $('#topadmAddRemotePortNameContainer,#modalAcceptAddLink').addClass('hide');
        $('#topadmLinkToSwitchContainer').removeClass('hide');
    });
    // энтер в окне ввода свитча, с которым хотим соединиться
    $('#inp-connect').keypress(function(e) {
        // 13 - enter
        if (e.which === 13) {
            var $btn = $('#topadm-switch-to-button');
            e.preventDefault();
            $btn.trigger('click');
        }
    });
    // обработка свитча, с которым хотим соединиться
    $('#topadm-switch-to-button').on('click', function(e) {
        e.preventDefault();
        // спрячем элементы которые еще рано видеть
        $('#topadmAddRemotePortNameContainer,#modalAcceptAddLink').addClass('hide');
        var srcIp = $topadmPlaceHolder.data('ip');
        var dstIp = $.trim($('#inp-connect').val());
        if (dstIp === '') {
            displayNotification('Укажите IP свитча для продолжения!', 'error');
            return false;
        }
        if (srcIp === dstIp) {
            displayNotification('Делать петли плохо!', 'error');
            return false;
        }
        $('#inp-connect').data('ip', dstIp);
        // заполним селект выбора на удаленном свитче
        var xhr = $.ajax({
            type: 'POST',
            url: '/topology/ports',
            data: {
                ip  : dstIp
            },
            dataType: 'json'
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при получении списка портов на свитче';
                    displayNotification(msg, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('У Вас не хватает прав!', 'error');
                    break;
                case Status.SUCCESS:
                    var $el = $('#topadmAddRemotePortName');
                    $el.select2('val', '')
                        // removing all old options
                        .find('option')
                        .remove()
                        // fill with new options from db
                        .append($('<option></option>'));
                    // заполним select портами пришедшими из запроса
                    $.each(data.data, function(key, value) {
                        $el.append($('<option></option>')
                            .attr('value', value)
                            .text(value));
                    });
                    // покажем элемент в модальном окне
                    $('#topadmAddRemotePortNameContainer').removeClass('hide');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при получении списка портов на свитче!', 'error');
        });
    });
    // выбрали удаленный порт
    $('#topadmAddRemotePortName').on('select2-selecting', function() {
        // покажем кнопку добавления в модальном окне
        $('#modalAcceptAddLink').removeClass('hide');
    });
    // сохраняем линк в базе
    $('#modalAcceptAddLink').on('click', function(e) {
        e.preventDefault();
        var srcIp = $topadmPlaceHolder.data('ip');
        var dstIp = $('#inp-connect').data('ip');
        var localPort = $('#topadmAddPortName').val();
        var remotePort = $('#topadmAddRemotePortName').val();
        var xhr = $.ajax({
            type: 'POST',
            url: '/topology/add',
            data: {
                srcip   : srcIp,
                srcport : localPort,
                dstip   : dstIp,
                dstport : remotePort
            },
            dataType: 'json'
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    displayNotification('Ошибка при удалении линка!', 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Нет доступа просматривать топологию!', 'error');
                    break;
                case Status.SUCCESS:
                    displayNotification('Порт успешно добавлен!', 'success');
                    $('#inp-topadm').val(srcIp);
                    $('#topadm-button').trigger('click');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при получении топологии!', 'error');
        });
    });

// удаление свитча из базы
    // нажатие на кнопку удалить объект
    $(document).on('click', '#topadm-del-object-button', function(e) {
        e.preventDefault();
        var $modal = $('#modalDelObjectContainer');
        $modal.modal({
            show: true,
            backdrop: 'static'
        });
    });
    // подтверждение удаления свитча
    $('#modalAcceptDelObject').on('click', function(e) {
        e.preventDefault();
        var ip = $topadmPlaceHolder.data('ip');
        var xhr = $.ajax({
            type: 'POST',
            url: '/topology/switch/del',
            data: {
                ip     : ip
            },
            dataType: 'json'
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    displayNotification('Ошибка при удалении свитча!', 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('У Вас не хватает прав!', 'error');
                    break;
                case Status.SUCCESS:
                    displayNotification('Свитч удален!', 'success');
                    $('#inp-topadm').val(ip);
                    $('#topadm-button').trigger('click');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при удалении свитча!', 'error');
        });
    });
});
