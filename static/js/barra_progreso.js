const progressBar = document.getElementById('myProgressBar');
const startButtons = document.querySelectorAll('.remisionLink');
const progressPercentage = document.querySelector('.progress-percentage');
const modal = document.getElementById('modal');
const progressBarContainer = document.getElementById('progressBarContainer');
let progress = 0;
let interval;

function updateProgressBar() {
    if (progress < 100) {
        progress += 10;
        progressBar.style.width = progress + '%';
        progressPercentage.textContent = progress + '%';
    } else {
        clearInterval(interval);
    }
}

startButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        event.preventDefault(); // Evita la navegación inmediata
        modal.style.display = 'block';
        progressBarContainer.style.display = 'block';
        progress = 0;
        progressBar.style.width = progress + '%';
        clearInterval(interval);
        interval = setInterval(updateProgressBar, 50);

        setTimeout(() => {
            progressBarContainer.style.display = 'none';
            modal.style.display = 'none';
            window.location.href = button.href; // Navega al enlace después de la animación
        }, 2000);
    });
});
