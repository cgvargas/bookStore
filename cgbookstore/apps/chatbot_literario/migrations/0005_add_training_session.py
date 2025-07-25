# Generated by Django 5.1.8 on 2025-06-29 12:15

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot_literario', '0004_chatanalytics_alter_conversation_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='is_training_session',
            field=models.BooleanField(default=False, help_text='Indica se esta conversa é do simulador de treinamento', verbose_name='Sessão de Treinamento'),
        ),
        migrations.AddField(
            model_name='conversation',
            name='title',
            field=models.CharField(blank=True, help_text='Título descritivo da conversa', max_length=200, verbose_name='Título'),
        ),
        migrations.AddField(
            model_name='message',
            name='corrected_at',
            field=models.DateTimeField(blank=True, help_text='Data e hora da correção', null=True, verbose_name='Corrigida em'),
        ),
        migrations.AddField(
            model_name='message',
            name='corrected_by',
            field=models.ForeignKey(blank=True, help_text='Admin que realizou a correção', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='corrected_messages', to=settings.AUTH_USER_MODEL, verbose_name='Corrigida por'),
        ),
        migrations.AddField(
            model_name='message',
            name='corrected_response',
            field=models.TextField(blank=True, help_text='A resposta correta fornecida durante o treinamento', verbose_name='Resposta Corrigida'),
        ),
        migrations.AddField(
            model_name='message',
            name='was_corrected',
            field=models.BooleanField(default=False, help_text='Indica se esta resposta foi corrigida via treinamento', verbose_name='Foi Corrigida'),
        ),
        migrations.CreateModel(
            name='TrainingSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(blank=True, help_text='Identificador único da sessão de treinamento', max_length=100, verbose_name='ID da Sessão')),
                ('training_type', models.CharField(choices=[('manual_correction', 'Correção Manual via Simulador'), ('manual_addition', 'Adição Manual de Conhecimento'), ('bulk_training', 'Treinamento em Lote'), ('auto_learning', 'Aprendizado Automático'), ('embedding_update', 'Atualização de Embeddings'), ('knowledge_cleanup', 'Limpeza da Base de Conhecimento')], default='manual_correction', max_length=20, verbose_name='Tipo de Treinamento')),
                ('original_question', models.TextField(help_text='Pergunta que gerou a necessidade de treinamento', verbose_name='Pergunta Original')),
                ('original_answer', models.TextField(blank=True, help_text='Resposta incorreta que foi dada pelo sistema', verbose_name='Resposta Original')),
                ('corrected_answer', models.TextField(help_text='Resposta correta fornecida durante o treinamento', verbose_name='Resposta Corrigida')),
                ('notes', models.TextField(blank=True, help_text='Notas adicionais sobre a sessão de treinamento', verbose_name='Observações')),
                ('success', models.BooleanField(default=True, help_text='Indica se o treinamento foi aplicado com sucesso', verbose_name='Sucesso')),
                ('error_message', models.TextField(blank=True, help_text='Detalhes do erro caso o treinamento tenha falhado', verbose_name='Mensagem de Erro')),
                ('response_time', models.FloatField(blank=True, help_text='Tempo que levou para processar o treinamento', null=True, verbose_name='Tempo de Resposta (ms)')),
                ('confidence_score', models.FloatField(blank=True, help_text='Score de confiança na correção aplicada (0.0 a 1.0)', null=True, verbose_name='Score de Confiança')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('conversation', models.ForeignKey(blank=True, help_text='Conversa onde ocorreu o erro (se aplicável)', null=True, on_delete=django.db.models.deletion.SET_NULL, to='chatbot_literario.conversation', verbose_name='Conversa Relacionada')),
                ('knowledge_item', models.ForeignKey(blank=True, help_text='Item da KB criado/modificado durante esta sessão', null=True, on_delete=django.db.models.deletion.SET_NULL, to='chatbot_literario.knowledgeitem', verbose_name='Item de Conhecimento')),
                ('trainer_user', models.ForeignKey(blank=True, help_text='Admin que realizou o treinamento', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Usuário Treinador')),
            ],
            options={
                'verbose_name': 'Sessão de Treinamento',
                'verbose_name_plural': 'Sessões de Treinamento',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['trainer_user', '-created_at'], name='chatbot_lit_trainer_910172_idx'), models.Index(fields=['training_type', '-created_at'], name='chatbot_lit_trainin_7ad486_idx'), models.Index(fields=['success', '-created_at'], name='chatbot_lit_success_51dc86_idx'), models.Index(fields=['-created_at'], name='chatbot_lit_created_62e462_idx')],
            },
        ),
    ]
