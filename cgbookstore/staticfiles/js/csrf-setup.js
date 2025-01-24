// static/js/csrf-setup.js

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // Estes métodos HTTP não requerem proteção CSRF
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// Configuração do token CSRF para todas as requisições AJAX
document.addEventListener('DOMContentLoaded', function() {
    const xhr = new XMLHttpRequest();
    xhr.setRequestHeader = function(name, value) {
        if (name === 'X-CSRFToken') {
            this.setRequestHeader(name, csrftoken);
        }
    };
});