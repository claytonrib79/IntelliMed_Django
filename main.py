"""
IntelliMed - Sistema de Gestão de Clínicas
Backend Django Completo em Arquivo Único
Multi-tenant com autenticação JWT integrada
"""

import os
import sys
import json
import re
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pathlib import Path
import base64
import asyncio

# ============================================
# CARREGAR VARIÁVEIS DE AMBIENTE (.env)
# ============================================

def load_env_file(env_path='.env'):
    """Carregar variáveis do arquivo .env"""
    env_file = Path(env_path)
    
    if not env_file.exists():
        print(f"⚠️  Arquivo {env_path} não encontrado")
        return False
    
    print(f"✓ Carregando variáveis do arquivo: {env_path}")
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Ignorar linhas vazias e comentários
            if not line or line.startswith('#'):
                continue
            
            # Processar linha no formato KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remover aspas se houver
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Definir variável de ambiente
                os.environ[key] = value
    
    print("✓ Variáveis de ambiente carregadas com sucesso")
    return True

# Carregar .env na inicialização
load_env_file('.env')

# ============================================
# CONFIGURAÇÕES GLOBAIS
# ============================================

class Config:
    """Configurações globais do sistema"""
    
    # JWT - carregar do .env ou usar padrão
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'intellimed-2025-chave-super-secreta-mudar-em-producao')
    JWT_ALGORITHM = "HS256"
    
    # Google Gemini - carregar do .env
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')
    
    # Servidor
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    
    # Debug
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    # Banco de dados
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'intellimed.db')
    
    # Configurar Gemini
    @classmethod
    def configure_gemini(cls):
        """Configura a API do Google Gemini"""
        if cls.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=cls.GEMINI_API_KEY)
                return True
            except:
                return False
        return False

# ============================================
# CONFIGURAÇÃO DO DJANGO (ANTES DOS IMPORTS DO DRF)
# ============================================

import django
from django.conf import settings

# Configurar Django ANTES de importar qualquer coisa do DRF
if not settings.configured:
    settings.configure(
        DEBUG=Config.DEBUG,
        SECRET_KEY='intellimed-secret-key-change-in-production',
        ALLOWED_HOSTS=['*'],
        
        # Apps instalados
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework',
            'channels',
        ],
        
        # Middleware
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.common.CommonMiddleware',
        ],
        
        # Banco de dados SQLite
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': Config.DATABASE_NAME,
            }
        },
        
        # Configuração REST Framework
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'rest_framework.authentication.SessionAuthentication',
            ],
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticated',
            ],
            'DEFAULT_RENDERER_CLASSES': [
                'rest_framework.renderers.JSONRenderer',
            ],
            'DEFAULT_PARSER_CLASSES': [
                'rest_framework.parsers.JSONParser',
                'rest_framework.parsers.MultiPartParser',
                'rest_framework.parsers.FormParser',
            ],
            
            'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
            'PAGE_SIZE': 20, 
        },
        
        # Configuração Channels (WebSocket)
        ASGI_APPLICATION = 'main.application',
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer'
            }
        },
        
        # Timezone
        USE_TZ=True,
        TIME_ZONE='America/Sao_Paulo',
        
        # Idioma
        LANGUAGE_CODE='pt-br',
        
        # CORS (permitir todos durante desenvolvimento)
        CORS_ALLOW_ALL_ORIGINS=True,
        
        # Root URL
        ROOT_URLCONF='__main__',
    )
    
    django.setup()

# ============================================
# AGORA SIM: IMPORTS DO DJANGO E DRF
# ============================================

from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum, Count
from django.utils import timezone

# Django REST Framework
from rest_framework import serializers, viewsets, status, filters
from rest_framework.decorators import api_view, action, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

# JWT
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

# Para WebSocket (transcrição de áudio)
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path, re_path

# Google Gemini
try:
    import google.generativeai as genai
except ImportError:
    print("⚠️  google-generativeai não instalado. Transcrições não funcionarão.")
    genai = None

# ASGI
from django.core.asgi import get_asgi_application

# ============================================
# UTILITÁRIOS E VALIDADORES
# ============================================

class Validador:
    """Classe com métodos de validação"""
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF usando algoritmo oficial"""
        cpf_numeros = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf_numeros) != 11:
            return False
        
        if len(set(cpf_numeros)) == 1:
            return False
        
        # Validação do primeiro dígito
        soma = sum(int(cpf_numeros[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        if digito1 == 10:
            digito1 = 0
        
        # Validação do segundo dígito
        soma = sum(int(cpf_numeros[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        if digito2 == 10:
            digito2 = 0
        
        return cpf_numeros[9] == str(digito1) and cpf_numeros[10] == str(digito2)
    
    @staticmethod
    def formatar_cpf(cpf: str) -> str:
        """Formata CPF para XXX.XXX.XXX-XX"""
        cpf_numeros = re.sub(r'[^0-9]', '', cpf)
        if len(cpf_numeros) == 11:
            return f"{cpf_numeros[:3]}.{cpf_numeros[3:6]}.{cpf_numeros[6:9]}-{cpf_numeros[9:]}"
        return cpf
    
    @staticmethod
    def formatar_telefone(telefone: str) -> str:
        """Formata telefone para (XX) XXXXX-XXXX ou (XX) XXXX-XXXX"""
        tel_numeros = re.sub(r'[^0-9]', '', telefone)
        if len(tel_numeros) == 11:
            return f"({tel_numeros[:2]}) {tel_numeros[2:7]}-{tel_numeros[7:]}"
        elif len(tel_numeros) == 10:
            return f"({tel_numeros[:2]}) {tel_numeros[2:6]}-{tel_numeros[6:]}"
        return telefone
    
    @staticmethod
    def formatar_cep(cep: str) -> str:
        """Formata CEP para XXXXX-XXX"""
        cep_numeros = re.sub(r'[^0-9]', '', cep)
        if len(cep_numeros) == 8:
            return f"{cep_numeros[:5]}-{cep_numeros[5:]}"
        return cep
    
    @staticmethod
    def validar_email_format(email: str) -> bool:
        """Valida formato de email"""
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def validar_data_nascimento(data_nasc: str) -> bool:
        """Valida se a data de nascimento é válida e não é futura"""
        try:
            data = datetime.strptime(data_nasc, '%Y-%m-%d').date()
            return data <= date.today()
        except:
            return False

# ============================================
# AUTENTICAÇÃO JWT CUSTOMIZADA
# ============================================
class AuthenticatedUser:
    """Classe wrapper para usuário autenticado via JWT"""
    
    def __init__(self, payload):
        self.payload = payload
        self.is_authenticated = True
        self.is_active = True
    
    def get(self, key, default=None):
        return self.payload.get(key, default)
    
    def __getitem__(self, key):
        return self.payload[key]
    
class JWTAuthentication(BaseAuthentication):
    """Autenticação JWT customizada"""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        try:
            parts = auth_header.split()
            
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                raise AuthenticationFailed('Formato de token inválido')
            
            token = parts[1]
            
            payload = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM]
            )
            
            user = AuthenticatedUser(payload)
            return (user, None)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expirado')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token inválido')
        except Exception:
            raise AuthenticationFailed('Erro na autenticação')
                            
    def authenticate_header(self, request):
        return 'Bearer'

# ============================================
# PERMISSÕES CUSTOMIZADAS POR FUNÇÃO
# ============================================

class IsAdminOrMedico(BasePermission):
    """
    Permissão: Apenas admin ou médico
    Usado em: Consultas, Exames IA, dados clínicos sensíveis
    """
    
    def has_permission(self, request, view):
        if not hasattr(request, 'user') or not request.user:
            return False
        
        funcao = request.user.get('funcao')
        return funcao in ['super_admin', 'admin', 'medico']
    
    message = 'Apenas administradores e médicos têm acesso a este recurso.'

class IsSecretariaOrAbove(BasePermission):
    """
    Permissão: Secretária, médico ou admin
    Usado em: Pacientes, Agendamentos, Faturamento
    """
    
    def has_permission(self, request, view):
        if not hasattr(request, 'user') or not request.user:
            return False
        
        funcao = request.user.get('funcao')
        return funcao in ['super_admin', 'admin', 'medico', 'secretaria']
    
    message = 'Você não tem permissão para acessar este recurso.'

class IsAdminOnly(BasePermission):
    """
    Permissão: Apenas admin ou super_admin
    Usado em: Gestão de usuários, configurações críticas
    """
    
    def has_permission(self, request, view):
        if not hasattr(request, 'user') or not request.user:
            return False
        
        funcao = request.user.get('funcao')
        return funcao in ['super_admin', 'admin']
    
    message = 'Apenas administradores têm acesso a este recurso.'

class TenantMiddleware:
    """Middleware para isolar dados por tenant (clinica_id)"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extrair clinica_id do usuário autenticado
        if hasattr(request, 'user') and request.user:
            if isinstance(request.user, dict):
                request.clinica_id = request.user.get('clinica_id')
            else:
                request.clinica_id = getattr(request.user, 'clinica_id', None)
        else:
            request.clinica_id = None
        
        response = self.get_response(request)
        return response
    
# ============================================
# MODELS - BASE COM MULTI-TENANT
# ============================================

class TenantModel(models.Model):
    """Model abstrato base para multi-tenant"""
    clinica_id = models.IntegerField(db_index=True)
    
    class Meta:
        abstract = True
    
    @classmethod
    def filter_by_clinica(cls, clinica_id):
        """Filtra registros pela clínica"""
        return cls.objects.filter(clinica_id=clinica_id)


# ============================================
# MODEL PACIENTE
# ============================================

class Paciente(TenantModel):
    """Model de Paciente"""
    
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ]
    
    CONVENIO_CHOICES = [
        ('PARTICULAR', 'Particular'),
        ('UNIMED', 'Unimed'),
        ('BRADESCO SAUDE', 'Bradesco Saúde'),
        ('SULAMERICA', 'SulAmérica'),
        ('AMIL', 'Amil'),
        ('HAPVIDA', 'Hapvida'),
        ('NOTREDAME INTERMEDICA', 'NotreDame Intermédica'),
        ('PREVENT SENIOR', 'Prevent Senior'),
        ('OUTRO', 'Outro'),
    ]
    
    # Dados pessoais
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    profissao = models.CharField(max_length=100, blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    convenio = models.CharField(max_length=50, choices=CONVENIO_CHOICES)
    
    # Contato
    telefone_celular = models.CharField(max_length=20)
    telefone_fixo = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Endereço
    cep = models.CharField(max_length=10)
    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    
    # Status
    ativo = models.BooleanField(default=True)
    
    # Auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'pacientes'
        ordering = ['nome_completo']
        indexes = [
            models.Index(fields=['clinica_id', 'ativo']),
            models.Index(fields=['cpf']),
        ]
    
    def __str__(self):
        return f"{self.nome_completo} - CPF: {self.cpf}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        # Validar CPF
        if self.cpf and not Validador.validar_cpf(self.cpf):
            errors['cpf'] = 'CPF inválido'
        
        # Validar email
        if self.email and not Validador.validar_email_format(self.email):
            errors['email'] = 'Email inválido'
        
        # Validar data de nascimento
        if self.data_nascimento and self.data_nascimento > date.today():
            errors['data_nascimento'] = 'Data de nascimento não pode ser futura'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Formatar campos antes de salvar
        if self.cpf:
            self.cpf = Validador.formatar_cpf(self.cpf)
        if self.telefone_celular:
            self.telefone_celular = Validador.formatar_telefone(self.telefone_celular)
        if self.telefone_fixo:
            self.telefone_fixo = Validador.formatar_telefone(self.telefone_fixo)
        if self.cep:
            self.cep = Validador.formatar_cep(self.cep)
        if self.nome_completo:
            self.nome_completo = self.nome_completo.title()
        if self.email:
            self.email = self.email.lower()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def idade(self):
        """Calcula a idade do paciente"""
        if self.data_nascimento:
            hoje = date.today()
            idade = hoje.year - self.data_nascimento.year
            if hoje.month < self.data_nascimento.month or \
               (hoje.month == self.data_nascimento.month and hoje.day < self.data_nascimento.day):
                idade -= 1
            return idade
        return 0
    
    @property
    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        endereco = f"{self.logradouro}, {self.numero}"
        if self.complemento:
            endereco += f" - {self.complemento}"
        endereco += f", {self.bairro} - {self.cidade}/{self.estado} - CEP: {self.cep}"
        return endereco
    
    def get_historico_consultas(self):
        """Retorna histórico de consultas do paciente"""
        return self.consultas.all().order_by('-data_consulta')
    
    def get_historico_exames(self):
        """Retorna histórico de exames do paciente"""
        return self.exames.all().order_by('-data_exame')
    
# ============================================
# MODEL AGENDAMENTO
# ============================================

class Agendamento(TenantModel):
    """Model de Agendamento"""
    
    STATUS_CHOICES = [
        ('Agendado', 'Agendado'),
        ('Confirmado', 'Confirmado'),
        ('Realizado', 'Realizado'),
        ('Cancelado', 'Cancelado'),
        ('Faltou', 'Faltou'),
    ]
    
    SERVICO_CHOICES = [
        ('Consulta', 'Consulta'),
        ('Exame', 'Exame'),
    ]
    
    TIPO_CONSULTA_CHOICES = [
        ('Primeira Consulta', 'Primeira Consulta'),
        ('Revisão', 'Revisão'),
        ('Consulta de Urgência', 'Consulta de Urgência'),
    ]
    
    # Relacionamentos
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='agendamentos'
    )
    
    # Dados do agendamento (desnormalizados para performance)
    paciente_nome = models.CharField(max_length=200)
    paciente_cpf = models.CharField(max_length=14)
    convenio = models.CharField(max_length=50)
    
    # Tipo de serviço
    servico = models.CharField(max_length=20, choices=SERVICO_CHOICES)
    tipo = models.CharField(max_length=50)
    
    # Data e hora
    data = models.DateField()
    hora = models.TimeField()
    
    # Financeiro
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Observações
    observacoes = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Agendado')
    
    # Auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'agendamentos'
        ordering = ['-data', '-hora']
        indexes = [
            models.Index(fields=['clinica_id', 'data', 'hora']),
            models.Index(fields=['clinica_id', 'status']),
            models.Index(fields=['paciente']),
        ]
        unique_together = [['clinica_id', 'data', 'hora']]
    
    def __str__(self):
        return f"{self.servico} - {self.paciente_nome} - {self.data} {self.hora}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        # Validar se a data não é passada para novos agendamentos
        if not self.pk and self.data and self.data < date.today():
            errors['data'] = 'Não é possível agendar para datas passadas'
        
        # Validar se o paciente pertence à mesma clínica
        if self.paciente and self.paciente.clinica_id != self.clinica_id:
            errors['paciente'] = 'Paciente não pertence a esta clínica'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Preencher dados do paciente automaticamente
        if self.paciente:
            self.paciente_nome = self.paciente.nome_completo
            self.paciente_cpf = self.paciente.cpf
            if not self.convenio:
                self.convenio = self.paciente.convenio
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def verificar_disponibilidade(cls, clinica_id, data, hora, excluir_id=None):
        """Verifica se um horário está disponível"""
        query = cls.objects.filter(
            clinica_id=clinica_id,
            data=data,
            hora=hora
        ).exclude(status__in=['Cancelado', 'Realizado'])
        
        if excluir_id:
            query = query.exclude(id=excluir_id)
        
        return not query.exists()
    
    @classmethod
    def obter_proximos_agendamentos(cls, clinica_id, limite=10):
        """Obtém os próximos agendamentos"""
        hoje = date.today()
        return cls.objects.filter(
            clinica_id=clinica_id,
            data__gte=hoje,
            status__in=['Agendado', 'Confirmado']
        ).order_by('data', 'hora')[:limite]


# ============================================
# MODEL CONSULTA
# ============================================

class Consulta(TenantModel):
    """Model de Consulta"""
    
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('confirmada', 'Confirmada'),
        ('em_atendimento', 'Em Atendimento'),
        ('gravando', 'Gravando Consulta'),
        ('transcrevendo', 'Transcrevendo'),
        ('gerando_documentos', 'Gerando Documentos'),
        ('aguardando_revisao', 'Aguardando Revisão'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
        ('faltou', 'Faltou'),
    ]
    
    TIPO_CHOICES = [
        ('primeira_consulta', 'Primeira Consulta'),
        ('retorno', 'Retorno'),
        ('emergencia', 'Emergência'),
        ('teleconsulta', 'Teleconsulta'),
        ('avaliacao', 'Avaliação'),
        ('procedimento', 'Procedimento'),
    ]
    
    # Relacionamentos
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='consultas'
    )
    
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas'
    )
    
    # Dados da consulta
    data_consulta = models.DateTimeField()
    tipo_consulta = models.CharField(max_length=30, choices=TIPO_CHOICES, default='primeira_consulta')
    duracao_minutos = models.IntegerField(null=True, blank=True, help_text="Duração da consulta em minutos")
    
    # Informações clínicas
    queixa_principal = models.TextField(blank=True, null=True)
    historia_doenca_atual = models.TextField(blank=True, null=True)
    anamnese = models.TextField(blank=True, null=True)
    exame_fisico = models.TextField(blank=True, null=True)
    hipotese_diagnostica = models.TextField(blank=True, null=True)
    diagnostico = models.TextField(blank=True, null=True)
    conduta = models.TextField(blank=True, null=True)
    prescricao = models.TextField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    
    # Gravação e transcrição
    audio_consulta = models.TextField(blank=True, null=True, help_text="Áudio da consulta em base64")
    audio_duracao_segundos = models.IntegerField(null=True, blank=True)
    audio_formato = models.CharField(max_length=20, blank=True, null=True, help_text="webm, mp3, wav, etc")
    
    transcricao_completa = models.TextField(blank=True, null=True, help_text="Transcrição completa da consulta")
    transcricao_ia = models.TextField(blank=True, null=True, help_text="Transcrição formatada pela IA")
    transcricao_medico = models.TextField(blank=True, null=True, help_text="Falas do médico")
    transcricao_paciente = models.TextField(blank=True, null=True, help_text="Falas do paciente")
    confianca_transcricao = models.FloatField(null=True, blank=True)
    tempo_processamento_transcricao = models.FloatField(null=True, blank=True)
    
    # Documentos gerados
    documentos_gerados = models.JSONField(default=list, blank=True, help_text="Lista de documentos gerados")
    # Estrutura: [{"tipo": "atestado", "conteudo": "...", "editado": false, "data_geracao": "..."}]
    
    atestado_medico = models.TextField(blank=True, null=True)
    anamnese_documento = models.TextField(blank=True, null=True)
    evolucao_medica = models.TextField(blank=True, null=True)
    prescricao_documento = models.TextField(blank=True, null=True)
    relatorio_medico = models.TextField(blank=True, null=True)
    
    # Médico responsável
    medico_responsavel = models.CharField(max_length=200, blank=True, null=True)
    medico_crm = models.CharField(max_length=20, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='agendada')
    
    # Auditoria
    data_inicio_atendimento = models.DateTimeField(null=True, blank=True)
    data_fim_atendimento = models.DateTimeField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'consultas'
        ordering = ['-data_consulta']
        indexes = [
            models.Index(fields=['clinica_id', 'paciente']),
            models.Index(fields=['clinica_id', 'data_consulta']),
            models.Index(fields=['clinica_id', 'status']),
        ]
    
    def __str__(self):
        return f"Consulta - {self.paciente.nome_completo} - {self.data_consulta.strftime('%d/%m/%Y %H:%M')}"
    
    def clean(self):
        """Validações customizadas"""
        if self.paciente and self.paciente.clinica_id != self.clinica_id:
            raise ValidationError({'paciente': 'Paciente não pertence a esta clínica'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def iniciar_atendimento(self):
        """Marca início do atendimento"""
        self.status = 'em_atendimento'
        self.data_inicio_atendimento = timezone.now()
        self.save(update_fields=['status', 'data_inicio_atendimento'])
    
    def finalizar_atendimento(self):
        """Marca fim do atendimento"""
        self.status = 'finalizada'
        self.data_fim_atendimento = timezone.now()
        
        if self.data_inicio_atendimento:
            duracao = (self.data_fim_atendimento - self.data_inicio_atendimento).total_seconds() / 60
            self.duracao_minutos = int(duracao)
        
        self.save(update_fields=['status', 'data_fim_atendimento', 'duracao_minutos'])

# ============================================
# MODEL EXAME
# ============================================

class Exame(TenantModel):
    """Model de Exame"""
    
    STATUS_CHOICES = [
        ('solicitado', 'Solicitado'),
        ('agendado', 'Agendado'),
        ('realizado', 'Realizado'),
        ('enviado_ia', 'Enviado para IA'),
        ('processando_ia', 'Processando IA'),
        ('interpretado_ia', 'Interpretado por IA'),
        ('revisado_medico', 'Revisado por Médico'),
        ('finalizado', 'Finalizado'),
        ('erro_ia', 'Erro na IA'),
        ('cancelado', 'Cancelado'),
    ]
    
    TIPO_CHOICES = [
        ('hemograma', 'Hemograma'),
        ('glicemia', 'Glicemia'),
        ('colesterol_total', 'Colesterol Total'),
        ('urinalise', 'Urinálise'),
        ('raio_x', 'Raio-X'),
        ('ultrassonografia', 'Ultrassonografia'),
        ('tomografia', 'Tomografia'),
        ('ressonancia', 'Ressonância'),
        ('eletrocardiograma', 'Eletrocardiograma'),
        ('ecocardiograma', 'Ecocardiograma'),
        ('endoscopia', 'Endoscopia'),
        ('colonoscopia', 'Colonoscopia'),
        ('mamografia', 'Mamografia'),
        ('densitometria', 'Densitometria Óssea'),
        ('espirometria', 'Espirometria'),
        ('outros', 'Outros'),
    ]
    
    # Relacionamentos
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='exames'
    )
    
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exames'
    )
    
    # Dados do exame
    tipo_exame = models.CharField(max_length=50, choices=TIPO_CHOICES)
    tipo_exame_identificado_ia = models.CharField(max_length=100, blank=True, null=True, help_text="Tipo identificado pela IA")
    data_exame = models.DateField()
    data_resultado = models.DateField(null=True, blank=True)
    
    # Arquivos e resultados
    arquivo_exame = models.TextField(blank=True, null=True, help_text="Path ou base64 do arquivo")
    arquivo_nome = models.CharField(max_length=255, blank=True, null=True)
    arquivo_tipo = models.CharField(max_length=50, blank=True, null=True, help_text="image/png, application/pdf, etc")
    
    resultado_original = models.TextField(blank=True, null=True)
    
    # Interpretação IA
    interpretacao_ia = models.TextField(blank=True, null=True, help_text="Laudo completo gerado pela IA")
    confianca_ia = models.FloatField(null=True, blank=True, help_text="Nível de confiança da IA (0-1)")
    fontes_consultadas = models.TextField(blank=True, null=True, help_text="Fontes médicas consultadas pela IA")
    tempo_processamento = models.FloatField(null=True, blank=True, help_text="Tempo de processamento em segundos")
    erro_ia = models.TextField(blank=True, null=True, help_text="Mensagem de erro caso ocorra")
    
    # Revisão médica
    revisado_por_medico = models.BooleanField(default=False)
    medico_revisor_nome = models.CharField(max_length=200, blank=True, null=True)
    medico_revisor_crm = models.CharField(max_length=20, blank=True, null=True)
    data_revisao = models.DateTimeField(null=True, blank=True)
    observacoes_medico = models.TextField(blank=True, null=True, help_text="Observações do médico revisor")
    
    # Outros profissionais
    medico_solicitante = models.CharField(max_length=200, blank=True, null=True)
    medico_solicitante_crm = models.CharField(max_length=20, blank=True, null=True)
    laboratorio = models.CharField(max_length=200, blank=True, null=True)
    
    observacoes = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='solicitado')
    
    # Auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'exames'
        ordering = ['-data_exame']
        indexes = [
            models.Index(fields=['clinica_id', 'paciente']),
            models.Index(fields=['clinica_id', 'data_exame']),
            models.Index(fields=['clinica_id', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_exame_display()} - {self.paciente.nome_completo} - {self.data_exame}"
    
    def clean(self):
        """Validações customizadas"""
        if self.paciente and self.paciente.clinica_id != self.clinica_id:
            raise ValidationError({'paciente': 'Paciente não pertence a esta clínica'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# ============================================
# MODEL CATEGORIA RECEITA
# ============================================

class CategoriaReceita(TenantModel):
    """Model de Categoria de Receita"""
    
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    cor = models.CharField(max_length=7, default='#4CAF50', help_text="Cor em hex (#RRGGBB)")
    ativo = models.BooleanField(default=True)
    
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'categorias_receitas'
        ordering = ['nome']
        unique_together = [['clinica_id', 'nome']]
        indexes = [
            models.Index(fields=['clinica_id', 'ativo']),
        ]
    
    def __str__(self):
        return self.nome

# ============================================
# MODEL CATEGORIA DESPESA
# ============================================

class CategoriaDespesa(TenantModel):
    """Model de Categoria de Despesa"""
    
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    cor = models.CharField(max_length=7, default='#F44336', help_text="Cor em hex (#RRGGBB)")
    ativo = models.BooleanField(default=True)
    
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'categorias_despesas'
        ordering = ['nome']
        unique_together = [['clinica_id', 'nome']]
        indexes = [
            models.Index(fields=['clinica_id', 'ativo']),
        ]
    
    def __str__(self):
        return self.nome

# ============================================
# MODEL RECEITA
# ============================================

class Receita(TenantModel):
    """Model de Receita"""
    
    STATUS_CHOICES = [
        ('a_receber', 'A Receber'),
        ('recebida', 'Recebida'),
        ('vencida', 'Vencida'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('Dinheiro', 'Dinheiro'),
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('Cartão de Débito', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('Transferência Bancária', 'Transferência Bancária'),
        ('Boleto', 'Boleto'),
        ('Cheque', 'Cheque'),
        ('Convênio', 'Convênio'),
    ]
    
    # Relacionamentos
    categoria = models.ForeignKey(
        CategoriaReceita,
        on_delete=models.PROTECT,
        related_name='receitas',
        null=True,
        blank=True
    )
    
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receitas'
    )
    
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='receitas'
    )
    
    # Dados financeiros
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField()
    data_recebimento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='a_receber')
    forma_pagamento = models.CharField(max_length=30, choices=FORMA_PAGAMENTO_CHOICES, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    
    # Auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'receitas'
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['clinica_id', 'status']),
            models.Index(fields=['clinica_id', 'data_vencimento']),
            models.Index(fields=['paciente']),
            models.Index(fields=['agendamento']),
        ]
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor} - {self.data_vencimento}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        if self.valor and self.valor <= 0:
            errors['valor'] = 'Valor deve ser maior que zero'
        
        if self.paciente and self.paciente.clinica_id != self.clinica_id:
            errors['paciente'] = 'Paciente não pertence a esta clínica'
        
        if self.categoria and self.categoria.clinica_id != self.clinica_id:
            errors['categoria'] = 'Categoria não pertence a esta clínica'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Atualizar status automaticamente baseado nas datas
        if self.status == 'a_receber' and self.data_vencimento < date.today():
            self.status = 'vencida'
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def marcar_como_recebida(self, data_recebimento=None, forma_pagamento=None):
        """Marca a receita como recebida"""
        self.status = 'recebida'
        self.data_recebimento = data_recebimento or date.today()
        if forma_pagamento:
            self.forma_pagamento = forma_pagamento
        self.save()
    
    @classmethod
    def atualizar_status_vencidos(cls, clinica_id):
        """Atualiza status de receitas vencidas"""
        hoje = date.today()
        cls.objects.filter(
            clinica_id=clinica_id,
            status='a_receber',
            data_vencimento__lt=hoje
        ).update(status='vencida')

# ============================================
# MODEL DESPESA
# ============================================

class Despesa(TenantModel):
    """Model de Despesa"""
    
    STATUS_CHOICES = [
        ('a_pagar', 'A Pagar'),
        ('paga', 'Paga'),
        ('vencida', 'Vencida'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('Dinheiro', 'Dinheiro'),
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('Cartão de Débito', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('Transferência Bancária', 'Transferência Bancária'),
        ('Boleto', 'Boleto'),
        ('Cheque', 'Cheque'),
    ]
    
    # Relacionamentos
    categoria = models.ForeignKey(
        CategoriaDespesa,
        on_delete=models.PROTECT,
        related_name='despesas',
        null=True,
        blank=True
    )
    
    # Dados financeiros
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='a_pagar')
    fornecedor = models.CharField(max_length=200, blank=True, null=True)
    forma_pagamento = models.CharField(max_length=30, choices=FORMA_PAGAMENTO_CHOICES, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    
    # Auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'despesas'
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['clinica_id', 'status']),
            models.Index(fields=['clinica_id', 'data_vencimento']),
        ]
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor} - {self.data_vencimento}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        if self.valor and self.valor <= 0:
            errors['valor'] = 'Valor deve ser maior que zero'
        
        if self.categoria and self.categoria.clinica_id != self.clinica_id:
            errors['categoria'] = 'Categoria não pertence a esta clínica'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Atualizar status automaticamente baseado nas datas
        if self.status == 'a_pagar' and self.data_vencimento < date.today():
            self.status = 'vencida'
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def marcar_como_paga(self, data_pagamento=None, forma_pagamento=None):
        """Marca a despesa como paga"""
        self.status = 'paga'
        self.data_pagamento = data_pagamento or date.today()
        if forma_pagamento:
            self.forma_pagamento = forma_pagamento
        self.save()
    
    @classmethod
    def atualizar_status_vencidos(cls, clinica_id):
        """Atualiza status de despesas vencidas"""
        hoje = date.today()
        cls.objects.filter(
            clinica_id=clinica_id,
            status='a_pagar',
            data_vencimento__lt=hoje
        ).update(status='vencida')

# ============================================
# MODEL TRANSCRIÇÃO
# ============================================

class Transcricao(TenantModel):
    """Model de Transcrição de Áudio de Consultas"""
    
    STATUS_CHOICES = [
        ('aguardando', 'Aguardando'),
        ('processando', 'Processando'),
        ('concluida', 'Concluída'),
        ('erro', 'Erro'),
    ]
    
    TIPO_CHOICES = [
        ('tempo_real', 'Tempo Real'),
        ('arquivo', 'Arquivo'),
    ]
    
    # Relacionamentos
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='transcricoes'
    )
    
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='transcricoes'
    )
    
    # Dados da transcrição
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='tempo_real')
    
    # Áudio
    arquivo_audio = models.TextField(blank=True, null=True, help_text="Path ou base64 do arquivo de áudio")
    duracao_segundos = models.IntegerField(null=True, blank=True, help_text="Duração do áudio em segundos")
    formato_audio = models.CharField(max_length=10, blank=True, null=True, help_text="mp3, wav, ogg, etc")
    
    # Transcrição
    texto_transcrito = models.TextField(blank=True, null=True, help_text="Texto transcrito pelo Gemini")
    confianca = models.FloatField(null=True, blank=True, help_text="Nível de confiança da transcrição (0-1)")
    
    # Processamento IA
    resumo_ia = models.TextField(blank=True, null=True, help_text="Resumo gerado pela IA")
    palavras_chave = models.TextField(blank=True, null=True, help_text="Palavras-chave identificadas")
    sentimento = models.CharField(max_length=50, blank=True, null=True, help_text="Análise de sentimento")
    
    # Extração de informações médicas
    sintomas_identificados = models.TextField(blank=True, null=True, help_text="Sintomas mencionados")
    medicamentos_mencionados = models.TextField(blank=True, null=True, help_text="Medicamentos citados")
    diagnostico_sugerido = models.TextField(blank=True, null=True, help_text="Diagnóstico sugerido pela IA")
    
    # Status e metadados
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aguardando')
    erro_mensagem = models.TextField(blank=True, null=True)
    tempo_processamento = models.FloatField(null=True, blank=True, help_text="Tempo de processamento em segundos")
    
    # Médico responsável
    medico_nome = models.CharField(max_length=200, blank=True, null=True)
    
    # Auditoria
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'transcricoes'
        ordering = ['-data_inicio']
        indexes = [
            models.Index(fields=['clinica_id', 'consulta']),
            models.Index(fields=['clinica_id', 'paciente']),
            models.Index(fields=['clinica_id', 'status']),
            models.Index(fields=['data_inicio']),
        ]
    
    def __str__(self):
        return f"Transcrição - {self.paciente.nome_completo} - {self.data_inicio.strftime('%d/%m/%Y %H:%M')}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        if self.consulta and self.consulta.clinica_id != self.clinica_id:
            errors['consulta'] = 'Consulta não pertence a esta clínica'
        
        if self.paciente and self.paciente.clinica_id != self.clinica_id:
            errors['paciente'] = 'Paciente não pertence a esta clínica'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def marcar_como_processando(self):
        """Marca transcrição como em processamento"""
        self.status = 'processando'
        self.save(update_fields=['status', 'data_atualizacao'])
    
    def marcar_como_concluida(self, tempo_processamento=None):
        """Marca transcrição como concluída"""
        self.status = 'concluida'
        self.data_conclusao = timezone.now()
        if tempo_processamento:
            self.tempo_processamento = tempo_processamento
        self.save(update_fields=['status', 'data_conclusao', 'tempo_processamento', 'data_atualizacao'])
    
    def marcar_como_erro(self, mensagem_erro):
        """Marca transcrição com erro"""
        self.status = 'erro'
        self.erro_mensagem = mensagem_erro
        self.data_conclusao = timezone.now()
        self.save(update_fields=['status', 'erro_mensagem', 'data_conclusao', 'data_atualizacao'])
    
    async def processar_com_gemini(self, audio_base64=None, audio_path=None):
        """
        Processa áudio com Google Gemini
        
        Args:
            audio_base64: Áudio em base64
            audio_path: Caminho do arquivo de áudio
        """
        import time
        inicio = time.time()
        
        try:
            self.marcar_como_processando()
            
            # Verificar se Gemini está configurado
            if not Config.configure_gemini():
                raise Exception("API Gemini não configurada")
            
            # Preparar o modelo
            model = genai.GenerativeModel(Config.GEMINI_MODEL)
            
            # Preparar prompt para contexto médico
            prompt = """
            Você é um assistente médico especializado em transcrever e analisar consultas médicas.
            
            Transcreva o áudio da consulta médica e forneça:
            
            1. TRANSCRIÇÃO COMPLETA do diálogo
            2. RESUMO CLÍNICO (principais pontos da consulta)
            3. SINTOMAS identificados
            4. MEDICAMENTOS mencionados
            5. PALAVRAS-CHAVE relevantes
            6. POSSÍVEL DIAGNÓSTICO (baseado apenas no que foi mencionado)
            
            Formate a resposta em JSON com as chaves:
            - transcricao: texto completo
            - resumo: resumo clínico
            - sintomas: lista de sintomas
            - medicamentos: lista de medicamentos
            - palavras_chave: lista de palavras-chave
            - diagnostico_sugerido: possível diagnóstico
            
            Seja preciso, objetivo e mantenha terminologia médica quando apropriado.
            """
            
            # Processar áudio
            if audio_base64:
                # Decodificar base64
                audio_data = base64.b64decode(audio_base64)
                # Aqui você processaria com Gemini
                # Por enquanto, simulação de resposta
                response_text = await self._simular_processamento_gemini(prompt, audio_data)
            elif audio_path:
                # Ler arquivo de áudio
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                response_text = await self._simular_processamento_gemini(prompt, audio_data)
            else:
                raise Exception("Nenhum áudio fornecido")
            
            # Parsear resposta JSON
            try:
                resultado = json.loads(response_text)
                
                self.texto_transcrito = resultado.get('transcricao', '')
                self.resumo_ia = resultado.get('resumo', '')
                self.sintomas_identificados = json.dumps(resultado.get('sintomas', []), ensure_ascii=False)
                self.medicamentos_mencionados = json.dumps(resultado.get('medicamentos', []), ensure_ascii=False)
                self.palavras_chave = json.dumps(resultado.get('palavras_chave', []), ensure_ascii=False)
                self.diagnostico_sugerido = resultado.get('diagnostico_sugerido', '')
                self.confianca = 0.95  # Simular confiança alta
                
                # Atualizar consulta relacionada
                if self.consulta:
                    self.consulta.transcricao_ia = self.texto_transcrito
                    self.consulta.save(update_fields=['transcricao_ia'])
                
            except json.JSONDecodeError:
                # Se não for JSON válido, salvar como texto simples
                self.texto_transcrito = response_text
            
            # Calcular tempo de processamento
            tempo_total = time.time() - inicio
            self.marcar_como_concluida(tempo_total)
            
            return True
            
        except Exception as e:
            self.marcar_como_erro(str(e))
            return False
    
    async def _simular_processamento_gemini(self, prompt, audio_data):
        """
        Simulação de processamento - substituir por chamada real ao Gemini
        """
        # Em produção, aqui seria a chamada real:
        # response = await model.generate_content([prompt, audio_data])
        # return response.text
        
        # Simulação para desenvolvimento
        await asyncio.sleep(2)  # Simular processamento
        
        return json.dumps({
            "transcricao": "Médico: Bom dia, como está se sentindo?\nPaciente: Doutor, estou com dor de cabeça há 3 dias e febre baixa.\nMédico: Entendo. Vou prescrever um analgésico e solicitar exames.",
            "resumo": "Paciente relata cefaleia há 3 dias associada a febre baixa. Conduta: prescrição de analgésico e solicitação de exames complementares.",
            "sintomas": ["dor de cabeça", "febre baixa", "cefaleia"],
            "medicamentos": ["analgésico"],
            "palavras_chave": ["dor", "febre", "exames", "analgésico"],
            "diagnostico_sugerido": "Possível quadro viral. Necessário acompanhamento e exames para descartar outras causas."
        }, ensure_ascii=False)

# ============================================
# MODELS - CLÍNICAS E USUÁRIOS
# ============================================

class Clinica(models.Model):
    """Model de Clínica/Consultório"""
    
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('suspensa', 'Suspensa'),
    ]
    
    # Dados da clínica
    nome = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Endereço
    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=10)
    
    # Responsável
    responsavel_nome = models.CharField(max_length=200)
    responsavel_cpf = models.CharField(max_length=14)
    responsavel_telefone = models.CharField(max_length=20)
    responsavel_email = models.EmailField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    
    # Auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'clinicas'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class Usuario(models.Model):
    """Model de Usuário"""
    
    FUNCAO_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Administrador'),
        ('medico', 'Médico'),
        ('secretaria', 'Secretária'),
    ]
    
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('alerta', 'Alerta'),
    ]
    
    # Relacionamento
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE,
        related_name='usuarios',
        null=True,
        blank=True
    )
    
    # Dados pessoais
    nome_completo = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    password = models.CharField(max_length=255)  # Hash da senha
    data_nascimento = models.DateField()
    telefone_celular = models.CharField(max_length=20)
    
    # Função
    funcao = models.CharField(max_length=20, choices=FUNCAO_CHOICES)
    
    # Campos específicos para médicos
    crm = models.CharField(max_length=20, blank=True, null=True)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    
    # Auditoria
    last_login = models.DateTimeField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        db_table = 'usuarios'
        ordering = ['nome_completo']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['cpf']),
        ]
    
    def __str__(self):
        return f"{self.nome_completo} - {self.get_funcao_display()}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        # Validar CPF
        if self.cpf and not Validador.validar_cpf(self.cpf):
            errors['cpf'] = 'CPF inválido'
        
        # Médico deve ter CRM e especialidade
        if self.funcao == 'medico' and (not self.crm or not self.especialidade):
            errors['crm'] = 'Médicos devem ter CRM e especialidade'
        
        # Super admin não pode ter clínica
        if self.funcao == 'super_admin' and self.clinica:
            errors['clinica'] = 'Super admin não pode estar vinculado a uma clínica'
        
        # Outros usuários devem ter clínica
        if self.funcao != 'super_admin' and not self.clinica:
            errors['clinica'] = 'Usuário deve estar vinculado a uma clínica'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Formatar campos
        if self.cpf:
            self.cpf = Validador.formatar_cpf(self.cpf)
        if self.telefone_celular:
            self.telefone_celular = Validador.formatar_telefone(self.telefone_celular)
        if self.email:
            self.email = self.email.lower()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def set_password(self, raw_password):
        """Define senha com hash"""
        import hashlib
        self.password = hashlib.sha256(raw_password.encode()).hexdigest()
    
    def check_password(self, raw_password):
        """Verifica senha"""
        import hashlib
        return self.password == hashlib.sha256(raw_password.encode()).hexdigest()
    
    def generate_jwt_token(self):
        """Gera token JWT para o usuário"""
        from datetime import timedelta
        from django.utils import timezone
    
        agora = timezone.now()
    
        payload = {
            'sub': str(self.id),
            'email': self.email,
            'nome': self.nome_completo,
            'funcao': self.funcao,
            'clinica_id': self.clinica_id if self.clinica else None,
            'exp': agora + timedelta(hours=24),
            'iat': agora
        }
    
        token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
        return token

# ============================================
# SERIALIZERS - CLÍNICAS E USUÁRIOS
# ============================================

class ClinicaSerializer(serializers.ModelSerializer):
    """Serializer para Clínica"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_usuarios = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinica
        fields = [
            'id', 'nome', 'cnpj', 'telefone', 'email',
            'logradouro', 'numero', 'bairro', 'cidade', 'estado', 'cep',
            'responsavel_nome', 'responsavel_cpf', 'responsavel_telefone', 'responsavel_email',
            'status', 'status_display', 'total_usuarios',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ['id', 'data_cadastro', 'data_atualizacao']
    
    def get_total_usuarios(self, obj):
        return obj.usuarios.count()
    
    def to_representation(self, instance):
        """Formatar saída para compatibilidade com admin_panel"""
        data = super().to_representation(instance)
        
        # Formatar endereço
        data['endereco'] = {
            'logradouro': instance.logradouro,
            'numero': instance.numero,
            'bairro': instance.bairro,
            'cidade': instance.cidade,
            'estado': instance.estado,
            'cep': instance.cep
        }
        
        # Formatar responsável
        data['responsavel'] = {
            'nome': instance.responsavel_nome,
            'cpf': instance.responsavel_cpf,
            'telefone': instance.responsavel_telefone,
            'email': instance.responsavel_email
        }
        
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para Usuário"""
    
    funcao_display = serializers.CharField(source='get_funcao_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    clinica_nome = serializers.CharField(source='clinica.nome', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'clinica', 'clinica_id', 'clinica_nome', 'nome_completo', 'email', 
            'cpf', 'password', 'data_nascimento', 'telefone_celular',
            'funcao', 'funcao_display', 'crm', 'especialidade',
            'status', 'status_display', 'last_login',
            'data_cadastro', 'data_atualizacao'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},  # ← ADICIONE required=False
        }
        read_only_fields = ['id', 'last_login', 'data_cadastro', 'data_atualizacao']
    
    def validate_cpf(self, value):
        """Validar CPF"""
        if not Validador.validar_cpf(value):
            raise serializers.ValidationError("CPF inválido")
        
        cpf_formatado = Validador.formatar_cpf(value)
        query = Usuario.objects.filter(cpf=cpf_formatado)
        
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise serializers.ValidationError("CPF já cadastrado")
        
        return value
    
    def validate_email(self, value):
        """Validar email"""
        query = Usuario.objects.filter(email=value.lower())
        
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise serializers.ValidationError("Email já cadastrado")
        
        return value
    
    def validate(self, data):
        """Validações gerais"""
        # Médico deve ter CRM e especialidade
        if data.get('funcao') == 'medico':
            if not data.get('crm') or not data.get('especialidade'):
                raise serializers.ValidationError({
                    'crm': 'Médicos devem ter CRM e especialidade'
                })
        
        return data
    
    def create(self, validated_data):
        """Criar usuário com senha hasheada"""
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario
    
    def update(self, instance, validated_data):  # ← ADICIONE ESTE MÉTODO
        """Atualizar usuário"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Só atualizar senha se foi fornecida
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    """Serializer para Login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

# ============================================
# FUNÇÃO PARA INTERPRETAR EXAME COM GEMINI
# ============================================

async def interpretar_exame_com_gemini(exame_id):
    """
    Interpreta exame médico usando Google Gemini Vision
    
    Args:
        exame_id: ID do exame a ser interpretado
    
    Returns:
        dict com resultado da interpretação
    """
    import time
    import mimetypes
    
    inicio = time.time()
    
    try:
        exame = Exame.objects.get(id=exame_id)
        
        # Marcar como processando
        exame.status = 'processando_ia'
        exame.save(update_fields=['status'])
        
        # Verificar se Gemini está configurado
        if not Config.GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY não configurada no .env")
        
        if not genai:
            raise Exception("Biblioteca google-generativeai não instalada")
        
        # Configurar Gemini
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Usar modelo com visão para imagens
        if exame.arquivo_tipo and 'image' in exame.arquivo_tipo:
            model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Preparar prompt médico detalhado
        prompt = f"""
Você é um sistema de apoio diagnóstico médico especializado. Sua função é interpretar exames médicos com rigor científico.

IMPORTANTE:
- Você deve fornecer uma interpretação técnica baseada APENAS em fontes médicas confiáveis
- Sempre indique que esta é uma interpretação por IA e requer validação médica
- Cite as referências médicas utilizadas (sociedades médicas, guidelines, literatura científica)
- Seja claro sobre limitações e incertezas
- Use terminologia médica apropriada

PACIENTE:
Nome: {exame.paciente.nome_completo}
Idade: {exame.paciente.idade} anos
Sexo: {exame.paciente.get_sexo_display()}

EXAME SOLICITADO: {exame.get_tipo_exame_display()}
Data do Exame: {exame.data_exame.strftime('%d/%m/%Y')}

TAREFA:
1. IDENTIFIQUE o tipo exato de exame apresentado
2. ANALISE todos os parâmetros e resultados visíveis
3. INTERPRETE os achados considerando:
   - Valores de referência padrão
   - Idade e sexo do paciente
   - Correlações clínicas relevantes
4. FORNEÇA um laudo estruturado contendo:
   - Tipo de exame identificado
   - Técnica utilizada (se aplicável)
   - Descrição dos achados
   - Impressão diagnóstica
   - Sugestões de conduta (quando apropriado)
   - Nível de confiança da interpretação (0-100%)

5. CITE as fontes médicas consultadas (sociedades médicas, guidelines, estudos)

FORMATO DA RESPOSTA (JSON):
{{
    "tipo_exame_identificado": "nome do exame",
    "confianca": 0.95,
    "tecnica": "descrição da técnica",
    "achados": "descrição detalhada dos achados",
    "impressao_diagnostica": "conclusão diagnóstica",
    "valores_alterados": ["lista de valores fora da normalidade"],
    "recomendacoes": "sugestões de conduta",
    "fontes_consultadas": ["Sociedade Brasileira de...", "Guidelines de...", etc],
    "observacoes": "limitações e considerações importantes",
    "requer_atencao_urgente": false
}}

Baseie sua análise em:
- Diretrizes da Sociedade Brasileira de Patologia Clínica
- Guidelines internacionais (AHA, ESC, etc)
- Valores de referência estabelecidos em literatura médica
- Correlações clínico-patológicas reconhecidas

PROCEDA COM A ANÁLISE:
"""
        
        # Preparar dados do arquivo
        if exame.arquivo_exame:
            # Arquivo está em base64
            if exame.arquivo_exame.startswith('data:'):
                # Remover prefixo data:
                base64_data = exame.arquivo_exame.split(',')[1]
                arquivo_bytes = base64.b64decode(base64_data)
            else:
                # Já é base64 puro
                arquivo_bytes = base64.b64decode(exame.arquivo_exame)
            
            # Determinar mime type
            mime_type = exame.arquivo_tipo or 'image/jpeg'
            
            # Preparar conteúdo para Gemini
            if 'image' in mime_type:
                # Processar imagem
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(arquivo_bytes))
                
                # Gerar interpretação
                response = model.generate_content([prompt, image])
            else:
                # Processar PDF ou texto
                # Para PDFs, o Gemini pode processar diretamente
                response = model.generate_content([
                    prompt,
                    {"mime_type": mime_type, "data": arquivo_bytes}
                ])
        else:
            raise Exception("Nenhum arquivo de exame disponível")
        
        # Processar resposta
        response_text = response.text
        
        # Tentar parsear JSON
        try:
            # Limpar markdown se houver
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            resultado = json.loads(response_text)
            
            # Montar laudo formatado
            laudo = f"""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                           LAUDO DE EXAME - INTERPRETAÇÃO POR IA                        ║
║                    ⚠️  ESTE LAUDO REQUER VALIDAÇÃO MÉDICA ⚠️                          ║
╚════════════════════════════════════════════════════════════════════════════════════════╝

DADOS DO PACIENTE:
Nome: {exame.paciente.nome_completo}
CPF: {exame.paciente.cpf}
Idade: {exame.paciente.idade} anos
Sexo: {exame.paciente.get_sexo_display()}

IDENTIFICAÇÃO DO EXAME:
Tipo: {resultado.get('tipo_exame_identificado', 'Não identificado')}
Data de Realização: {exame.data_exame.strftime('%d/%m/%Y')}
Técnica: {resultado.get('tecnica', 'Não especificada')}

───────────────────────────────────────────────────────────────────────────────────────

ACHADOS:
{resultado.get('achados', 'Nenhum achado descrito')}

───────────────────────────────────────────────────────────────────────────────────────

VALORES ALTERADOS:
{chr(10).join('• ' + valor for valor in resultado.get('valores_alterados', [])) if resultado.get('valores_alterados') else '• Nenhum valor significativamente alterado'}

───────────────────────────────────────────────────────────────────────────────────────

IMPRESSÃO DIAGNÓSTICA:
{resultado.get('impressao_diagnostica', 'Não especificada')}

───────────────────────────────────────────────────────────────────────────────────────

RECOMENDAÇÕES:
{resultado.get('recomendacoes', 'Consulte seu médico para avaliação completa')}

───────────────────────────────────────────────────────────────────────────────────────

OBSERVAÇÕES IMPORTANTES:
{resultado.get('observacoes', 'Nenhuma observação adicional')}

{'⚠️  ATENÇÃO: Este exame pode requerer avaliação médica urgente!' if resultado.get('requer_atencao_urgente') else ''}

───────────────────────────────────────────────────────────────────────────────────────

FONTES MÉDICAS CONSULTADAS:
{chr(10).join('• ' + fonte for fonte in resultado.get('fontes_consultadas', ['Diretrizes médicas padrão']))}

───────────────────────────────────────────────────────────────────────────────────────

NÍVEL DE CONFIANÇA DA IA: {float(resultado.get('confianca', 0)) * 100:.1f}%

───────────────────────────────────────────────────────────────────────────────────────

IMPORTANTE:
Esta interpretação foi gerada por Inteligência Artificial e deve ser utilizada apenas
como ferramenta de apoio diagnóstico. A validação e interpretação final devem ser
realizadas por médico habilitado.

Data da Interpretação: {timezone.now().strftime('%d/%m/%Y às %H:%M')}
Sistema: IntelliMed - Interpretação por IA (Google Gemini)

═══════════════════════════════════════════════════════════════════════════════════════

MÉDICO SOLICITANTE:
Dr. {exame.medico_solicitante or '[Não informado]'}
CRM: {exame.medico_solicitante_crm or '[Não informado]'}

═══════════════════════════════════════════════════════════════════════════════════════
"""
            
            # Atualizar exame
            exame.tipo_exame_identificado_ia = resultado.get('tipo_exame_identificado', '')
            exame.interpretacao_ia = laudo
            exame.confianca_ia = float(resultado.get('confianca', 0))
            exame.fontes_consultadas = json.dumps(resultado.get('fontes_consultadas', []), ensure_ascii=False)
            exame.status = 'interpretado_ia'
            exame.data_resultado = date.today()
            
        except json.JSONDecodeError:
            # Se não for JSON, usar resposta como texto simples
            exame.interpretacao_ia = f"""
LAUDO DE EXAME - INTERPRETAÇÃO POR IA
⚠️  ESTE LAUDO REQUER VALIDAÇÃO MÉDICA ⚠️

PACIENTE: {exame.paciente.nome_completo}
EXAME: {exame.get_tipo_exame_display()}
DATA: {exame.data_exame.strftime('%d/%m/%Y')}

{response_text}

───────────────────────────────────────────────────────────────────

IMPORTANTE: Esta interpretação foi gerada por IA e requer validação médica.
Data: {timezone.now().strftime('%d/%m/%Y às %H:%M')}
"""
            exame.confianca_ia = 0.75  # Confiança padrão quando não há JSON
            exame.status = 'interpretado_ia'
        
        # Calcular tempo de processamento
        tempo_total = time.time() - inicio
        exame.tempo_processamento = tempo_total
        exame.save()
        
        return {
            'sucesso': True,
            'exame_id': exame.id,
            'tempo_processamento': tempo_total,
            'status': exame.status
        }
        
    except Exame.DoesNotExist:
        return {
            'sucesso': False,
            'erro': 'Exame não encontrado'
        }
    except Exception as e:
        # Marcar exame com erro
        try:
            exame.status = 'erro_ia'
            exame.erro_ia = str(e)
            exame.save(update_fields=['status', 'erro_ia'])
        except:
            pass
        
        return {
            'sucesso': False,
            'erro': str(e)
        }

# ============================================
# FUNÇÃO DE TRANSCRIÇÃO DE CONSULTA COM IA
# ============================================

async def transcrever_consulta_com_gemini(consulta_id):
    """
    Transcreve consulta identificando falas do médico e paciente
    
    Args:
        consulta_id: ID da consulta
    
    Returns:
        dict com resultado da transcrição
    """
    import time
    
    inicio = time.time()
    
    try:
        consulta = Consulta.objects.get(id=consulta_id)
        
        # Marcar como transcrevendo
        consulta.status = 'transcrevendo'
        consulta.save(update_fields=['status'])
        
        # Verificar Gemini
        if not Config.GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY não configurada")
        
        if not genai:
            raise Exception("google-generativeai não instalado")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Preparar dados do paciente
        paciente = consulta.paciente
        
        # Prompt especializado para transcrição médica
        prompt = f"""
Você é um sistema especializado em transcrição de consultas médicas.

CONTEXTO DA CONSULTA:
Paciente: {paciente.nome_completo}
Idade: {paciente.idade} anos
Sexo: {paciente.get_sexo_display()}
Data da Consulta: {consulta.data_consulta.strftime('%d/%m/%Y')}
Tipo: {consulta.get_tipo_consulta_display()}
Médico: Dr. {consulta.medico_responsavel or '[Nome do médico]'}

TAREFA:
1. Transcreva todo o áudio da consulta médica
2. Identifique e separe as falas:
   - MÉDICO: geralmente quem pergunta, usa terminologia técnica, conduz a conversa
   - PACIENTE: geralmente quem responde, pode usar linguagem popular
   - ACOMPANHANTE: se houver outras pessoas presentes

3. Extraia informações estruturadas:
   - Queixa principal
   - História da doença atual
   - Exame físico realizado
   - Hipóteses diagnósticas mencionadas
   - Conduta proposta
   - Medicações prescritas

FORMATO DA RESPOSTA (JSON):
{{
    "transcricao_completa": "transcrição literal de toda a consulta",
    "dialogo": [
        {{"tipo": "medico", "texto": "Bom dia, como posso ajudar?"}},
        {{"tipo": "paciente", "texto": "Doutor, estou com dor de cabeça..."}},
        {{"tipo": "medico", "texto": "Há quanto tempo?"}},
        ...
    ],
    "resumo_estruturado": {{
        "queixa_principal": "Cefaleia há 3 dias",
        "historia_doenca_atual": "Paciente relata...",
        "exame_fisico": "PA: 120x80, FC: 72bpm...",
        "hipotese_diagnostica": "Cefaleia tensional",
        "conduta": "Analgésico, repouso...",
        "medicacoes": ["Dipirona 500mg", "..."]
    }},
    "falas_medico": "todas as falas do médico concatenadas",
    "falas_paciente": "todas as falas do paciente concatenadas",
    "confianca": 0.95,
    "duracao_consulta_minutos": 15
}}

PROCEDA COM A TRANSCRIÇÃO DO ÁUDIO:
"""
        
        # Processar áudio
        if consulta.audio_consulta:
            # Decodificar base64
            if consulta.audio_consulta.startswith('data:'):
                base64_data = consulta.audio_consulta.split(',')[1]
            else:
                base64_data = consulta.audio_consulta
            
            audio_bytes = base64.b64decode(base64_data)
            
            # Enviar para Gemini
            response = model.generate_content([
                prompt,
                {"mime_type": f"audio/{consulta.audio_formato or 'webm'}", "data": audio_bytes}
            ])
            
            response_text = response.text
            
            # Parsear JSON
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            resultado = json.loads(response_text)
            
            # Atualizar consulta
            consulta.transcricao_completa = resultado.get('transcricao_completa', '')
            consulta.transcricao_medico = resultado.get('falas_medico', '')
            consulta.transcricao_paciente = resultado.get('falas_paciente', '')
            consulta.confianca_transcricao = float(resultado.get('confianca', 0))
            
            # Preencher campos estruturados
            resumo = resultado.get('resumo_estruturado', {})
            consulta.queixa_principal = resumo.get('queixa_principal', '')
            consulta.historia_doenca_atual = resumo.get('historia_doenca_atual', '')
            consulta.exame_fisico = resumo.get('exame_fisico', '')
            consulta.hipotese_diagnostica = resumo.get('hipotese_diagnostica', '')
            consulta.conduta = resumo.get('conduta', '')
            
            # Formatar transcrição para visualização
            dialogo = resultado.get('dialogo', [])
            transcricao_formatada = "\n".join([
                f"{'[MÉDICO]' if fala['tipo'] == 'medico' else '[PACIENTE]' if fala['tipo'] == 'paciente' else '[ACOMPANHANTE]'}: {fala['texto']}"
                for fala in dialogo
            ])
            consulta.transcricao_ia = transcricao_formatada
            
            # Tempo de processamento
            tempo_total = time.time() - inicio
            consulta.tempo_processamento_transcricao = tempo_total
            
            # Mudar status
            consulta.status = 'aguardando_revisao'
            consulta.save()
            
            return {
                'sucesso': True,
                'consulta_id': consulta.id,
                'tempo_processamento': tempo_total,
                'confianca': consulta.confianca_transcricao
            }
        else:
            raise Exception("Nenhum áudio disponível")
    
    except Consulta.DoesNotExist:
        return {'sucesso': False, 'erro': 'Consulta não encontrada'}
    except Exception as e:
        try:
            consulta.status = 'em_atendimento'
            consulta.save(update_fields=['status'])
        except:
            pass
        return {'sucesso': False, 'erro': str(e)}

# ============================================
# FUNÇÃO DE GERAÇÃO DE DOCUMENTOS MÉDICOS
# ============================================

async def gerar_documento_medico(consulta_id, tipo_documento, medico_nome, medico_crm):
    """
    Gera documento médico baseado na consulta
    
    Args:
        consulta_id: ID da consulta
        tipo_documento: 'atestado', 'anamnese', 'evolucao', 'prescricao', 'relatorio'
        medico_nome: Nome do médico (com Dr.)
        medico_crm: CRM do médico
    
    Returns:
        dict com documento gerado
    """
    try:
        consulta = Consulta.objects.get(id=consulta_id)
        paciente = consulta.paciente
        
        # Configurar Gemini
        if not Config.GEMINI_API_KEY or not genai:
            raise Exception("Gemini não configurado")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Data por extenso
        from datetime import datetime
        meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        data_extenso = f"{consulta.data_consulta.day} de {meses[consulta.data_consulta.month-1]} de {consulta.data_consulta.year}"
        
        # Prompts específicos por tipo de documento
        prompts = {
            'atestado': f"""
Gere um ATESTADO MÉDICO profissional baseado na consulta.

DADOS DO PACIENTE:
Nome: {paciente.nome_completo}
CPF: {paciente.cpf}
Data de Nascimento: {paciente.data_nascimento.strftime('%d/%m/%Y')}

DADOS DA CONSULTA:
Data: {data_extenso}
Queixa: {consulta.queixa_principal or 'Não informada'}
Diagnóstico: {consulta.diagnostico or consulta.hipotese_diagnostica or 'A esclarecer'}

MÉDICO:
{medico_nome}
CRM: {medico_crm}

FORMATO DO ATESTADO:
- Cabeçalho com título "ATESTADO MÉDICO"
- Atesto que o(a) paciente...
- CID se aplicável
- Dias de afastamento recomendados (se necessário)
- Local, data por extenso
- Assinatura do médico com CRM

Gere o atestado de forma profissional e formatada.
""",
            
            'anamnese': f"""
Gere uma ANAMNESE COMPLETA baseada na transcrição da consulta.

PACIENTE: {paciente.nome_completo}
IDADE: {paciente.idade} anos
SEXO: {paciente.get_sexo_display()}

TRANSCRIÇÃO DA CONSULTA:
{consulta.transcricao_ia or consulta.transcricao_completa or 'Não disponível'}

ESTRUTURA DA ANAMNESE:
1. Identificação
2. Queixa Principal
3. História da Doença Atual (HDA)
4. Revisão de Sistemas
5. Antecedentes Pessoais
6. Antecedentes Familiares
7. Hábitos de Vida
8. Exame Físico
9. Hipóteses Diagnósticas

Médico: {medico_nome} - CRM: {medico_crm}
Data: {data_extenso}

Gere a anamnese completa e bem estruturada.
""",
            
            'evolucao': f"""
Gere uma EVOLUÇÃO MÉDICA baseada na consulta.

PACIENTE: {paciente.nome_completo}

DADOS DA CONSULTA:
{consulta.transcricao_ia or 'Sem transcrição'}

Queixa: {consulta.queixa_principal or 'Não informada'}
Exame Físico: {consulta.exame_fisico or 'Não realizado'}
Diagnóstico: {consulta.diagnostico or 'A esclarecer'}
Conduta: {consulta.conduta or 'Não definida'}

FORMATO:
Data/Hora: {consulta.data_consulta.strftime('%d/%m/%Y %H:%M')}
S (Subjetivo): relato do paciente
O (Objetivo): achados do exame
A (Avaliação): impressão diagnóstica
P (Plano): conduta proposta

Médico: {medico_nome} - CRM: {medico_crm}
""",
            
            'prescricao': f"""
Gere uma PRESCRIÇÃO MÉDICA baseada na consulta.

PACIENTE: {paciente.nome_completo}
IDADE: {paciente.idade} anos
PESO: [Se mencionado na consulta]

MEDICAÇÕES MENCIONADAS NA CONSULTA:
{consulta.conduta or 'Ver transcrição'}

TRANSCRIÇÃO:
{consulta.transcricao_medico or 'Não disponível'}

FORMATO DA PRESCRIÇÃO:
1. Cabeçalho com dados do paciente
2. Lista numerada de medicações com:
   - Nome do medicamento
   - Concentração/dosagem
   - Via de administração
   - Posologia (horários)
   - Duração do tratamento
3. Orientações gerais
4. Data e assinatura do médico

Médico: {medico_nome}
CRM: {medico_crm}
Data: {data_extenso}

Gere prescrição clara e detalhada.
""",
            
            'relatorio': f"""
Gere um RELATÓRIO MÉDICO COMPLETO da consulta.

PACIENTE: {paciente.nome_completo}
CPF: {paciente.cpf}
IDADE: {paciente.idade} anos
CONVÊNIO: {paciente.convenio}

CONSULTA REALIZADA EM: {data_extenso}
TIPO: {consulta.get_tipo_consulta_display()}

DADOS CLÍNICOS:
Queixa Principal: {consulta.queixa_principal or 'Não informada'}
História: {consulta.historia_doenca_atual or 'Ver transcrição'}
Exame Físico: {consulta.exame_fisico or 'Não descrito'}
Hipótese Diagnóstica: {consulta.hipotese_diagnostica or 'A esclarecer'}
Conduta: {consulta.conduta or 'Não definida'}

TRANSCRIÇÃO COMPLETA:
{consulta.transcricao_ia or 'Não disponível'}

FORMATO DO RELATÓRIO:
- Título: RELATÓRIO MÉDICO
- Identificação do paciente
- Motivo da consulta
- Histórico clínico
- Exame físico detalhado
- Conclusão diagnóstica
- Plano terapêutico
- Prognóstico e orientações
- Data, local, médico e CRM

Gere relatório médico profissional e completo.
"""
        }
        
        prompt = prompts.get(tipo_documento, '')
        
        if not prompt:
            raise Exception(f"Tipo de documento inválido: {tipo_documento}")
        
        # Gerar documento
        response = model.generate_content(prompt)
        documento = response.text
        
        # Limpar markdown se houver
        if '```' in documento:
            documento = documento.replace('```', '')
        
        return {
            'sucesso': True,
            'tipo': tipo_documento,
            'conteudo': documento,
            'data_geracao': timezone.now().isoformat()
        }
    
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e)
        }

# ============================================
# VIEWSETS - CLÍNICAS E USUÁRIOS
# ============================================

class ClinicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Clínicas
    
    Endpoints:
    - GET /api/clinicas/ - Listar clínicas (apenas super_admin)
    - POST /api/clinicas/ - Criar clínica (apenas super_admin)
    - PUT /api/clinicas/{id}/ - Atualizar clínica
    - DELETE /api/clinicas/{id}/ - Excluir clínica
    """
    
    serializer_class = ClinicaSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    ordering = ['nome']
    
    def get_queryset(self):
        """Apenas super_admin vê todas as clínicas"""
        user = self.request.user
        
        if user.get('funcao') == 'super_admin':
            return Clinica.objects.all()
        else:
            # Outros usuários veem apenas sua clínica
            clinica_id = user.get('clinica_id')
            return Clinica.objects.filter(id=clinica_id) if clinica_id else Clinica.objects.none()
    
    def perform_create(self, serializer):
        """Apenas super_admin pode criar clínicas"""
        if self.request.user.get('funcao') != 'super_admin':
            raise PermissionDenied("Apenas super admin pode criar clínicas")
        serializer.save()

class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Usuários
    
    Endpoints:
    - GET /api/usuarios/ - Listar usuários
    - POST /api/usuarios/ - Criar usuário
    - PUT /api/usuarios/{id}/ - Atualizar usuário
    - DELETE /api/usuarios/{id}/ - Excluir usuário
    """
    
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, IsAdminOnly]
    authentication_classes = [JWTAuthentication]
    ordering = ['nome_completo']
    
    def get_queryset(self):
        """Filtrar usuários conforme permissão"""
        user = self.request.user
        
        if user.get('funcao') == 'super_admin':
            return Usuario.objects.all()
        else:
            # Outros usuários veem apenas da própria clínica
            clinica_id = user.get('clinica_id')
            return Usuario.objects.filter(clinica_id=clinica_id) if clinica_id else Usuario.objects.none()
    
    @action(detail=True, methods=['post'], url_path='alterar-status')
    def alterar_status(self, request, pk=None):
        """
        Alterar status do usuário
        POST /api/usuarios/{id}/alterar-status/
        Body: {"status": "ativo"} ou {"status": "inativo"}
        """
        usuario = self.get_object()
        novo_status = request.data.get('status')
    
        if not novo_status or novo_status not in dict(Usuario.STATUS_CHOICES):
            return Response({'erro': 'Status inválido'}, status=400)
    
        usuario.status = novo_status
        usuario.save(update_fields=['status'])
    
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)
    
# ============================================
# VIEW DE LOGIN
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login de usuário
    POST /api/login/
    Body: {"email": "user@example.com", "password": "senha123"}
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({'mensagem': 'Dados inválidos'}, status=400)
    
    email = serializer.validated_data['email'].lower()
    password = serializer.validated_data['password']
    
    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return Response({'mensagem': 'Email ou senha incorretos'}, status=401)
    
    # Verificar senha
    if not usuario.check_password(password):
        return Response({'mensagem': 'Email ou senha incorretos'}, status=401)
    
    # Verificar se usuário está ativo
    if usuario.status != 'ativo':
        return Response({'mensagem': 'Usuário inativo'}, status=403)
    
    # Atualizar last_login
    usuario.last_login = timezone.now()
    usuario.save(update_fields=['last_login'])
    
    # Gerar token JWT
    token = usuario.generate_jwt_token()
    
    # Retornar resposta compatível com admin_panel
    return Response({
        'access_token': token,
        'user_info': {
            'id': usuario.id,
            'nome_completo': usuario.nome_completo,
            'email': usuario.email,
            'funcao': usuario.funcao,
            'clinica_id': usuario.clinica_id,
            'status': usuario.status
        }
    }, status=200)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def register_view(request):
    """
    Registrar novo usuário
    POST /register
    Requer autenticação de super_admin ou admin
    """
    user = request.user
    funcao = user.payload.get('funcao')
    
    if funcao not in ['super_admin', 'admin']:
        return Response({'mensagem': 'Sem permissão'}, status=403)
    
    # DEBUG: Ver o que está chegando
    print(f"\n🔍 DEBUG REGISTER:")
    print(f"Dados recebidos: {request.data}")
    print(f"Headers: {request.headers}")
    
    serializer = UsuarioSerializer(data=request.data)
    
    if not serializer.is_valid():
        print(f"❌ Erros de validação: {serializer.errors}")
        return Response({'mensagem': serializer.errors}, status=400)
    
    usuario = serializer.save()
    
    return Response({
        'mensagem': 'Usuário cadastrado com sucesso',
        'id': usuario.id
    }, status=201)
    
# ============================================
# SERIALIZERS - Django REST Framework
# ============================================

from rest_framework import serializers

# ============================================
# SERIALIZER PACIENTE
# ============================================

class PacienteSerializer(serializers.ModelSerializer):
    """Serializer para Paciente"""
    
    idade = serializers.ReadOnlyField()
    endereco_completo = serializers.ReadOnlyField()
    sexo_display = serializers.CharField(source='get_sexo_display', read_only=True)
    convenio_display = serializers.CharField(source='get_convenio_display', read_only=True)
    
    class Meta:
        model = Paciente
        fields = [
            'id', 'clinica_id', 'nome_completo', 'cpf', 'data_nascimento', 
            'idade', 'profissao', 'sexo', 'sexo_display', 'convenio', 
            'convenio_display', 'telefone_celular', 'telefone_fixo', 'email',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 
            'cidade', 'estado', 'endereco_completo', 'ativo',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ['id', 'data_cadastro', 'data_atualizacao']
    
    def validate_cpf(self, value):
        """Validar CPF"""
        if not Validador.validar_cpf(value):
            raise serializers.ValidationError("CPF inválido")
        
        cpf_formatado = Validador.formatar_cpf(value)
        
        # Procura por CPFs duplicados APENAS em pacientes ATIVOS
        query = Paciente.objects.filter(cpf=cpf_formatado, ativo=True)
        
        # Se estiver editando (self.instance existe), exclui o próprio paciente da busca
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise serializers.ValidationError("Este CPF já está em uso por outro paciente ativo.")
        
        return value
    
    def validate_email(self, value):
        """Validar email"""
        if value and not Validador.validar_email_format(value):
            raise serializers.ValidationError("Email inválido")
        return value
    
    def validate_data_nascimento(self, value):
        """Validar data de nascimento"""
        if value > date.today():
            raise serializers.ValidationError("Data de nascimento não pode ser futura")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        # Garantir que clinica_id vem do request (não do payload)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['clinica_id'] = request.user.get('clinica_id')
        
        return data


class PacienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de pacientes"""
    
    # Esta linha já estava correta e é a chave da solução
    idade = serializers.ReadOnlyField() 
    sexo_display = serializers.CharField(source='get_sexo_display', read_only=True)
    
    class Meta:
        model = Paciente
        fields = [
            'id', 'nome_completo', 'cpf', 'data_nascimento', 'idade', 'sexo_display', # <-- ADICIONEI 'data_nascimento'
            'convenio', 'telefone_celular', 'email', 'cidade', 'estado', 'ativo'
        ]


# ============================================
# SERIALIZER AGENDAMENTO
# ============================================

class AgendamentoSerializer(serializers.ModelSerializer):
    """Serializer para Agendamento"""
    
    paciente_nome = serializers.ReadOnlyField()
    paciente_cpf = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    servico_display = serializers.CharField(source='get_servico_display', read_only=True)
    
    class Meta:
        model = Agendamento
        fields = [
            'id', 'clinica_id', 'paciente', 'paciente_nome', 'paciente_cpf',
            'convenio', 'servico', 'servico_display', 'tipo', 'data', 'hora',
            'valor', 'observacoes', 'status', 'status_display',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ['id', 'paciente_nome', 'paciente_cpf', 'data_cadastro', 'data_atualizacao']
    
    def validate_paciente(self, value):
        """Validar se paciente pertence à clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            if value.clinica_id != clinica_id:
                raise serializers.ValidationError("Paciente não pertence a esta clínica")
        return value
    
    def validate_data(self, value):
        """Validar data do agendamento"""
        # Apenas para novos agendamentos
        if not self.instance and value < date.today():
            raise serializers.ValidationError("Não é possível agendar para datas passadas")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            data['clinica_id'] = clinica_id
            
            # Verificar disponibilidade de horário
            if 'data' in data and 'hora' in data:
                excluir_id = self.instance.id if self.instance else None
                if not Agendamento.verificar_disponibilidade(
                    clinica_id, data['data'], data['hora'], excluir_id
                ):
                    raise serializers.ValidationError({
                        'hora': 'Já existe um agendamento para este horário'
                    })
        
        return data


class AgendamentoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de agendamentos"""
    
    paciente_nome = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Agendamento
        fields = [
            'id', 'paciente_nome', 'servico', 'tipo', 'data', 'hora',
            'valor', 'status', 'status_display'
        ]

# ============================================
# SERIALIZER CONSULTA COMPLETO
# ============================================

class ConsultaSerializer(serializers.ModelSerializer):
    """Serializer para Consulta"""
    
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    paciente_cpf = serializers.CharField(source='paciente.cpf', read_only=True)
    tipo_consulta_display = serializers.CharField(source='get_tipo_consulta_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Consulta
        fields = [
            'id', 'clinica_id', 'paciente', 'paciente_nome', 'paciente_cpf', 'agendamento',
            'data_consulta', 'tipo_consulta', 'tipo_consulta_display', 'duracao_minutos',
            'queixa_principal', 'historia_doenca_atual', 'anamnese', 'exame_fisico',
            'hipotese_diagnostica', 'diagnostico', 'conduta', 'prescricao', 'observacoes',
            'audio_consulta', 'audio_duracao_segundos', 'audio_formato',
            'transcricao_completa', 'transcricao_ia', 'transcricao_medico', 'transcricao_paciente',
            'confianca_transcricao', 'tempo_processamento_transcricao',
            'documentos_gerados',
            'atestado_medico', 'anamnese_documento', 'evolucao_medica', 
            'prescricao_documento', 'relatorio_medico',
            'medico_responsavel', 'medico_crm',
            'status', 'status_display',
            'data_inicio_atendimento', 'data_fim_atendimento',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = [
            'id', 'transcricao_completa', 'transcricao_ia', 
            'transcricao_medico', 'transcricao_paciente',
            'confianca_transcricao', 'tempo_processamento_transcricao',
            'data_inicio_atendimento', 'data_fim_atendimento',
            'data_cadastro', 'data_atualizacao'
        ]
    
    def validate_paciente(self, value):
        """Validar se paciente pertence à clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            if value.clinica_id != clinica_id:
                raise serializers.ValidationError("Paciente não pertence a esta clínica")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['clinica_id'] = request.user.get('clinica_id')
        return data

class ConsultaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de consultas"""
    
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tem_audio = serializers.SerializerMethodField()
    tem_transcricao = serializers.SerializerMethodField()
    total_documentos = serializers.SerializerMethodField()
    
    class Meta:
        model = Consulta
        fields = [
            'id', 'paciente_nome', 'data_consulta', 'tipo_consulta',
            'medico_responsavel', 'status', 'status_display',
            'duracao_minutos', 'tem_audio', 'tem_transcricao', 'total_documentos'
        ]
    
    def get_tem_audio(self, obj):
        return bool(obj.audio_consulta)
    
    def get_tem_transcricao(self, obj):
        return bool(obj.transcricao_ia or obj.transcricao_completa)
    
    def get_total_documentos(self, obj):
        count = 0
        if obj.atestado_medico:
            count += 1
        if obj.anamnese_documento:
            count += 1
        if obj.evolucao_medica:
            count += 1
        if obj.prescricao_documento:
            count += 1
        if obj.relatorio_medico:
            count += 1
        return count

class ConsultaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de consultas"""
    
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Consulta
        fields = [
            'id', 'paciente_nome', 'data_consulta', 'tipo_consulta',
            'medico_responsavel', 'status', 'status_display'
        ]

# ============================================
# SERIALIZER EXAME
# ============================================

class ExameSerializer(serializers.ModelSerializer):
    """Serializer para Exame"""
    
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    tipo_exame_display = serializers.CharField(source='get_tipo_exame_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Exame
        fields = [
            'id', 'clinica_id', 'paciente', 'paciente_nome', 'consulta',
            'tipo_exame', 'tipo_exame_display', 'tipo_exame_identificado_ia',
            'data_exame', 'data_resultado',
            'arquivo_exame', 'arquivo_nome', 'arquivo_tipo',
            'resultado_original', 
            'interpretacao_ia', 'confianca_ia', 'fontes_consultadas',
            'tempo_processamento', 'erro_ia',
            'revisado_por_medico', 'medico_revisor_nome', 'medico_revisor_crm',
            'data_revisao', 'observacoes_medico',
            'medico_solicitante', 'medico_solicitante_crm', 'laboratorio',
            'observacoes',
            'status', 'status_display', 
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = [
            'id', 'interpretacao_ia', 'confianca_ia', 'fontes_consultadas',
            'tempo_processamento', 'erro_ia', 'tipo_exame_identificado_ia',
            'data_cadastro', 'data_atualizacao'
        ]
    
    def validate_paciente(self, value):
        """Validar se paciente pertence à clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            if value.clinica_id != clinica_id:
                raise serializers.ValidationError("Paciente não pertence a esta clínica")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['clinica_id'] = request.user.get('clinica_id')
        return data

class ExameListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de exames"""
    
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    tipo_exame_display = serializers.CharField(source='get_tipo_exame_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tem_interpretacao_ia = serializers.SerializerMethodField()
    revisado = serializers.BooleanField(source='revisado_por_medico', read_only=True)
    
    class Meta:
        model = Exame
        fields = [
            'id', 'paciente_nome', 'tipo_exame', 'tipo_exame_display',
            'data_exame', 'data_resultado', 'status', 'status_display',
            'tem_interpretacao_ia', 'revisado', 'confianca_ia'
        ]
    
    def get_tem_interpretacao_ia(self, obj):
        return bool(obj.interpretacao_ia)
    
# ============================================
# SERIALIZER CATEGORIA RECEITA
# ============================================

class CategoriaReceitaSerializer(serializers.ModelSerializer):
    """Serializer para Categoria de Receita"""
    
    class Meta:
        model = CategoriaReceita
        fields = ['id', 'clinica_id', 'nome', 'descricao', 'cor', 'ativo', 'data_cadastro']
        read_only_fields = ['id', 'data_cadastro']
    
    def validate_nome(self, value):
        """Validar duplicidade de nome na mesma clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            query = CategoriaReceita.objects.filter(clinica_id=clinica_id, nome=value)
            
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise serializers.ValidationError("Já existe uma categoria com este nome")
        
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['clinica_id'] = request.user.get('clinica_id')
        return data

# ============================================
# SERIALIZER CATEGORIA DESPESA
# ============================================

class CategoriaDespesaSerializer(serializers.ModelSerializer):
    """Serializer para Categoria de Despesa"""
    
    class Meta:
        model = CategoriaDespesa
        fields = ['id', 'clinica_id', 'nome', 'descricao', 'cor', 'ativo', 'data_cadastro']
        read_only_fields = ['id', 'data_cadastro']
    
    def validate_nome(self, value):
        """Validar duplicidade de nome na mesma clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            query = CategoriaDespesa.objects.filter(clinica_id=clinica_id, nome=value)
            
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise serializers.ValidationError("Já existe uma categoria com este nome")
        
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['clinica_id'] = request.user.get('clinica_id')
        return data

# ============================================
# SERIALIZER RECEITA
# ============================================

class ReceitaSerializer(serializers.ModelSerializer):
    """Serializer para Receita"""
    
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Receita
        fields = [
            'id', 'clinica_id', 'descricao', 'valor', 'categoria', 'categoria_nome',
            'data_vencimento', 'data_recebimento', 'status', 'status_display',
            'agendamento', 'paciente', 'paciente_nome', 'forma_pagamento',
            'observacoes', 'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ['id', 'data_cadastro', 'data_atualizacao']
    
    def validate_valor(self, value):
        """Validar valor positivo"""
        if value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero")
        return value
    
    def validate_categoria(self, value):
        """Validar se categoria pertence à clínica"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                clinica_id = request.user.get('clinica_id')
                if value.clinica_id != clinica_id:
                    raise serializers.ValidationError("Categoria não pertence a esta clínica")
        return value
    
    def validate_paciente(self, value):
        """Validar se paciente pertence à clínica"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                clinica_id = request.user.get('clinica_id')
                if value.clinica_id != clinica_id:
                    raise serializers.ValidationError("Paciente não pertence a esta clínica")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['clinica_id'] = request.user.get('clinica_id')
        return data

class ReceitaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de receitas"""
    
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Receita
        fields = [
            'id', 'descricao', 'valor', 'categoria_nome', 'data_vencimento',
            'data_recebimento', 'status', 'status_display', 'paciente_nome'
        ]

# ============================================
# SERIALIZER DESPESA
# ============================================

class DespesaSerializer(serializers.ModelSerializer):
    """Serializer para Despesa"""
    
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Despesa
        fields = [
            'id', 'clinica_id', 'descricao', 'valor', 'categoria', 'categoria_nome',
            'data_vencimento', 'data_pagamento', 'status', 'status_display',
            'fornecedor', 'forma_pagamento', 'observacoes',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ['id', 'data_cadastro', 'data_atualizacao']
    
    def validate_valor(self, value):
        """Validar valor positivo"""
        if value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero")
        return value
    
    def validate_categoria(self, value):
        """Validar se categoria pertence à clínica"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                clinica_id = request.user.get('clinica_id')
                if value.clinica_id != clinica_id:
                    raise serializers.ValidationError("Categoria não pertence a esta clínica")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['clinica_id'] = request.user.get('clinica_id')
        return data

class DespesaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de despesas"""
    
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Despesa
        fields = [
            'id', 'descricao', 'valor', 'categoria_nome', 'data_vencimento',
            'data_pagamento', 'status', 'status_display', 'fornecedor'
        ]

# ============================================
# SERIALIZER TRANSCRIÇÃO
# ============================================

class TranscricaoSerializer(serializers.ModelSerializer):
    """Serializer para Transcrição"""
    
    consulta_data = serializers.DateTimeField(source='consulta.data_consulta', read_only=True)
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transcricao
        fields = [
            'id', 'clinica_id', 'consulta', 'consulta_data', 'paciente',
            'paciente_nome', 'tipo', 'tipo_display', 'arquivo_audio',
            'duracao_segundos', 'formato_audio', 'texto_transcrito',
            'confianca', 'resumo_ia', 'palavras_chave', 'sentimento',
            'sintomas_identificados', 'medicamentos_mencionados',
            'diagnostico_sugerido', 'status', 'status_display',
            'erro_mensagem', 'tempo_processamento', 'medico_nome',
            'data_inicio', 'data_conclusao', 'data_atualizacao'
        ]
        read_only_fields = [
            'id', 'texto_transcrito', 'confianca', 'resumo_ia',
            'palavras_chave', 'sentimento', 'sintomas_identificados',
            'medicamentos_mencionados', 'diagnostico_sugerido',
            'status', 'erro_mensagem', 'tempo_processamento',
            'data_inicio', 'data_conclusao', 'data_atualizacao'
        ]
    
    def validate_consulta(self, value):
        """Validar se consulta pertence à clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            if value.clinica_id != clinica_id:
                raise serializers.ValidationError("Consulta não pertence a esta clínica")
        return value
    
    def validate_paciente(self, value):
        """Validar se paciente pertence à clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            if value.clinica_id != clinica_id:
                raise serializers.ValidationError("Paciente não pertence a esta clínica")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['clinica_id'] = request.user.get('clinica_id')
            
            # Preencher médico automaticamente
            if not data.get('medico_nome'):
                data['medico_nome'] = request.user.get('nome', '')
        
        return data


class TranscricaoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de transcrições"""
    
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transcricao
        fields = [
            'id', 'paciente_nome', 'tipo', 'duracao_segundos',
            'status', 'status_display', 'data_inicio', 'data_conclusao'
        ]

# ============================================
# VIEWSETS - Django REST Framework
# ============================================

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

# ============================================
# VIEWSET PACIENTE
# ============================================

class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Pacientes
    
    Endpoints:
    - GET /api/pacientes/ - Listar pacientes
    - POST /api/pacientes/ - Criar paciente
    - GET /api/pacientes/{id}/ - Obter paciente
    - PUT /api/pacientes/{id}/ - Atualizar paciente
    - PATCH /api/pacientes/{id}/ - Atualizar parcial
    - DELETE /api/pacientes/{id}/ - Excluir (soft delete)
    """
    
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome_completo', 'cpf', 'email']
    ordering_fields = ['nome_completo', 'data_nascimento', 'data_cadastro']
    ordering = ['nome_completo']
    
    def get_queryset(self):
        """Filtrar pacientes: super_admin vê todos, outros usuários veem apenas da sua clínica."""
        user = self.request.user
        funcao = user.get('funcao')
        clinica_id = user.get('clinica_id')

        # DEBUG: Adicione este print para ver o que o backend está recebendo em cada requisição
        print(f"🔍 DEBUG get_queryset: User Função='{funcao}', Clinica ID='{clinica_id}', Action='{self.action}'")

        # Lógica robusta que lida com todos os tipos de usuário
        if funcao == 'super_admin':
            queryset = Paciente.objects.filter(ativo=True)
        elif clinica_id is not None:
            queryset = Paciente.objects.filter(clinica_id=clinica_id, ativo=True)
        else:
            # Se não for super_admin e não tiver clinica_id, não pode ver nenhum paciente.
            return Paciente.objects.none()
        
        # Filtros de busca (para a lista)
        busca = self.request.query_params.get('busca', None)
        if busca:
            queryset = queryset.filter(
                Q(nome_completo__icontains=busca) |
                Q(cpf__icontains=busca)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return PacienteListSerializer
        return PacienteSerializer
    
    def perform_destroy(self, instance):
        """Soft delete - marcar como inativo"""
        instance.ativo = False
        instance.save()
    
    @action(detail=True, methods=['get'])
    def completo(self, request, pk=None):
        """
        Obter paciente com histórico completo
        GET /api/pacientes/{id}/completo/
        """
        paciente = self.get_object()
        
        # Serializar paciente
        paciente_data = PacienteSerializer(paciente, context={'request': request}).data
        
        # Adicionar históricos
        consultas = ConsultaListSerializer(
            paciente.consultas.all()[:10], 
            many=True, 
            context={'request': request}
        ).data
        
        exames = ExameListSerializer(
            paciente.exames.all()[:10], 
            many=True, 
            context={'request': request}
        ).data
        
        return Response({
            'paciente': paciente_data,
            'consultas': consultas,
            'exames': exames,
            'total_consultas': paciente.consultas.count(),
            'total_exames': paciente.exames.count()
        })
    
    @action(detail=False, methods=['post'])
    def verificar_cpf(self, request):
        """
        Verificar se CPF já está cadastrado
        POST /api/pacientes/verificar_cpf/
        Body: {"cpf": "123.456.789-00"}
        """
        cpf = request.data.get('cpf')
        if not cpf:
            return Response({'erro': 'CPF não fornecido'}, status=400)
        
        cpf_formatado = Validador.formatar_cpf(cpf)
        clinica_id = request.user.get('clinica_id')
        
        existe = Paciente.objects.filter(
            clinica_id=clinica_id,
            cpf=cpf_formatado,
            ativo=True
        ).exists()
        
        return Response({'duplicado': existe})
    
    @action(detail=False, methods=['get'], url_path='inativos')
    def listar_inativos(self, request):
        """
        Listar pacientes inativos (soft-deleted).
        GET /api/pacientes/inativos/
        """
        clinica_id = request.user.get('clinica_id')
        pacientes_inativos = Paciente.objects.filter(clinica_id=clinica_id, ativo=False)
        serializer = self.get_serializer(pacientes_inativos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='reativar')
    def reativar_paciente(self, request, pk=None):
        """
        Reativar um paciente inativo.
        POST /api/pacientes/{id}/reativar/
        """
        try:
            paciente = Paciente.objects.get(pk=pk, clinica_id=request.user.get('clinica_id'))
            
            # Verifica se já existe um paciente ativo com o mesmo CPF
            if Paciente.objects.filter(cpf=paciente.cpf, ativo=True).exists():
                return Response(
                    {'erro': f'Não é possível reativar. Já existe um paciente ativo com o CPF {paciente.cpf}.'},
                    status=status.HTTP_409_CONFLICT
                )

            paciente.ativo = True
            paciente.save()
            serializer = self.get_serializer(paciente)
            return Response(serializer.data)
        except Paciente.DoesNotExist:
            return Response({'erro': 'Paciente não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

# ============================================
# VIEWSET AGENDAMENTO
# ============================================

class AgendamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Agendamentos
    
    Endpoints:
    - GET /api/agendamentos/ - Listar agendamentos
    - POST /api/agendamentos/ - Criar agendamento
    - GET /api/agendamentos/{id}/ - Obter agendamento
    - PUT /api/agendamentos/{id}/ - Atualizar agendamento
    - PATCH /api/agendamentos/{id}/ - Atualizar parcial
    - DELETE /api/agendamentos/{id}/ - Excluir agendamento
    """
    
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['paciente_nome', 'paciente_cpf']
    ordering_fields = ['data', 'hora']
    ordering = ['-data', '-hora']
    
    def get_queryset(self):
        """Filtrar agendamentos pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        queryset = Agendamento.objects.filter(clinica_id=clinica_id)
        
        # Filtros via query params
        data_inicial = self.request.query_params.get('data_inicial', None)
        data_final = self.request.query_params.get('data_final', None)
        status = self.request.query_params.get('status', None)
        servico = self.request.query_params.get('servico', None)
        mes = self.request.query_params.get('mes', None)
        ano = self.request.query_params.get('ano', None)
        
        if data_inicial and data_final:
            queryset = queryset.filter(data__range=[data_inicial, data_final])
        elif data_inicial:
            queryset = queryset.filter(data=data_inicial)

        if status:
            queryset = queryset.filter(status=status)
        
        if servico:
            queryset = queryset.filter(servico=servico)
        
        if mes and ano:
            queryset = queryset.filter(data__year=ano, data__month=mes)
        elif ano and not mes:
            queryset = queryset.filter(data__year=ano)
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return AgendamentoListSerializer
        return AgendamentoSerializer
    
    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """
        Obter próximos agendamentos
        GET /api/agendamentos/proximos/?limite=10
        """
        clinica_id = request.user.get('clinica_id')
        limite = int(request.query_params.get('limite', 10))
        
        agendamentos = Agendamento.obter_proximos_agendamentos(clinica_id, limite)
        serializer = AgendamentoListSerializer(agendamentos, many=True, context={'request': request})
        
        return Response({
            'agendamentos': serializer.data,
            'total': agendamentos.count()
        })
    
    @action(detail=False, methods=['get'])
    def agenda_dia(self, request):
        """
        Obter agenda de um dia específico
        GET /api/agendamentos/agenda_dia/?data=2025-10-05
        """
        data = request.query_params.get('data')
        if not data:
            return Response({'erro': 'Data não fornecida'}, status=400)
        
        clinica_id = request.user.get('clinica_id')
        agendamentos = Agendamento.objects.filter(
            clinica_id=clinica_id,
            data=data
        ).order_by('hora')
        
        serializer = AgendamentoSerializer(agendamentos, many=True, context={'request': request})
        
        return Response({
            'agendamentos': serializer.data,
            'total': agendamentos.count()
        })
    
    @action(detail=False, methods=['get'])
    def verificar_disponibilidade(self, request):
        """
        Verificar disponibilidade de horário
        GET /api/agendamentos/verificar_disponibilidade/?data=2025-10-05&hora=14:00
        """
        data = request.query_params.get('data')
        hora = request.query_params.get('hora')
        
        if not data or not hora:
            return Response({'erro': 'Data e hora são obrigatórios'}, status=400)
        
        clinica_id = request.user.get('clinica_id')
        disponivel = Agendamento.verificar_disponibilidade(clinica_id, data, hora)
        
        return Response({
            'disponivel': disponivel,
            'mensagem': 'Horário disponível' if disponivel else 'Horário não disponível'
        })
    
    @action(detail=True, methods=['patch'])
    def alterar_status(self, request, pk=None):
        """
        Alterar status do agendamento
        PATCH /api/agendamentos/{id}/alterar_status/
        Body: {"status": "Confirmado"}
        """
        agendamento = self.get_object()
        novo_status = request.data.get('status')
        
        if not novo_status:
            return Response({'erro': 'Status não fornecido'}, status=400)
        
        if novo_status not in dict(Agendamento.STATUS_CHOICES):
            return Response({'erro': 'Status inválido'}, status=400)
        
        agendamento.status = novo_status
        agendamento.save()
        
        # Se status for "Realizado" e tiver valor, pode criar receita automaticamente
        # (implementar lógica de integração com faturamento se necessário)
        
        serializer = AgendamentoSerializer(agendamento, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estatisticas_mes(self, request):
        """
        Estatísticas de agendamentos do mês
        GET /api/agendamentos/estatisticas_mes/?mes=10&ano=2025
        """
        mes = request.query_params.get('mes')
        ano = request.query_params.get('ano')
        
        if not mes or not ano:
            return Response({'erro': 'Mês e ano são obrigatórios'}, status=400)
        
        clinica_id = request.user.get('clinica_id')
        agendamentos = Agendamento.objects.filter(
            clinica_id=clinica_id,
            data__year=ano,
            data__month=mes
        )
        
        total = agendamentos.count()
        agendados = agendamentos.filter(status='Agendado').count()
        confirmados = agendamentos.filter(status='Confirmado').count()
        realizados = agendamentos.filter(status='Realizado').count()
        cancelados = agendamentos.filter(status='Cancelado').count()
        faltas = agendamentos.filter(status='Faltou').count()
        
        return Response({
            'mes': mes,
            'ano': ano,
            'estatisticas': {
                'total': total,
                'agendados': agendados,
                'confirmados': confirmados,
                'realizados': realizados,
                'cancelados': cancelados,
                'faltas': faltas,
                'taxa_realizacao': (realizados / total * 100) if total > 0 else 0,
                'taxa_cancelamento': (cancelados / total * 100) if total > 0 else 0,
                'taxa_falta': (faltas / total * 100) if total > 0 else 0
            }
        })
    
# ============================================
# VIEWSET CONSULTA COMPLETO
# ============================================

class ConsultaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Consultas com Transcrição e Geração de Documentos
    
    Endpoints:
    - GET /api/consultas/ - Listar consultas
    - POST /api/consultas/ - Criar consulta
    - GET /api/consultas/{id}/ - Obter consulta
    - PUT /api/consultas/{id}/ - Atualizar consulta
    - DELETE /api/consultas/{id}/ - Excluir consulta
    - GET /api/consultas/fila-hoje/ - Fila de atendimento de hoje
    - POST /api/consultas/{id}/iniciar-atendimento/ - Iniciar atendimento
    - POST /api/consultas/{id}/enviar-audio/ - Enviar áudio da consulta
    - POST /api/consultas/{id}/transcrever/ - Transcrever áudio
    - POST /api/consultas/{id}/gerar-documento/ - Gerar documento médico
    - POST /api/consultas/{id}/salvar-documento/ - Salvar documento editado
    - POST /api/consultas/{id}/finalizar/ - Finalizar consulta
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrMedico] 
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['paciente__nome_completo']
    ordering_fields = ['data_consulta']
    ordering = ['-data_consulta']
    
    def get_queryset(self):
        """Filtrar consultas pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        queryset = Consulta.objects.filter(clinica_id=clinica_id)
        
        # Filtros via query params
        paciente_id = self.request.query_params.get('paciente_id', None)
        status = self.request.query_params.get('status', None)
        data_inicial = self.request.query_params.get('data_inicial', None)
        data_final = self.request.query_params.get('data_final', None)
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if data_inicial and data_final:
            queryset = queryset.filter(data_consulta__date__range=[data_inicial, data_final])
        elif data_inicial:
            queryset = queryset.filter(data_consulta__date__gte=data_inicial)
        elif data_final:
            queryset = queryset.filter(data_consulta__date__lte=data_final)
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return ConsultaListSerializer
        return ConsultaSerializer
    
    @action(detail=False, methods=['get'], url_path='fila-hoje')
    def fila_hoje(self, request):
        """
        Retorna fila de atendimento de hoje
        GET /api/consultas/fila-hoje/
        
        Retorna agendamentos do dia com status para iniciar atendimento
        """
        clinica_id = request.user.get('clinica_id')
        hoje = date.today()
        
        # Buscar agendamentos de hoje
        agendamentos_hoje = Agendamento.objects.filter(
            clinica_id=clinica_id,
            data=hoje,
            status__in=['Agendado', 'Confirmado']
        ).select_related('paciente').order_by('hora')
        
        fila = []
        for agend in agendamentos_hoje:
            # Verificar se já tem consulta criada
            consulta_existente = Consulta.objects.filter(
                agendamento=agend,
                data_consulta__date=hoje
            ).first()
            
            fila.append({
                'agendamento_id': agend.id,
                'paciente_id': agend.paciente.id,
                'paciente_nome': agend.paciente_nome,
                'paciente_cpf': agend.paciente_cpf,
                'hora': agend.hora.strftime('%H:%M'),
                'tipo': agend.tipo,
                'convenio': agend.convenio,
                'observacoes': agend.observacoes,
                'consulta_id': consulta_existente.id if consulta_existente else None,
                'consulta_status': consulta_existente.status if consulta_existente else None,
                'pode_iniciar': not consulta_existente or consulta_existente.status in ['agendada', 'confirmada']
            })
        
        return Response({
            'data': hoje.isoformat(),
            'total': len(fila),
            'fila': fila
        })
    
    @action(detail=True, methods=['post'], url_path='iniciar-atendimento')
    def iniciar_atendimento(self, request, pk=None):
        """
        Iniciar atendimento da consulta
        POST /api/consultas/{id}/iniciar-atendimento/
        """
        consulta = self.get_object()
        usuario = request.user.payload
        
        if consulta.status not in ['agendada', 'confirmada']:
            return Response({
                'erro': 'Consulta não pode ser iniciada neste status'
            }, status=400)
        
        # Buscar dados do médico
        try:
            medico = Usuario.objects.get(
                id=usuario.get('sub'),
                clinica_id=usuario.get('clinica_id')
            )
            medico_nome = medico.nome_completo
            medico_crm = medico.crm or ''
        except Usuario.DoesNotExist:
            medico_nome = usuario.get('nome', '')
            medico_crm = ''
        
        # Adicionar "Dr." se não tiver
        if not medico_nome.startswith('Dr.'):
            medico_nome = f"Dr. {medico_nome}"
        
        consulta.medico_responsavel = medico_nome
        consulta.medico_crm = medico_crm
        consulta.iniciar_atendimento()
        
        # Atualizar agendamento se existir
        if consulta.agendamento:
            consulta.agendamento.status = 'Realizado'
            consulta.agendamento.save(update_fields=['status'])
        
        serializer = ConsultaSerializer(consulta, context={'request': request})
        return Response({
            'mensagem': 'Atendimento iniciado',
            'consulta': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='enviar-audio')
    def enviar_audio(self, request, pk=None):
        """
        Enviar áudio da consulta
        POST /api/consultas/{id}/enviar-audio/
        
        Body:
        - audio_base64: áudio em base64
        - audio_formato: formato do áudio (webm, mp3, wav)
        - audio_duracao: duração em segundos
        """
        consulta = self.get_object()
        
        if consulta.status not in ['em_atendimento', 'gravando']:
            return Response({
                'erro': 'Consulta não está em atendimento'
            }, status=400)
        
        audio_base64 = request.data.get('audio_base64')
        if not audio_base64:
            return Response({'erro': 'Áudio não fornecido'}, status=400)
        
        # Salvar áudio
        consulta.audio_consulta = audio_base64
        consulta.audio_formato = request.data.get('audio_formato', 'webm')
        consulta.audio_duracao_segundos = request.data.get('audio_duracao', 0)
        consulta.status = 'gravando'
        consulta.save()
        
        serializer = ConsultaSerializer(consulta, context={'request': request})
        return Response({
            'mensagem': 'Áudio recebido com sucesso',
            'consulta': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='transcrever')
    def transcrever(self, request, pk=None):
        """
        Transcrever áudio da consulta
        POST /api/consultas/{id}/transcrever/
        """
        consulta = self.get_object()
        
        if not consulta.audio_consulta:
            return Response({
                'erro': 'Consulta não possui áudio gravado'
            }, status=400)
        
        if consulta.status == 'transcrevendo':
            return Response({
                'erro': 'Consulta já está sendo transcrita'
            }, status=400)
        
        # Processar transcrição
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resultado = loop.run_until_complete(
                transcrever_consulta_com_gemini(consulta.id)
            )
            
            if resultado['sucesso']:
                consulta.refresh_from_db()
                serializer = ConsultaSerializer(consulta, context={'request': request})
                return Response({
                    'mensagem': 'Transcrição concluída',
                    'consulta': serializer.data,
                    'tempo_processamento': resultado['tempo_processamento']
                })
            else:
                return Response({
                    'erro': 'Erro na transcrição',
                    'detalhes': resultado['erro']
                }, status=500)
        finally:
            loop.close()
    
    @action(detail=True, methods=['post'], url_path='gerar-documento')
    def gerar_documento(self, request, pk=None):
        """
        Gerar documento médico
        POST /api/consultas/{id}/gerar-documento/
        
        Body:
        - tipo: 'atestado', 'anamnese', 'evolucao', 'prescricao', 'relatorio'
        """
        consulta = self.get_object()
        tipo = request.data.get('tipo')
        
        if not tipo:
            return Response({'erro': 'Tipo de documento não fornecido'}, status=400)
        
        tipos_validos = ['atestado', 'anamnese', 'evolucao', 'prescricao', 'relatorio']
        if tipo not in tipos_validos:
            return Response({
                'erro': f'Tipo inválido. Use: {", ".join(tipos_validos)}'
            }, status=400)
        
        # Verificar se já tem médico
        if not consulta.medico_responsavel or not consulta.medico_crm:
            return Response({
                'erro': 'Consulta sem médico responsável'
            }, status=400)
        
        # Marcar status
        consulta.status = 'gerando_documentos'
        consulta.save(update_fields=['status'])
        
        # Gerar documento
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resultado = loop.run_until_complete(
                gerar_documento_medico(
                    consulta.id,
                    tipo,
                    consulta.medico_responsavel,
                    consulta.medico_crm
                )
            )
            
            if resultado['sucesso']:
                return Response({
                    'mensagem': 'Documento gerado com sucesso',
                    'documento': {
                        'tipo': resultado['tipo'],
                        'conteudo': resultado['conteudo'],
                        'data_geracao': resultado['data_geracao']
                    }
                })
            else:
                consulta.status = 'aguardando_revisao'
                consulta.save(update_fields=['status'])
                return Response({
                    'erro': 'Erro ao gerar documento',
                    'detalhes': resultado['erro']
                }, status=500)
        finally:
            loop.close()
    
    @action(detail=True, methods=['post'], url_path='salvar-documento')
    def salvar_documento(self, request, pk=None):
        """
        Salvar documento médico (após revisão/edição)
        POST /api/consultas/{id}/salvar-documento/
        
        Body:
        - tipo: tipo do documento
        - conteudo: conteúdo do documento (pode estar editado)
        - editado: true/false se foi editado pelo médico
        """
        consulta = self.get_object()
        
        tipo = request.data.get('tipo')
        conteudo = request.data.get('conteudo')
        editado = request.data.get('editado', False)
        
        if not tipo or not conteudo:
            return Response({
                'erro': 'Tipo e conteúdo são obrigatórios'
            }, status=400)
        
        # Salvar no campo específico
        campo_map = {
            'atestado': 'atestado_medico',
            'anamnese': 'anamnese_documento',
            'evolucao': 'evolucao_medica',
            'prescricao': 'prescricao_documento',
            'relatorio': 'relatorio_medico'
        }
        
        campo = campo_map.get(tipo)
        if campo:
            setattr(consulta, campo, conteudo)
        
        # Adicionar ao histórico de documentos
        documento_info = {
            'tipo': tipo,
            'data_geracao': timezone.now().isoformat(),
            'editado': editado,
            'medico': consulta.medico_responsavel,
            'crm': consulta.medico_crm
        }
        
        if not consulta.documentos_gerados:
            consulta.documentos_gerados = []
        
        # Verificar se já existe e atualizar, senão adicionar
        encontrado = False
        for i, doc in enumerate(consulta.documentos_gerados):
            if doc.get('tipo') == tipo:
                consulta.documentos_gerados[i] = documento_info
                encontrado = True
                break
        
        if not encontrado:
            consulta.documentos_gerados.append(documento_info)
        
        consulta.save()
        
        serializer = ConsultaSerializer(consulta, context={'request': request})
        return Response({
            'mensagem': 'Documento salvo com sucesso',
            'consulta': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        """
        Finalizar consulta
        POST /api/consultas/{id}/finalizar/
        """
        consulta = self.get_object()
        
        if consulta.status == 'finalizada':
            return Response({'erro': 'Consulta já finalizada'}, status=400)
        
        consulta.finalizar_atendimento()
        
        serializer = ConsultaSerializer(consulta, context={'request': request})
        return Response({
            'mensagem': 'Consulta finalizada com sucesso',
            'consulta': serializer.data
        })
    
    @action(detail=True, methods=['get'], url_path='documentos')
    def listar_documentos(self, request, pk=None):
        """
        Listar todos os documentos da consulta
        GET /api/consultas/{id}/documentos/
        """
        consulta = self.get_object()
        
        documentos = []
        
        if consulta.atestado_medico:
            documentos.append({
                'tipo': 'atestado',
                'titulo': 'Atestado Médico',
                'conteudo': consulta.atestado_medico
            })
        
        if consulta.anamnese_documento:
            documentos.append({
                'tipo': 'anamnese',
                'titulo': 'Anamnese',
                'conteudo': consulta.anamnese_documento
            })
        
        if consulta.evolucao_medica:
            documentos.append({
                'tipo': 'evolucao',
                'titulo': 'Evolução Médica',
                'conteudo': consulta.evolucao_medica
            })
        
        if consulta.prescricao_documento:
            documentos.append({
                'tipo': 'prescricao',
                'titulo': 'Prescrição Médica',
                'conteudo': consulta.prescricao_documento
            })
        
        if consulta.relatorio_medico:
            documentos.append({
                'tipo': 'relatorio',
                'titulo': 'Relatório Médico',
                'conteudo': consulta.relatorio_medico
            })
        
        return Response({
            'consulta_id': consulta.id,
            'paciente': consulta.paciente.nome_completo,
            'data_consulta': consulta.data_consulta,
            'medico': consulta.medico_responsavel,
            'total_documentos': len(documentos),
            'documentos': documentos,
            'historico': consulta.documentos_gerados
        })

# ============================================
# VIEWSET EXAME
# ============================================

class ExameViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Exames e Interpretação por IA
    
    Endpoints:
    - GET /api/exames/ - Listar exames
    - POST /api/exames/ - Criar exame
    - POST /api/exames/upload-ia/ - Upload e interpretação por IA
    - GET /api/exames/{id}/ - Obter exame
    - PUT /api/exames/{id}/ - Atualizar exame
    - PATCH /api/exames/{id}/ - Atualizar parcial
    - DELETE /api/exames/{id}/ - Excluir exame
    - POST /api/exames/{id}/interpretar-ia/ - Interpretar exame existente
    - POST /api/exames/{id}/revisar-medico/ - Adicionar revisão médica
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrMedico] 
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['paciente__nome_completo', 'tipo_exame']
    ordering_fields = ['data_exame']
    ordering = ['-data_exame']
    
    def get_queryset(self):
        """Filtrar exames pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        queryset = Exame.objects.filter(clinica_id=clinica_id)
        
        # Filtros via query params
        paciente_id = self.request.query_params.get('paciente_id', None)
        status = self.request.query_params.get('status', None)
        tipo = self.request.query_params.get('tipo', None)
        interpretado_ia = self.request.query_params.get('interpretado_ia', None)
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if tipo:
            queryset = queryset.filter(tipo_exame=tipo)
        
        if interpretado_ia == 'true':
            queryset = queryset.filter(status__in=['interpretado_ia', 'revisado_medico', 'finalizado'])
        elif interpretado_ia == 'false':
            queryset = queryset.exclude(status__in=['interpretado_ia', 'revisado_medico', 'finalizado'])
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return ExameListSerializer
        return ExameSerializer
    
    @action(detail=False, methods=['post'], url_path='upload-ia')
    def upload_interpretar_ia(self, request):
        """
        Upload de arquivo de exame e interpretação automática por IA
        POST /api/exames/upload-ia/
        
        Body (multipart/form-data ou JSON):
        - paciente_id: ID do paciente (obrigatório)
        - arquivo: arquivo do exame (imagem ou PDF)
        - tipo_exame: tipo do exame (opcional, IA identificará)
        - data_exame: data do exame (opcional, padrão hoje)
        - medico_solicitante: nome do médico (opcional)
        - medico_solicitante_crm: CRM do médico (opcional)
        - observacoes: observações adicionais (opcional)
        """
        clinica_id = request.user.get('clinica_id')
        usuario_nome = request.user.get('nome', '')
        
        # Validar paciente
        paciente_id = request.data.get('paciente_id')
        if not paciente_id:
            return Response({'erro': 'paciente_id é obrigatório'}, status=400)
        
        try:
            paciente = Paciente.objects.get(id=paciente_id, clinica_id=clinica_id)
        except Paciente.DoesNotExist:
            return Response({'erro': 'Paciente não encontrado'}, status=404)
        
        # Processar arquivo
        arquivo = request.FILES.get('arquivo')
        arquivo_base64 = request.data.get('arquivo_base64')
        
        if not arquivo and not arquivo_base64:
            return Response({'erro': 'Arquivo é obrigatório'}, status=400)
        
        # Converter arquivo para base64
        if arquivo:
            arquivo_bytes = arquivo.read()
            arquivo_base64_str = base64.b64encode(arquivo_bytes).decode('utf-8')
            arquivo_nome = arquivo.name
            arquivo_tipo = arquivo.content_type
            
            # Adicionar prefixo data: para compatibilidade
            arquivo_base64_completo = f"data:{arquivo_tipo};base64,{arquivo_base64_str}"
        else:
            # Já veio em base64
            arquivo_base64_completo = arquivo_base64
            arquivo_nome = request.data.get('arquivo_nome', 'exame.pdf')
            arquivo_tipo = request.data.get('arquivo_tipo', 'application/pdf')
        
        # Criar exame
        exame = Exame.objects.create(
            clinica_id=clinica_id,
            paciente=paciente,
            tipo_exame=request.data.get('tipo_exame', 'outros'),
            data_exame=request.data.get('data_exame', date.today()),
            arquivo_exame=arquivo_base64_completo,
            arquivo_nome=arquivo_nome,
            arquivo_tipo=arquivo_tipo,
            medico_solicitante=request.data.get('medico_solicitante', usuario_nome),
            medico_solicitante_crm=request.data.get('medico_solicitante_crm', ''),
            observacoes=request.data.get('observacoes', ''),
            status='enviado_ia'
        )
        
        # Processar com IA de forma assíncrona
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resultado = loop.run_until_complete(interpretar_exame_com_gemini(exame.id))
            
            if resultado['sucesso']:
                exame.refresh_from_db()
                serializer = ExameSerializer(exame, context={'request': request})
                return Response({
                    'mensagem': 'Exame interpretado com sucesso',
                    'exame': serializer.data,
                    'tempo_processamento': resultado['tempo_processamento']
                }, status=201)
            else:
                return Response({
                    'erro': 'Erro ao interpretar exame',
                    'detalhes': resultado['erro']
                }, status=500)
        finally:
            loop.close()
    
    @action(detail=True, methods=['post'], url_path='interpretar-ia')
    def interpretar_ia(self, request, pk=None):
        """
        Interpretar exame existente com IA
        POST /api/exames/{id}/interpretar-ia/
        """
        exame = self.get_object()
        
        if not exame.arquivo_exame:
            return Response({'erro': 'Exame não possui arquivo anexado'}, status=400)
        
        if exame.status in ['processando_ia']:
            return Response({'erro': 'Exame já está sendo processado'}, status=400)
        
        # Processar com IA
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resultado = loop.run_until_complete(interpretar_exame_com_gemini(exame.id))
            
            if resultado['sucesso']:
                exame.refresh_from_db()
                serializer = ExameSerializer(exame, context={'request': request})
                return Response({
                    'mensagem': 'Exame interpretado com sucesso',
                    'exame': serializer.data
                })
            else:
                return Response({
                    'erro': 'Erro ao interpretar exame',
                    'detalhes': resultado['erro']
                }, status=500)
        finally:
            loop.close()
    
    @action(detail=True, methods=['post'], url_path='revisar-medico')
    def revisar_medico(self, request, pk=None):
        """
        Adicionar revisão médica ao laudo de IA
        POST /api/exames/{id}/revisar-medico/
        
        Body:
        - observacoes_medico: observações do médico revisor
        - medico_crm: CRM do médico (opcional, pega do usuário logado)
        """
        exame = self.get_object()
        usuario = request.user.payload
        
        if exame.status not in ['interpretado_ia', 'revisado_medico']:
            return Response({
                'erro': 'Exame deve estar interpretado pela IA antes de ser revisado'
            }, status=400)
        
        # Buscar dados do médico logado
        try:
            medico = Usuario.objects.get(
                id=usuario.get('sub'),
                clinica_id=usuario.get('clinica_id')
            )
            
            medico_nome = f"Dr. {medico.nome_completo}" if not medico.nome_completo.startswith('Dr.') else medico.nome_completo
            medico_crm = request.data.get('medico_crm', medico.crm or '')
        except Usuario.DoesNotExist:
            medico_nome = f"Dr. {usuario.get('nome', '')}"
            medico_crm = request.data.get('medico_crm', '')
        
        # Atualizar exame com revisão
        exame.revisado_por_medico = True
        exame.medico_revisor_nome = medico_nome
        exame.medico_revisor_crm = medico_crm
        exame.data_revisao = timezone.now()
        exame.observacoes_medico = request.data.get('observacoes_medico', '')
        exame.status = 'revisado_medico'
        
        # Adicionar revisão ao laudo
        if exame.interpretacao_ia:
            revisao_texto = f"""

═══════════════════════════════════════════════════════════════════════════════════════

REVISÃO MÉDICA:

Médico Revisor: {medico_nome}
CRM: {medico_crm}
Data da Revisão: {timezone.now().strftime('%d/%m/%Y às %H:%M')}

OBSERVAÇÕES DO MÉDICO REVISOR:
{exame.observacoes_medico}

═══════════════════════════════════════════════════════════════════════════════════════
✓ Laudo revisado e validado por médico habilitado
═══════════════════════════════════════════════════════════════════════════════════════
"""
            exame.interpretacao_ia += revisao_texto
        
        exame.save()
        
        serializer = ExameSerializer(exame, context={'request': request})
        return Response({
            'mensagem': 'Revisão médica adicionada com sucesso',
            'exame': serializer.data
        })
    
    @action(detail=True, methods=['patch'])
    def alterar_status(self, request, pk=None):
        """
        Alterar status do exame
        PATCH /api/exames/{id}/alterar_status/
        Body: {"status": "finalizado"}
        """
        exame = self.get_object()
        novo_status = request.data.get('status')
        
        if not novo_status:
            return Response({'erro': 'Status não fornecido'}, status=400)
        
        if novo_status not in dict(Exame.STATUS_CHOICES):
            return Response({'erro': 'Status inválido'}, status=400)
        
        exame.status = novo_status
        exame.save()
        
        serializer = ExameSerializer(exame, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estatisticas_ia(self, request):
        """
        Estatísticas de uso da IA para interpretação de exames
        GET /api/exames/estatisticas_ia/
        """
        clinica_id = request.user.get('clinica_id')
        
        exames = Exame.objects.filter(clinica_id=clinica_id)

        total = exames.count()
        interpretados_ia = exames.filter(status__in=['interpretado_ia', 'revisado_medico', 'finalizado']).count()
        revisados = exames.filter(revisado_por_medico=True).count()
        processando = exames.filter(status='processando_ia').count()
        erros = exames.filter(status='erro_ia').count()
        
        # Tempo médio de processamento
        tempo_medio = exames.filter(
            tempo_processamento__isnull=False
        ).aggregate(media=models.Avg('tempo_processamento'))['media']
        
        # Confiança média da IA
        confianca_media = exames.filter(
            confianca_ia__isnull=False
        ).aggregate(media=models.Avg('confianca_ia'))['media']
        
        # Taxa de revisão médica
        taxa_revisao = (revisados / interpretados_ia * 100) if interpretados_ia > 0 else 0
        
        # Tipos de exames mais interpretados
        top_tipos = exames.filter(
            status__in=['interpretado_ia', 'revisado_medico', 'finalizado']
        ).values('tipo_exame').annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        return Response({
            'total_exames': total,
            'interpretados_ia': interpretados_ia,
            'revisados_medico': revisados,
            'processando': processando,
            'erros': erros,
            'tempo_medio_segundos': float(tempo_medio) if tempo_medio else 0,
            'confianca_media': float(confianca_media) if confianca_media else 0,
            'taxa_revisao_medica': round(taxa_revisao, 1),
            'top_tipos_exames': list(top_tipos)
        })
    
# ============================================
# VIEWSET CATEGORIA RECEITA
# ============================================

class CategoriaReceitaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Categorias de Receita
    
    Endpoints:
    - GET /api/faturamento/categorias/receitas/ - Listar categorias
    - POST /api/faturamento/categorias/receitas/ - Criar categoria
    - GET /api/faturamento/categorias/receitas/{id}/ - Obter categoria
    - PUT /api/faturamento/categorias/receitas/{id}/ - Atualizar categoria
    - DELETE /api/faturamento/categorias/receitas/{id}/ - Excluir categoria
    """
    
    serializer_class = CategoriaReceitaSerializer
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    ordering = ['nome']
    
    def get_queryset(self):
        """Filtrar categorias pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        return CategoriaReceita.objects.filter(clinica_id=clinica_id, ativo=True)

# ============================================
# VIEWSET CATEGORIA DESPESA
# ============================================

class CategoriaDespesaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Categorias de Despesa
    
    Endpoints:
    - GET /api/faturamento/categorias/despesas/ - Listar categorias
    - POST /api/faturamento/categorias/despesas/ - Criar categoria
    - GET /api/faturamento/categorias/despesas/{id}/ - Obter categoria
    - PUT /api/faturamento/categorias/despesas/{id}/ - Atualizar categoria
    - DELETE /api/faturamento/categorias/despesas/{id}/ - Excluir categoria
    """
    
    serializer_class = CategoriaDespesaSerializer
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    ordering = ['nome']
    
    def get_queryset(self):
        """Filtrar categorias pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        return CategoriaDespesa.objects.filter(clinica_id=clinica_id, ativo=True)

# ============================================
# VIEWSET RECEITA
# ============================================

class ReceitaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Receitas
    
    Endpoints:
    - GET /api/faturamento/receitas/ - Listar receitas
    - POST /api/faturamento/receitas/ - Criar receita
    - GET /api/faturamento/receitas/{id}/ - Obter receita
    - PUT /api/faturamento/receitas/{id}/ - Atualizar receita
    - DELETE /api/faturamento/receitas/{id}/ - Excluir receita
    """
    
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao']
    ordering_fields = ['data_vencimento', 'valor']
    ordering = ['-data_vencimento']
    
    def get_queryset(self):
        """Filtrar receitas pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        
        # Atualizar status vencidos antes de listar
        Receita.atualizar_status_vencidos(clinica_id)
        
        queryset = Receita.objects.filter(clinica_id=clinica_id)
        
        # Filtros via query params
        status = self.request.query_params.get('status', None)
        categoria_id = self.request.query_params.get('categoria_id', None)
        paciente_id = self.request.query_params.get('paciente_id', None)
        data_inicial = self.request.query_params.get('data_inicial', None)
        data_final = self.request.query_params.get('data_final', None)
        mes = self.request.query_params.get('mes', None)
        ano = self.request.query_params.get('ano', None)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        if data_inicial and data_final:
            queryset = queryset.filter(data_vencimento__range=[data_inicial, data_final])
        elif mes and ano:
            queryset = queryset.filter(data_vencimento__year=ano, data_vencimento__month=mes)
        elif ano:
            queryset = queryset.filter(data_vencimento__year=ano)
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return ReceitaListSerializer
        return ReceitaSerializer
    
    @action(detail=True, methods=['post'])
    def receber(self, request, pk=None):
        """
        Marcar receita como recebida
        POST /api/faturamento/receitas/{id}/receber/
        Body: {"data_recebimento": "2025-10-05", "forma_pagamento": "PIX"}
        """
        receita = self.get_object()
        data_recebimento = request.data.get('data_recebimento', date.today())
        forma_pagamento = request.data.get('forma_pagamento')
        
        if not forma_pagamento:
            return Response({'erro': 'Forma de pagamento não fornecida'}, status=400)
        
        receita.marcar_como_recebida(data_recebimento, forma_pagamento)
        
        serializer = ReceitaSerializer(receita, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def receber_de_agendamento(self, request):
        """
        Criar receita a partir de agendamento realizado
        POST /api/faturamento/receitas/receber_de_agendamento/
        Body: {"agendamento_id": 123, "forma_pagamento": "PIX"}
        """
        agendamento_id = request.data.get('agendamento_id')
        forma_pagamento = request.data.get('forma_pagamento')
        
        if not agendamento_id or not forma_pagamento:
            return Response({'erro': 'Dados incompletos'}, status=400)
        
        clinica_id = request.user.get('clinica_id')
        
        try:
            agendamento = Agendamento.objects.get(id=agendamento_id, clinica_id=clinica_id)
        except Agendamento.DoesNotExist:
            return Response({'erro': 'Agendamento não encontrado'}, status=404)
        
        # Verificar se está realizado
        if agendamento.status != 'Realizado':
            return Response({'erro': 'Agendamento deve estar com status "Realizado"'}, status=400)
        
        # Verificar se tem valor
        if not agendamento.valor or agendamento.valor <= 0:
            return Response({'erro': 'Agendamento não possui valor definido'}, status=400)
        
        # Verificar se já existe receita
        if Receita.objects.filter(agendamento=agendamento).exists():
            return Response({'erro': 'Já existe receita para este agendamento'}, status=400)
        
        # Buscar categoria apropriada
        categoria = None
        if agendamento.servico == 'Consulta':
            categoria = CategoriaReceita.objects.filter(clinica_id=clinica_id, nome='Consultas').first()
        elif agendamento.servico == 'Exame':
            categoria = CategoriaReceita.objects.filter(clinica_id=clinica_id, nome='Exames').first()
        
        # Criar receita
        receita = Receita.objects.create(
            clinica_id=clinica_id,
            descricao=f"{agendamento.servico} - {agendamento.paciente_nome}",
            valor=agendamento.valor,
            categoria=categoria,
            data_vencimento=agendamento.data,
            data_recebimento=date.today(),
            status='recebida',
            agendamento=agendamento,
            paciente=agendamento.paciente,
            forma_pagamento=forma_pagamento,
            observacoes=f"Recebimento de {agendamento.tipo} - {agendamento.data}"
        )
        
        serializer = ReceitaSerializer(receita, context={'request': request})
        return Response(serializer.data, status=201)
    
    @action(detail=False, methods=['get'])
    def agendamentos_pendentes(self, request):
        """
        Listar agendamentos realizados pendentes de recebimento
        GET /api/faturamento/receitas/agendamentos_pendentes/
        """
        clinica_id = request.user.get('clinica_id')
        
        # Buscar agendamentos realizados com valor
        agendamentos = Agendamento.objects.filter(
            clinica_id=clinica_id,
            status='Realizado',
            valor__gt=0
        )
        
        # Filtrar apenas os que não têm receita
        pendentes = []
        for agend in agendamentos:
            if not Receita.objects.filter(agendamento=agend).exists():
                pendentes.append(AgendamentoSerializer(agend, context={'request': request}).data)
        
        return Response({
            'agendamentos': pendentes,
            'total': len(pendentes)
        })

# ============================================
# VIEWSET DESPESA
# ============================================

class DespesaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Despesas
    
    Endpoints:
    - GET /api/faturamento/despesas/ - Listar despesas
    - POST /api/faturamento/despesas/ - Criar despesa
    - GET /api/faturamento/despesas/{id}/ - Obter despesa
    - PUT /api/faturamento/despesas/{id}/ - Atualizar despesa
    - DELETE /api/faturamento/despesas/{id}/ - Excluir despesa
    """
    
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao', 'fornecedor']
    ordering_fields = ['data_vencimento', 'valor']
    ordering = ['-data_vencimento']
    
    def get_queryset(self):
        """Filtrar despesas pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        
        # Atualizar status vencidos antes de listar
        Despesa.atualizar_status_vencidos(clinica_id)
        
        queryset = Despesa.objects.filter(clinica_id=clinica_id)
        
        # Filtros via query params
        status = self.request.query_params.get('status', None)
        categoria_id = self.request.query_params.get('categoria_id', None)
        data_inicial = self.request.query_params.get('data_inicial', None)
        data_final = self.request.query_params.get('data_final', None)
        mes = self.request.query_params.get('mes', None)
        ano = self.request.query_params.get('ano', None)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        if data_inicial and data_final:
            queryset = queryset.filter(data_vencimento__range=[data_inicial, data_final])
        elif mes and ano:
            queryset = queryset.filter(data_vencimento__year=ano, data_vencimento__month=mes)
        elif ano:
            queryset = queryset.filter(data_vencimento__year=ano)
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return DespesaListSerializer
        return DespesaSerializer
    
    @action(detail=True, methods=['post'])
    def pagar(self, request, pk=None):
        """
        Marcar despesa como paga
        POST /api/faturamento/despesas/{id}/pagar/
        Body: {"data_pagamento": "2025-10-05", "forma_pagamento": "PIX"}
        """
        despesa = self.get_object()
        data_pagamento = request.data.get('data_pagamento', date.today())
        forma_pagamento = request.data.get('forma_pagamento')
        
        if not forma_pagamento:
            return Response({'erro': 'Forma de pagamento não fornecida'}, status=400)
        
        despesa.marcar_como_paga(data_pagamento, forma_pagamento)
        
        serializer = DespesaSerializer(despesa, context={'request': request})
        return Response(serializer.data)

# ============================================
# VIEW DASHBOARD FINANCEIRO
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_financeiro(request):
    """
    Dashboard com estatísticas financeiras
    GET /api/faturamento/dashboard/
    
    Query params opcionais:
    - data_inicial: filtro de data inicial
    - data_final: filtro de data final
    - mes: filtro por mês
    - ano: filtro por ano
    """
    clinica_id = request.user.get('clinica_id')
    
    # Atualizar status vencidos
    Receita.atualizar_status_vencidos(clinica_id)
    Despesa.atualizar_status_vencidos(clinica_id)
    
    # Preparar filtros
    filtros = {}
    data_inicial = request.query_params.get('data_inicial')
    data_final = request.query_params.get('data_final')
    mes = request.query_params.get('mes')
    ano = request.query_params.get('ano')
    
    if data_inicial and data_final:
        filtros['data_vencimento__range'] = [data_inicial, data_final]
    elif mes and ano:
        filtros['data_vencimento__year'] = ano
        filtros['data_vencimento__month'] = mes
    elif ano:
        filtros['data_vencimento__year'] = ano
    
    # Calcular receitas
    receitas = Receita.objects.filter(clinica_id=clinica_id, **filtros)
    receitas_recebidas = receitas.filter(status='recebida').aggregate(total=Sum('valor'))['total'] or 0
    receitas_a_receber = receitas.filter(status='a_receber').aggregate(total=Sum('valor'))['total'] or 0
    receitas_vencidas = receitas.filter(status='vencida').aggregate(total=Sum('valor'))['total'] or 0
    
    # Calcular despesas
    despesas = Despesa.objects.filter(clinica_id=clinica_id, **filtros)
    despesas_pagas = despesas.filter(status='paga').aggregate(total=Sum('valor'))['total'] or 0
    despesas_a_pagar = despesas.filter(status='a_pagar').aggregate(total=Sum('valor'))['total'] or 0
    despesas_vencidas = despesas.filter(status='vencida').aggregate(total=Sum('valor'))['total'] or 0
    
    # Calcular totais
    total_receitas = float(receitas_recebidas)
    total_despesas = float(despesas_pagas)
    lucro_liquido = total_receitas - total_despesas
    
    return Response({
        'receitas': {
            'recebidas': float(receitas_recebidas),
            'a_receber': float(receitas_a_receber),
            'vencidas': float(receitas_vencidas),
            'total': total_receitas
        },
        'despesas': {
            'pagas': float(despesas_pagas),
            'a_pagar': float(despesas_a_pagar),
            'vencidas': float(despesas_vencidas),
            'total': total_despesas
        },
        'lucro_liquido': lucro_liquido,
        'a_receber': float(receitas_a_receber)
    })

# ============================================
# VIEW DADOS DA CLÍNICA COMPLETO
# ============================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def dados_clinica_completo(request):
    """
    Retorna dados completos da clínica/consultório
    GET /api/dados-clinica/
    
    Retorna:
    - Dados cadastrais da clínica
    - Estatísticas gerais
    - Lista de usuários
    - Métricas de uso do sistema
    - Informações financeiras resumidas
    - Dados de pacientes e agendamentos
    """
    user = request.user
    clinica_id = user.payload.get('clinica_id')
    funcao = user.payload.get('funcao')
    
    # Super admin pode ver qualquer clínica via query param
    if funcao == 'super_admin':
        clinica_id_param = request.query_params.get('clinica_id')
        if clinica_id_param:
            clinica_id = int(clinica_id_param)
    
    if not clinica_id:
        return Response({
            'erro': 'Usuário sem clínica vinculada'
        }, status=400)
    
    try:
        clinica = Clinica.objects.get(id=clinica_id)
    except Clinica.DoesNotExist:
        return Response({
            'erro': 'Clínica não encontrada'
        }, status=404)
    
    # ============================================
    # 1. DADOS CADASTRAIS DA CLÍNICA
    # ============================================
    
    dados_clinica = {
        'id': clinica.id,
        'nome': clinica.nome,
        'cnpj': clinica.cnpj,
        'status': clinica.status,
        'status_display': clinica.get_status_display(),
        'contato': {
            'telefone': clinica.telefone,
            'email': clinica.email,
        },
        'endereco': {
            'logradouro': clinica.logradouro,
            'numero': clinica.numero,
            'bairro': clinica.bairro,
            'cidade': clinica.cidade,
            'estado': clinica.estado,
            'cep': clinica.cep,
            'endereco_completo': f"{clinica.logradouro}, {clinica.numero} - {clinica.bairro}, {clinica.cidade}/{clinica.estado} - CEP: {clinica.cep}"
        },
        'responsavel': {
            'nome': clinica.responsavel_nome,
            'cpf': clinica.responsavel_cpf,
            'telefone': clinica.responsavel_telefone,
            'email': clinica.responsavel_email,
        },
        'datas': {
            'cadastro': clinica.data_cadastro,
            'atualizacao': clinica.data_atualizacao,
            'dias_cadastrado': (timezone.now() - clinica.data_cadastro).days
        }
    }
    
    # ============================================
    # 2. USUÁRIOS DA CLÍNICA
    # ============================================
    
    usuarios = Usuario.objects.filter(clinica_id=clinica_id)
    
    usuarios_lista = []
    for usuario in usuarios:
        usuarios_lista.append({
            'id': usuario.id,
            'nome_completo': usuario.nome_completo,
            'email': usuario.email,
            'cpf': usuario.cpf,
            'telefone': usuario.telefone_celular,
            'funcao': usuario.funcao,
            'funcao_display': usuario.get_funcao_display(),
            'status': usuario.status,
            'status_display': usuario.get_status_display(),
            'crm': usuario.crm,
            'especialidade': usuario.especialidade,
            'last_login': usuario.last_login,
            'data_cadastro': usuario.data_cadastro,
        })
    
    # Estatísticas de usuários por função
    usuarios_por_funcao = {
        'admin': usuarios.filter(funcao='admin').count(),
        'medico': usuarios.filter(funcao='medico').count(),
        'secretaria': usuarios.filter(funcao='secretaria').count(),
    }
    
    usuarios_por_status = {
        'ativo': usuarios.filter(status='ativo').count(),
        'inativo': usuarios.filter(status='inativo').count(),
        'alerta': usuarios.filter(status='alerta').count(),
    }
    
    # ============================================
    # 3. ESTATÍSTICAS GERAIS DO SISTEMA
    # ============================================
    
    # Pacientes
    total_pacientes = Paciente.objects.filter(clinica_id=clinica_id, ativo=True).count()
    pacientes_por_convenio = Paciente.objects.filter(
        clinica_id=clinica_id, 
        ativo=True
    ).values('convenio').annotate(total=Count('id')).order_by('-total')[:5]
    
    # Agendamentos
    hoje = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    total_agendamentos = Agendamento.objects.filter(clinica_id=clinica_id).count()
    agendamentos_mes = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__year=ano_atual,
        data__month=mes_atual
    ).count()
    
    agendamentos_hoje = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data=hoje
    ).count()
    
    proximos_7_dias = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gte=hoje,
        data__lte=hoje + timedelta(days=7),
        status__in=['Agendado', 'Confirmado']
    ).count()
    
    agendamentos_por_status = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__year=ano_atual,
        data__month=mes_atual
    ).values('status').annotate(total=Count('id'))
    
    # Consultas
    total_consultas = Consulta.objects.filter(clinica_id=clinica_id).count()
    consultas_mes = Consulta.objects.filter(
        clinica_id=clinica_id,
        data_consulta__year=ano_atual,
        data_consulta__month=mes_atual
    ).count()
    
    consultas_por_status = Consulta.objects.filter(
        clinica_id=clinica_id,
        data_consulta__year=ano_atual,
        data_consulta__month=mes_atual
    ).values('status').annotate(total=Count('id'))
    
    # Exames
    total_exames = Exame.objects.filter(clinica_id=clinica_id).count()
    exames_mes = Exame.objects.filter(
        clinica_id=clinica_id,
        data_exame__year=ano_atual,
        data_exame__month=mes_atual
    ).count()
    
    exames_por_tipo = Exame.objects.filter(
        clinica_id=clinica_id,
        data_exame__year=ano_atual,
        data_exame__month=mes_atual
    ).values('tipo_exame').annotate(total=Count('id')).order_by('-total')[:5]
    
    # ============================================
    # 4. DADOS FINANCEIROS RESUMIDOS
    # ============================================
    
    # Atualizar status vencidos
    Receita.atualizar_status_vencidos(clinica_id)
    Despesa.atualizar_status_vencidos(clinica_id)
    
    # Receitas do mês
    receitas_mes = Receita.objects.filter(
        clinica_id=clinica_id,
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    )
    
    receitas_recebidas_mes = receitas_mes.filter(status='recebida').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    receitas_a_receber_mes = receitas_mes.filter(status='a_receber').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    receitas_vencidas = receitas_mes.filter(status='vencida').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    # Despesas do mês
    despesas_mes = Despesa.objects.filter(
        clinica_id=clinica_id,
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual
    )
    
    despesas_pagas_mes = despesas_mes.filter(status='paga').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    despesas_a_pagar_mes = despesas_mes.filter(status='a_pagar').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    despesas_vencidas = despesas_mes.filter(status='vencida').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    # Totais gerais
    total_receitas_recebidas = Receita.objects.filter(
        clinica_id=clinica_id,
        status='recebida'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    total_despesas_pagas = Despesa.objects.filter(
        clinica_id=clinica_id,
        status='paga'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    lucro_liquido_total = float(total_receitas_recebidas) - float(total_despesas_pagas)
    lucro_liquido_mes = float(receitas_recebidas_mes) - float(despesas_pagas_mes)
    
    # Categorias mais usadas
    top_categorias_receita = Receita.objects.filter(
        clinica_id=clinica_id,
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual,
        categoria__isnull=False
    ).values('categoria__nome').annotate(
        total=Sum('valor'),
        quantidade=Count('id')
    ).order_by('-total')[:5]
    
    top_categorias_despesa = Despesa.objects.filter(
        clinica_id=clinica_id,
        data_vencimento__year=ano_atual,
        data_vencimento__month=mes_atual,
        categoria__isnull=False
    ).values('categoria__nome').annotate(
        total=Sum('valor'),
        quantidade=Count('id')
    ).order_by('-total')[:5]
    
    # ============================================
    # 5. MÉTRICAS DE USO DO SISTEMA
    # ============================================
    
    # Transcrições
    total_transcricoes = Transcricao.objects.filter(clinica_id=clinica_id).count()
    transcricoes_concluidas = Transcricao.objects.filter(
        clinica_id=clinica_id,
        status='concluida'
    ).count()
    
    # Taxa de utilização de IA
    taxa_uso_ia = (transcricoes_concluidas / total_consultas * 100) if total_consultas > 0 else 0
    
    # Últimas atividades (últimos 30 dias)
    trinta_dias_atras = hoje - timedelta(days=30)
    
    atividades_recentes = {
        'pacientes_cadastrados': Paciente.objects.filter(
            clinica_id=clinica_id,
            data_cadastro__gte=trinta_dias_atras
        ).count(),
        'agendamentos_criados': Agendamento.objects.filter(
            clinica_id=clinica_id,
            data_cadastro__gte=trinta_dias_atras
        ).count(),
        'consultas_realizadas': Consulta.objects.filter(
            clinica_id=clinica_id,
            data_consulta__gte=trinta_dias_atras
        ).count(),
        'exames_solicitados': Exame.objects.filter(
            clinica_id=clinica_id,
            data_cadastro__gte=trinta_dias_atras
        ).count(),
    }
    
    # ============================================
    # 6. ALERTAS E PENDÊNCIAS
    # ============================================
    
    alertas = []
    
    # Receitas vencidas
    if receitas_vencidas > 0:
        qtd_receitas_vencidas = receitas_mes.filter(status='vencida').count()
        alertas.append({
            'tipo': 'financeiro',
            'gravidade': 'alta',
            'titulo': 'Receitas Vencidas',
            'mensagem': f'{qtd_receitas_vencidas} receita(s) vencida(s) totalizando R$ {float(receitas_vencidas):.2f}',
            'acao': 'Verificar receitas vencidas'
        })
    
    # Despesas vencidas
    if despesas_vencidas > 0:
        qtd_despesas_vencidas = despesas_mes.filter(status='vencida').count()
        alertas.append({
            'tipo': 'financeiro',
            'gravidade': 'alta',
            'titulo': 'Despesas Vencidas',
            'mensagem': f'{qtd_despesas_vencidas} despesa(s) vencida(s) totalizando R$ {float(despesas_vencidas):.2f}',
            'acao': 'Verificar despesas vencidas'
        })
    
    # Agendamentos para hoje
    if agendamentos_hoje > 0:
        alertas.append({
            'tipo': 'operacional',
            'gravidade': 'media',
            'titulo': 'Agendamentos Hoje',
            'mensagem': f'{agendamentos_hoje} agendamento(s) para hoje',
            'acao': 'Ver agenda do dia'
        })
    
    # Exames pendentes de resultado
    exames_pendentes = Exame.objects.filter(
        clinica_id=clinica_id,
        status__in=['solicitado', 'agendado', 'realizado']
    ).count()
    
    if exames_pendentes > 0:
        alertas.append({
            'tipo': 'clinico',
            'gravidade': 'baixa',
            'titulo': 'Exames Pendentes',
            'mensagem': f'{exames_pendentes} exame(s) aguardando resultado',
            'acao': 'Verificar exames pendentes'
        })
    
    # ============================================
    # MONTAR RESPOSTA COMPLETA
    # ============================================
    
    return Response({
        'clinica': dados_clinica,
        
        'usuarios': {
            'lista': usuarios_lista,
            'total': usuarios.count(),
            'ativos': usuarios.filter(status='ativo').count(),
            'por_funcao': usuarios_por_funcao,
            'por_status': usuarios_por_status,
        },
        
        'estatisticas_gerais': {
            'pacientes': {
                'total': total_pacientes,
                'top_convenios': list(pacientes_por_convenio)
            },
            'agendamentos': {
                'total': total_agendamentos,
                'mes_atual': agendamentos_mes,
                'hoje': agendamentos_hoje,
                'proximos_7_dias': proximos_7_dias,
                'por_status': list(agendamentos_por_status)
            },
            'consultas': {
                'total': total_consultas,
                'mes_atual': consultas_mes,
                'por_status': list(consultas_por_status)
            },
            'exames': {
                'total': total_exames,
                'mes_atual': exames_mes,
                'top_tipos': list(exames_por_tipo)
            }
        },
        
        'financeiro': {
            'mes_atual': {
                'receitas': {
                    'recebidas': float(receitas_recebidas_mes),
                    'a_receber': float(receitas_a_receber_mes),
                    'vencidas': float(receitas_vencidas),
                },
                'despesas': {
                    'pagas': float(despesas_pagas_mes),
                    'a_pagar': float(despesas_a_pagar_mes),
                    'vencidas': float(despesas_vencidas),
                },
                'lucro_liquido': lucro_liquido_mes
            },
            'totais': {
                'receitas_recebidas': float(total_receitas_recebidas),
                'despesas_pagas': float(total_despesas_pagas),
                'lucro_liquido': lucro_liquido_total
            },
            'top_categorias_receita': list(top_categorias_receita),
            'top_categorias_despesa': list(top_categorias_despesa)
        },
        
        'metricas_uso': {
            'transcricoes': {
                'total': total_transcricoes,
                'concluidas': transcricoes_concluidas,
                'taxa_uso_ia': round(taxa_uso_ia, 2)
            },
            'atividades_30_dias': atividades_recentes
        },
        
        'alertas': alertas,
        
        'periodo': {
            'mes': mes_atual,
            'ano': ano_atual,
            'data_consulta': hoje.isoformat()
        }
    })

# ============================================
# VIEW DASHBOARD PRINCIPAL
# ============================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def dashboard_principal(request):
    """
    Dashboard principal do sistema - Página inicial
    GET /api/dashboard/
    
    Retorna:
    - Total de pacientes cadastrados
    - Total de agendamentos hoje
    - Total de pacientes pendentes de atendimento hoje
    - Total de agendamentos futuros
    - Lista de espera de hoje (pacientes agendados para hoje)
    - Consultas pendentes de ação
    - Estatísticas rápidas
    """
    user = request.user
    clinica_id = user.payload.get('clinica_id')
    funcao = user.payload.get('funcao')
    
    if not clinica_id:
        return Response({
            'erro': 'Usuário sem clínica vinculada'
        }, status=400)
    
    hoje = date.today()
    agora = timezone.now()
    
    # ============================================
    # 1. TOTAL DE PACIENTES CADASTRADOS
    # ============================================
    
    total_pacientes = Paciente.objects.filter(
        clinica_id=clinica_id,
        ativo=True
    ).count()
    
    # ============================================
    # 2. AGENDAMENTOS DE HOJE
    # ============================================
    
    agendamentos_hoje = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data=hoje
    ).order_by('hora')
    
    total_agendamentos_hoje = agendamentos_hoje.count()
    
    # ============================================
    # 3. PACIENTES PENDENTES DE HOJE
    # (Agendados ou Confirmados = ainda não atendidos)
    # ============================================
    
    agendamentos_pendentes_hoje = agendamentos_hoje.filter(
        status__in=['Agendado', 'Confirmado']
    )
    
    total_pendentes_hoje = agendamentos_pendentes_hoje.count()
    
    # ============================================
    # 4. AGENDAMENTOS FUTUROS
    # ============================================
    
    total_agendamentos_futuros = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gt=hoje,
        status__in=['Agendado', 'Confirmado']
    ).count()
    
    # Próximos 7 dias
    proximos_7_dias = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gt=hoje,
        data__lte=hoje + timedelta(days=7),
        status__in=['Agendado', 'Confirmado']
    ).count()
    
    # Próximos 30 dias
    proximos_30_dias = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gt=hoje,
        data__lte=hoje + timedelta(days=30),
        status__in=['Agendado', 'Confirmado']
    ).count()
    
    # ============================================
    # 5. LISTA DE ESPERA DE HOJE (HISTÓRICO)
    # ============================================
    
    lista_espera_hoje = []
    
    for agendamento in agendamentos_hoje:
        # Calcular tempo de espera se já passou da hora
        tempo_espera = None
        status_atendimento = agendamento.status
        
        # Verificar se já passou da hora do agendamento
        hora_agendamento = timezone.make_aware(
            datetime.combine(hoje, agendamento.hora)
        )
        
        if agora > hora_agendamento and status_atendimento in ['Agendado', 'Confirmado']:
            tempo_espera_segundos = (agora - hora_agendamento).total_seconds()
            tempo_espera_minutos = int(tempo_espera_segundos / 60)
            tempo_espera = f"{tempo_espera_minutos} minutos"
        
        lista_espera_hoje.append({
            'id': agendamento.id,
            'paciente_id': agendamento.paciente.id,
            'paciente_nome': agendamento.paciente_nome,
            'paciente_cpf': agendamento.paciente_cpf,
            'hora': agendamento.hora.strftime('%H:%M'),
            'servico': agendamento.servico,
            'tipo': agendamento.tipo,
            'status': agendamento.status,
            'status_display': agendamento.get_status_display(),
            'convenio': agendamento.convenio,
            'tempo_espera': tempo_espera,
            'observacoes': agendamento.observacoes
        })
    
    # ============================================
    # 6. CONSULTAS PENDENTES DE AÇÃO
    # ============================================
    
    # Consultas em atendimento ou agendadas/confirmadas
    consultas_pendentes = Consulta.objects.filter(
        clinica_id=clinica_id,
        status__in=['agendada', 'confirmada', 'em_atendimento']
    ).select_related('paciente').order_by('data_consulta')[:20]
    
    consultas_pendentes_lista = []
    
    for consulta in consultas_pendentes:
        # Calcular dias até a consulta ou dias de atraso
        dias_diferenca = (consulta.data_consulta.date() - hoje).days
        
        if dias_diferenca < 0:
            tempo_status = f"Atrasada {abs(dias_diferenca)} dia(s)"
            prioridade = "alta"
        elif dias_diferenca == 0:
            tempo_status = "Hoje"
            prioridade = "alta"
        elif dias_diferenca == 1:
            tempo_status = "Amanhã"
            prioridade = "media"
        else:
            tempo_status = f"Em {dias_diferenca} dia(s)"
            prioridade = "baixa"
        
        consultas_pendentes_lista.append({
            'id': consulta.id,
            'paciente_id': consulta.paciente.id,
            'paciente_nome': consulta.paciente.nome_completo,
            'data_consulta': consulta.data_consulta,
            'tipo_consulta': consulta.tipo_consulta,
            'tipo_consulta_display': consulta.get_tipo_consulta_display(),
            'status': consulta.status,
            'status_display': consulta.get_status_display(),
            'medico_responsavel': consulta.medico_responsavel,
            'tempo_status': tempo_status,
            'prioridade': prioridade,
            'tem_transcricao': bool(consulta.transcricao_ia),
        })
    
    # ============================================
    # 7. ESTATÍSTICAS RÁPIDAS ADICIONAIS
    # ============================================
    
    # Atendimentos realizados hoje
    atendimentos_realizados_hoje = agendamentos_hoje.filter(
        status='Realizado'
    ).count()
    
    # Faltas de hoje
    faltas_hoje = agendamentos_hoje.filter(
        status='Faltou'
    ).count()
    
    # Cancelamentos de hoje
    cancelamentos_hoje = agendamentos_hoje.filter(
        status='Cancelado'
    ).count()
    
    # Taxa de comparecimento de hoje
    if total_agendamentos_hoje > 0:
        taxa_comparecimento = (atendimentos_realizados_hoje / total_agendamentos_hoje) * 100
    else:
        taxa_comparecimento = 0
    
    # Receitas pendentes (vencidas + a vencer hoje)
    receitas_pendentes = Receita.objects.filter(
        clinica_id=clinica_id,
        status__in=['a_receber', 'vencida'],
        data_vencimento__lte=hoje
    ).count()
    
    # Despesas pendentes
    despesas_pendentes = Despesa.objects.filter(
        clinica_id=clinica_id,
        status__in=['a_pagar', 'vencida'],
        data_vencimento__lte=hoje
    ).count()
    
    # Exames pendentes de resultado
    exames_pendentes = Exame.objects.filter(
        clinica_id=clinica_id,
        status__in=['solicitado', 'agendado', 'realizado']
    ).count()
    
    # ============================================
    # 8. RESUMO DA SEMANA
    # ============================================
    
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    
    agendamentos_semana = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gte=inicio_semana,
        data__lte=fim_semana
    )
    
    resumo_semana = {
        'total': agendamentos_semana.count(),
        'realizados': agendamentos_semana.filter(status='Realizado').count(),
        'pendentes': agendamentos_semana.filter(status__in=['Agendado', 'Confirmado']).count(),
        'cancelados': agendamentos_semana.filter(status='Cancelado').count(),
    }
    
    # ============================================
    # 9. PRÓXIMO AGENDAMENTO
    # ============================================
    
    proximo_agendamento = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gte=hoje,
        status__in=['Agendado', 'Confirmado']
    ).order_by('data', 'hora').first()
    
    proximo_agendamento_data = None
    if proximo_agendamento:
        proximo_agendamento_data = {
            'id': proximo_agendamento.id,
            'paciente_nome': proximo_agendamento.paciente_nome,
            'data': proximo_agendamento.data,
            'hora': proximo_agendamento.hora.strftime('%H:%M'),
            'servico': proximo_agendamento.servico,
            'tipo': proximo_agendamento.tipo,
        }
    
    # ============================================
    # MONTAR RESPOSTA COMPLETA
    # ============================================
    
    return Response({
        'resumo_principal': {
            'total_pacientes': total_pacientes,
            'agendamentos_hoje': total_agendamentos_hoje,
            'pendentes_hoje': total_pendentes_hoje,
            'agendamentos_futuros': total_agendamentos_futuros,
            'atendimentos_realizados_hoje': atendimentos_realizados_hoje,
            'faltas_hoje': faltas_hoje,
            'cancelamentos_hoje': cancelamentos_hoje,
            'taxa_comparecimento_hoje': round(taxa_comparecimento, 1)
        },
        
        'agendamentos_futuros_detalhado': {
            'total': total_agendamentos_futuros,
            'proximos_7_dias': proximos_7_dias,
            'proximos_30_dias': proximos_30_dias,
        },
        
        'lista_espera_hoje': lista_espera_hoje,
        
        'consultas_pendentes': {
            'total': consultas_pendentes.count(),
            'lista': consultas_pendentes_lista
        },
        
        'alertas_rapidos': {
            'receitas_pendentes': receitas_pendentes,
            'despesas_pendentes': despesas_pendentes,
            'exames_pendentes': exames_pendentes,
        },
        
        'resumo_semana': resumo_semana,
        
        'proximo_agendamento': proximo_agendamento_data,
        
        'informacoes': {
            'data_atual': hoje.isoformat(),
            'hora_atual': agora.time().strftime('%H:%M:%S'),
            'dia_semana': hoje.strftime('%A'),
            'clinica_id': clinica_id,
            'usuario': user.payload.get('nome'),
            'funcao': funcao
        }
    })

# ============================================
# VIEW TERMOS DE USO IA
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def termos_uso_ia(request):
    """
    Retorna termos de uso da interpretação por IA
    GET /api/exames/termos-uso-ia/
    """
    termos = {
        'versao': '1.0',
        'data_atualizacao': '2025-10-06',
        'titulo': 'Termos de Uso - Interpretação de Exames por Inteligência Artificial',
        'conteudo': """
TERMOS DE USO - INTERPRETAÇÃO DE EXAMES POR INTELIGÊNCIA ARTIFICIAL

1. NATUREZA DO SERVIÇO
Este serviço utiliza Inteligência Artificial (Google Gemini) para interpretar exames médicos.
As interpretações fornecidas são AUXILIARES e NÃO substituem a avaliação médica profissional.

2. OBRIGATORIEDADE DE SUPERVISÃO MÉDICA
- Toda interpretação gerada por IA DEVE ser revisada por médico habilitado
- O laudo da IA é uma ferramenta de APOIO diagnóstico
- A responsabilidade final pela interpretação e conduta é EXCLUSIVAMENTE MÉDICA

3. LIMITAÇÕES DA IA
- A IA pode cometer erros de interpretação
- Fatores clínicos individuais podem não ser considerados adequadamente
- A IA não tem acesso ao histórico completo do paciente
- Resultados podem variar dependendo da qualidade da imagem/documento

4. USO ADEQUADO
- Envie apenas exames de pacientes devidamente cadastrados
- Use imagens ou PDFs de boa qualidade
- Forneça informações clínicas relevantes quando disponível
- Sempre valide os resultados com um médico

5. PRIVACIDADE E SEGURANÇA
- Todos os dados são processados de forma segura
- Exames são vinculados ao prontuário do paciente
- Acesso restrito apenas a profissionais autorizados da clínica

6. FONTES E REFERÊNCIAS
A IA consulta diretrizes médicas reconhecidas, incluindo:
- Sociedades médicas brasileiras e internacionais
- Guidelines clínicos atualizados
- Literatura médica científica validada

7. RESPONSABILIDADE
O usuário reconhece que:
- A interpretação final é de responsabilidade médica
- A IA é uma ferramenta auxiliar
- Decisões clínicas não devem se basear APENAS na interpretação da IA
- É necessária validação médica profissional

8. CONSENTIMENTO
Ao utilizar este serviço, você declara:
- Ter lido e compreendido estes termos
- Concordar com as limitações descritas
- Comprometer-se a usar o serviço de forma adequada e ética
- Garantir que haverá supervisão médica das interpretações

Data de vigência: 06 de outubro de 2025
""",
        'aceite_obrigatorio': True,
        'aviso_importante': '⚠️ ATENÇÃO: Este serviço NÃO substitui consulta médica. Toda interpretação DEVE ser validada por profissional habilitado.'
    }
    
    return Response(termos)

# ============================================
# VIEWSET TRANSCRIÇÃO
# ============================================

class TranscricaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Transcrições
    
    Endpoints:
    - GET /api/transcricoes/ - Listar transcrições
    - POST /api/transcricoes/ - Criar transcrição
    - GET /api/transcricoes/{id}/ - Obter transcrição
    - PUT /api/transcricoes/{id}/ - Atualizar transcrição
    - DELETE /api/transcricoes/{id}/ - Excluir transcrição
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrMedico]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['paciente__nome_completo']
    ordering_fields = ['data_inicio']
    ordering = ['-data_inicio']
    
    def get_queryset(self):
        """Filtrar transcrições pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        queryset = Transcricao.objects.filter(clinica_id=clinica_id)
        
        # Filtros via query params
        consulta_id = self.request.query_params.get('consulta_id', None)
        paciente_id = self.request.query_params.get('paciente_id', None)
        status = self.request.query_params.get('status', None)
        
        if consulta_id:
            queryset = queryset.filter(consulta_id=consulta_id)
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return TranscricaoListSerializer
        return TranscricaoSerializer
    
    @action(detail=True, methods=['post'])
    def processar(self, request, pk=None):
        """
        Processar transcrição com Gemini
        POST /api/transcricoes/{id}/processar/
        Body: {"audio_base64": "..."} ou {"audio_path": "..."}
        """
        transcricao = self.get_object()
        
        if transcricao.status in ['processando', 'concluida']:
            return Response(
                {'erro': f'Transcrição já está {transcricao.status}'}, 
                status=400
            )
        
        audio_base64 = request.data.get('audio_base64')
        audio_path = request.data.get('audio_path')
        
        if not audio_base64 and not audio_path:
            return Response({'erro': 'Nenhum áudio fornecido'}, status=400)
        
        # Processar de forma assíncrona
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resultado = loop.run_until_complete(
                transcricao.processar_com_gemini(audio_base64, audio_path)
            )
            
            if resultado:
                serializer = TranscricaoSerializer(transcricao, context={'request': request})
                return Response(serializer.data)
            else:
                return Response(
                    {'erro': transcricao.erro_mensagem}, 
                    status=500
                )
        finally:
            loop.close()
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Estatísticas de transcrições
        GET /api/transcricoes/estatisticas/
        """
        clinica_id = request.user.get('clinica_id')
        transcricoes = Transcricao.objects.filter(clinica_id=clinica_id)
        
        total = transcricoes.count()
        aguardando = transcricoes.filter(status='aguardando').count()
        processando = transcricoes.filter(status='processando').count()
        concluidas = transcricoes.filter(status='concluida').count()
        erros = transcricoes.filter(status='erro').count()
        
        # Tempo médio de processamento
        tempo_medio = transcricoes.filter(
            status='concluida', 
            tempo_processamento__isnull=False
        ).aggregate(media=models.Avg('tempo_processamento'))['media']
        
        return Response({
            'total': total,
            'aguardando': aguardando,
            'processando': processando,
            'concluidas': concluidas,
            'erros': erros,
            'tempo_medio_segundos': float(tempo_medio) if tempo_medio else 0
        })


# ============================================
# WEBSOCKET CONSUMER PARA TRANSCRIÇÃO EM TEMPO REAL
# ============================================

class TranscricaoConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer para transcrição de áudio em tempo real
    
    Uso:
    ws://localhost:8000/ws/transcricao/{consulta_id}/
    
    Mensagens enviadas pelo cliente:
    {
        "type": "audio_chunk",
        "data": "base64_audio_data",
        "format": "webm"
    }
    
    Mensagens recebidas pelo cliente:
    {
        "type": "transcription_partial",
        "text": "texto parcial...",
        "confidence": 0.95
    }
    {
        "type": "transcription_final",
        "text": "texto final completo",
        "confidence": 0.98
    }
    {
        "type": "error",
        "message": "mensagem de erro"
    }
    """
    
    async def connect(self):
        """Conectar WebSocket"""
        self.consulta_id = self.scope['url_route']['kwargs']['consulta_id']
        self.room_group_name = f'transcricao_{self.consulta_id}'
        
        # Verificar autenticação (simplificado - melhorar em produção)
        # Em produção, extrair token do query params ou headers
        
        # Adicionar ao grupo
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar confirmação de conexão
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Conectado à transcrição da consulta {self.consulta_id}'
        }))
    
    async def disconnect(self, close_code):
        """Desconectar WebSocket"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receber mensagem do cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'audio_chunk':
                # Receber chunk de áudio
                audio_data = data.get('data')
                audio_format = data.get('format', 'webm')
                
                # Processar áudio com Gemini
                await self.process_audio_chunk(audio_data, audio_format)
            
            elif message_type == 'start_recording':
                # Iniciar gravação
                await self.send(text_data=json.dumps({
                    'type': 'recording_started',
                    'message': 'Gravação iniciada'
                }))
            
            elif message_type == 'stop_recording':
                # Finalizar gravação
                await self.send(text_data=json.dumps({
                    'type': 'recording_stopped',
                    'message': 'Gravação finalizada'
                }))
                
                # Processar transcrição final
                await self.finalize_transcription()
        
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def process_audio_chunk(self, audio_base64, audio_format):
        """Processar chunk de áudio"""
        try:
            # Decodificar áudio
            audio_bytes = base64.b64decode(audio_base64)
            
            # Aqui você processaria com Gemini em tempo real
            # Por enquanto, simulação
            await asyncio.sleep(0.5)  # Simular processamento
            
            # Enviar transcrição parcial
            await self.send(text_data=json.dumps({
                'type': 'transcription_partial',
                'text': 'Texto transcrito parcialmente...',
                'confidence': 0.85
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erro ao processar áudio: {str(e)}'
            }))
    
    async def finalize_transcription(self):
        """Finalizar transcrição completa"""
        try:
            # Aqui você finalizaria o processamento
            # Salvar no banco de dados
            
            await self.send(text_data=json.dumps({
                'type': 'transcription_final',
                'text': 'Transcrição final completa salva no banco de dados.',
                'confidence': 0.95
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erro ao finalizar transcrição: {str(e)}'
            }))

# ============================================
# URLS - Rotas da API (VERSÃO COMPLETA)
# ============================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Criar router
router = DefaultRouter()

# Registrar ViewSets
router.register(r'pacientes', PacienteViewSet, basename='paciente')
router.register(r'agendamentos', AgendamentoViewSet, basename='agendamento')
router.register(r'consultas', ConsultaViewSet, basename='consulta')
router.register(r'exames', ExameViewSet, basename='exame')
router.register(r'faturamento/categorias/receitas', CategoriaReceitaViewSet, basename='categoria-receita')
router.register(r'faturamento/categorias/despesas', CategoriaDespesaViewSet, basename='categoria-despesa')
router.register(r'faturamento/receitas', ReceitaViewSet, basename='receita')
router.register(r'faturamento/despesas', DespesaViewSet, basename='despesa')
router.register(r'transcricoes', TranscricaoViewSet, basename='transcricao')
router.register(r'clinicas', ClinicaViewSet, basename='clinica')
router.register(r'usuarios', UsuarioViewSet, basename='usuario')

# URL patterns
urlpatterns = [
    # Autenticação (sem autenticação JWT)
    path('login', login_view, name='login'),
    path('register', register_view, name='register'),
    
    # API REST (com autenticação JWT)
    path('api/', include(router.urls)),
    
    # Dashboards
    path('api/dashboard/', dashboard_principal, name='dashboard-principal'), 
    path('api/faturamento/dashboard/', dashboard_financeiro, name='dashboard-financeiro'),
    path('api/dados-clinica/', dados_clinica_completo, name='dados-clinica'),

    # IA - Termos de uso
    path('api/exames/termos-uso-ia/', termos_uso_ia, name='termos-uso-ia'),

    # Health check
    path('api/health/', lambda request: JsonResponse({'status': 'ok'}), name='health'),
]

# ============================================
# WEBSOCKET ROUTING
# ============================================

from channels.routing import URLRouter
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r'ws/transcricao/(?P<consulta_id>\w+)/$', TranscricaoConsumer.as_asgi()),
]

# ============================================
# ASGI APPLICATION
# ============================================

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

# ============================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================

def inicializar_banco():
    """Criar tabelas e super admin padrão"""
    from django.core.management import execute_from_command_line
    
    print("Criando tabelas do banco de dados...")
    
    # Criar migrations e aplicar
    try:
        execute_from_command_line(['manage.py', 'makemigrations', '--verbosity', '0'])
        execute_from_command_line(['manage.py', 'migrate', '--verbosity', '0'])
    except SystemExit:
        pass  # Django chama sys.exit(), ignorar
    except Exception as e:
        print(f"Aviso ao inicializar banco: {e}")
    
    print("Verificando super admin padrão...")
    
    # Criar super admin padrão se não existir
    try:
        if not Usuario.objects.filter(email='superadmin@intellimed.com').exists():
            super_admin = Usuario(
                nome_completo='Super Administrador',
                email='superadmin@intellimed.com',
                cpf='111.444.777-35',
                data_nascimento='1990-01-01',
                telefone_celular='(00) 00000-0000',
                funcao='super_admin',
                status='ativo'
            )
            super_admin.set_password('superadmin123')
            super_admin.save()
            print("✓ Super admin criado:")
            print("  Email: superadmin@intellimed.com")
            print("  Senha: superadmin123")
            print("  ⚠️  ALTERE A SENHA EM PRODUÇÃO!")
        else:
            print("✓ Super admin já existe")
    except Exception as e:
        print(f"Erro ao criar super admin: {e}")
    
    print("Banco de dados inicializado com sucesso!")

# ============================================
# POPULAR CATEGORIAS PADRÃO POR CLÍNICA
# ============================================

def popular_categorias_padrao(clinica_id):
    """Popular categorias padrão para uma clínica"""
    
    # Categorias de Receita padrão
    categorias_receita = [
        {'nome': 'Consultas', 'descricao': 'Receitas de consultas médicas', 'cor': '#4CAF50'},
        {'nome': 'Exames', 'descricao': 'Receitas de exames', 'cor': '#2196F3'},
        {'nome': 'Procedimentos', 'descricao': 'Receitas de procedimentos', 'cor': '#9C27B0'},
        {'nome': 'Convênios', 'descricao': 'Receitas de convênios', 'cor': '#FF9800'},
        {'nome': 'Outras', 'descricao': 'Outras receitas', 'cor': '#607D8B'},
    ]
    
    for cat_data in categorias_receita:
        CategoriaReceita.objects.get_or_create(
            clinica_id=clinica_id,
            nome=cat_data['nome'],
            defaults={
                'descricao': cat_data['descricao'],
                'cor': cat_data['cor']
            }
        )
    
    # Categorias de Despesa padrão
    categorias_despesa = [
        {'nome': 'Aluguel', 'descricao': 'Despesas com aluguel do consultório', 'cor': '#F44336'},
        {'nome': 'Salários', 'descricao': 'Pagamento de salários', 'cor': '#E91E63'},
        {'nome': 'Energia', 'descricao': 'Contas de energia elétrica', 'cor': '#9C27B0'},
        {'nome': 'Água', 'descricao': 'Contas de água', 'cor': '#2196F3'},
        {'nome': 'Internet', 'descricao': 'Serviços de internet', 'cor': '#00BCD4'},
        {'nome': 'Telefone', 'descricao': 'Contas de telefone', 'cor': '#009688'},
        {'nome': 'Material de Consumo', 'descricao': 'Materiais e insumos', 'cor': '#4CAF50'},
        {'nome': 'Equipamentos', 'descricao': 'Compra e manutenção de equipamentos', 'cor': '#FF9800'},
        {'nome': 'Marketing', 'descricao': 'Despesas com divulgação', 'cor': '#FF5722'},
        {'nome': 'Impostos', 'descricao': 'Impostos e taxas', 'cor': '#795548'},
        {'nome': 'Outras', 'descricao': 'Outras despesas', 'cor': '#607D8B'},
    ]
    
    for cat_data in categorias_despesa:
        CategoriaDespesa.objects.get_or_create(
            clinica_id=clinica_id,
            nome=cat_data['nome'],
            defaults={
                'descricao': cat_data['descricao'],
                'cor': cat_data['cor']
            }
        )
    
    print(f"Categorias padrão criadas para clínica {clinica_id}")

# ============================================
# ENDPOINT PARA POPULAR CATEGORIAS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_clinica(request):
    """
    Configurar categorias padrão para a clínica
    POST /api/setup/
    """
    clinica_id = request.user.get('clinica_id')
    
    if not clinica_id:
        return Response({
            'sucesso': False,
            'mensagem': 'Usuário sem clínica vinculada'
        }, status=400)
    
    try:
        popular_categorias_padrao(clinica_id)
        return Response({
            'sucesso': True,
            'mensagem': 'Categorias padrão criadas com sucesso'
        })
    except Exception as e:
        return Response({
            'sucesso': False,
            'mensagem': str(e)
        }, status=500)

# ============================================
# COMANDO PARA RODAR O SERVIDOR
# ============================================

def run_server():
    """Iniciar servidor Django"""
    import sys
    from django.core.management import execute_from_command_line
    
    print("="*70)
    print("INTELLIMED - SISTEMA DE GESTÃO DE CLÍNICAS")
    print("Backend Django Multi-Tenant com Autenticação Completa")
    print("="*70)
    
    # Inicializar banco
    try:
        inicializar_banco()
    except Exception as e:
        print(f"Aviso ao inicializar banco: {e}")
    
    # Configurar Gemini
    if Config.configure_gemini():
        print("✓ Google Gemini configurado")
    else:
        print("⚠  Google Gemini não configurado (configure GEMINI_API_KEY no .env)")
    
    print("\n" + "="*70)
    print("ENDPOINTS DISPONÍVEIS:")
    print("="*70)
    
    print("\n🔐 AUTENTICAÇÃO:")
    print("  POST   /login                                   - Login (email + senha)")
    print("  POST   /register                                - Registrar usuário (requer auth)")
    
    print("\n🏢 GESTÃO:")
    print("  GET    /api/clinicas/                           - Listar clínicas")
    print("  POST   /api/clinicas/                           - Criar clínica (super_admin)")
    print("  PUT    /api/clinicas/{id}/                      - Atualizar clínica")
    print("  DELETE /api/clinicas/{id}/                      - Excluir clínica")
    
    print("\n👥 USUÁRIOS:")
    print("  GET    /api/usuarios/                           - Listar usuários")
    print("  POST   /api/usuarios/{id}/alterar-status/       - Alterar status usuário")
    print("  DELETE /api/usuarios/{id}/                      - Excluir usuário")
    
    print("\n📋 PACIENTES:")
    print("  GET    /api/pacientes/                          - Listar pacientes")
    print("  POST   /api/pacientes/                          - Criar paciente")
    print("  GET    /api/pacientes/{id}/completo/            - Paciente com histórico completo")
    
    print("\n📅 AGENDAMENTOS:")
    print("  GET    /api/agendamentos/                       - Listar agendamentos")
    print("  POST   /api/agendamentos/                       - Criar agendamento")
    print("  GET    /api/agendamentos/proximos/              - Próximos agendamentos")
    print("  GET    /api/agendamentos/agenda_dia/            - Agenda do dia específico")
    print("  GET    /api/agendamentos/estatisticas_mes/      - Estatísticas mensais")
    
    print("\n🩺 CONSULTAS COM IA:")
    print("  GET    /api/consultas/fila-hoje/                - Fila de atendimento de hoje")
    print("  POST   /api/consultas/{id}/iniciar-atendimento/ - Iniciar consulta")
    print("  POST   /api/consultas/{id}/enviar-audio/        - Enviar áudio da consulta")
    print("  POST   /api/consultas/{id}/transcrever/         - Transcrever com IA")
    print("  POST   /api/consultas/{id}/gerar-documento/     - Gerar documento médico")
    print("  POST   /api/consultas/{id}/salvar-documento/    - Salvar documento editado")
    print("  GET    /api/consultas/{id}/documentos/          - Listar documentos da consulta")
    print("  POST   /api/consultas/{id}/finalizar/           - Finalizar consulta")
    
    print("\n🔬 EXAMES IA:")
    print("  GET    /api/exames/termos-uso-ia/               - Termos de uso da IA")
    print("  POST   /api/exames/upload-ia/                   - Upload e interpretação por IA")
    print("  POST   /api/exames/{id}/interpretar-ia/         - Interpretar exame existente")
    print("  POST   /api/exames/{id}/revisar-medico/         - Adicionar revisão médica")
    print("  GET    /api/exames/estatisticas_ia/             - Estatísticas de uso da IA")
    
    print("\n💰 FATURAMENTO:")
    print("  GET    /api/faturamento/receitas/               - Listar receitas")
    print("  GET    /api/faturamento/despesas/               - Listar despesas")
    print("  GET    /api/faturamento/dashboard/              - Dashboard financeiro")
    
    print("\n📊 DASHBOARDS:")
    print("  GET    /api/dashboard/                          - Dashboard principal")
    print("  GET    /api/dados-clinica/                      - Dados completos da clínica")
    
    print("\n🎤 TRANSCRIÇÕES:")
    print("  GET    /api/transcricoes/                       - Listar transcrições")
    print("  POST   /api/transcricoes/{id}/processar/        - Processar com Gemini")
    print("  WS     ws://localhost:8000/ws/transcricao/{id}/ - WebSocket tempo real")
    
    print("\n⚙️  OUTROS:")
    print("  GET    /api/health/                             - Health check")
    
    print("\n" + "="*70)
    print(f"🚀 Servidor iniciando em http://{Config.HOST}:{Config.PORT}")
    print("="*70)
    print("\n📝 CREDENCIAIS PADRÃO:")
    print("  Email: superadmin@intellimed.com")
    print("  Senha: superadmin123")
    print("  ⚠️  ALTERE EM PRODUÇÃO!")
    print("\n💡 SISTEMA COMPLETO:")
    print("  ✅ Gestão de Clínicas e Usuários")
    print("  ✅ Gestão de Pacientes")
    print("  ✅ Agendamentos e Consultas")
    print("  ✅ Consultas com Transcrição IA")
    print("  ✅ Exames com Interpretação IA")
    print("  ✅ Geração de Documentos Médicos")
    print("  ✅ Faturamento Completo")
    print("  ✅ Dashboards e Relatórios")
    print("\nPressione CTRL+C para parar o servidor\n")
    
    # Rodar servidor
    sys.argv = ['manage.py', 'runserver', f'{Config.HOST}:{Config.PORT}', '--noreload']
    execute_from_command_line(sys.argv)

# ============================================
# PONTO DE ENTRADA
# ============================================

if __name__ == '__main__':
    run_server()