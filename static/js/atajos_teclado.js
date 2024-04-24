$(document).ready(function() {
    $(document).on('keydown', function(event) {
        var symbol;
        if (event.key === 'F7') {
            symbol = 'f7';
        } else if (event.key === 'F8') {
            symbol = 'f8';
        } else if (event.key === 'F9') {
            symbol = 'f9';
        }

        if (symbol) {
            $.post('/add_symbol', {symbol: symbol}, function(data) {
                var activeElement = document.activeElement;
                if (activeElement && activeElement.value !== undefined) {
                    var cursorPosition = activeElement.selectionStart;
                    activeElement.value = activeElement.value.substring(0, cursorPosition) + data + activeElement.value.substring(cursorPosition);
                }
            });
        }
    });
});