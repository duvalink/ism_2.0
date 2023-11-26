$('#modal-body').on('shown.bs.modal', function () {
    // Cuando cambia el valor de 'cantidad' o 'precio'
    $('#cantidad, #precio').change(function () {
        var cantidad = parseFloat($('#cantidad').val()) || 0;
        var precio = parseFloat($('#precio').val()) || 0;
        var importe = cantidad * precio;
        $('#importe').val(importe.toFixed(2));
    });
});