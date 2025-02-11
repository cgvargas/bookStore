Para a implementação das expansões do dashboard, precisaremos dos seguintes arquivos principais:

1. **Arquivos Atuais do Dashboard:**
   ```
   cgbookstore/apps/core/recommendations/analytics/admin_dashboard/
   ├── views.py
   ├── urls.py
   ├── utils.py
   └── templates/core/admin_dashboard/
       ├── dashboard.html
       └── metrics.html
   ```

2. **Arquivos do Sistema de Analytics:**
   ```
   cgbookstore/apps/core/recommendations/analytics/
   ├── models.py (para ver a estrutura do RecommendationInteraction)
   ├── tracker.py
   ├── endpoints.py
   └── urls.py
   ```

3. **Configuração do Admin:**
   ```
   cgbookstore/apps/core/templates/admin/index.html
   ```

4. **Documentação:**
   - `chat_padronizado_03_02_2025.md` (já atualizado)
   - `structure-28-01-2025.txt` (estrutura do projeto)

Estes arquivos nos permitirão:
- Entender a estrutura atual do dashboard
- Visualizar os modelos de dados disponíveis
- Compreender os endpoints existentes
- Expandir corretamente as funcionalidades mantendo a consistência do projeto

