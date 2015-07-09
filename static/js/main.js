/*global Handlebars, displayNotification, Status */

// templates
Handlebars.registerHelper('ifObject', function(item, options) {
    'use strict';
    if (typeof item === 'object') {
        return options.fn(this);
    } else {
        return options.inverse(this);
    }
});

var template = '';
if (document.getElementById('bras-template') !== null) {
    template = $('#bras-template').html();
    var brasTemplate = Handlebars.compile(template);
}
if (document.getElementById('dhcp-template') !== null) {
    template = $('#dhcp-template').html();
    var dhcpTemplate = Handlebars.compile(template);
}
if (document.getElementById('switch-template') !== null) {
    template = $('#switch-template').html();
    var switchTemplate = Handlebars.compile(template);
}
if (document.getElementById('admin-edit-template') !== null) {
    template = $('#admin-edit-template').html();
    var adminEditTemplate = Handlebars.compile(template);
}
if (document.getElementById('admin-copy-template') !== null) {
    template = $('#admin-copy-template').html();
    var adminCopyTemplate = Handlebars.compile(template);
}
if (document.getElementById('cabdiag-template') !== null) {
    template = $('#cabdiag-template').html();
    var cabdiagTemplate = Handlebars.compile(template);
}
if (document.getElementById('switch-port-template') !== null) {
    template = $('#switch-port-template').html();
    var switchPortTemplate = Handlebars.compile(template);
}
if (document.getElementById('aggregator-template') !== null) {
    template = $('#aggregator-template').html();
    var aggregatorTemplate = Handlebars.compile(template);
}
if (document.getElementById('paginator-template') !== null) {
    template = $('#paginator-template').html();
    var paginatorTemplate = Handlebars.compile(template);
}
if (document.getElementById('porterr-template') !== null) {
    template = $('#porterr-template').html();
    var porterrTemplate = Handlebars.compile(template);
}
if (document.getElementById('macs-template') !== null) {
    template = $('#macs-template').html();
    var macsTemplate = Handlebars.compile(template);
}
if (document.getElementById('topadm-template') !== null) {
    template = $('#topadm-template').html();
    var topadmTemplate = Handlebars.compile(template);
}

var $brasPlaceHolder = $('#session-content');
var $dhcpPlaceHolder = $('#dhcp-content');
var $switchPlaceHolder = $('#switch-content');
var $adminEditPlaceHolder = $('#admin-edit-content');
var $adminCopyPlaceHolder = $('#admin-copy-content');
var $switchPortPlaceHolder = $('#dhcp_swp');
var $aggregatorPlaceHolder = $('#dhcp_gw');
var $paginatorPlaceHolder = $('#paginator-content');
var $porterrPlaceHolder = $('#porterr-content');
var $macsPlaceHolder = $('#macs-content');
var $topadmPlaceHolder = $('#topadm-content');

// vars
var brasses         = [];
var $menuResult     = $('.menu-result');
var $spinner        = $('#spinner');
var timeStarted     = 0;
var maxTimeInSwitch = 60;
var $datacells      = $('.datacell');
var $clientsTable   = $('#clients-result');
var $subMenus       = $('#clients-submenu');
var urls            = ['sbms', 'orange'];

// релоадить страницу каждые 2 часа
var refreshTime = 2 * 3600000;
var timeout = setTimeout(function() {
    'use strict';
    window.location.reload(true);
}, refreshTime);

// global binds
// сбрасываем обновление страницы при неактивности
$(document).click(function() {
    'use strict';
    resetTimeout();
});
$(document).on('click', '.reload-session', function onReloadSession(e) {
    'use strict';
    e.preventDefault();
    var source = $.trim($(this).parent().text());
    fetchSession([source]);
});
$(document).on('click', '.delete-session', function onDeleteSession(e) {
    'use strict';
    e.preventDefault();
    var source = $.trim($(this).parent().text());
    $menuResult.empty();
    deleteSession(source);
});

$(document).on('click', '#cidr', function onCidrClick(e) {
    'use strict';
    e.preventDefault();
    var $cidr = $(this);
    var tmp   = $cidr.data('value');
    var text  = $cidr.text();
    $cidr.text(tmp)
        .data('value', text);
});
$(document).on('click', '#swIp', function onSwIpToMacClick(event) {
    'use strict';
    event.preventDefault();
    var $this = $(this);
    //console.log(event);
    if (!event.ctrlKey && !event.altKey) {
        //console.log($(this).attr('data'));
        $('#inp-sw').val($this.data('ip'));
        $('#menuTabs a[href="#tab-switch"]').tab('show');
        $('#switch-button').trigger('click');
        history.pushState(null, null, $this.attr('href'));
        return;
    }
});
$(document).on('click', '.dhcp-ip', function(e) {
    'use strict';
    e.preventDefault();
    var $this = $(this);
    $('#dhcp-ip').val($this.text());
    $('#menuTabs a[href="#tab-dhcp"]').tab('show');
    history.pushState(null, null, $this.attr('href'));
});
$(document).on('click', '.dhcp-mac', function(e) {
    'use strict';
    e.preventDefault();
    var $this = $(this);
    $('#dhcp-mac').val($this.text());
    $('#menuTabs a[href="#tab-dhcp"]').tab('show');
    history.pushState(null, null, $this.attr('href'));
});
$(document).on('click', '.dhcp-host', function(e) {
    'use strict';
    e.preventDefault();
    var $this = $(this);
    $('#dhcp-host').val($this.text());
    $('#menuTabs a[href="#tab-dhcp"]').tab('show');
    history.pushState(null, null, $this.attr('href'));
});
$(document).on('click', '.dhcp-switch', function(e) {
    'use strict';
    e.preventDefault();
    var $this = $(this);
    $('#dhcp-switch').val($this.text());
    $('#menuTabs a[href="#tab-dhcp"]').tab('show');
    history.pushState(null, null, $this.attr('href'));
});

$(document).on('click', '#modalAcceptRelease', releasePortFromSwitchTab);

$(document).on('click', '#modalAcceptReserve', reservePortFromSwitchTab);

$(document).on('click', '#modalDeclineRelease', function onDeclineRelease() {
    'use strict';
    $('#switch-content').find('.ready-for-release').removeClass('ready-for-release');
});

$(document).on('click', '#modalDeclineReserve', function onDeclineReserve() {
    'use strict';
    $('#switch-content').find('.ready-for-reserve').removeClass('ready-for-reserve');
});

$(document).on('click', '.release-port', function onReleasePortClick(e) {
    'use strict';
    e.preventDefault();
    var t = parseInt(new Date().getTime() / 1000);
    if ((t - timeStarted) > maxTimeInSwitch) {
        displayNotification('Отвязывать можно только в первые ' +
            maxTimeInSwitch + ' секунд после запроса абонентов на свитче!', 'info');
        return;
    }
    var $this = $(this);
    var $tr = $this.closest('tr');
    $tr.addClass('ready-for-release');

    var $warn = $('#modalReleasePortWarning');
    if (!$tr.find('.days-blocked').length) {
        $warn.text('Вы уверены, что хотите отвязать активного абонента?');
    } else {
        var n = parseInt($tr.find('.days-blocked').text());
        var days = n%10==1 && n%100!=11 ? 'день' : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 'дня' : 'дней';
        $warn.text('Абонент неактивен ' + n + ' ' + days + ', продолжить?');
    }
    $('#modalReleasePortContainer').modal({
        show: true,
        backdrop: 'static'
    });
});
$(document).on('click', '.reserve-port', function onReservePortClick(e) {
    'use strict';
    e.preventDefault();
    var t = parseInt(new Date().getTime() / 1000);
    if ((t - timeStarted) > maxTimeInSwitch) {
        displayNotification('Привязывать можно только в первые ' +
            maxTimeInSwitch + ' секунд после запроса абонентов на свитче!', 'info');
        return;
    }
    var $this = $(this);
    var $tr = $this.closest('tr');
    $tr.addClass('ready-for-reserve');

    $('#modalReservePortBill').val('');
    $('#modalReservePortContainer').modal({
        show: true,
        backdrop: 'static'
    });
});
$(document).on('click', '.billid', function onBillIdClick(e) {
    'use strict';
    e.preventDefault();
    var $this = $(this);
    $('#inp-ip').val($this.text());
    $('#menuTabs a[href="#tab-ipaddr"]').tab('show');
    $('#ipaddr-button').trigger('click');
    history.pushState(null, null, $this.attr('href'));
});
$(document).on('click', '#modalShutdownPort', function onAcceptDownPort() {
    'use strict';
    changePortStatus();
});
$(document).on('click', '#swPortStatus', function onSwPortStatusClick() {
    'use strict';
    var $this = $(this);
    var trigger = $this.data('value');
    if (parseInt(trigger) === 1 && $this.hasClass('pointer')) {
        $('#modalOffPort').modal({
            show: true,
            backdrop: 'static'
        });
        return;
    }
    // up port
    changePortStatus();
});

$(document).on('click', '#natfin', function onNatFinClick(e) {
    'use strict';
    e.preventDefault();
});
(function() {
    'use strict';
    var moved = 0;
    $(document).on('mouseup', '.cabdiag-content', function onCabDiagOnSwitch(e) {
        e.preventDefault();
        if (moved > 5) {
            return;
        }
        var $this = $(this);
        var $cbpr = $('#switch-cabdiag-all');
        var port = $this.closest('tr').find('.port-number').text();
        if (parseInt($this.val()) === 0 || !port) {
            return;
        }
        if ($cbpr.data('busy') === 1) {
            displayNotification('Дождитесь выполнения предыдущей операции!', 'info');
            return;
        }
        $this.val(0);
        $cbpr.data('busy', 1);
        $this.html('<i class="fa fa-refresh fa-spin"></i>');
        $.post('/cabdiag/port', {
            ip    : $switchPlaceHolder.data('ip'),
            port  : port
        }, function(data) {
            $this.html('');
            if (!data) {
                return;
            }
            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при попытке сделать каб. диаг!';
                    displayNotification(msg, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Вы не можете делать каб. диаг!', 'error');
                    break;
                case Status.CBNOINFO:
                    displayNotification('Коммутатор не смог корректно измерить длину кабеля!', 'info', 10);
                    break;
                case Status.SUCCESS:
                    $this.html(cabdiagTemplate(data.data));
                    break;
                case Status.CANTESTABLISH:
                    displayNotification('Не смог установить соединение со свитчем!', 'error');
                    break;
                case Status.NOTFOUND:
                    displayNotification('Не смог определить тип свитча!', 'error');
                    break;
            }
            $this.val(1);
            $cbpr.data('busy', 0);
        }, 'json')
        .fail(function() {
            displayNotification('Критическая ошибка при попытке сделать каб. диаг!', 'error');
            $this.html('').val(1);
            $cbpr.data('busy', 0);
        });
    });
    $(document).on('mousedown', '.cabdiag-content', function() {
        moved = 0;
    });

    $(document).on('mousemove', '.cabdiag-content', function() {
        moved++;
    });
})();
(function() {
    'use strict';
    var moved = 0;
    $('#cab-diag').on('mouseup', function onCabDiagOnClient(e) {
        e.preventDefault();
        if (moved > 5) {
            return;
        }
        var $this = $(this);
        var $switchPort = $('#swPort');
        if (parseInt($this.val()) === 0 || !$switchPort.text()) {
            return;
        }
        $this.val(0);
        $this.html('<i class="fa fa-refresh fa-spin"></i>');
        $.post('/cabdiag/port', {
            ip        : $('#swIp').data('ip'),
            port      : $switchPort.text()
        }, function(data) {
            $this.html('');
            if (!data) {
                return;
            }
            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при попытке сделать каб. диаг!';
                    displayNotification(msg, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Вы не можете делать каб. диаг!', 'error');
                    break;
                case Status.CBNOINFO:
                    displayNotification('Коммутатор не смог корректно измерить длину кабеля!', 'info', 10);
                    break;
                case Status.SUCCESS:
                    $this.html(cabdiagTemplate(data.data));
                    break;
                case Status.CANTESTABLISH:
                    displayNotification('Не смог установить соединение со свитчем!', 'error');
                    break;
                case Status.NOTFOUND:
                    displayNotification('Не смог определить тип свитча!', 'error');
                    break;
            }
            $this.val(1);
            moved = 0;
        }, 'json')
        .fail(function() {
            displayNotification('Критическая ошибка при попытке сделать каб. диаг!', 'error');
            $this.html('').val(1);
        });
    });

    $('#cab-diag').on('mousedown', function() {
        moved = 0;
    });

    $('#cab-diag').on('mousemove', function() {
        moved++;
    });
})();

$(document).on('click', '#switch-ports-status', function(e) {
    'use strict';
    e.preventDefault();
    var ip = $switchPlaceHolder.data('ip');
    $('.port-number').removeClass('text-success text-danger');
    $spinner.removeClass('hide');
    var xhr = $.ajax({
        type: 'POST',
        url: '/switch/ports/all',
        data: {
            ip : ip
        },
        dataType: 'json'
    })
    .done(function(data) {
        $spinner.addClass('hide');
        if (!data) {
            displayNotification('Сервер не вернул никаких данных!', 'error');
            return;
        }
        switch (data.status) {
            case Status.ERROR:
                displayNotification('Предположительно свитч лежит!', 'error');
                break;
            case Status.SUCCESS:
                $.each($('.port-number'), function(idx) {
                    var cl = parseInt(data.data[idx]) === 1 ? 'text-success' : 'text-danger';
                    $(this).addClass(cl);
                });
                break;
        }
    })
    .fail(function() {
        $spinner.addClass('hide');
        displayNotification('Критическая ошибка при попытке получить статус портов!', 'error');
    });
});

$(document).on('click', '#switch-cabdiag-all', function(e) {
    'use strict';
    e.preventDefault();
    $spinner.removeClass('hide');
    var xhr = $.ajax({
        type: 'POST',
        url: '/cabdiag/ports',
        data: {
            ip : $switchPlaceHolder.data('ip')
        },
        dataType: 'json'
    })
    .done(function(data) {
        $spinner.addClass('hide');
        if (!data) {
            displayNotification('Сервер не вернул никаких данных!', 'error');
            return;
        }
        var $cb = $('#switch-content .cabdiag-content');
        switch (data.status) {
            case Status.SUCCESS:
                $.each(data.data, function(key, v) {
                    switch (v.status) {
                        case Status.SUCCESS:
                            $cb.filter('[data-portnum=' + key + ']').html(cabdiagTemplate(v.data));
                            break;
                        case Status.CBNOINFO:
                            $cb.filter('[data-portnum=' + key + ']').html('');
                            displayNotification('Кабель в порту ' + key +
                                ' воткнут в активное оборудование, замер не произвести!', 'info');
                            break;
                        case Status.ERROR:
                            $cb.filter('[data-portnum=' + key + ']').html('');
                            displayNotification('Ошибка при каб. диаге порта ' + key + '!', 'error');
                            break;
                    }
                });
                break;
            case Status.CANTESTABLISH:
                displayNotification('Не смог установить соединение со свитчем!', 'error');
                break;
            case Status.ERROR:
                var msg = data.msg ? data.msg : 'Ошибка при попытке выполнить масс каб. диаг!';
                displayNotification(msg, 'error');
                break;
            case Status.NOAUTH:
                displayNotification('Вы не можете делать каб. диаг!', 'error');
                break;
        }
    })
    .fail(function() {
        $spinner.addClass('hide');
        displayNotification('Критическая ошибка при попытке выполнить масс каб. диаг!', 'error');
    });
});

$(document).on('click', '#porterr', function(e) {
    'use strict';
    e.preventDefault();
    showPortErrors();
});

$(document).on('click', '#abons-paginator a', function(e) {
    'use strict';
    e.preventDefault();
    if ($(this).parent('li').hasClass('disabled')) {
        return;
    }
    $('#inp-ip').val($(this).data('ip'));
    $('#ipaddr-button').trigger('click');
});

$('#inp-sw').keypress(function(e) {
    'use strict';
    // 13 - enter
    if (e.which === 13) {
        var $btn = $('#switch-button');
        e.preventDefault();
        if (!$btn.prop('disabled')) {
            $btn.trigger('click');
        }
    }
});

$('#switch-button').click(function(e) {
    'use strict';
    e.preventDefault();
    disableBtn($(this));
    $switchPlaceHolder.data('ip', '');
    var inp = $.trim($('#inp-sw').val());
    if (!inp) {
        displayNotification('Для поиска укажите IP или Sysname свитча!', 'error');
        return;
    }
    $spinner.removeClass('hide');
    $switchPlaceHolder.empty();
    var xhr = $.ajax({
        type: 'POST',
        url: '/orangesw',
        data: {
            inp : inp
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
                displayNotification('Ошибка при получении клиентов со свитча!', 'error');
                break;
            case Status.NOAUTH:
                displayNotification('Нет доступа просматривать клиентов на свитче!', 'error');
                break;
            case Status.EMPTY:
                displayNotification('Нет информации о данном устройстве!', 'error');
                break;
            case Status.SUCCESS:
                timeStarted = parseInt(new Date().getTime() / 1000);
                $switchPlaceHolder.data('ip', data.swip);
                $switchPlaceHolder.append(switchTemplate(data));
                break;
        }
    })
    .fail(function() {
        displayNotification('Критическая ошибка при выполнении запроса клиентов на свитче!', 'error');
        $spinner.addClass('hide');
    });
});

$('#inp-ip').keypress(function(e) {
    'use strict';
    // 13 - enter
    if (e.which === 13) {
        var $btn = $('#ipaddr-button');
        e.preventDefault();
        if (!$btn.prop('disabled')) {
            $btn.trigger('click');
        }
    }
});

$('#ipaddr-button').click(function(e) {
    'use strict';
    e.preventDefault();
    var $btn = $(this);
    brasses = [];
    $menuResult.empty();
    $paginatorPlaceHolder.empty();

    $clientsTable.addClass('hide');
    $subMenus.addClass('hide');

    disableBtn($btn);

    $datacells.empty();

    var inp = $.trim($('#inp-ip').val());
    if (!inp) {
        displayNotification('Для поиска укажите IP или номер договора клиента!', 'error');
        return;
    }
    $spinner.removeClass('hide');
    $.each(urls, function(i, url) {
        var xhr = $.ajax({
            type: 'POST',
            url: '/' + url,
            data: {
                inp : inp
            },
            dataType: 'json',
            timeout: function() {
                displayNotification('Превышено время ожидания от базы ' + url, 'error');
            }
        })
        .done(function(data) {
            $spinner.addClass('hide');
            if (!data) {
                displayNotification('Сервер не вернул данных ' + url, 'error');
                return;
            }
            switch (data.status) {
                case Status.SUCCESS:
                    // TODO new structure class <> js | what? :D
                    processData(data.data);
                    break;
                case Status.EMPTY:
                    displayNotification('Нет информации в базе ' + data.db, 'info');
                    break;
                case Status.ERROR:
                    displayNotification('Ошибка при поиске в базе ' + data.db, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Нет прав просматривать этот регион в базе ' + data.db, 'error');
                    break;
            }
        })
        .fail(function() {
            $spinner.addClass('hide');
            displayNotification('Критическая ошибка при поиске в базе ' + url, 'error');
        });
    });
});

$('#sub-menu-tabs a').click(function onMenuTabClick(e) {
    'use strict';
    e.preventDefault();

    var $this = $(this);
    if (!$this.hasClass('ready')) {
        return;
    }
    // делаем линки неактивными на Х секунд
    var sec = 2;
    var $suba = $('#sub-menu-tabs a');
    $suba.removeClass('ready');
    setTimeout(function() {
        $suba.addClass('ready');
        $this.parent('li').removeClass('active');
    }, sec * 1000);

    switch (this.id) {
        case 'dhcp-link':
            fetchDhcpLogs();
            break;
        case 'session-link':
            fetchSession();
            break;
        case 'macs-link':
            fetchMacs();
            break;
        case 'traffic-link':
            fetchTraffic();
            break;
        default:
            break;
    }
});
