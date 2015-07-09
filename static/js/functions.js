// functions
/*global Status, $spinner, timeout, refreshTime, messenger,
$porterrPlaceHolder, porterrTemplate,
$switchPortPlaceHolder, switchPortTemplate,
$switchPlaceHolder, $menuResult,
$dhcpPlaceHolder, dhcpTemplate,
brasses, $brasPlaceHolder, brasTemplate,
Backbone, Backgrid, $subMenus,
$paginatorPlaceHolder, paginatorTemplate, $clientsTable,
$macsPlaceHolder, macsTemplate,
trafficOptions, Highcharts, displayNotification, $aggregatorPlaceHolder */

var resetTimeout = function resetTimeout() {
    'use strict';
    clearTimeout(timeout);
    timeout = setTimeout(function() {
        window.location.reload(true);
    }, refreshTime);
};

// TODO ajax + error handling + function
var showPortErrors = function showPortErrors() {
    'use strict';
    var $porterr = $('#porterr');
    var errors = parseInt($porterr.text()) || 0;
    $porterrPlaceHolder.html('<i class="fa fa-refresh fa-spin"></i>');
    var xhr = $.ajax({
        type: 'POST',
        url: '/porterrors',
        data: {
            ip      : $('#swIp').data('ip'),
            port    : $('#swPort').text(),
            curr    : errors
        },
        dataType: 'json'
    })
    .done(function(data) {
        $porterrPlaceHolder.html('');
        if (!data) {
            displayNotification('Сервер не вернул никаких данных!', 'error');
            return;
        }
        switch (data.status) {
            case Status.ERROR:
                displayNotification('Не смог получить количество ошибок со свитча!', 'error');
                break;
            case Status.NOTFOUND:
                displayNotification('Не смог определить тип свитча!', 'error');
                break;
            case Status.SUCCESS:
                $porterrPlaceHolder.html(porterrTemplate(data));
                break;
        }
    })
    .fail(function() {
        $porterrPlaceHolder.html('');
        displayNotification('Критическая ошибка при попытке получить ошибки со свитча!', 'error');
    });
};

var getSwitchInfo = function getSwitchInfo(ip, port) {
    'use strict';
    var $swIp       = $('#swIp');
    var $swPort     = $('#swPort');
    if (!ip) {
        ip = $swIp.data('ip');
    }
    if (!port) {
        port = $swPort.text();
    }
    $.post('/switch/ports', {
        ip      : ip,
        port    : port
    }, function(data) {
        if (!data) {
            return;
        }
        //console.log(JSON.stringify(data));
        $switchPortPlaceHolder.html(switchPortTemplate(data));

        if (data.isup === 1) {
            // TODO норм кнопку
            $('#cab-diag').html('<a href="#">Показать</a>');
            $porterrPlaceHolder.html('<a href="#" id="porterr">Показать</a>');
        }
    }, 'json');
};

var getAggrStatus = function getAggrStatus(ip) {
    'use strict';
    var xhr = $.ajax({
        type: 'POST',
        url: '/switch/status',
        data: {
            ip : ip
        },
        dataType: 'json'
    })
    .done(function(data) {
        //console.log(JSON.stringify(data));
        if (!data) {
            return;
        }
        switch (data.status) {
            case Status.ERROR:
                displayNotification('Не смог получить статус агрегатора!', 'error');
                break;
            case Status.SUCCESS:
                var ip = $.trim($('#dhcp_gw').text());
                $aggregatorPlaceHolder.html(aggregatorTemplate({
                    'status': data.swstatus,
                    'ip'    : ip
                }));
                break;
        }
    })
    .fail(function() {
        displayNotification('Критическая ошибка при попытке получить статус агрегатора!', 'error');
    });
};

var changePortStatus = function changePortStatus() {
    'use strict';
    var $swPortStatus = $('#swPortStatus');
    var ip = $('#swIp').data('ip');
    var port = $('#swPort').text();
    var trigger = $swPortStatus.data('value');
    $swPortStatus.removeClass('fa-arrow-up fa-arrow-down pointer')
        .addClass('fa-refresh fa-spin');
    $.post('/changeportstatus', {
        ip      : ip,
        port    : port,
        data    : trigger
    }, function(data) {
        if (!data) {
            displayNotification('Сервер не вернул никаких данных!', 'error');
            $swPortStatus.removeClass('fa-spin');
            return;
        }
        switch(data.status) {
            case Status.SUCCESS:
                getSwitchInfo(ip, port);
                break;
            case Status.NOAUTH:
                displayNotification('У Вас нет прав изменять статус порта!', 'error');
                $swPortStatus.removeClass('pointer');
                break;
            case Status.ERROR:
                displayNotification('Ошибка при попытке сменить статус порта!', 'error');
                break;
        }
    }, 'json');
};
var releasePortFromSwitchTab = function releasePortFromSwitchTab() {
    'use strict';
    var $tr = $('#switch-content').find('.ready-for-release');
    $tr.removeClass('ready-for-release');
    var bill = $tr.find('.billid').text();
    var daysBlocked = $tr.find('.days-blocked');
    var days = daysBlocked.length ? daysBlocked.text() : 0;
    var portid = $tr.find('.port-number').data('id');
    var swport = $tr.find('.port-number').text();
    var swip = $switchPlaceHolder.data('ip');
    $spinner.removeClass('hide');
    var xhr = $.ajax({
        type: 'POST',
        url: '/port/release',
        data: {
            billid : bill,
            portid : portid,
            days   : days,
            swip   : swip,
            swport : swport
        },
        dataType: 'json'
    })
    .done(function(data) {
        $spinner.addClass('hide');
        if (!data) {
            displayNotification('Сервер не вернул данных!', 'error');
            return;
        }

        switch (data.status) {
            case Status.ERROR:
                displayNotification('Какая-то ошибка!', 'error');
                break;
            case Status.NOAUTH:
                displayNotification('У Вас нет прав отвязать этот порт!', 'error');
                break;
            case Status.EMPTY:
                // TODO отделять есть ли такой свитч реально
                displayNotification('Порт не зарезервирован!', 'info');
                break;
            case Status.SUCCESS:
                //$row.find('td').not('.port-number,.cab-diag').empty();
                displayNotification('Порт освобожден!', 'success');
                $('#inp-sw').val($('#switch-content').data('ip'));
                $('#switch-button').trigger('click');
                break;
        }
    })
    .fail(function() {
        $spinner.addClass('hide');
        displayNotification('Критическая ошибка при отвязке!', 'error');
    });
};
var reservePortFromSwitchTab = function reservePortFromSwitchTab() {
    'use strict';
    var $tr = $('#switch-content').find('.ready-for-reserve');
    $tr.removeClass('ready-for-reserve');
    var bill = $('#modalReservePortBill').val();
    if (!bill) {
        return;
    }
    var portid = $tr.find('.port-number').data('id');
    if (!portid) {
        return;
    }
    var swport = $tr.find('.port-number').text();
    var swip = $switchPlaceHolder.data('ip');
    $spinner.removeClass('hide');
    var xhr = $.ajax({
        type: 'POST',
        url: '/port/reserve',
        data: {
            billid : bill,
            portid : portid,
            swip   : swip,
            swport : swport
        },
        dataType: 'json'
    })
    .done(function(data) {
        $spinner.addClass('hide');
        if (!data) {
            displayNotification('Сервер не вернул данных!', 'error');
            return;
        }

        switch (data.status) {
            case Status.ERROR:
                var msg = data.msg ? data.msg : 'Какая-то ошибка!';
                displayNotification(msg, 'error');
                break;
            case Status.NOAUTH:
                displayNotification('У Вас нет прав привязать этот порт!', 'error');
                break;
            case Status.SUCCESS:
                displayNotification('Порт привязан!', 'success');
                $('#inp-sw').val($('#switch-content').data('ip'));
                $('#switch-button').trigger('click');
                break;
        }
    })
    .fail(function() {
        $spinner.addClass('hide');
        displayNotification('Критическая ошибка при привязке!', 'error');
    });
};
var fetchMacs = function fetchMacs() {
    'use strict';
    var ip = $('#swIp').data('ip');
    var port = $('#swPort').data('value');

    if (ip === undefined || port === undefined) {
        displayNotification('Не нашел IP свитча или порт!', 'error');
        return;
    }

    $spinner.removeClass('hide');
    $menuResult.empty();

    var xhr = $.ajax({
        type: 'POST',
        url: '/macs',
        data: {
            ip      : ip,
            port    : port
        },
        dataType: 'json'
    })
    .done(function(data) {
        $spinner.addClass('hide');
        if (!data) {
            return;
        }
        switch (data.status) {
            case Status.ERROR:
                var msg = data.msg ? data.msg : 'Ошибка при выполнении запроса!';
                displayNotification(msg, 'error');
                break;
            case Status.EMPTY:
                displayNotification('Ничего не найдено!', 'info');
                break;
            case Status.NOAUTH:
                displayNotification('Вы не можете просматривать логи!', 'error');
                break;
            case Status.SUCCESS:
                $macsPlaceHolder.html(macsTemplate({object: data.data}));
                break;
        }
    })
    .fail(function() {
        displayNotification('Критическая ошибка при просмотре логов!', 'error');
        $spinner.addClass('hide');
    });
};
var fetchTraffic = function fetchTraffic() {
    'use strict';
    var ip = $('#int-ip-addr').text();
    var bill = $('#billid').text();

    if (bill === undefined || bill === '') {
        displayNotification('Не смог найти договор!', 'error');
        return;
    }

    if (ip === undefined || ip === 'None') {
        displayNotification('У клиента нет IP!', 'error');
        return;
    }

    $spinner.removeClass('hide');
    $menuResult.empty();

    var xhr = $.ajax({
        type: 'POST',
        url: '/traffic',
        data: {
            ip      : ip,
            bill    : bill
        },
        dataType: 'json'
    })
    .done(function(data) {
        $spinner.addClass('hide');
        if (!data) {
            return;
        }
        switch (data.status) {
            case Status.ERROR:
                var msg = data.msg ? data.msg : 'Ошибка при выполнении запроса!';
                displayNotification(msg, 'error');
                break;
            case Status.EMPTY:
                displayNotification('Ничего не найдено!', 'info');
                break;
            case Status.NOAUTH:
                displayNotification('Вы не можете просматривать траффик!', 'error');
                break;
            case Status.SUCCESS:
                //console.log(data.data);
                //console.log(data.timeline);
                trafficOptions.series[0].data = data.data;
                trafficOptions.series[1].data = data.timeline;
                trafficOptions.yAxis.type = 'logarithmic';
                new Highcharts.Chart(trafficOptions);
                break;
        }
    })
    .fail(function() {
        displayNotification('Критическая ошибка при просмотре логов!', 'error');
        $spinner.addClass('hide');
    });
};
var fetchDhcpLogs = function fetchDhcpLogs() {
    'use strict';
    var ip = $('#int-ip-addr').text();

    if (ip === undefined || ip === 'None' || ip === '') {
        ip = $('#orange-ip-addr').text();

        if (ip === undefined || ip === 'None' || ip === '') {
            displayNotification('У клиента нет IP!', 'error');
            return;
        }
    }

    $spinner.removeClass('hide');
    $menuResult.empty();

    var xhr = $.ajax({
        type: 'POST',
        url: '/dhcp/short',
        data: {
            ip : ip
        },
        dataType: 'json'
    })
    .done(function(data) {
        $spinner.addClass('hide');
        if (!data) {
            return;
        }
        switch (data.status) {
            case Status.ERROR:
                displayNotification('Ошибка при выполнении запроса!', 'error');
                break;
            case Status.EMPTY:
                displayNotification('Ничего не найдено!', 'info');
                break;
            case Status.NOAUTH:
                displayNotification('Вы не можете просматривать логи!', 'error');
                break;
            case Status.SUCCESS:
                $dhcpPlaceHolder.append(dhcpTemplate(data));
                break;
        }
    })
    .fail(function() {
        displayNotification('Критическая ошибка при просмотре логов!', 'error');
        $spinner.addClass('hide');
    });
};
var getListOfBrasses = function getListOfBrasses() {
    'use strict';
    var bill = $('#billid').text();
    if (!bill) {
        displayNotification('Не могу извлечь данные для определения региона!', 'error');
        return;
    }
    $.ajax({
        type: 'GET',
        url: '/bras',
        data: {
            bill : bill
        },
        dataType: 'json'
    })
    .done(function(data) {
        if (!data) {
            displayNotification('Сервер не вернул никаких данных при попытке получения списка брасов!', 'error');
            return;
        }
        switch (data.status) {
            case Status.EMPTY:
                displayNotification('Для этого региона нет брасов!', 'error');
                break;
            case Status.ERROR:
                displayNotification('Ошибка при получении списка брасов!', 'error');
                break;
            case Status.TIMEOUT:
                displayNotification('Превышено время ожидания при попытке получить список брасов!', 'error');
                break;
            case Status.NOAUTH:
                displayNotification('Нет прав просмотривать сессии!', 'error');
                break;
            case Status.SUCCESS:
                //displayNotification('Список брасов успешно получен!', 'success');
                brasses = data.data;
                fetchSession();
                break;
        }
    })
    .fail(function() {
        displayNotification('Критическая ошибка при получении списка брасов!', 'error');
    });
};
var fetchSession = function fetchSession(from) {
    'use strict';
    if (typeof from === 'undefined') {
        if (0 === brasses.length) {
            getListOfBrasses();
            return;
        }
        from = brasses;
    }
    if (0 === from.length) {
        return;
    }
    var ip = $('#int-ip-addr').text();

    if (ip === undefined || ip === 'None' || ip === '') {
        ip = $('#orange-ip-addr').text();

        if (ip === undefined || ip === 'None' || ip === '') {
            displayNotification('У клиента нет IP!', 'error');
            return;
        }
    }

    $menuResult.empty();
    $spinner.removeClass('hide');
    $.each(from, function(i, bras) {
        var xhr = $.ajax({
            type: 'POST',
            url: '/bras',
            data: {
                bras    : bras.toLowerCase(),
                action  : 'fetch',
                ip      : ip
            },
            dataType: 'json'
        })
        .done(function(data) {
            $spinner.addClass('hide');
            if (!data) {
                displayNotification('Сервер не вернул данных ' + bras, 'error');
                return;
            }

            switch (data.status) {
                case Status.EMPTY:
                    displayNotification('Нет сессии на ' + bras, 'info');
                    break;
                case Status.ERROR:
                    displayNotification('Ошибка на ' + bras, 'error');
                    break;
                case Status.TIMEOUT:
                    displayNotification('Превышено время ожидания от ' + bras, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Нет прав просматривать ' + bras, 'error');
                    break;
                case Status.SUCCESS:
                    $brasPlaceHolder.append(brasTemplate(data.body));
                    break;
                case Status.CANTESTABLISH:
                    displayNotification('Не смог установить соединение с ' + bras, 'error');
                    break;
            }
        })
        .fail(function() {
            $spinner.addClass('hide');
            displayNotification('Критическая ошибка на ' + bras, 'error');
        });
    });
};
var disableBtn = function disableBtn(btn, sec) {
    'use strict';
    sec = typeof sec !== 'undefined' ? sec : 2;
    if (!btn) {
        return;
    }
    btn.prop('disabled', true);

    setTimeout(function() {
        btn.prop('disabled', false);
    }, sec * 1000);
};
var deleteSession = function deleteSession(from) {
    'use strict';
    if (!from) {
        return;
    }
    var ip = $('#int-ip-addr').text();
    if (ip === undefined || ip === 'None') {
        displayNotification('У клиента нет IP!', 'error');
        return;
    }

    $spinner.removeClass('hide');
    var xhr = $.ajax({
        type: 'POST',
        url: '/bras',
        data: {
            bras    : from.toLowerCase(),
            action  : 'delete',
            ip      : ip
        },
        dataType: 'json'
    })
    .done(function(data) {
        $spinner.addClass('hide');
        if (!data) {
            displayNotification('Сервер не вернул данных ' + from, 'error');
            return;
        }
        switch (data.status) {
            case Status.EMPTY:
                displayNotification('Не было сессии на ' + from, 'info');
                break;
            case Status.ERROR:
                displayNotification('Ошибка при удалении сессии на ' + from, 'error');
                break;
            case Status.NOAUTH:
                displayNotification('Нет прав удалять сессию на ' + from, 'error');
                break;
            case Status.TIMEOUT:
                displayNotification('Превышено время ожидания на ' + from, 'error');
                break;
            case Status.SUCCESS:
                displayNotification('Сессия сброшена на ' + from, 'success');
                break;
            case Status.CANTESTABLISH:
                displayNotification('Не смог установить соединение с ' + from, 'error');
                break;
        }
    })
    .fail(function() {
        $spinner.removeClass('hide');
        displayNotification('Критическая ошибка на ' + from, 'error');
    });
};

var processData = function processData(data) {
    'use strict';
    $clientsTable.removeClass('hide');
    $.each(data, function(key, value) {
        if (key === 'sbms-abons') {
            //console.log(value);
            $paginatorPlaceHolder.html(paginatorTemplate({object : value}));
            //console.log(JSON.stringify(value));
            return true;
        }
        $('#' + key).html(value);

        if (key === 'dhcp_gw') {
            getAggrStatus(value);
            return true;
        }
        if (key === 'dhcp_swp') {
            getSwitchInfo();
            return true;
        }
        if (key === 'sbms_ip' || key === 'dhcp_ip') {
            $subMenus.removeClass('hide');
            return true;
        }
    });
};
