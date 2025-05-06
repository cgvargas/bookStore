# Documentação: Sistema de Background Personalizado

## Introdução
Este documento detalha a implementação e uso do sistema de background personalizado com esmaecimento adaptativo para os temas claro e escuro.

## Índice
1. Implementação Técnica
2. Correção do Admin
3. Como Utilizar o Recurso
4. Referência Rápida

---

## 1. Implementação Técnica

### Modelo de Dados
```python
class BackgroundSettings(models.Model):
    """Modelo para gerenciar a imagem de fundo do site"""
    section = models.OneToOneField(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='background_settings',
        limit_choices_to={'tipo': 'background'},
        verbose_name='Seção'
    )
    imagem = models.ImageField('Imagem de Fundo', upload_to='backgrounds/')
    opacidade = models.IntegerField(
        'Opacidade do Esmaecimento (%)', 
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Define a intensidade do esmaecimento nas bordas (0-100%)'
    )
    habilitado = models.BooleanField('Habilitado', default=True)
    aplicar_em = models.CharField(
        'Aplicar em', 
        max_length=20,
        choices=[
            ('both', 'Ambos os temas'),
            ('light', 'Apenas tema claro'), 
            ('dark', 'Apenas tema escuro')
        ],
        default='both'
    )
    posicao = models.CharField(
        'Posição', 
        max_length=20,
        choices=[
            ('center', 'Centralizado'),
            ('top', 'Superior'),
            ('bottom', 'Inferior')
        ],
        default='center'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
```

### CSS para Esmaecimento
O CSS implementado cria um efeito de esmaecimento nas bordas da imagem, adaptando-se automaticamente ao tema escolhido:

```css
/* Background personalizado com esmaecimento */
.custom-background {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    pointer-events: none;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

/* Esmaecimento para tema claro */
.light-mode .custom-background::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(
        ellipse at center,
        rgba(255, 255, 255, 0) 30%,
        rgba(255, 255, 255, 0.85) 80%,
        rgba(255, 255, 255, 0.95) 100%
    );
    transition: background 0.3s ease;
}

/* Esmaecimento para tema escuro */
.dark-mode .custom-background::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(
        ellipse at center,
        rgba(0, 0, 0, 0) 30%,
        rgba(0, 0, 0, 0.85) 80%,
        rgba(0, 0, 0, 0.95) 100%
    );
    transition: background 0.3s ease;
}
```

---

## 2. Correção do Admin

### Problema Identificado
Atualmente, há um problema no admin que impede o acesso direto à configuração de background através da interface administrativa.

### Soluções Propostas

#### 1. Correção do Registro no Admin
Verifique se o arquivo `admin.py` está corretamente configurado:

```python
from ..models.home_content import BackgroundSettings

@admin.register(BackgroundSettings)
class BackgroundSettingsAdmin(admin.ModelAdmin):
    list_display = ('section', 'habilitado', 'aplicar_em', 'posicao', 'opacidade', 'updated_at')
    list_filter = ('habilitado', 'aplicar_em', 'posicao')
    search_fields = ('section__titulo',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('section', 'imagem', 'habilitado')
        }),
        ('Configurações de Exibição', {
            'fields': ('aplicar_em', 'posicao', 'opacidade')
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
```

#### 2. Implementação de Inline Admin para HomeSection
Para facilitar a edição do background diretamente da página da seção, adicione este código em `content_admin.py`:

```python
class BackgroundSettingsInline(admin.StackedInline):
    model = BackgroundSettings
    can_delete = False
    verbose_name_plural = 'Configuração de Background'
    fk_name = 'section'
    
class HomeSectionAdmin(admin.ModelAdmin):
    # Código existente...
    inlines = []  # Lista existente
    
    def get_inlines(self, request, obj=None):
        inlines = super().get_inlines(request, obj)
        # Adiciona o inline apenas para seções do tipo 'background'
        if obj and obj.tipo == 'background':
            inlines.append(BackgroundSettingsInline)
        return inlines
```

#### 3. Modificação do `urls.py` do Admin
Se o problema persistir, verifique se as URLs do admin estão corretamente configuradas:

```python
# Em cgbookstore/apps/core/admin/urls.py ou similar
from django.contrib import admin

# Certifique-se de que o modelo BackgroundSettings está registrado no site admin
admin.site.register(BackgroundSettings, BackgroundSettingsAdmin)
```

#### 4. Criar Menu Personalizado no Admin
Adicione um link direto na página inicial do admin:

```python
# Em cgbookstore/apps/core/admin/site.py ou similar
class CustomAdminSite(admin.AdminSite):
    # Código existente...
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['background_config_url'] = reverse('admin:core_backgroundsettings_changelist')
        return super().index(request, extra_context)
```

---

## 3. Como Utilizar o Recurso

### Criação de Background via Admin (Quando Corrigido)

1. **Acessar o Admin**: Navegue para `http://seusite.com/admin/`
2. **Criar Seção de Background**:
   - Acesse "Seções" e clique em "Adicionar Seção"
   - Preencha:
     - Título: "Background Site"
     - Tipo de Seção: "Imagem de Fundo do Site"
     - Ativo: Marque esta opção
   - Clique em "Salvar"

3. **Configurar o Background**:
   - Após salvar, você deverá ver a opção "Configuração de Background"
   - Clique em "Adicionar Configuração de Background"
   - Faça upload da imagem
   - Configure:
     - Opacidade: valor entre 0-100%
     - Aplicar em: escolha entre "Ambos os temas", "Apenas tema claro", "Apenas tema escuro"
     - Posição: escolha "Centralizado", "Superior" ou "Inferior"
   - Clique em "Salvar"

### Enquanto o Admin Não Estiver Corrigido

Se o admin não estiver funcionando corretamente, o administrador do sistema pode usar o shell do Django:

```python
# Obter a seção atual
background_section = HomeSection.objects.get(titulo='Background Site')

# Obter a configuração
config = BackgroundSettings.objects.get(section=background_section)

# Para alterar configurações
config.opacidade = 70  # Valor entre 0-100
config.posicao = 'center'  # 'center', 'top', 'bottom'
config.aplicar_em = 'both'  # 'both', 'light', 'dark'
config.habilitado = True  # True para ativar, False para desativar
config.save()

# Para trocar a imagem
import os
from django.core.files import File
img_path = "caminho/para/nova_imagem.jpg"
with open(img_path, 'rb') as img_file:
    config.imagem.save(
        os.path.basename(img_path),
        File(img_file),
        save=True
    )
```

---

## 4. Referência Rápida

### Tamanhos de Imagem Recomendados
- **Resolução ideal**: 1920x1080px
- **Alta qualidade**: 2560x1440px 
- **Formato recomendado**: JPEG com 80-85% de qualidade ou PNG para imagens com transparência
- **Tamanho máximo recomendado**: 500KB para melhor desempenho

### Ajustes de Opacidade
- **0%**: Sem esmaecimento (imagem completamente visível)
- **50%**: Esmaecimento moderado
- **70%**: Configuração recomendada
- **100%**: Esmaecimento máximo (bordas quase invisíveis)

### Posições da Imagem
- **Centralizado**: Posição padrão, funciona bem com a maioria das imagens
- **Superior**: Enfatiza a parte superior da imagem
- **Inferior**: Enfatiza a parte inferior da imagem

---

## Próximos Passos

1. **Corrigir acesso via Admin**:
   - Implementar as soluções propostas na seção 2
   - Testar acesso às configurações via interface de administração

2. **Melhorias Futuras**:
   - Adicionar preview da imagem no admin
   - Implementar opção para backgrounds diferentes por página
   - Adicionar opção para carregar versões diferentes da imagem para mobile/desktop