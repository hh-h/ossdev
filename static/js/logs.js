/*global Backgrid, Backbone, Status, displayNotification */
$(function() {
    'use strict';

    var fetchLogs = function fetchLogs(data) {
        Backgrid.InputCellEditor.prototype.attributes.class = 'form-control input-sm';

        var Territory = Backbone.Model.extend({});

        var PageableTerritories = Backbone.PageableCollection.extend({
            model: Territory,
            url: '/logs',
            state: {
                pageSize: 20
            },
            mode: 'client',
            parse: function(response) {
                switch (response.status) {
                    case Status.SUCCESS:
                        return response.data;
                    case Status.ERROR:
                        var msg = data.msg ? data.msg : 'Ошибка при поиске в логах!';
                        displayNotification(msg, 'error');
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
            name: 'user',
            label: 'USER',
            editable: false,
            cell: 'string'
        }, {
            name: 'time',
            label: 'TIME',
            editable: false,
            cell: 'string'
        }, {
            name: 'action',
            label: 'ACTION',
            editable: false,
            cell: 'string',
            sortable: false
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
            data: {data: data},
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                if (data.length > 0) {
                    $('#tableLogs').append(pageableGrid.render().$el).append(paginator.render().$el);
                }
            },
            error: function() {
                displayNotification('Критическая ошибка при поиске в логах!', 'error');
            }
        });
    };

    $('#logs-datestart,#logs-dateend').datetimepicker({
        sideBySide: true,
        locale: 'ru'
    });
    $('#logs-datestart').on('dp.change', function(e) {
        $('#logs-dateend').data('DateTimePicker').minDate(e.date);
    });
    $('#logs-datestart').on('dp.hide', function(e) {
        if ($('#logs-dateend').val() === '') {
            $('#logs-dateend').data('DateTimePicker').date(e.date);
        }
    });
    $('#logs-dateend').on('dp.change', function(e) {
        $('#logs-datestart').data('DateTimePicker').maxDate(e.date);
    });

    $('#logs-search-button').click(function(e) {
        e.preventDefault();
        $('#tableLogs').empty();
        var data = {};
        var value = $.trim($('#logs-module').val());
        if (value && value !== 'all') {
            data.module = value;
        }
        value = $.trim($('#logs-user').val());
        if (value && value !== 'all') {
            data.user = value;
        }
        value = $.trim($('#logs-phrase').val());
        if (value) {
            data.phrase = value;
        }
        var dateStart = $('#logs-datestart').val();
        var dateEnd = $('#logs-dateend').val();
        if (dateStart && dateEnd) {
            data.startdate = dateStart;
            data.enddate = dateEnd;
        }
        // console.log(data);
        fetchLogs(JSON.stringify(data));
    });

    $('#logs-clear-button').click(function(e) {
        e.preventDefault();
        $('#logs-module,#logs-user').select2('val', 'all');
        $('#logs-phrase,#logs-datestart,#logs-dateend').val('');

    });
});
