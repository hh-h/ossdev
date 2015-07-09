/*global Highcharts */

Highcharts.setOptions({
    lang: {
        months: [
            'Январь', 'Февраль', 'Март',
            'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь',
            'Октябрь', 'Ноябрь', 'Декабрь'
        ],
        weekdays: ['ВС', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ'],
        shortMonths: [
            'Янв', 'Февр', 'Март',
            'Апр', 'Май', 'Июнь',
            'Июль', 'Авг', 'Сент',
            'Окт', 'Нояб', 'Дек'
        ]
    }
});

var trafficOptions = {
    chart: {
        renderTo: 'traffic-content',
        type: 'column',
        events: {
            click: function() {
                'use strict';
                this.options.yAxis[0].type = (this.options.yAxis[0].type === 'logarithmic') ? 'line' : 'logarithmic';
                new Highcharts.Chart(this.options);
                // console.log(this.options.yAxis[0].type);
            }
        }
    },
    xAxis: {
        type: 'datetime'
    },
    yAxis: {
        title: {
            text: 'Трафик (Мегабайты)'
        },
        type: 'logarithmic'
    },
    plotOptions: {
        series: {
            pointWidth: 0
        },
        pointPadding: 10,
        column: {
            pointRange: 0,
            stacking: 'normal'
        }
    },
    legend: {
        enabled: false
    },
    title: {
        text: null
    },
    tooltip: {
        pointFormat: 'Трафик: <b>{point.y:.1f} Мб</b>'
    },
    series: [{
        name: 'Traffic',
        pointStart: 1,
        borderWidth: 1
    }, {
        name: 'Timeline',
        borderWidth: 0,
        enableMouseTracking: false,
        color: '#FFF'
    }]
};
