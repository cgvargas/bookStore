# Implementação do Módulo de Prateleiras Personalizadas

Este guia contém as instruções para implementar o módulo de prateleiras personalizadas no projeto CGBookStore, permitindo a integração adequada entre os tipos de prateleiras (`DefaultShelfType`) e as prateleiras de livros (`BookShelfSection`).

## Arquivos Modificados

1. `cgbookstore/apps/core/models/home_content.py`
2. `cgbookstore/apps/core/admin.py`
3. `cgbookstore/apps/core/views/general.py`

## Arquivo de Migration

- `cgbookstore/apps/core/migrations/XXXX_add_shelf_type_field.py`
   - Este arquivo deve ser colocado na pasta de migrações, renomeando XXXX para o próximo número sequencial.

## Instruções de Implementação

### Passo 1: Atualizar o Código dos Modelos

Substitua o conteúdo do arquivo `cgbookstore/apps/core/models/home_content.py` pelo código fornecido.

### Passo 2: Atualizar o Painel Administrativo

Substitua o conteúdo do arquivo `cgbookstore/apps/core/admin.py` pelo código fornecido.

### Passo 3: Atualizar as Views

Substitua o método `get_context_data` da classe `IndexView` no arquivo `cgbookstore/apps/core/views/general.py` pelo código fornecido.

### Passo 4: Criar Migration

1. Crie um novo arquivo de migration na pasta `cgbookstore/apps/core/migrations/` usando o código fornecido.
2. Renomeie o arquivo para seguir a sequência numérica correta das migrations existentes.

Alternativamente, você pode gerar a migration automaticamente executando:

```bash
python manage.py makemigrations core
```

### Passo 5: Aplicar as Migrations

Execute o comando para aplicar a migration:

```bash
python manage.py migrate core
```

### Passo 6: Testar as Alterações

1. Acesse o painel administrativo do Django (`/admin/`).
2. Crie alguns tipos de prateleira em **Tipos de Prateleiras Padrão**.
3. Crie uma seção da home do tipo "Prateleira de Livros".
4. Crie uma prateleira de livros associada a essa seção, selecionando um dos tipos de prateleira que você criou.
5. Verifique se a prateleira aparece corretamente na página inicial.

## Notas Importantes

- O campo `tipo_shelf` ainda está disponível para manter compatibilidade com código existente.
- Para novas prateleiras, prefira usar o campo `shelf_type`.
- Os tipos de prateleira personalizados devem ter o campo `ativo` marcado para aparecerem na lista de seleção.