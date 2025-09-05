// fix-customize-button.js - Script para garantir que o botão de customização esteja visível

document.addEventListener('DOMContentLoaded', function() {
    console.log('Iniciando correção do botão de customização...');

    // Esperar um pouco para ter certeza que outros scripts carregaram
    setTimeout(function() {
        // Encontrar o card de perfil
        const profileCard = document.querySelector('.profile-sidebar .customizable-card');

        if (profileCard) {
            console.log('Card de perfil encontrado, verificando botão de customização');

            // Verificar se o botão já existe
            let customizeBtn = profileCard.querySelector('.customize-button, #direct-customize-btn');

            // Se não existir, criar um novo
            if (!customizeBtn) {
                console.log('Botão não encontrado, criando novo botão...');

                // Criar botão fixo
                customizeBtn = document.createElement('button');
                customizeBtn.id = 'direct-customize-btn';
                customizeBtn.className = 'btn btn-sm btn-primary';
                customizeBtn.innerHTML = '<i class="bi bi-brush"></i> Personalizar';

                // Posicionar com estilos inline
                customizeBtn.style.position = 'absolute';
                customizeBtn.style.top = '10px';
                customizeBtn.style.right = '10px';
                customizeBtn.style.zIndex = '1000';
                customizeBtn.style.fontSize = '12px';

                // Garantir que o card tenha posição relativa
                profileCard.style.position = 'relative';

                // Adicionar evento de clique para abrir o modal
                customizeBtn.addEventListener('click', function() {
                    try {
                        const modal = document.getElementById('customizeCardModal');
                        if (modal) {
                            const bsModal = new bootstrap.Modal(modal);
                            bsModal.show();
                        } else {
                            console.error('Modal de customização não encontrado');
                        }
                    } catch (error) {
                        console.error('Erro ao abrir modal:', error);
                    }
                });

                // Adicionar ao card
                profileCard.appendChild(customizeBtn);
                console.log('Novo botão de customização adicionado com sucesso');
            } else {
                console.log('Botão já existe, garantindo visibilidade');
                // Garantir que o botão existente esteja visível
                customizeBtn.style.opacity = '1';
                customizeBtn.style.display = 'block';
                customizeBtn.style.position = 'absolute';
                customizeBtn.style.top = '10px';
                customizeBtn.style.right = '10px';
                customizeBtn.style.zIndex = '1000';
            }
        } else {
            console.error('Card de perfil não encontrado');
        }
    }, 500); // Pequeno atraso para garantir que outros scripts carregaram
});