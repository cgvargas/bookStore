É comum quando se trabalha com PostgreSQL em diferentes máquinas, especialmente relacionado a permissões do esquema public.

Para referência futura, o procedimento que seguimos:

1. Diagnosticamos o erro de codificação UTF-8 inicialmente, relacionado à forma como o PostgreSQL estava lidando com caracteres especiais
2. Ajustamos a configuração no settings.py para corrigir o problema de codificação
3. Criamos um backup do banco de dados PostgreSQL em uma máquina
4. Transferimos o backup para a segunda máquina através do OneDrive
5. Concedemos as permissões necessárias ao usuário no banco de dados da segunda máquina
6. Restauramos o backup com sucesso

Essas etapas serão úteis se você precisar sincronizar novamente os ambientes de desenvolvimento no futuro.
