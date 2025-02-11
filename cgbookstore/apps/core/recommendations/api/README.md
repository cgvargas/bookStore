# API de Recomendações - Documentação

## Endpoints Disponíveis

### 1. Recomendações Gerais
- **URL**: `/api/recommendations/`
- **Método**: GET
- **Autenticação**: Requerida
- **Parâmetros Query**:
  - `limit` (opcional): Número máximo de recomendações (padrão: 10)
- **Resposta**:
  ```json
  [
    {
      "id": 1,
      "titulo": "Nome do Livro",
      "autor": "Nome do Autor",
      "editora": "Nome da Editora",
      "categoria": "Categoria do Livro",
      "capa_url": "/media/livros/capas/livro1.jpg",
      "preco_formatado": {
        "moeda": "BRL",
        "valor_formatado": "R$ 59,90",
        "valor_promocional_formatado": "R$ 49,90"
      },
      "e_lancamento": false,
      "preco_promocional": 49.90
    }
  ]
  


### 2. Prateleira Personalizada
- **URL**: `/api/recommendations/shelf/`
- **Método**: GET
- **Autenticação**: Requerida
- **Parâmetros Query**:
  - `shelf_size` (opcional): Número de livros por seção (padrão: 5)
- **Resposta**:
  ```json
  {
    "based_on_history": [
      {
        "id": 1,
        "titulo": "Nome do Livro",
        "autor": "Nome do Autor",
        ...
      }
    ],
    "based_on_categories": [
      ...
    ],
    "you_might_like": [
      ...
    ]
  }
  ```

## Cache

- Todas as respostas são cacheadas por 24 horas
- Cache é invalidado automaticamente quando:
  - Usuário adiciona livro à prateleira
  - Usuário remove livro da prateleira
  - Usuário move livro entre prateleiras

## Exemplos de Uso

### Curl
```bash
# Obter recomendações gerais
curl -X GET \
  'http://seu-dominio/api/recommendations/?limit=5' \
  -H 'Authorization: Token seu-token'

# Obter prateleira personalizada
curl -X GET \
  'http://seu-dominio/api/recommendations/shelf/?shelf_size=3' \
  -H 'Authorization: Token seu-token'
```

### JavaScript
```javascript
// Obter recomendações gerais
fetch('/api/recommendations/?limit=5', {
  headers: {
    'Authorization': 'Token seu-token'
  }
})
.then(response => response.json())
.then(data => console.log(data));

// Obter prateleira personalizada
fetch('/api/recommendations/shelf/?shelf_size=3', {
  headers: {
    'Authorization': 'Token seu-token'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

## Códigos de Erro

- **401**: Não autorizado - Token inválido ou ausente
- **403**: Proibido - Usuário sem permissão
- **404**: Não encontrado - Recurso não existe
- **500**: Erro interno do servidor

## Observações

- As recomendações são baseadas no histórico do usuário, categorias e similaridade
- Os livros já lidos pelo usuário são automaticamente excluídos das recomendações
- A API utiliza cache para otimizar o tempo de resposta
```

Esta documentação está completa e pronta para ser incluída no projeto. Quer que eu faça mais algum ajuste ou adição?