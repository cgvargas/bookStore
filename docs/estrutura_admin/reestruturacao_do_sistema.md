# Documento de Planejamento: Implementação Proativa - Sistema CGBookstore

## 1. Visão Geral

Considerando que o sistema CGBookstore está ainda em fase de desenvolvimento, temos a oportunidade ideal para implementar mudanças estruturais importantes antes que se tornem mais difíceis e custosas de implementar. Este documento detalha as implementações prioritárias para criar uma base sólida para o crescimento futuro do sistema.

## 2. Áreas de Implementação Prioritária

### 2.1. Reestruturação dos Módulos

**Objetivos imediatos:**
- Renomear o módulo CORE para "Organizador" - nome mais intuitivo e menos técnico
- Criar módulo dedicado "Autenticação e Autorização" para gestão de usuários e permissões
- Estabelecer clara separação de responsabilidades entre módulos

**Benefícios:**
- Estrutura mais intuitiva para administradores
- Organização de código mais clara para desenvolvedores
- Base escalável para expansões futuras

### 2.2. Implementação do Modelo Hierárquico

**Estrutura Proposta:**
```
Seção (Section)
  └── Estante (Shelf) 
       └── Prateleira (ShelfRack)
            └── Itens (Livros/Conteúdos)
```

**Regras de negócio fundamentais:**
- Itens padrão (Seções Padrão, Estantes Padrão, Prateleiras Padrão) são protegidos contra exclusão
- Seções com estantes ativas não podem ser excluídas
- Estantes com prateleiras ativas não podem ser excluídas
- Notificações claras quando operações são bloqueadas por estas regras

### 2.3. Interface Administrativa Personalizada

**Substituição completa da interface Django Admin por:**
- Design visual personalizado e consistente
- Experiência unificada sem transições abruptas entre telas
- Formulários simplificados para operações comuns
- Modo avançado opcional para acesso a todos os campos

### 2.4. Sistema de Personalização Visual

**Implementação de capacidades de personalização:**
- Formatos de imagem (quadrado, arredondado, circular)
- Esquemas de cores customizáveis
- Layouts de prateleira flexíveis
- Tipografia e espaçamento personalizáveis

## 3. Implementação Incremental

Considerando que o sistema está em desenvolvimento, recomendamos uma abordagem por incrementos graduais:

### Sprint 1: Fundação do Novo Sistema (2 semanas)
- Criar estrutura básica do módulo "Organizador"
- Implementar modelo base de Seção, Estante e Prateleira
- Protótipo inicial da interface administrativa personalizada

### Sprint 2: Sistema de Personalização (2 semanas)
- Desenvolver modelo completo de ShelfStyle
- Implementar interface de personalização
- Criar templates de renderização dinâmica

### Sprint 3: Migração de Usuários (1 semana)
- Criar módulo de Autenticação e Autorização
- Migrar modelos relacionados a usuários
- Atualizar referências no sistema

### Sprint 4: Refinamento e Integração (2 semanas)
- Testes integrados de todo o sistema
- Refinamento da interface administrativa
- Documentação completa para desenvolvedores

## 4. Considerações Técnicas Específicas

1. **Migração de Dados**
   - Desenvolver migrações Django que preservem dados existentes
   - Implementar a nova estrutura sem perder dados de teste já inseridos
   - Manter consistência de ForeignKeys e relações

2. **Naming Conventions**
   - Padronizar nomenclatura em todo o projeto
   - Documentar convenções para futuras adições
   - Traduzir nomes de campos para português nas interfaces de usuário

3. **Controle de Versão**
   - Criar branches específicas para cada sprint
   - Implementar testes automatizados para cada mudança estrutural
   - Revisão de código obrigatória antes de merge

## 5. Modelos de Dados Propostos

### Seção (Section)
```python
class Section(models.Model):
    name = models.CharField('Nome', max_length=200)
    description = models.TextField('Descrição', blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField('Padrão', default=False)
    display_order = models.IntegerField('Ordem de exibição', default=0)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    def can_delete(self):
        """Verifica se a seção pode ser excluída"""
        if self.is_default:
            return False, "Seções padrão não podem ser excluídas"
        if self.shelf_set.filter(is_active=True).exists():
            return False, "Esta seção contém estantes ativas e não pode ser excluída"
        return True, ""
```

### Estante (Shelf)
```python
class Shelf(models.Model):
    name = models.CharField('Nome', max_length=200)
    section = models.ForeignKey(Section, on_delete=models.PROTECT, verbose_name='Seção')
    description = models.TextField('Descrição', blank=True)
    shelf_type = models.CharField('Tipo', max_length=50, choices=SHELF_TYPE_CHOICES)
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField('Padrão', default=False)
    display_order = models.IntegerField('Ordem de exibição', default=0)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    def can_delete(self):
        """Verifica se a estante pode ser excluída"""
        if self.is_default:
            return False, "Estantes padrão não podem ser excluídas"
        if self.shelfrack_set.filter(is_active=True).exists():
            return False, "Esta estante contém prateleiras ativas e não pode ser excluída"
        return True, ""
```

### Prateleira (ShelfRack)
```python
class ShelfRack(models.Model):
    name = models.CharField('Nome', max_length=200)
    shelf = models.ForeignKey(Shelf, on_delete=models.PROTECT, verbose_name='Estante')
    description = models.TextField('Descrição', blank=True)
    max_items = models.IntegerField('Máximo de itens', default=12)
    style = models.ForeignKey('ShelfStyle', on_delete=models.SET_DEFAULT, default=1, verbose_name='Estilo')
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField('Padrão', default=False)
    display_order = models.IntegerField('Ordem de exibição', default=0)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    def can_delete(self):
        """Verifica se a prateleira pode ser excluída"""
        if self.is_default:
            return False, "Prateleiras padrão não podem ser excluídas"
        if self.items.exists():
            return False, "Esta prateleira contém itens e não pode ser excluída"
        return True, ""
```

### Estilo de Prateleira (ShelfStyle)
```python
class ShelfStyle(models.Model):
    name = models.CharField('Nome', max_length=100)
    image_format = models.CharField('Formato de imagem', choices=IMAGE_FORMAT_CHOICES, default='square')
    image_size = models.CharField('Tamanho', choices=SIZE_CHOICES, default='medium')
    background_color = models.CharField('Cor de fundo', max_length=20, default='#ffffff')
    text_color = models.CharField('Cor do texto', max_length=20, default='#000000')
    layout_type = models.CharField('Tipo de layout', choices=LAYOUT_CHOICES, default='grid')
    font_family = models.CharField('Família de fonte', choices=FONT_CHOICES, default='default')
    spacing = models.CharField('Espaçamento', choices=SPACING_CHOICES, default='normal')
    is_system = models.BooleanField('Sistema', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
```

## 6. Próximos Passos

1. Priorização das implementações definidas neste documento
2. Definição do time de desenvolvimento para cada sprint
3. Criação de branches específicas no repositório
4. Início imediato da Sprint 1

## 7. Benefícios da Implementação Proativa

1. Evitar dívida técnica desde o início do projeto
2. Estabelecer fundações sólidas para crescimento futuro
3. Reduzir custo total de desenvolvimento ao implementar corretamente desde o início
4. Criar experiência administrativa superior, diferenciando o produto no mercado

---

Este documento serve como guia para implementação imediata destas melhorias fundamentais no sistema CGBookstore, aproveitando a fase atual de desenvolvimento para estabelecer bases sólidas para o futuro.