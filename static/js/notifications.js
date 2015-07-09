/*global Messenger */

// messages notification
$.globalMessenger({
    theme: 'air'
});
Messenger.options = {
    theme: 'air'
};

var messenger = new Messenger();

var displayNotification = function displayNotification(msg, type, t) {
    'use strict';
    if (typeof t === 'undefined') {
        t = 5;
    }
    messenger.post({
        message: msg,
        type: type,
        hideAfter: t,
        showCloseButton: true
    });
};
