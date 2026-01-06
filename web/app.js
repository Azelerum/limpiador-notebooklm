document.getElementById('drop-zone').addEventListener('click', () => {
    document.getElementById('file-input').click();
});

document.getElementById('file-input').addEventListener('change', function (e) {
    if (this.files.length > 0) {
        handleFileSelect(this.files[0]);
    }
});

const dropZone = document.getElementById('drop-zone');
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drop-zone--over');
});

['dragleave', 'dragend'].forEach(type => {
    dropZone.addEventListener(type, () => {
        dropZone.classList.remove('drop-zone--over');
    });
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drop-zone--over');

    if (e.dataTransfer.files.length) {
        document.getElementById('file-input').files = e.dataTransfer.files;
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

let selectedFile = null;

function handleFileSelect(file) {
    const allowedExtensions = ['.pdf', '.jpg', '.jpeg', '.png'];
    const extension = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        alert('Por favor, selecciona un archivo válido (.pdf, .jpg, .png)');
        return;
    }
    selectedFile = file;
    document.querySelector('.drop-zone__prompt').textContent = `Seleccionado: ${file.name}`;
    document.getElementById('process-section').classList.remove('hidden');
}

document.getElementById('process-btn').addEventListener('click', async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    toggleLoading(true);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('status-msg').textContent = result.message;
            document.getElementById('download-link').href = result.download_url;
            document.getElementById('process-section').classList.add('hidden');
            document.getElementById('download-section').classList.remove('hidden');
        } else {
            document.getElementById('status-msg').textContent = `Error: ${result.message}`;
        }
    } catch (error) {
        document.getElementById('status-msg').textContent = 'Error al conectar con el servidor';
    } finally {
        toggleLoading(false);
    }
});

document.getElementById('reset-btn').addEventListener('click', () => {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.querySelector('.drop-zone__prompt').textContent = 'Arrastra tu archivo aquí o haz clic para subir';
    document.getElementById('process-section').classList.add('hidden');
    document.getElementById('download-section').classList.add('hidden');
    document.getElementById('status-msg').textContent = '';
});

function toggleLoading(show) {
    document.getElementById('loader').classList.toggle('hidden', !show);
    document.getElementById('process-btn').disabled = show;
}
