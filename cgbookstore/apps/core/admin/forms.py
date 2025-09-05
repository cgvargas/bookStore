# Arquivo: cgbookstore/apps/core/admin/forms.py

import logging
from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError

from ..models.book import Book
from ..models.home_content import HomeSection

logger = logging.getLogger(__name__)


class BookAdminForm(forms.ModelForm):
    """
    Formulário personalizado para o admin de Livros.
    Com sistema de prateleiras especiais corrigido.
    """

    tipo_shelf_especial = forms.ChoiceField(
        label=Book._meta.get_field('tipo_shelf_especial').verbose_name,
        required=False,
        help_text=(
            "Selecione uma prateleira especial para exibir este livro na home. "
            "Deixe em branco se não deseja exibir em prateleiras especiais."
        ),
        widget=forms.Select(attrs={
            'style': 'height: 32px; line-height: 30px; vertical-align: middle; padding: 4px 8px;',
            'class': 'form-control'
        }),
        # As opções serão preenchidas no __init__
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # >>> Lógica ATUALIZADA para configurar o campo tipo_shelf_especial <<<
        try:
            # Chama o método estático do modelo Book para obter as opções
            choices = Book.get_shelf_special_choices()
            self.fields['tipo_shelf_especial'].choices = choices
            logger.info(f"[BookAdminForm] Campo tipo_shelf_especial configurado com {len(choices)} opções")
        except Exception as e:
            logger.error(f"[BookAdminForm] Erro ao configurar choices de prateleiras: {e}")
            # Fallback para opções básicas (agora que o campo é ChoiceField, isso funcionará)
            self.fields['tipo_shelf_especial'].choices = [
                ('', 'Nenhum'),
                ('lancamentos', 'Lançamentos'),
                ('mais_vendidos', 'Mais Vendidos'),
                ('destaques', 'Destaques'),
                ('mangas', 'Mangás'),
                # Adicione outras opções padrão que você tinha, se houver
            ]
            # Mantenha o valor atual do campo se o formulário for uma instância existente
            if self.instance and self.instance.tipo_shelf_especial:
                current_value = self.instance.tipo_shelf_especial
                # Adiciona o valor atual à lista de choices se ele não estiver lá
                # Isso garante que um valor salvo inválido ainda seja exibido
                if not any(choice[0] == current_value for choice in self.fields['tipo_shelf_especial'].choices):
                    self.fields['tipo_shelf_especial'].choices.append(
                        (current_value, f"{current_value} (Inválido/Customizado)"))
                self.initial['tipo_shelf_especial'] = current_value

        # Configurações adicionais dos outros campos (manter o que já existia)
        if 'visibility' in self.fields:
            self.fields['visibility'].help_text = (
                "Público: visível para todos os usuários. "
                "Privado: apenas para o usuário que adicionou e administradores."
            )

        if 'ordem_exibicao' in self.fields:
            self.fields['ordem_exibicao'].help_text = (
                "Ordem de exibição nas prateleiras. Menor valor = maior prioridade."
            )

        # O método clean_tipo_shelf_especial pode ser mantido como está

    def clean_tipo_shelf_especial(self):
        """
        Validação customizada para o campo tipo_shelf_especial.
        """
        valor = self.cleaned_data.get('tipo_shelf_especial')

        if not valor:  # Valor vazio é válido
            return valor

        # Verificar se o valor está nas opções válidas
        valid_choices = dict(Book.get_shelf_special_choices())

        if valor not in valid_choices:
            # Aqui, se o valor atual da instância é um valor customizado, podemos aceitá-lo
            # para evitar erro na edição, mesmo que não esteja nas opções dinâmicas.
            # No entanto, a declaração do ChoiceField já deve cuidar disso no initial.
            # Para validação de *novos* valores, ele deve estar nas opções.
            raise ValidationError(
                f'Valor inválido para prateleira especial: "{valor}". '
                f'Valores válidos: {list(valid_choices.keys())}'
            )

        logger.info(f"[BookAdminForm] Prateleira especial validada: {valor}")
        return valor

        # ... (manter clean e save_model como estão, eles já estão corretos para a sincronização) ...

    def clean(self):
        """
        Validação geral do formulário com lógica de negócio.
        """
        cleaned_data = super().clean()

        # Validações de prateleiras especiais baseadas em checkboxes
        tipo_shelf = cleaned_data.get('tipo_shelf_especial')
        e_lancamento = cleaned_data.get('e_lancamento', False)
        e_destaque = cleaned_data.get('e_destaque', False)
        adaptado_filme = cleaned_data.get('adaptado_filme', False)
        e_manga = cleaned_data.get('e_manga', False)

        # Auto-definir tipo_shelf_especial baseado nos checkboxes
        # (apenas se não foi explicitamente definido)
        if not tipo_shelf:
            if e_lancamento:
                cleaned_data['tipo_shelf_especial'] = 'lancamentos'
                logger.info("[BookAdminForm] Auto-definido tipo_shelf_especial para 'lancamentos'")
            elif e_destaque:
                cleaned_data['tipo_shelf_especial'] = 'destaques'
                logger.info("[BookAdminForm] Auto-definido tipo_shelf_especial para 'destaques'")
            elif adaptado_filme:
                cleaned_data['tipo_shelf_especial'] = 'filmes'
                logger.info("[BookAdminForm] Auto-definido tipo_shelf_especial para 'filmes'")
            elif e_manga:
                cleaned_data['tipo_shelf_especial'] = 'mangas'
                logger.info("[BookAdminForm] Auto-definido tipo_shelf_especial para 'mangas'")

        # Sincronizar checkboxes com o tipo_shelf_especial selecionado
        if tipo_shelf:
            sync_map = {
                'lancamentos': 'e_lancamento',
                'destaques': 'e_destaque',
                'filmes': 'adaptado_filme',
                'mangas': 'e_manga'
            }

            # Ativar o checkbox correspondente
            if tipo_shelf in sync_map:
                field_name = sync_map[tipo_shelf]
                cleaned_data[field_name] = True
                logger.info(f"[BookAdminForm] Sincronizado {field_name}=True para tipo_shelf='{tipo_shelf}'")

        return cleaned_data

    def save(self, commit=True):
        """
        Override do save para garantir consistência de dados.
        """
        instance = super().save(commit=False)

        # Garantir que campos booleanos estão sincronizados
        tipo_shelf = instance.tipo_shelf_especial

        if tipo_shelf:
            # Resetar todos os flags primeiro
            instance.e_lancamento = False
            instance.e_destaque = False
            instance.adaptado_filme = False
            instance.e_manga = False

            # Ativar o flag correto
            if tipo_shelf == 'lancamentos':
                instance.e_lancamento = True
            elif tipo_shelf == 'destaques':
                instance.e_destaque = True
            elif tipo_shelf == 'filmes':
                instance.adaptado_filme = True
            elif tipo_shelf == 'mangas':
                instance.e_manga = True

            logger.info(f"[BookAdminForm] Flags sincronizados para tipo_shelf='{tipo_shelf}'")

        if commit:
            instance.save()
            # Limpar cache das opções após salvar
            Book.clear_shelf_choices_cache()

        return instance

    class Meta:
        model = Book
        fields = '__all__'
        widgets = {
            'capa': forms.FileInput(attrs={'accept': 'image/*'}),
            'capa_preview': forms.FileInput(attrs={'accept': 'image/*'}),
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'enredo': forms.Textarea(attrs={'rows': 3}),
            'temas': forms.Textarea(attrs={'rows': 2}),
            'personagens': forms.Textarea(attrs={'rows': 2}),
            'premios': forms.Textarea(attrs={'rows': 2}),
            'adaptacoes': forms.Textarea(attrs={'rows': 2}),
            'citacoes': forms.Textarea(attrs={'rows': 3}),
            'curiosidades': forms.Textarea(attrs={'rows': 3}),
            # CORREÇÃO DO CHECKBOX DESALINHADO
            'adaptado_filme': forms.CheckboxInput(attrs={
                'style': 'vertical-align: middle; margin-right: 8px; transform: scale(1.1);'
            }),
            'e_lancamento': forms.CheckboxInput(attrs={
                'style': 'vertical-align: middle; margin-right: 8px; transform: scale(1.1);'
            }),
            'e_destaque': forms.CheckboxInput(attrs={
                'style': 'vertical-align: middle; margin-right: 8px; transform: scale(1.1);'
            }),
            'e_manga': forms.CheckboxInput(attrs={
                'style': 'vertical-align: middle; margin-right: 8px; transform: scale(1.1);'
            }),
        }
        exclude = ['authors']  # Gerenciado via inline


class CustomAdminImportForm(forms.Form):
    """
    Formulário para importação de dados no admin.
    """
    import_file = forms.FileField(
        label="Arquivo para Importação",
        help_text="Selecione um arquivo CSV, JSON ou Excel para importar dados."
    )
    update_existing = forms.BooleanField(
        label="Atualizar Existentes",
        required=False,
        initial=True,
        help_text="Se marcado, registros existentes serão atualizados. Caso contrário, serão ignorados."
    )
    ignore_errors = forms.BooleanField(
        label="Ignorar Erros",
        required=False,
        initial=False,
        help_text="Se marcado, a importação continuará mesmo se encontrar erros em alguns registros."
    )