# Notas de Migração: DatabaseCache para Redis

## Visão Geral

Esta migração substitui o sistema de cache atual baseado em `DatabaseCache` por uma solução Redis. As principais melhorias incluem:

- Performance muito superior (operações em memória vs. operações em banco de dados)
- Menor sobrecarga no banco de dados principal
- Isolamento lógico dos diferentes tipos de cache em bancos Redis separados
- Tempos de expiração otimizados para cada tipo de conteúdo
- Compressão para o cache de imagens

## Arquivos Modificados

1. `settings.py` - Configuração principal do Redis
2. `image_proxy.py` - Otimização do proxy de imagens
3. `cache_manager.py` - Atualização para usar caches Redis específicos
4. `google_books_service.py` - Atualização da classe de cache para Google Books

## Novo Arquivo

- `cache_migrate.py` - Comando para migração, validação e manutenção do sistema de cache

## Passos para o Deploy

1. Instalar e configurar o Redis (se ainda não estiver em execução):

```bash
# Verificar se o Redis está em execução
redis-cli ping
# Deve retornar: PONG

## Configuração para Windows com WSL

Ao executar o Redis no WSL e o Django no Windows, algumas configurações adicionais podem ser necessárias:

1. Use `localhost` em vez de `127.0.0.1` nas configurações CACHES:
   ```python
   'LOCATION': 'redis://localhost:6379/0',

## Configuração Condicional para Desenvolvimento/Produção

Para facilitar o desenvolvimento em ambientes Windows, onde a configuração do Redis com WSL pode ser complexa, implementamos uma configuração condicional no `settings.py`:

- Em ambiente de **produção**: Uso completo do Redis com todas as otimizações
- Em ambiente de **desenvolvimento**: Continua usando o DatabaseCache, evitando problemas de conectividade com Redis

Para alternar entre estes modos, basta ajustar a variável de ambiente `DJANGO_ENV`:

- Produção: `DJANGO_ENV=production`
- Desenvolvimento: `DJANGO_ENV=development` (padrão)

Isso permite que o código seja compatível com ambos os ambientes sem modificações adicionais, já que todas as classes foram atualizadas para usar `caches[nome_do_cache]`.