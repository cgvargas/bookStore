document.addEventListener('DOMContentLoaded', function() {
    // Configuração do comportamento "sticky" com animação suave
    const weatherCardWrapper = document.querySelector('.weather-card-wrapper');

    if (weatherCardWrapper) {
        // Detectar quando o card ficar "sticky"
        const observer = new IntersectionObserver(
            ([e]) => {
                const weatherCard = weatherCardWrapper.querySelector('.weather-card');
                if (e.intersectionRatio < 1) {
                    weatherCard.classList.add('is-sticky');
                } else {
                    weatherCard.classList.remove('is-sticky');
                }
            },
            { threshold: [1] }
        );

        observer.observe(weatherCardWrapper);
    }
    // Elementos do DOM
    const weatherWidget = document.getElementById('weather-widget');
    const locationInput = document.getElementById('weather-location');
    const searchButton = document.getElementById('search-location');
    const loadingElement = document.getElementById('weather-loading');
    const contentElement = document.getElementById('weather-content');
    const errorElement = document.getElementById('weather-error');
    const errorMessage = document.getElementById('error-message');
    const weatherIcon = document.getElementById('weather-icon');
    const cityName = document.getElementById('city-name');
    const currentTemp = document.getElementById('current-temp');
    const weatherDescription = document.getElementById('weather-description');
    const humidity = document.getElementById('humidity');
    const windSpeed = document.getElementById('wind-speed');
    const lastUpdated = document.getElementById('last-updated');
    const toggleButton = document.getElementById('toggle-weather-card');

    // Verificar se todos os elementos existem
    if (!weatherWidget || !locationInput || !searchButton) {
        console.error('Elementos do widget de clima não encontrados');
        return;
    }

    // Estado inicial
    let userLocation = localStorage.getItem('weatherLocation') || 'São Paulo';
    locationInput.value = userLocation;

    // Carregar dados do clima na inicialização
    loadWeatherData(userLocation);

    // Verificar se o card estava recolhido anteriormente
    const isCollapsed = localStorage.getItem('weatherCardCollapsed') === 'true';
    if (isCollapsed) {
        weatherWidget.classList.add('collapsed');
    }

    // Event Listeners
    searchButton.addEventListener('click', function() {
        searchWeather();
    });

    locationInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchWeather();
        }
    });

    // Botão para recolher/expandir o card
    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            weatherWidget.classList.toggle('collapsed');
            // Salvar preferência do usuário
            localStorage.setItem('weatherCardCollapsed', weatherWidget.classList.contains('collapsed'));
        });
    }

    // Função para buscar clima
    function searchWeather() {
        const location = locationInput.value.trim();
        if (location) {
            loadWeatherData(location);
            localStorage.setItem('weatherLocation', location);
        }
    }

    // Função principal para carregar dados do clima
    function loadWeatherData(location) {
        // Mostrar loading e esconder outros estados
        showLoading();

        // Fazer requisição para o endpoint do Django
        fetch(`/api/weather/?location=${encodeURIComponent(location)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Falha ao obter dados do clima');
                }
                return response.json();
            })
            .then(data => {
                if (data.config_missing) {
                    showError(data.error, true);
                    console.error('Erro de configuração da API de clima:', data.error);
                } else {
                    updateWeatherDisplay(data);
                }
            })
            .catch(error => {
                showError(error.message);
                console.error('Erro ao buscar dados do clima:', error);
            });
    }

    // Função para atualizar a exibição com os dados do clima
    function updateWeatherDisplay(data) {
        if (!data || data.error) {
            showError(data?.error || 'Dados do clima indisponíveis');
            return;
        }

        // Atualizar os elementos com os dados recebidos
        cityName.textContent = data.city;
        currentTemp.textContent = Math.round(data.temperature);
        weatherDescription.textContent = data.description;
        humidity.textContent = `${data.humidity}%`;
        windSpeed.textContent = `${data.wind_speed} km/h`;

        // Atualizar timestamp
        const now = new Date();
        lastUpdated.textContent = now.toLocaleTimeString();

        // Atualizar ícone com base na condição climática
        updateWeatherIcon(data.weather_condition, data.is_day);

        // Mostrar conteúdo e esconder loading
        showContent();
    }

    // Função para atualizar o ícone do clima
    function updateWeatherIcon(condition, isDay) {
        weatherIcon.innerHTML = '';
        weatherIcon.className = 'weather-icon';

        // Adicionar classe baseada na condição
        if (condition.includes('clear') || condition.includes('sunny')) {
            weatherIcon.classList.add('sunny');
            weatherIcon.innerHTML = createSunIcon(isDay);
        } else if (condition.includes('rain') || condition.includes('drizzle')) {
            weatherIcon.classList.add('rainy');
            weatherIcon.innerHTML = createRainIcon();
        } else if (condition.includes('cloud') || condition.includes('overcast')) {
            weatherIcon.classList.add('cloudy');
            weatherIcon.innerHTML = createCloudIcon(isDay);
        } else if (condition.includes('thunder') || condition.includes('storm')) {
            weatherIcon.classList.add('stormy');
            weatherIcon.innerHTML = createStormIcon();
        } else if (condition.includes('snow') || condition.includes('sleet')) {
            weatherIcon.classList.add('snowy');
            weatherIcon.innerHTML = createSnowIcon();
        } else if (condition.includes('mist') || condition.includes('fog')) {
            weatherIcon.classList.add('foggy');
            weatherIcon.innerHTML = createFogIcon();
        } else {
            // Ícone padrão para outras condições
            weatherIcon.classList.add(isDay ? 'sunny' : 'cloudy');
            weatherIcon.innerHTML = isDay ? createSunIcon(true) : createCloudIcon(false);
        }
    }

    // Funções para criar SVGs de ícones do clima
    function createSunIcon(isDay) {
        if (isDay) {
            return `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="5" fill="#FFD700" />
                <path d="M12 3V4M12 20V21M3 12H4M20 12H21M5.5 5.5L6.5 6.5M18.5 18.5L17.5 17.5M5.5 18.5L6.5 17.5M18.5 5.5L17.5 6.5"
                      stroke="#FFD700" stroke-width="2" stroke-linecap="round" />
            </svg>`;
        } else {
            return `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="5" fill="#E1E1E1" />
                <path d="M12 3V4M12 20V21M3 12H4M20 12H21M5.5 5.5L6.5 6.5M18.5 18.5L17.5 17.5M5.5 18.5L6.5 17.5M18.5 5.5L17.5 6.5"
                      stroke="#E1E1E1" stroke-width="2" stroke-linecap="round" />
            </svg>`;
        }
    }

    function createCloudIcon(isDay) {
        const color = isDay ? "#E1E1E1" : "#BBBBBB";
        return `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5.5 16C3.6 16 2 14.4 2 12.5C2 10.6 3.6 9 5.5 9C5.6 9 5.7 9 5.8 9C6.2 7.2 7.9 6 10 6C12.2 6 14 7.5 14.3 9.5C14.4 9.5 14.4 9.5 14.5 9.5C16.4 9.5 18 11.1 18 13C18 14.9 16.4 16.5 14.5 16.5H5.5V16Z"
                  fill="${color}" />
        </svg>`;
    }

    function createRainIcon() {
        return `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5.5 16C3.6 16 2 14.4 2 12.5C2 10.6 3.6 9 5.5 9C5.6 9 5.7 9 5.8 9C6.2 7.2 7.9 6 10 6C12.2 6 14 7.5 14.3 9.5C14.4 9.5 14.4 9.5 14.5 9.5C16.4 9.5 18 11.1 18 13C18 14.9 16.4 16.5 14.5 16.5H5.5V16Z"
                  fill="#BBBBBB" />
            <path class="rain-drop" style="--i:1" d="M8 18V20" stroke="#64B5F6" stroke-width="2" stroke-linecap="round" />
            <path class="rain-drop" style="--i:2" d="M12 18V20" stroke="#64B5F6" stroke-width="2" stroke-linecap="round" />
            <path class="rain-drop" style="--i:3" d="M16 18V20" stroke="#64B5F6" stroke-width="2" stroke-linecap="round" />
        </svg>`;
    }

    function createStormIcon() {
        return `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5.5 16C3.6 16 2 14.4 2 12.5C2 10.6 3.6 9 5.5 9C5.6 9 5.7 9 5.8 9C6.2 7.2 7.9 6 10 6C12.2 6 14 7.5 14.3 9.5C14.4 9.5 14.4 9.5 14.5 9.5C16.4 9.5 18 11.1 18 13C18 14.9 16.4 16.5 14.5 16.5H5.5V16Z"
                  fill="#9E9E9E" />
            <path d="M10 12L8 16H12L10 20" stroke="#FFD700" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>`;
    }

    function createSnowIcon() {
        return `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5.5 14C3.6 14 2 12.4 2 10.5C2 8.6 3.6 7 5.5 7C5.6 7 5.7 7 5.8 7C6.2 5.2 7.9 4 10 4C12.2 4 14 5.5 14.3 7.5C14.4 7.5 14.4 7.5 14.5 7.5C16.4 7.5 18 9.1 18 11C18 12.9 16.4 14.5 14.5 14.5H5.5V14Z"
                  fill="#E1E1E1" />
            <circle cx="8" cy="17" r="1" fill="white" />
            <circle cx="12" cy="19" r="1" fill="white" />
            <circle cx="16" cy="17" r="1" fill="white" />
            <circle cx="10" cy="20" r="1" fill="white" />
            <circle cx="14" cy="22" r="1" fill="white" />
        </svg>`;
    }

    function createFogIcon() {
        return `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 8H19" stroke="#E1E1E1" stroke-width="2" stroke-linecap="round" />
            <path d="M3 12H21" stroke="#E1E1E1" stroke-width="2" stroke-linecap="round" />
            <path d="M5 16H19" stroke="#E1E1E1" stroke-width="2" stroke-linecap="round" />
        </svg>`;
    }

    // Funções de controle de visibilidade
    function showLoading() {
        loadingElement.style.display = 'flex';
        contentElement.style.display = 'none';
        errorElement.style.display = 'none';
    }

    function showContent() {
        loadingElement.style.display = 'none';
        contentElement.style.display = 'flex';
        errorElement.style.display = 'none';
    }

    function showError(message, isConfigError = false) {
        loadingElement.style.display = 'none';
        contentElement.style.display = 'none';
        errorElement.style.display = 'flex';

        if (isConfigError) {
            errorMessage.innerHTML = 'Configuração da API de clima incompleta. <br>Entre em contato com o administrador.';
        } else {
            errorMessage.textContent = message || 'Erro ao obter previsão do tempo';
        }
    }
});