/*global cytoscape, disableBtn, displayNotification,
$spinner, Status, $topadmPlaceHolder, topadmTemplate */
$(function() {
    'use strict';
    var initCy = function initCy(elements, layout) {
        var st = cytoscape.stylesheet()
            .selector('node')
                .style({
                    content: 'data(ip)',
                    'background-color': 'data(color)',
                    shape: 'data(shape)',
                    //'background-blacken': 'data(blacken) ? data(blacken) : 1'
                    'background-blacken': function(ele) {
                        if ('blacken' in ele.data()) {
                            return ele.data('blacken');
                        }
                        return 0;
                    },
                    'text-wrap': 'wrap',
                    'text-background-color': '#fff'
                })
            .selector('edge')
                .style({
                    width: 2,
                    content: function(ele) {
                        if ('errors' in ele.data() && ele.data('errors') > 0) {
                            return ele.data('errors');
                        }
                        return '';
                    },
                    'line-color': 'data(color)',
                    'edge-text-rotation': 'autorotate',
                    'control-point-step-size': 150,
                    'text-background-color': '#fff'
                });

        var el = document.getElementById('topology-content');
        el.style.height = '700px';

        var cy = window.cy = cytoscape({
            container: el,
            layout: layout,
            style: st,
            elements: elements,
            wheelSensitivity: 0.1,
            motionBlur: true
        });
        // переход во вкладку свитчи по клику на ноду
        cy.on('tap', 'node', function(event) {
            var node = event.cyTarget;
            var ip = node.data('ip');
            // переходим во вкладку свитчи только если айпи начинается на "10.""
            if (ip.lastIndexOf('10.', 0) !== 0) {
                return;
            }
            $('#inp-sw').val(node.data('ip'));
            $('#menuTabs a[href="#tab-switch"]').tab('show');
            $('#switch-button').trigger('click');
            history.pushState(null, null, '#tab-switch');
        });
    };

    // смена отображения айпи - сиснейм - улица
    $('#topology-cycle-view').on('click', function() {
        var $this = $(this);
        // выключим кнопку
        $this.prop('disabled', true);
        // массив видов между которыми можно переключаться 
        var cycle = ['ip', 'sysname', 'location'];
        // следующий индекс
        var nextIdx = (cycle.indexOf($this.data('visual')) + 1) % cycle.length;
        // какой вид будем отображать
        var visual = cycle[nextIdx];
        // заменим отображение на всех нодах
        window.cy.style().selector('node').css({
            'content': 'data(' + visual + ')'
        }).update();
        // сохраним вид в объекте и включим кнопку обратно
        $this.data('visual', visual)
            .prop('disabled', false);
    });

    // нажатие enter в форме поиска
    $('#inp-topology').keypress(function(e) {
        // 13 - enter
        if (e.which === 13) {
            var $btn = $('#topology-button');
            e.preventDefault();
            if (!$btn.prop('disabled')) {
                $btn.trigger('click');
            }
        }
    });

    // клик по кнопке поиска
    $('#topology-button').click(function(e) {
        e.preventDefault();
        var $btn = $(this);

        disableBtn($btn);

        var inp = $.trim($('#inp-topology').val());
        if (!inp) {
            displayNotification('Для поиска укажите IP или Sysname свитча!', 'error');
            return;
        }
        $spinner.removeClass('hide');
        // сбросим отображение контента нод и покажем кнопку
        $('#topology-cycle-view').data('visual', 'ip')
            .removeClass('hide')
            .prop('disabled', false);
        $('#topology-content').empty()
            .height(0);
        var xhr = $.ajax({
            type: 'POST',
            url: '/topology',
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
                    displayNotification('Ошибка при получении топологии!', 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Нет доступа просматривать топологию!', 'error');
                    break;
                case Status.EMPTY:
                    displayNotification('Свитч не найден в базе!', 'info');
                    break;
                case Status.SUCCESS:
                    //console.log(data.elements);
                    //console.log(data.layout);
                    initCy(data.elements, data.layout);
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при получении топологии!', 'error');
            $spinner.addClass('hide');
        });
    });
});
