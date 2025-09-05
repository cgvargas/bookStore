// /static/js/chatbot-sw.js

const CACHE_NAME = 'cg-bookstore-chatbot-v1';
const urlsToCache = [
    '/static/css/chatbot-enhanced.css',
    '/static/js/chatbot-enhanced.js',
    '/static/images/favicon.svg',
    '/chatbot/'
];

// Instalação do Service Worker
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('📦 Cache do chatbot criado');
                return cache.addAll(urlsToCache);
            })
            .catch(function(error) {
                console.log('❌ Erro ao criar cache:', error);
            })
    );
});

// Interceptação de requests
self.addEventListener('fetch', function(event) {
    // Só cachear requests GET
    if (event.request.method !== 'GET') {
        return;
    }

    // Não cachear API calls do chatbot
    if (event.request.url.includes('/chatbot/api/')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Cache hit - retorna resposta
                if (response) {
                    return response;
                }

                return fetch(event.request);
            }
        )
    );
});

// Ativação do Service Worker
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑️ Removendo cache antigo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Notificações push (opcional - para futuras implementações)
self.addEventListener('push', function(event) {
    const options = {
        body: event.data ? event.data.text() : 'Nova mensagem do chatbot',
        icon: '/static/images/favicon.svg',
        badge: '/static/images/favicon.svg'
    };

    event.waitUntil(
        self.registration.showNotification('CG BookStore', options)
    );
});

// Click em notificações
self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    event.waitUntil(
        clients.openWindow('/chatbot/')
    );
});