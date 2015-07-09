$(function() {
    'use strict';
    $('.selectpicker').selectpicker();
    $('.select2').each(function() {
        $(this).select2($(this).data());
    });
    $('.tooltip2').tooltip();
    $('#slider-dhcp-results').slider();
});
