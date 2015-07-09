/*global Backgrid, Backbone, Status, displayNotification */
$(function() {
    'use strict';
    // кнопка поиска
    $('#dhcp-search-button').click(function(e) {
        e.preventDefault();
        $('#dhcpLogs').empty();
        var dict = {};
        $('#dhcp-form input').each(function() {
            dict[$(this).data('name')] = $(this).val();
        });
        fetchLogs(JSON.stringify(dict));
    });
    // очистка всех полей в форме
    $('#dhcp-clear-button').click(function(e) {
        e.preventDefault();
        $(this).closest('form').find('input[type=text]').val('');
    });

    var fetchLogs = function fetchLogs(dict) {
        Backgrid.InputCellEditor.prototype.attributes.class = 'form-control input-sm';

        var Territory = Backbone.Model.extend({});

        var PageableTerritories = Backbone.PageableCollection.extend({
            model: Territory,
            url: '/dhcp/full',
            state: {
                pageSize: 20
            },
            mode: 'client',
            parse: function(response) {
                switch (response.status) {
                    case Status.SUCCESS:
                        return response.data;
                    case Status.ERROR:
                        displayNotification('Ошибка при поиске в логах!', 'error');
                        break;
                    case Status.EMPTY:
                        displayNotification('Ничего не найдено!', 'info');
                        break;
                    default:
                        displayNotification('error!', 'error');
                        break;
                }
            }
        });

        var pageableTerritories = new PageableTerritories();

        var columns = [{
            name: 'time',
            label: 'Время',
            editable: false,
            cell: 'string'
        }, {
            name: 'server',
            label: 'Сервер',
            editable: false,
            cell: 'string'
        }, {
            name: 'type',
            label: 'Тип',
            editable: false,
            cell: 'string'
        }, {
            name: 'ip',
            label: 'IP',
            editable: false,
            cell: 'string'
        }, {
            name: 'gw',
            label: 'Шлюз',
            editable: false,
            cell: 'string'
        }, {
            name: 'mac',
            label: 'MAC',
            editable: false,
            cell: 'string'
        }, {
            name: 'host',
            label: 'Хост',
            editable: false,
            cell: 'string'
        }, {
            name: 'swp',
            label: 'Свитч',
            editable: false,
            cell: 'string'
        }];

        var pageableGrid = new Backgrid.Grid({
                columns: columns,
                collection: pageableTerritories,
                className: 'table table-striped table-editable no-margin'
            });
        var paginator = new Backgrid.Extension.Paginator({
                slideScale: 0.25,
                goBackFirstOnSort: false,
                collection: pageableTerritories,
                controls: {
                    rewind: {
                        label: '<i class="fa fa-angle-double-left fa-lg"></i>',
                        title: 'First'
                    },
                    back: {
                        label: '<i class="fa fa-angle-left fa-lg"></i>',
                        title: 'Previous'
                    },
                    forward: {
                        label: '<i class="fa fa-angle-right fa-lg"></i>',
                        title: 'Next'
                    },
                    fastForward: {
                        label: '<i class="fa fa-angle-double-right fa-lg"></i>',
                        title: 'Last'
                    }
                }
            });

        pageableTerritories.fetch({
            data: {data: dict},
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                if (data.length > 0) {
                    $('#dhcpLogs').append(pageableGrid.render().$el).append(paginator.render().$el);
                }
            },
            error: function() {
                displayNotification('Критическая ошибка при поиске в логах!', 'error');
            }
        });
    };
});
