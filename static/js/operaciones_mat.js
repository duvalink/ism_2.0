// Obtener los campos de cantidad, precio unitario y total
const cantidad = document.getElementById("cantidad");
const precio = document.getElementById("precio");
const importe = document.getElementById("importe");

// Escuchar los cambios en los campos de cantidad y precio unitario
cantidad.addEventListener("input", actualizarImporte);
precio.addEventListener("input", actualizarImporte);

// Función para actualizar el campo de total
function actualizarImporte() {
  // Obtener los valores de cantidad y precio unitario
  const cantidadValor = cantidad.value;
  const precioValor = precio.value;

  // Calcular el total
  const importeValor = cantidadValor * precioValor;

  // Actualizar el campo de total
  importe.value = importeValor;
  console.log(importe)
}






function showModal(event) {
  event.preventDefault();
  const button = event.relatedTarget;
  const action = button.getAttribute('data-action');
  const modalTitle = document.querySelector('#myModal .modal-title');
  const submitBtn = document.querySelector('#myModal .modal-footer button[type="submit"]');

  if (action === 'add') {
    modalTitle.textContent = 'Agregar producto';
    submitBtn.textContent = 'Agregar';
  } else if (action === 'edit') {
    modalTitle.textContent = 'Editar producto';
    submitBtn.textContent = 'Guardar cambios';
    // Rellenar formulario con los datos del producto
    document.querySelector('#id').value = button.getAttribute('data-id');
    document.querySelector('#descripcion').value = button.getAttribute('data-descripcion');
    document.querySelector('#material').value = button.getAttribute('data-material');
    document.querySelector('#cantidad').value = button.getAttribute('data-cantidad');
    document.querySelector('#precio').value = button.getAttribute('data-precio');
    document.querySelector('#importe').value = button.getAttribute('data-importe');
  }

  // Abre el modal
  const myModal = new bootstrap.Modal(document.getElementById('myModal'));
  myModal.show();
}
