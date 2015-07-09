/*global Backgrid, Backbone, displayNotification, Status */
$(function() {
    'use strict';
    $('#netadm-button').on('click', function() {
        var lxType = $('#netadmType').val();
        var device = $('#netadmDevice').val();
        var dict = JSON.stringify({type: lxType, device: device});
        Backgrid.InputCellEditor.prototype.attributes.class = 'form-control';

        var Territory = Backbone.Model.extend({});

        var PageableTerritories = Backbone.PageableCollection.extend({
            model: Territory,
            url: '/netadm',
            state: {
                pageSize: 25,
                sortKey: 'bill'
            },
            mode: 'client'
        });

        var pageableTerritories = new PageableTerritories();

        var EditCell = Backgrid.Cell.extend({
            template: _.template('<button type="button" class="btn-xs btn-primary">E</button>'),
            events: {
                click: function() {
                    //console.log(this.model.attributes._id.$oid + this.model.attributes.description);
                    var attrs = this.model.attributes;
                    $('#modalEditPortDesc, #modalEditPortId, #modalEditPortBill, #modalEditPortHeader').empty();
                    $('#modalEditPortType').select2('val', attrs.type);
                    $('#modalEditPortHeader').text(attrs.portname);
                    $('#modalEditPortId').text(attrs.id);
                    $('#modalEditPortBill').val(attrs.bill);
                    $('#modalEditPortDesc').val(attrs.descr);
                    $('#modalEditPort').modal({
                        show: true,
                        backdrop: 'static'
                    });
                }
            },
            render: function() {
                this.$el.html(this.template());
                this.delegateEvents();
                return this;
            }
        });
        var portCell = Backgrid.StringCell.extend({
            initialize: function(options) {
                //console.log(this);
                //var bill = '';
                //console.log(this.model);
                portCell.__super__.initialize.apply(this, arguments);
                //console.log(this.model.arguments);
                // this.listenTo(this.model, 'backgrid:edited', function(model, column, command) {
                //     console.log(model.get('bill'));
                //     //console.log(bill);
                //     //console.log(this);
                // });
            }
        });
        var billCell = Backgrid.StringCell.extend({
            initialize: function(options) {
                //console.log(this);
                //var bill = '';
                //console.log(this.model);
                billCell.__super__.initialize.apply(this, arguments);
                //console.log(this.model.arguments);
                // this.listenTo(this.model, 'backgrid:edited', function(model, column, command) {
                //     console.log(model.get('bill'));
                //     //console.log(bill);
                //     //console.log(this);
                // });
            },
            render: function() {
                //console.log(this);
                Backgrid.StringCell.prototype.render.call(this);
                if (this.model.attributes.active === 1) {
                    //console.log(this);
                    //this.$el.text(this.model.attributes.bill);
                    this.$el.addClass('text-success');
                } else {
                    this.$el.addClass('text-danger');
                }

                return this;
            }
        });

        // var descrCell = Backgrid.StringCell.extend({
        //     initialize: function(options) {
        //         descrCell.__super__.initialize.apply(this, arguments);
        //         this.listenTo(this.model, 'backgrid:edited', function(model, column, command) {
        //             console.log(model.get('bill'));
        //             //console.log(bill);
        //             //console.log(this);
        //         });
        //     }
        // });

        var columns = new Backgrid.Columns([/*{
            name: "id",
            label: "ID",
            editable: !1,
            cell: Backgrid.IntegerCell.extend({
                orderSeparator: ""
            })
        }, */
        {
            label: 'edit',
            editable: false,
            sortable: false,
            cell: EditCell
        },
        {
            name: 'port',
            label: 'Интерфейс',
            editable: false,
            cell: portCell,
            sortable: true,
            sortType: 'toggle'
        }, {
            name: 'net',
            label: 'Подсеть',
            editable: false,
            cell: Backgrid.StringCell,
            sortable: true,
            sortType: 'toggle'
        }, {
        //     name: 'out_policy',
        //     label: 'исх',
        //     editable: false,
        //     cell: Backgrid.StringCell,
        //     sortable: false
        // }, {
        //     name: 'in_policy',
        //     label: 'вх',
        //     editable: false,
        //     cell: Backgrid.StringCell,
        //     sortable: false
        // }, {
            name: 'bill',
            label: 'Договор',
            editable: false,
            cell: billCell,
            sortable: true,
            sortType: 'toggle',
            direction : 'ascending'
        }, {
            name: 'policy',
            label: 'Полиси',
            editable: false,
            cell: Backgrid.StringCell,
            sortable: true,
            sortType: 'toggle'
        }, {
            name: 'descr',
            label: 'Описание',
            editable: false,
            cell: Backgrid.StringCell,
            sortable: false
        }]);

        var pageableGrid = new Backgrid.Grid({
                columns: columns,
                collection: pageableTerritories,
                className: 'table table-striped table-editable no-margin'
            });

        // pageableGrid.collection.on('change', function(e) {
        //     b.id = e.attributes.portname;
        //     console.log(b);
        // });
        var clientSideFilter = new Backgrid.Extension.ClientSideFilter({
            collection: pageableTerritories,
            placeholder: 'Фильтр портов',
            fields: ['port'],
            wait: 150
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
        $('#search-portname').empty()
            .prepend(clientSideFilter.render().el);
        $('#netadm-content').html('')
            .append(pageableGrid.render().$el)
            .append(paginator.render().$el);
        pageableTerritories.fetch({data: {data: dict}, type: 'GET', reset: true});
    });

    $('#modalAcceptEdit').click(function() {
        var descr   = $('#modalEditPortDesc').val();
        var portid  = $('#modalEditPortId').text();
        var bill    = $('#modalEditPortBill').val();
        var lxType  = $('#modalEditPortType').val();
        var data = {
            descr:  descr,
            portid: portid,
            bill:   bill,
            type:   lxType
        };
        var xhr = $.ajax({
            type: 'POST',
            url: '/netadm',
            data: data,
            dataType: 'json'
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при попытке обновления информации!';
                    displayNotification(msg, 'error', 10);
                    break;
                case Status.NOAUTH:
                    displayNotification('Нет доступа обновлять информацию!', 'error');
                    break;
                case Status.SUCCESS:
                    displayNotification('Информация сохранена в базе!', 'success');
                    $('#netadm-button').trigger('click');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при попытке обновления информации!', 'error');
        });
    });
});
