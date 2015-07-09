/*global displayNotification, Status, $adminEditPlaceHolder, adminEditTemplate, $spinner,
$adminCopyPlaceHolder, adminCopyTemplate*/
$(function() {
    'use strict';

    // Храним текущие права просматриваемого пользователя
    var currentPermissions = {};
    var currentUsers = [];

    // Сравнивает с правами пользователя полученными из базы
    var comparePermFromDB = function comparePermFromDB(perm) {
        // Если у пользователя есть такая опция, вернее ее значение
        if (currentPermissions[perm]) {
            return currentPermissions[perm];
        }
        // если нет опции, прав на опцию нет, вернем 0
        return 0;
    };
    // подсвечиваем измененные строки
    $(document).on('change', '#admin-edit-content input[type="checkbox"]', function() {
        var $saveBtn = $('#admin-edit-save');
        var $checkbox = $(this);
        var state = $checkbox.is(':checked') ? 1 : 0;
        var option = $checkbox.data('value');
        if (comparePermFromDB(option) === state) {
            $checkbox.closest('tr').removeClass('mark');
            // если были измененния, то показываем кнопку "сохранить"
            if ($adminEditPlaceHolder.find('.mark').length > 0) {
                $saveBtn.removeClass('hide');
            } else {
                $saveBtn.addClass('hide');
            }
        } else {
            $checkbox.closest('tr').addClass('mark');
            $saveBtn.removeClass('hide');
        }
    });
    // работа с чекбоксами при копировании прав
    $(document).on('change', '#admin-copy-content input[type="checkbox"]', function() {
        var $saveBtn = $('#admin-copy-save');
        var $checkbox = $(this);
        var state = $checkbox.is(':checked') ? 1 : 0;
        var user = $checkbox.data('value');
        // если поставили чекбокс, внесем в список пользователей
        if (state) {
            currentUsers.push(user);
            $saveBtn.removeClass('hide');
        } else {
            var index = currentUsers.indexOf(user);
            if (index > -1) {
                currentUsers.splice(index, 1);
            }
            if (currentUsers.length === 0) {
                $saveBtn.addClass('hide');
            }
        }
    });
    // удаление пользователя
    $('#admin-edit-delete').on('click', function() {
        var user = $('#admin-edit-select').val();
        if (!user) {
            displayNotification('Не знаю кого удалять!', 'error');
            return;
        }
        $('#user-to-delete').text(user);
        $('#modalDeleteUser').modal({
            show: true,
            backdrop: 'static'
        });
    });
    // подтверждение удаления из модального окна
    $('#modalAcceptDeleteUser').on('click', function() {
        var user = $('#user-to-delete').text();
        if (!user) {
            displayNotification('Не знаю кого удалять!', 'error');
            return;
        }
        $spinner.removeClass('hide');
        var xhr = $.ajax({
            type: 'POST',
            url: '/admin/delete',
            data: {
                user : user
            },
            dataType: 'json'
        })
        .always(function() {
            $spinner.addClass('hide');
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при попытке удаления пользователя!';
                    displayNotification(msg, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Вы не можете удалять пользователей!', 'error');
                    break;
                case Status.SUCCESS:
                    // очистим форму
                    $adminEditPlaceHolder.empty();
                    // спрячем кнопки
                    $('#admin-edit-save,#admin-edit-delete').addClass('hide');
                    // удалим из селекта этого пользователя
                    $('#admin-edit-select option[value="' + user + '"]').remove();
                    $('#admin-edit-select').select2('val', -1);
                    displayNotification('Пользователь удален!', 'success');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при попытке удаления пользователя!', 'error');
        });
    });
    // ищем изменившиеся чекбоксы и записываем в базу новые права
    $('#admin-edit-save').on('click', function(e) {
        e.preventDefault();
        var changed = $adminEditPlaceHolder.find('.mark').length;
        if (!changed) {
            displayNotification('Не было изменений в правах!', 'info');
            return;
        }
        var user = $('#admin-edit-select').val();
        if (!user) {
            displayNotification('Не знаю кому менять права!', 'error');
            return;
        }
        var d = {};
        $('#admin-edit-content input[type="checkbox"]').each(function() {
            var $this = $(this);
            var option = $this.data('value');
            var value = $this.prop('checked') | 0;
            d[option] = value;
        });
        d.regions = $('#regions').text();

        $spinner.removeClass('hide');
        var xhr = $.ajax({
            type: 'POST',
            url: '/admin/edit',
            data: {
                user : user,
                data : JSON.stringify(d)
            },
            dataType: 'json'
        })
        .always(function() {
            $spinner.addClass('hide');
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при попытке изменения прав!';
                    displayNotification(msg, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Нет доступа менять права!', 'error');
                    break;
                case Status.SUCCESS:
                    // запишем обновленные права, как будто мы их из базы достали
                    currentPermissions = d;
                    // уберем все подсвеченные строки
                    $adminEditPlaceHolder.find('.mark')
                        .removeClass('mark');
                    // спрячем кнопку "сохранить"
                    $('#admin-edit-save').addClass('hide');
                    displayNotification('Новые права установлены!', 'success');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при попытке изменения прав!', 'error');
        });
    });

    $('#admin-copy-save').on('click', function(e) {
        e.preventDefault();
        var user = $('#admin-copy-select').val();
        if (!user) {
            displayNotification('Не знаю с кого копировать права!', 'error');
            return;
        }
        if (currentUsers.length === 0) {
            displayNotification('Не знаю кому копировать права!', 'error');
            return;
        }
        $spinner.removeClass('hide');
        var xhr = $.ajax({
            type: 'POST',
            url: '/admin/copy',
            data: {
                user : user,
                to   : JSON.stringify(currentUsers)
            },
            dataType: 'json'
        })
        .always(function() {
            $spinner.addClass('hide');
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул данных!', 'error');
                return;
            }

            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Ошибка при попытке копирования прав!';
                    displayNotification(msg, 'error');
                    break;
                case Status.NOAUTH:
                    displayNotification('Нет доступа копировать права!', 'error');
                    break;
                case Status.SUCCESS:
                    // сотрем список пользователей
                    currentUsers = [];
                    // очистим вывод
                    $adminCopyPlaceHolder.empty();
                    // спрячем кнопку "сохранить"
                    $('#admin-copy-save').addClass('hide');
                    // сбросим значение на дефолтный селект
                    $('#admin-copy-select').select2('val', -1);
                    displayNotification('Права скопированы пользоватям успешно!', 'success');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при попытке изменения прав!', 'error');
        });
    });

    $('#admin-edit-select').on('select2-selecting', function(e) {
        // удалим содержимое контейнера
        $adminEditPlaceHolder.empty();
        // спрячем кнопку "сохранить"
        $('#admin-edit-save').addClass('hide');
        // спрячем кнопку "удалить"
        $('#admin-edit-delete').addClass('hide');
        currentPermissions = {};
        $spinner.removeClass('hide');
        var xhr = $.ajax({
            type: 'GET',
            url: '/admin',
            data: {
                user: e.val
            },
            dataType: 'json'
        })
        .always(function() {
            $spinner.addClass('hide');
        })
        .done(function(data) {
            if (!data) {
                displayNotification('Сервер не вернул никаких данных!', 'error');
                return;
            }
            switch (data.status) {
                case Status.ERROR:
                    var msg = data.msg ? data.msg : 'Какая-то ошибка!';
                    displayNotification(msg, 'error');
                    break;
                case Status.SUCCESS:
                    currentPermissions = data.data;
                    $adminEditPlaceHolder.html(adminEditTemplate(data.data));
                    // покажем кнопку "удалить"
                    $('#admin-edit-delete').removeClass('hide');
                    break;
            }
        })
        .fail(function() {
            displayNotification('Критическая ошибка при попытке авторизации!', 'error');
        });
    });

    // при выборе пользователя показать всех других, чтобы им можно было скопировать права
    $('#admin-copy-select').on('select2-selecting', function(e) {
        var userList = [];
        $adminCopyPlaceHolder.empty();
        // спрячем кнопку "сохранить"
        $('#admin-copy-edit').addClass('hide');
        currentUsers = [];
        $('#admin-copy-select option').each(function() {
            var value = $(this).val();
            if (value && value !== e.val) {
                userList.push(value);
            }
        });
        $adminCopyPlaceHolder.html(adminCopyTemplate({data: userList}));
    });
});
