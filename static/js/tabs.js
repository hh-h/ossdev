/*global $spinner, displayNotification, $adminEditPlaceHolder, $adminCopyPlaceHolder, cy */
$(function() {
    'use strict';
    window.addEventListener('popstate', function() {
        var activeTab = $('[href=' + location.hash + ']');
        if (activeTab.length) {
            activeTab.tab('show');
        } else {
            $('.nav-tabs a:first').tab('show');
        }
    });
    $('#menuTabs a').click(function(e) {
        e.preventDefault();
        var $this = $(this);
        history.pushState(null, null, $this.attr('href'));
        switch ($this.attr(('href'))) {
            case '#tab-logs':
                $spinner.removeClass('hide');
                $.get('/logs', function(data) {
                    $spinner.addClass('hide');
                    var $userLogs = $('#logs-user');
                    // removing all old options
                    $userLogs.find('option')
                        .remove();
                        // добавим еще всех пользователей
                    $userLogs.append($('<option></option>')
                            .attr('value', 'all')
                            .text('Все'))
                        .select2('val', 'all');
                    // заполним данными из базы
                    $.each(data, function(key, value) {
                        $userLogs.append($('<option></option>')
                            .attr('value', value)
                            .text(value));
                    });
                }, 'json')
                .fail(function() {
                    $spinner.addClass('hide');
                    displayNotification('Критическая ошибка при получении списка пользователей!', 'error');
                });
                break;
            case '#tab-admin':
                $adminEditPlaceHolder.empty();
                $adminCopyPlaceHolder.empty();
                $('#admin-copy-save,#admin-copy-save,#admin-edit-delete').addClass('hide');
                $spinner.removeClass('hide');
                $.get('/users', function(data) {
                    $spinner.addClass('hide');
                    var $selects = $('#admin-edit-select,#admin-copy-select');
                    $selects.select2('val', '');
                    // removing all old options
                    $selects.find('option')
                        .remove();
                    // fill with new options from db
                    $selects.append($('<option></option>'));
                    $.each(data, function(key, value) {
                        $selects.append($('<option></option>')
                            .attr('value', value)
                            .text(value));
                    });
                }, 'json')
                .fail(function() {
                    $spinner.addClass('hide');
                    displayNotification('Критическая ошибка при получении списка пользователей!', 'error');
                });
                break;
            case '#tab-topology':
                if (typeof cy !== 'undefined') {
                    // TODO по левому клику мышки при возврате на предыдущий таб, топология исчезает
                    // FIXME через 0.1 сек перерисовывает топологию
                    setTimeout(function() {
                        cy.fit(cy.elements, 20);
                    }, 200);
                }
                break;
        }
    });
});
