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
import secrets
import string
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
    # Diretório base do projeto
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_NAME = os.path.join(BASE_DIR, os.getenv('DATABASE_NAME', 'intellimed.db'))
    
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
from django.http import HttpResponse

# ============================================
# MIDDLEWARE CORS CUSTOMIZADO
# ============================================

# NO ARQUIVO: main.py
# ANTES DE: if not settings.configured:
# DEPOIS DE: from django.http import HttpResponse

# ============================================
# MIDDLEWARE CORS CUSTOMIZADO
# ============================================

class CorsMiddleware:
    """Middleware para tratar CORS e OPTIONS requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse()
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken"
            response["Access-Control-Max-Age"] = "3600"
            return response
        
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Credentials"] = "true"

        # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
        # Expõe o cabeçalho Content-Disposition para que o JavaScript do frontend possa lê-lo
        response["Access-Control-Expose-Headers"] = "Content-Disposition"
        # ▲▲▲ FIM DA CORREÇÃO ▲▲▲
        
        return response


if not settings.configured:
    # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
    # Garante que as variáveis do .env sejam lidas antes de serem usadas.
    # Esta abordagem é mais robusta para o ambiente de arquivo único.
    
    # Carrega os valores do .env para variáveis Python primeiro
    email_host_user = os.getenv('EMAIL_HOST_USER')
    email_host_password = os.getenv('EMAIL_HOST_PASSWORD')
    
    # Define o backend com base na existência das credenciais
    if email_host_user and email_host_password:
        email_backend = 'django.core.mail.backends.smtp.EmailBackend'
        default_from_email = f"IntelliMed <{email_host_user}>"
        print("✓ Configuração de E-mail: SMTP do Gmail será utilizado.")
    else:
        email_backend = 'django.core.mail.backends.console.EmailBackend'
        default_from_email = 'IntelliMed Backup <no-reply@intellimed.com>'
        print("⚠️  Configuração de E-mail: EMAIL_HOST_USER/PASSWORD não encontrados no .env. E-mails serão impressos no console.")
        
    settings.configure(
        DEBUG=Config.DEBUG,
        SECRET_KEY='intellimed-secret-key-change-in-production',
        ALLOWED_HOSTS=['*'],
        
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework',
            'channels',
            'django_apscheduler',
            # 'main',  # REMOVIDO - causa import circular
        ],
        
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'main.CorsMiddleware',
            'django.middleware.common.CommonMiddleware',
        ],
        
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': Config.DATABASE_NAME,
            }
        },
        
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
        
        ASGI_APPLICATION = 'main.application',
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer'
            }
        },
        
        USE_TZ=True,
        TIME_ZONE='America/Sao_Paulo',
        LANGUAGE_CODE='pt-br',
        CORS_ALLOW_ALL_ORIGINS=True,
        ROOT_URLCONF='main',
        
        # Configurações de E-mail agora são definidas dinamicamente
        EMAIL_BACKEND=email_backend,
        EMAIL_HOST='smtp.gmail.com',
        EMAIL_PORT=587,
        EMAIL_USE_TLS=True,
        EMAIL_HOST_USER=email_host_user,
        EMAIL_HOST_PASSWORD=email_host_password,
        DEFAULT_FROM_EMAIL=default_from_email,
    )
    # ▲▲▲ FIM DA CORREÇÃO ▲▲▲
    
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
from django.db import transaction 
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
from asgiref.sync import async_to_sync

# ▼▼▼ NOVAS IMPORTAÇÕES PARA BACKUP E AGENDAMENTO ▼▼▼
from django.db import transaction
# MOVIDO PARA DENTRO DA FUNÇÃO: from apscheduler.schedulers.background import BackgroundScheduler
# MOVIDO PARA DENTRO DA FUNÇÃO: from django_apscheduler.jobstores import DjangoJobStore
# MOVIDO PARA DENTRO DA FUNÇÃO: from django_apscheduler.models import DjangoJobExecution
from django.core.mail import send_mail
from django.core.files.base import ContentFile

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

def _enviar_email_nova_senha(email_usuario, senha_temporaria, contexto="novo_usuario"):
    """
    Envia um e-mail para o usuário com sua senha temporária.
    O conteúdo do e-mail varia com base no contexto.
    
    Args:
        email_usuario (str): E-mail do destinatário.
        senha_temporaria (str): A nova senha gerada.
        contexto (str): 'novo_usuario' ou 'recuperacao'.
    """
    if contexto == "recuperacao":
        assunto = "IntelliMed - Recuperação de Senha"
        mensagem = f"""
        Olá,

        Você solicitou a recuperação da sua senha no sistema IntelliMed.

        Seu login é o seu e-mail: {email_usuario}
        Sua nova senha temporária é: {senha_temporaria}

        Ao fazer login com esta senha, você será solicitado a criar uma nova senha pessoal.
        Se você não solicitou esta alteração, por favor, ignore este e-mail.

        Atenciosamente,
        Equipe IntelliMed
        """
    else: # Padrão para 'novo_usuario'
        assunto = "Bem-vindo ao IntelliMed - Suas Credenciais de Acesso"
        mensagem = f"""
        Olá,

        Uma conta foi criada para você no sistema IntelliMed.

        Seu login é o seu e-mail: {email_usuario}
        Sua senha temporária é: {senha_temporaria}

        No seu primeiro acesso, você será solicitado a criar uma nova senha pessoal.

        Atenciosamente,
        Equipe IntelliMed
        """
        
    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [email_usuario],
            fail_silently=False,
        )
        print(f"✓ E-mail (contexto: {contexto}) com senha temporária enviado para {email_usuario}")
    except Exception as e:
        print(f"✗ ERRO ao enviar e-mail (contexto: {contexto}): {str(e)}")

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
        ('SUS', 'SUS'),
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
    cpf = models.CharField(max_length=14)
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
            models.Index(fields=['clinica_id', 'cpf']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['clinica_id', 'cpf'],
                condition=Q(ativo=True),
                name='unique_ativo_cpf_por_clinica'
            )
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
    
    medico_responsavel = models.ForeignKey(
        "Usuario",
        on_delete=models.PROTECT,
        related_name='agendamentos_medicos',
        null=True,
        blank=True,
        limit_choices_to={'funcao': 'medico'}
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
            models.Index(fields=['medico_responsavel']),
        ]
        # O bloco 'constraints' foi removido daqui
    
    def __str__(self):
        return f"{self.servico} - {self.paciente_nome} - {self.data} {self.hora}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        if not self.pk and self.data and self.data < date.today():
            errors['data'] = 'Não é possível agendar para datas passadas'
        
        if self.paciente and self.paciente.clinica_id != self.clinica_id:
            errors['paciente'] = 'Paciente não pertence a esta clínica'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        if self.paciente:
            self.paciente_nome = self.paciente.nome_completo
            self.paciente_cpf = self.paciente.cpf
            if not self.convenio:
                self.convenio = self.paciente.convenio
    
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def verificar_disponibilidade(cls, clinica_id, data, hora, medico_id, excluir_id=None):
        """Verifica se um horário está disponível para um médico específico."""
        query = cls.objects.filter(
            clinica_id=clinica_id,
            data=data,
            hora=hora,
            medico_responsavel_id=medico_id
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
        """Marca início do atendimento e salva os dados do médico."""
        self.status = 'em_atendimento'
        self.data_inicio_atendimento = timezone.now()
        
        # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
        # Garante que os campos do médico sejam salvos no banco de dados.
        self.save(update_fields=['status', 'data_inicio_atendimento', 'medico_responsavel', 'medico_crm'])
        # ▲▲▲ FIM DA CORREÇÃO ▲▲▲
    
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
    
    # <<< INÍCIO DA CORREÇÃO >>>
    TIPO_CHOICES = [
        ('hemograma', 'Hemograma'),
        ('glicemia', 'Glicemia'),
        ('colesterol_total', 'Colesterol Total'),
        ('urinalise', 'Urinálise'),
        ('gasometria', 'Gasometria Arterial'), # OPÇÃO ADICIONADA
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
    # <<< FIM DA CORREÇÃO >>>
    
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
    
    # Auditoria de operações
    usuario_cadastro_id = models.IntegerField(null=True, blank=True, help_text="ID do usuário que cadastrou")
    usuario_cadastro_nome = models.CharField(max_length=200, null=True, blank=True)
    usuario_recebimento_id = models.IntegerField(null=True, blank=True, help_text="ID do usuário que marcou como recebida")
    usuario_recebimento_nome = models.CharField(max_length=200, null=True, blank=True)
    data_operacao_recebimento = models.DateTimeField(null=True, blank=True, help_text="Data/hora que foi marcada como recebida")
    
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
    
    def marcar_como_recebida(self, data_recebimento=None, forma_pagamento=None, usuario_id=None, usuario_nome=None):
        """Marca a receita como recebida com auditoria"""
        self.status = 'recebida'
        self.data_recebimento = data_recebimento or date.today()
        if forma_pagamento:
            self.forma_pagamento = forma_pagamento
        
        # Auditoria
        self.usuario_recebimento_id = usuario_id
        self.usuario_recebimento_nome = usuario_nome
        self.data_operacao_recebimento = timezone.now()
        
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
    
    # Auditoria de operações
    usuario_cadastro_id = models.IntegerField(null=True, blank=True, help_text="ID do usuário que cadastrou")
    usuario_cadastro_nome = models.CharField(max_length=200, null=True, blank=True)
    usuario_pagamento_id = models.IntegerField(null=True, blank=True, help_text="ID do usuário que marcou como paga")
    usuario_pagamento_nome = models.CharField(max_length=200, null=True, blank=True)
    data_operacao_pagamento = models.DateTimeField(null=True, blank=True, help_text="Data/hora que foi marcada como paga")
    
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
    
    def marcar_como_paga(self, data_pagamento=None, forma_pagamento=None, usuario_id=None, usuario_nome=None):
        """Marca a despesa como paga com auditoria"""
        self.status = 'paga'
        self.data_pagamento = data_pagamento or date.today()
        if forma_pagamento:
            self.forma_pagamento = forma_pagamento
        
        # Auditoria
        self.usuario_pagamento_id = usuario_id
        self.usuario_pagamento_nome = usuario_nome
        self.data_operacao_pagamento = timezone.now()
        
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

    BACKUP_FREQUENCIA_CHOICES = [
        ('manual', 'Manual'),
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
    ]

    # Configuração de Backup
    backup_frequencia = models.CharField(
        max_length=10, 
        choices=BACKUP_FREQUENCIA_CHOICES, 
        default='manual'
    )
    backup_ultimo_realizado = models.DateTimeField(null=True, blank=True)
    backup_email_notificacao = models.EmailField(blank=True, null=True, help_text="Email para receber o backup automático.")
    
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
    cpf = models.CharField(max_length=14)
    password = models.CharField(max_length=255)  # Hash da senha
    data_nascimento = models.DateField()
    telefone_celular = models.CharField(max_length=20)
    
    # Função
    funcao = models.CharField(max_length=20, choices=FUNCAO_CHOICES)
    
    # Campos específicos para médicos
    crm = models.CharField(max_length=20, blank=True, null=True)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    
    # ▼▼▼ CAMPO NOVO ADICIONADO AQUI ▼▼▼
    # Flag para forçar a troca de senha no primeiro login
    precisa_alterar_senha = models.BooleanField(
        default=True,
        help_text="Se True, o usuário deve alterar a senha no primeiro login."
    )
    # ▲▲▲ FIM DA ADIÇÃO ▲▲▲

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
        unique_together = [['clinica', 'cpf']]
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['cpf']),
        ]
    
    def __str__(self):
        return f"{self.nome_completo} - {self.get_funcao_display()}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        if self.cpf and not Validador.validar_cpf(self.cpf):
            errors['cpf'] = 'CPF inválido'
        
        if self.funcao == 'medico' and (not self.crm or not self.especialidade):
            errors['crm'] = 'Médicos devem ter CRM e especialidade'
        
        if self.funcao == 'super_admin' and self.clinica:
            errors['clinica'] = 'Super admin não pode estar vinculado a uma clínica'
        
        if self.funcao != 'super_admin' and not self.clinica:
            errors['clinica'] = 'Usuário deve estar vinculado a uma clínica'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Salvar usuário"""
        if self.cpf: self.cpf = Validador.formatar_cpf(self.cpf)
        if self.telefone_celular: self.telefone_celular = Validador.formatar_telefone(self.telefone_celular)
        if self.email: self.email = self.email.lower()
    
        if not kwargs.get('update_fields'):
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
            'sub': str(self.id), 'email': self.email, 'nome': self.nome_completo,
            'funcao': self.funcao, 'clinica_id': self.clinica_id if self.clinica else None,
            'exp': agora + timedelta(hours=24), 'iat': agora
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
            'data_cadastro', 'data_atualizacao',
            'backup_frequencia', 'backup_ultimo_realizado', 'backup_email_notificacao'
        ]
        read_only_fields = ['id', 'data_cadastro', 'data_atualizacao', 'backup_ultimo_realizado']
    
    def get_total_usuarios(self, obj):
        return obj.usuarios.count()
    
    def to_representation(self, instance):
        """Formatar saída para compatibilidade com admin_panel"""
        data = super().to_representation(instance)
        
        data['endereco'] = {
            'logradouro': instance.logradouro,
            'numero': instance.numero,
            'bairro': instance.bairro,
            'cidade': instance.cidade,
            'estado': instance.estado,
            'cep': instance.cep
        }
        
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
            'precisa_alterar_senha',
            'data_cadastro', 'data_atualizacao'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }
        read_only_fields = ['id', 'last_login', 'data_cadastro', 'data_atualizacao']
    
    def validate_email(self, value):
        """Validar email (continua sendo único globalmente)"""
        query = Usuario.objects.filter(email=value.lower())
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("Este e-mail já está em uso por outro usuário no sistema.")
        return value
    
    def validate(self, data):
        """Validações gerais, incluindo a nova regra de CPF."""
        cpf = data.get('cpf')
        clinica = data.get('clinica')

        if cpf and clinica:
            cpf_formatado = Validador.formatar_cpf(cpf)
            query = Usuario.objects.filter(clinica=clinica, cpf=cpf_formatado)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError({"cpf": "Este CPF já está cadastrado para um usuário nesta clínica."})

        if data.get('funcao') == 'medico':
            if not data.get('crm') or not data.get('especialidade'):
                raise serializers.ValidationError({'crm': 'Médicos devem ter CRM e especialidade'})
        
        return data
    
    def create(self, validated_data):
        """
        Cria um usuário, gera uma senha temporária e envia por e-mail.
        A senha enviada pelo admin panel é ignorada.
        """
        validated_data.pop('password', None)
        
        alfabeto = string.ascii_letters + string.digits
        senha_temporaria = ''.join(secrets.choice(alfabeto) for i in range(10))
        
        usuario = Usuario(**validated_data)
        
        usuario.set_password(senha_temporaria)
        usuario.precisa_alterar_senha = True
        
        usuario.save()
        
        _enviar_email_nova_senha(usuario.email, senha_temporaria, contexto="novo_usuario")
        
        return usuario
    
    # ▼▼▼ MÉTODO UPDATE TOTALMENTE CORRIGIDO ▼▼▼
    def update(self, instance, validated_data):
        """
        Atualiza um usuário. Se uma nova senha for fornecida,
        ela é tratada como uma senha temporária e enviada por e-mail.
        """
        # Remove o campo 'password' dos dados validados para tratá-lo separadamente.
        nova_senha_fornecida = validated_data.pop('password', None)

        # Atualiza todos os outros campos do modelo
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Verifica se uma nova senha foi de fato digitada no formulário
        if nova_senha_fornecida:
            # Gera uma nova senha temporária segura, ignorando o que foi digitado
            alfabeto = string.ascii_letters + string.digits
            senha_temporaria_reset = ''.join(secrets.choice(alfabeto) for i in range(10))
            
            # Define a nova senha temporária e marca o usuário para alterá-la
            instance.set_password(senha_temporaria_reset)
            instance.precisa_alterar_senha = True
            
            # Envia o e-mail de recuperação com a nova senha temporária
            _enviar_email_nova_senha(instance.email, senha_temporaria_reset, contexto="recuperacao")
            print(f"✓ Senha resetada para o usuário {instance.email}. E-mail de recuperação enviado.")

        instance.save()
        return instance
    # ▲▲▲ FIM DA CORREÇÃO ▲▲▲


class LoginSerializer(serializers.Serializer):
    """Serializer para Login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

# ============================================
# FUNÇÃO PARA INTERPRETAR EXAME COM GEMINI
# ============================================


def interpretar_exame_com_gemini(exame_id):
    """
    Interpreta exame médico usando Google Gemini Vision (versão síncrona)
    
    Args:
        exame_id: ID do exame a ser interpretado
    
    Returns:
        dict com resultado da interpretação
    """
    import time
    import mimetypes
    import traceback
    import re
    
    inicio = time.time()
    
    try:
        exame = Exame.objects.get(id=exame_id)
    except Exame.DoesNotExist:
        return {'sucesso': False, 'erro': 'Exame não encontrado no início do processo.'}

    try:
        exame.status = 'processando_ia'
        exame.save(update_fields=['status'])
        
        if not Config.GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY não configurada no .env")
        
        if not genai:
            raise Exception("Biblioteca google-generativeai não instalada")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        model_name = os.getenv('GEMINI_MODEL_EXAMS', 'gemini-2.5-flash')
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
Você é um sistema de apoio diagnóstico médico especializado. Sua função é interpretar exames médicos com rigor científico.

IMPORTANTE:
- Você deve fornecer uma interpretação técnica baseada APENAS em fontes médicas confiáveis
- Sempre indique que esta é uma interpretação por IA e requer validação médica
- Cite as referências médicas utilizadas (sociedades médicas, guidelines, literatura científica)
- Seja claro sobre limitações e incertezas
- Use terminologia médica apropriada
- NÃO USE FORMATAÇÃO MARKDOWN (asteriscos, etc) no resultado final do laudo. Gere texto limpo.

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
        
        if exame.arquivo_exame:
            if exame.arquivo_exame.startswith('data:'):
                parts = exame.arquivo_exame.split(',', 1)
                base64_string = parts[1] if len(parts) > 1 else parts[0]
                arquivo_bytes = base64.b64decode(base64_string)
            else:
                arquivo_bytes = base64.b64decode(exame.arquivo_exame)
            
            mime_type = exame.arquivo_tipo or 'image/jpeg'
            
            request_options = {"timeout": 120}
            
            if 'image' in mime_type:
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(arquivo_bytes))
                response = model.generate_content([prompt, image], request_options=request_options)
            else:
                arquivo_blob = {"mime_type": mime_type, "data": arquivo_bytes}
                response = model.generate_content([prompt, arquivo_blob], request_options=request_options)
        else:
            raise Exception("Nenhum arquivo de exame disponível")
        
        response_text = response.text
        
        try:
            json_str = response_text
            if json_str.strip().startswith("```json"):
                json_str = json_str.strip()[7:-3]
            
            json_str = json_str.strip()
            resultado = json.loads(json_str)
            
            # ▼▼▼ INÍCIO DA ALTERAÇÃO ▼▼▼
            medico_nome = f"Dr. {exame.medico_solicitante or '[Não informado]'}"
            medico_funcao = "Médico"
            
            # Busca a especialidade do médico no banco de dados
            try:
                if exame.medico_solicitante_crm:
                    medico_obj = Usuario.objects.get(crm=exame.medico_solicitante_crm, clinica_id=exame.clinica_id)
                    if medico_obj.especialidade:
                        medico_funcao = f"Médico - {medico_obj.especialidade}"
            except Usuario.DoesNotExist:
                # Se não encontrar o usuário pelo CRM, continua sem a especialidade
                pass

            medico_crm_str = f"CRM: {exame.medico_solicitante_crm or '[Não informado]'}"
            
            assinatura_linha = "_" * (len(medico_nome) + 4)
            largura_total = 95
            
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
{chr(10).join('• ' + str(valor) for valor in resultado.get('valores_alterados', [])) if resultado.get('valores_alterados') else '• Nenhum valor significativamente alterado'}

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
{chr(10).join('• ' + str(fonte) for fonte in resultado.get('fontes_consultadas', ['Diretrizes médicas padrão']))}

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


{assinatura_linha.center(largura_total)}
{medico_nome.center(largura_total)}
{medico_funcao.center(largura_total)}
{medico_crm_str.center(largura_total)}

═══════════════════════════════════════════════════════════════════════════════════════
"""
            # ▲▲▲ FIM DA ALTERAÇÃO ▲▲▲

            laudo_limpo = re.sub(r'\*?\*(.*?)\*\*?', r'\1', laudo)
            exame.interpretacao_ia = laudo_limpo
            
            exame.tipo_exame_identificado_ia = resultado.get('tipo_exame_identificado', '')
            exame.confianca_ia = float(resultado.get('confianca', 0))
            exame.fontes_consultadas = json.dumps(resultado.get('fontes_consultadas', []), ensure_ascii=False)
            exame.status = 'interpretado_ia'
            exame.data_resultado = date.today()
            
        except json.JSONDecodeError as json_error:
            texto_bruto = f"""
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
            exame.interpretacao_ia = re.sub(r'\*?\*(.*?)\*\*?', r'\1', texto_bruto)
            exame.confianca_ia = 0.75
            exame.status = 'interpretado_ia'
        
        tempo_total = time.time() - inicio
        exame.tempo_processamento = tempo_total
        exame.save()
        
        return {
            'sucesso': True,
            'exame_id': exame.id,
            'tempo_processamento': tempo_total,
            'status': exame.status
        }
        
    except Exception as e:
        print("\n--- ERRO CAPTURADO NO BLOCO GERAL ---")
        traceback.print_exc()
        print(f"-------------------------------------\n")
        
        exame.status = 'erro_ia'
        exame.erro_ia = str(e)
        exame.save(update_fields=['status', 'erro_ia'])

        return {
            'sucesso': False,
            'erro': str(e)
        }

# ============================================
# FUNÇÃO DE TRANSCRIÇÃO DE CONSULTA COM IA
# ============================================

def transcrever_consulta_com_gemini(consulta_id):
    """
    Transcreve consulta identificando falas do médico e paciente
    VERSÃO MELHORADA COM DEBUG
    """
    import time
    
    inicio = time.time()
    
    try:
        print(f"\n{'='*70}")
        print(f"🎤 TRANSCRIÇÃO - Consulta ID: {consulta_id}")
        print(f"{'='*70}")
        
        consulta = Consulta.objects.get(id=consulta_id)
        print(f"✓ Consulta encontrada")
        print(f"✓ Paciente: {consulta.paciente.nome_completo}")
        
        if not consulta.audio_consulta:
            print(f"❌ Áudio não encontrado!")
            raise Exception("Nenhum áudio disponível")
        
        audio_size = len(consulta.audio_consulta)
        print(f"✓ Áudio presente: {audio_size} caracteres")
        
        consulta.status = 'transcrevendo'
        consulta.save(update_fields=['status'])
        
        # Verificar Gemini
        if not Config.GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY não configurada")
        
        print(f"✓ API Key OK: {Config.GEMINI_API_KEY[:20]}...")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model_name = os.getenv('GEMINI_MODEL_TRANSCRIPTION', 'gemini-2.5-flash')
        model = genai.GenerativeModel(model_name)
        
        # Decodificar áudio
        if consulta.audio_consulta.startswith('data:'):
            partes = consulta.audio_consulta.split(',', 1)
            print(f"✓ Header do data URL: {partes[0]}")
            audio_bytes = base64.b64decode(partes[1])
        else:
            audio_bytes = base64.b64decode(consulta.audio_consulta)
        
        audio_kb = len(audio_bytes) / 1024
        audio_mb = audio_kb / 1024
        duracao_estimada = len(audio_bytes) / (16000 * 2)  # Estimativa aproximada
        
        print(f"✓ Áudio decodificado:")
        print(f"  - Tamanho: {len(audio_bytes)} bytes ({audio_kb:.2f} KB / {audio_mb:.2f} MB)")
        print(f"  - Duração estimada: {duracao_estimada:.1f} segundos")
        print(f"  - Formato: {consulta.audio_formato or 'webm'}")
        
        # SALVAR ÁUDIO PARA DEBUG (OPCIONAL - REMOVER DEPOIS)
        debug_audio_path = f"debug_audio_{consulta_id}.webm"
        try:
            with open(debug_audio_path, 'wb') as f:
                f.write(audio_bytes)
            print(f"✓ Áudio salvo em: {debug_audio_path}")
        except:
            pass
        
        # Prompt MUITO mais detalhado
        prompt = f"""Você é um transcritor médico especializado em português brasileiro.

TAREFA: Transcreva este áudio de uma consulta médica.

INSTRUÇÕES IMPORTANTES:
1. Transcreva TODO o áudio, palavra por palavra
2. Identifique quem está falando: MÉDICO ou PACIENTE
3. O médico geralmente faz perguntas e usa termos técnicos
4. O paciente geralmente responde e usa linguagem popular
5. Se não houver fala clara, indique "[inaudível]"
6. Se o áudio estiver vazio ou sem fala, diga "SEM_FALA" na transcrição

CONTEXTO:
- Paciente: {consulta.paciente.nome_completo}, {consulta.paciente.idade} anos
- Data: {consulta.data_consulta.strftime('%d/%m/%Y')}
- Tipo: {consulta.get_tipo_consulta_display()}

FORMATO DE RESPOSTA (JSON puro, sem markdown):
{{
    "transcricao_completa": "transcrição literal completa do áudio",
    "falas_medico": "todas as falas do médico concatenadas",
    "falas_paciente": "todas as falas do paciente concatenadas",
    "confianca": 0.95,
    "observacao": "qualquer problema encontrado no áudio"
}}

Se o áudio estiver vazio ou corrompido, retorne:
{{
    "transcricao_completa": "SEM_FALA",
    "falas_medico": "",
    "falas_paciente": "",
    "confianca": 0.0,
    "observacao": "áudio vazio ou sem fala detectável"
}}

TRANSCREVA AGORA:"""
        
        print(f"📤 Enviando para Gemini API...")
        print(f"  - Modelo: gemini-2.5-pro")
        print(f"  - Timeout: 300 segundos")
        
        response = model.generate_content([
            prompt,
            {"mime_type": f"audio/{consulta.audio_formato or 'webm'}", "data": audio_bytes}
        ], request_options={"timeout": 300})
        
        print(f"✓ Resposta recebida!")
        print(f"Resposta completa do Gemini:")
        print(response.text)
        print(f"")
        
        # Parse JSON
        json_str = response.text.strip()
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]
        
        resultado = json.loads(json_str.strip())
        
        transcricao = resultado.get('transcricao_completa', '').strip()
        
        # Verificar se a transcrição está vazia
        if not transcricao or transcricao == "SEM_FALA":
            print(f"⚠️ ATENÇÃO: Gemini retornou transcrição vazia!")
            print(f"Observação: {resultado.get('observacao', 'Nenhuma')}")
            
            # Ainda assim salvar o que vier
            consulta.transcricao_completa = "⚠️ Áudio sem fala detectável ou arquivo corrompido."
            consulta.transcricao_ia = consulta.transcricao_completa
            consulta.observacoes = f"Gemini não detectou fala. {resultado.get('observacao', '')}"
        else:
            print(f"✓ Transcrição OK: {len(transcricao)} caracteres")
            
            # Salvar normalmente
            consulta.transcricao_completa = transcricao
            consulta.transcricao_medico = resultado.get('falas_medico', '')
            consulta.transcricao_paciente = resultado.get('falas_paciente', '')
            consulta.transcricao_ia = transcricao
        
        consulta.confianca_transcricao = float(resultado.get('confianca', 0))
        consulta.tempo_processamento_transcricao = time.time() - inicio
        consulta.status = 'aguardando_revisao'
        consulta.save()
        
        print(f"✅ FINALIZADO!")
        print(f"  - Transcrição: {len(consulta.transcricao_completa)} caracteres")
        print(f"  - Confiança: {consulta.confianca_transcricao * 100:.1f}%")
        print(f"  - Tempo: {consulta.tempo_processamento_transcricao:.2f}s")
        
        return {
            'sucesso': True,
            'consulta_id': consulta.id,
            'tempo_processamento': time.time() - inicio,
            'confianca': consulta.confianca_transcricao
        }
    
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        try:
            consulta = Consulta.objects.get(id=consulta_id)
            consulta.status = 'em_atendimento'
            consulta.save()
        except:
            pass
        
        return {'sucesso': False, 'erro': str(e)}

# ============================================
# FUNÇÃO DE GERAÇÃO DE DOCUMENTOS MÉDICOS
# ============================================


def gerar_documento_medico_sync(consulta_id, tipo_documento, medico_nome, medico_crm):
    """
    Gera documento médico baseado na consulta - VERSÃO SÍNCRONA
    
    Args:
        consulta_id: ID da consulta
        tipo_documento: 'atestado', 'anamnese', 'evolucao', 'prescricao', 'relatorio'
        medico_nome: Nome do médico (com Dr.)
        medico_crm: CRM do médico
    
    Returns:
        dict com documento gerado
    """
    import time
    import re
    
    print(f"⏳ Aguardando 2 segundos antes de gerar documento...")
    time.sleep(2)
    
    try:
        consulta = Consulta.objects.get(id=consulta_id)
        paciente = consulta.paciente
        
        try:
            clinica = Clinica.objects.get(id=consulta.clinica_id)
            nome_clinica_upper = clinica.nome.upper()
            cidade_clinica = clinica.cidade
        except Clinica.DoesNotExist:
            nome_clinica_upper = "NOME DA CLÍNICA"
            cidade_clinica = "Cidade"

        titulos = {
            'atestado': 'ATESTADO MÉDICO',
            'anamnese': 'ANAMNESE',
            'evolucao': 'EVOLUÇÃO MÉDICA',
            'prescricao': 'PRESCRIÇÃO MÉDICA',
            'relatorio': 'RELATÓRIO MÉDICO'
        }
        titulo_documento_upper = titulos.get(tipo_documento.lower(), "DOCUMENTO MÉDICO")

        largura_total = 80
        
        cabecalho = (
            f"{'=' * largura_total}\n\n"
            f"{nome_clinica_upper.center(largura_total)}\n\n"
            f"{'=' * largura_total}\n\n\n"
            f"{titulo_documento_upper.center(largura_total)}\n\n\n"
        )

        if consulta.documentos_gerados:
            for doc in consulta.documentos_gerados:
                if doc.get('tipo') == tipo_documento:
                    return { 'sucesso': True, 'tipo': tipo_documento, 'conteudo': doc.get('conteudo'), 'data_geracao': doc.get('data_geracao'), 'from_cache': True }
        
        if not Config.GEMINI_API_KEY or not genai:
            raise Exception("Gemini não configurado")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        from datetime import datetime
        meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        data_extenso = f"{consulta.data_consulta.day} de {meses[consulta.data_consulta.month-1]} de {consulta.data_consulta.year}"

        medico_funcao = "Médico"
        try:
            if medico_crm:
                medico_obj = Usuario.objects.get(crm=medico_crm, clinica_id=consulta.clinica_id)
                if medico_obj.especialidade:
                    medico_funcao = f"Médico - {medico_obj.especialidade}"
        except Usuario.DoesNotExist:
            pass

        local_e_data = f"{cidade_clinica}, {data_extenso}."
        
        assinatura_bloco = f"""
{("_" * (len(medico_nome) + 8)).center(largura_total).rstrip()}
{medico_nome.center(largura_total).rstrip()}
{medico_funcao.center(largura_total).rstrip()}
{f'CRM: {medico_crm}'.center(largura_total).rstrip()}
"""
        # ▼▼▼ INÍCIO DA CORREÇÃO NOS PROMPTS ▼▼▼
        prompts = {
            'atestado': f"""
REGRAS CRÍTICAS:
1. Gere o documento em TEXTO PURO. NÃO use HTML ou Markdown.
2. Analise a transcrição da consulta para encontrar menções a dias de afastamento, repouso e CID.
3. Se a transcrição mencionar um número de dias, use-o no atestado. Ex: "necessitando de X dias de afastamento".
4. Se a transcrição mencionar um CID, inclua-o no formato "CID: [código]".
5. Se a transcrição NÃO mencionar dias ou CID, gere um atestado simples "para os devidos fins", sem inventar informações.
6. O texto deve ser formal e profissional.

TRANSCRIÇÃO DA CONSULTA:
'''{consulta.transcricao_ia or consulta.transcricao_completa or '[Sem transcrição]'}'''

DADOS DO PACIENTE:
- Nome: {paciente.nome_completo}
- CPF: {paciente.cpf}

INSTRUÇÕES:
Gere o CORPO do atestado médico com base nas regras e na transcrição. NÃO inclua o local e a data no final do corpo.

Exemplo de corpo se encontrar informações:
"Atesto para os devidos fins que o(a) paciente {paciente.nome_completo}, portador(a) do CPF {paciente.cpf}, esteve sob meus cuidados médicos nesta data, apresentando quadro compatível com [Diagnóstico se mencionado]. Recomendo afastamento de suas atividades laborais por [NÚMERO] dias a partir desta data. CID: [CÓDIGO SE MENCIONADO]."

Exemplo de corpo se NÃO encontrar informações:
"Atesto para os devidos fins que o(a) paciente {paciente.nome_completo}, portador(a) do CPF {paciente.cpf}, esteve sob meus cuidados médicos nesta data."
""",
            
            'anamnese': f"""Gere uma anamnese em TEXTO PURO. Use títulos (ex: "1. Identificação:") e parágrafos. Use "Não informado" para campos vazios. Transcrição: {consulta.transcricao_ia or '[Sem transcrição]'}. Dados: Paciente: {paciente.nome_completo}, Idade: {paciente.idade}. Estrutura: 1.Identificação, 2.Queixa Principal, 3.História da Doença Atual, 4.Antecedentes, 5.Exame Físico, 6.Hipótese Diagnóstica.""",
            
            'evolucao': f"""Gere uma evolução médica em TEXTO PURO no formato SOAP. Use os títulos "S (Subjetivo):", "O (Objetivo):", etc. Dados: Paciente: {paciente.nome_completo}, Data/Hora: {consulta.data_consulta.strftime('%d/%m/%Y %H:%M')}. Transcrição: {consulta.transcricao_ia or '[Sem transcrição]'}. Dados estruturados: Queixa:{consulta.queixa_principal}, Ex.Físico:{consulta.exame_fisico}, Diag.:{consulta.diagnostico}.""",
            
            # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
            # A instrução 'Use "Rp/" antes dos medicamentos.' foi removida do prompt abaixo.
            'prescricao': f"""Gere uma prescrição médica em TEXTO PURO. Se encontrar medicamentos na transcrição: {consulta.transcricao_ia or '[Sem transcrição]'} ou na conduta: {consulta.conduta}, liste nome, dosagem e posologia. Se não, escreva "Sem medicamentos prescritos". Dados: Paciente: {paciente.nome_completo}, Data: {data_extenso}.""",
            # ▲▲▲ FIM DA CORREÇÃO ▲▲▲
            
            'relatorio': f"""
REGRAS CRÍTICAS:
1. Gere o documento em TEXTO PURO. NÃO use HTML ou Markdown.
2. Sua principal fonte de informação é a TRANSCRIÇÃO COMPLETA da consulta. Use-a para preencher todos os campos do relatório de forma detalhada.
3. Use os dados estruturados apenas para complementar o que não estiver na transcrição.
4. O relatório deve ser completo, técnico e detalhado, refletindo o diálogo da consulta.

TRANSCRIÇÃO COMPLETA:
'''{consulta.transcricao_ia or consulta.transcricao_completa or '[Sem transcrição disponível]'}'''

DADOS ESTRUTURADOS (para complementar):
- Queixa Principal Registrada: {consulta.queixa_principal or '[Não registrada]'}
- Exame Físico Registrado: {consulta.exame_fisico or '[Não realizado]'}
- Hipótese Diagnóstica Registrada: {consulta.hipotese_diagnostica or '[Não definida]'}
- Conduta Registrada: {consulta.conduta or '[Não definida]'}

DADOS DO PACIENTE:
- Nome: {paciente.nome_completo}
- CPF: {paciente.cpf}
- Idade: {paciente.idade} anos

INSTRUÇÕES:
Gere o CORPO de um relatório médico detalhado, preenchendo as seções abaixo com o máximo de informações extraídas da TRANSCRIÇÃO.

FORMATO DO CORPO:
IDENTIFICAÇÃO:
(Use os dados do paciente)

CONSULTA REALIZADA EM: {data_extenso}

MOTIVO DA CONSULTA / QUEIXA PRINCIPAL:
(Descreva detalhadamente o que o paciente relatou como motivo da consulta, com base na transcrição)

HISTÓRIA DA DOENÇA ATUAL (HDA):
(Elabore um texto corrido detalhando o início, a evolução, as características dos sintomas e fatores associados, tudo com base na transcrição)

ANTECEDENTES:
(Liste todos os antecedentes pessoais e familiares mencionados na transcrição)

EXAME FÍSICO:
(Descreva todos os achados do exame físico mencionados pelo médico na transcrição)

HIPÓTESE DIAGNÓSTICA / CONCLUSÃO:
(Liste as hipóteses ou conclusões discutidas durante a consulta, conforme a transcrição)

PLANO / CONDUTA:
(Descreva as recomendações, prescrições e planos de tratamento mencionados pelo médico)
"""
        }
        # ▲▲▲ FIM DA CORREÇÃO NOS PROMPTS ▲▲▲
        
        prompt = prompts.get(tipo_documento, '')
        if not prompt:
            raise Exception(f"Tipo de documento inválido: {tipo_documento}")
        
        request_options = {"timeout": 180}
        response = model.generate_content(prompt, request_options=request_options)
        corpo_documento = response.text
        
        corpo_documento = re.sub(r'```[\w]*\n?', '', corpo_documento)
        corpo_documento = re.sub(r'\*?\*(.*?)\*\*?', r'\1', corpo_documento)

        documento_final = (
            f"{cabecalho}"
            f"{corpo_documento}\n\n\n"
            f"{local_e_data}\n\n"
            f"{assinatura_bloco}"
        )
        
        return {
            'sucesso': True,
            'tipo': tipo_documento,
            'conteudo': documento_final.strip(),
            'data_geracao': timezone.now().isoformat()
        }
    
    except Consulta.DoesNotExist:
        return {'sucesso': False, 'erro': 'Consulta não encontrada'}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ ERRO COMPLETO ao gerar documento:\n{error_detail}")
        return {'sucesso': False, 'erro': str(e)}

def transcrever_audio_geral_com_gemini(audio_base64, audio_formato="webm"):
    """
    Transcreve um clipe de áudio geral usando a API Gemini.
    
    Args:
        audio_base64: String do áudio codificado em base64.
        audio_formato: Formato do áudio (ex: 'webm').
    
    Returns:
        Dicionário com o resultado da transcrição.
    """
    try:
        if not Config.GEMINI_API_KEY or not genai:
            raise Exception("API Gemini não configurada")

        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-pro')

        prompt = "Transcreva o áudio a seguir da forma mais literal e precisa possível. O áudio contém o ditado de um resultado de exame médico. Mantenha a formatação, pontuação e quebras de linha que forem ditadas."

        audio_bytes = base64.b64decode(audio_base64)
        
        request_options = {"timeout": 120}
        response = model.generate_content(
            [prompt, {"mime_type": f"audio/{audio_formato}", "data": audio_bytes}],
            request_options=request_options
        )

        return {'sucesso': True, 'texto': response.text}

    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}

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
    
    # <<< ADICIONADO PARA CORRIGIR O PAINEL ADMIN >>>
    pagination_class = None
    
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
        """Apenas super_admin pode criar clínicas e popula as categorias padrão."""
        if self.request.user.get('funcao') != 'super_admin':
            raise PermissionDenied("Apenas super admin pode criar clínicas")
        
        # Salva a clínica primeiro
        instance = serializer.save()
        
        # AQUI ESTÁ A CORREÇÃO: Chama a função para criar as categorias
        popular_categorias_padrao(instance.id)

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
    
    # <<< ADICIONE ESTA LINHA >>>
    pagination_class = None
    
    def get_queryset(self):
        """Filtrar usuários conforme permissão"""
        user = self.request.user
        
        if user.get('funcao') == 'super_admin':
            return Usuario.objects.all()
        else:
            # Outros usuários veem apenas da própria clínica
            clinica_id = user.get('clinica_id')
            return Usuario.objects.filter(clinica_id=clinica_id) if clinica_id else Usuario.objects.none()
    
    @action(detail=True, methods=['patch', 'options'], authentication_classes=[], permission_classes=[])
    def alterar_status(self, request, pk=None):
        """
        Alterar status do agendamento
        PATCH /api/agendamentos/{id}/alterar_status/
        Body: {"status": "Confirmado"}
        """
        if request.method == 'OPTIONS':
            return Response(status=200)
    
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'erro': 'Token não fornecido'}, status=401)
    
        token = auth_header.split(' ')[1]
    
        try:
            import jwt
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
            clinica_id = payload.get('clinica_id')
        except:
            return Response({'erro': 'Token inválido ou expirado'}, status=401)
    
        try:
            agendamento = Agendamento.objects.get(id=pk, clinica_id=clinica_id)
        except Agendamento.DoesNotExist:
            return Response({'erro': 'Agendamento não encontrado'}, status=404)
    
        novo_status = request.data.get('status')
    
        if not novo_status:
            return Response({'erro': 'Status não fornecido'}, status=400)
    
        if novo_status not in dict(Agendamento.STATUS_CHOICES):
            return Response({'erro': 'Status inválido'}, status=400)
    
        agendamento.status = novo_status
        agendamento.save()
    
        serializer = AgendamentoSerializer(agendamento, context={'request': request})
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
        usuario = Usuario.objects.select_related('clinica').get(email=email)
    except Usuario.DoesNotExist:
        return Response({'mensagem': 'Email ou senha incorretos'}, status=401)
    
    if not usuario.check_password(password):
        return Response({'mensagem': 'Email ou senha incorretos'}, status=401)
    
    if usuario.status != 'ativo':
        return Response({'mensagem': 'Usuário inativo. Entre em contato com o administrador da sua clínica.'}, status=403)

    if usuario.funcao != 'super_admin':
        if not usuario.clinica:
            return Response({'mensagem': 'Erro de configuração: usuário não está vinculado a nenhuma clínica.'}, status=403)
        if usuario.clinica.status != 'ativo':
            return Response({'mensagem': f'Acesso negado. A clínica "{usuario.clinica.nome}" está com status "{usuario.clinica.get_status_display()}".'}, status=403)

    usuario.last_login = timezone.now()
    usuario.save(update_fields=['last_login'])
    
    token = usuario.generate_jwt_token()
    clinica_nome = usuario.clinica.nome if usuario.clinica else None

    # Retornar resposta compatível com admin_panel e frontend
    return Response({
        'access_token': token,
        'user_info': {
            'id': usuario.id,
            'nome_completo': usuario.nome_completo,
            'email': usuario.email,
            'funcao': usuario.funcao,
            'clinica_id': usuario.clinica_id,
            'clinica_nome': clinica_nome,
            'status': usuario.status,
            # ▼▼▼ CAMPO NOVO ADICIONADO À RESPOSTA ▼▼▼
            'precisa_alterar_senha': usuario.precisa_alterar_senha
            # ▲▲▲ FIM DA ADIÇÃO ▲▲▲
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
    funcao = user.get('funcao')
    
    if funcao not in ['super_admin', 'admin']:
        return Response({'mensagem': 'Sem permissão'}, status=403)
    
    print(f"\n🔍 DEBUG REGISTER:")
    print(f"Dados recebidos: {request.data}")
    
    serializer = UsuarioSerializer(data=request.data)
    
    if not serializer.is_valid():
        print(f"❌ Erros de validação: {serializer.errors}")
        return Response({'mensagem': serializer.errors}, status=400)
    
    try:
        usuario = serializer.save()
        print(f"✅ Usuário criado com ID: {usuario.id}")
        
        return Response({
            'mensagem': 'Usuário cadastrado com sucesso',
            'id': usuario.id
        }, status=201)
        
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
        import traceback
        traceback.print_exc()
        return Response({'mensagem': str(e)}, status=500)

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
        """Validar CPF (agora único por clínica para pacientes ativos)"""
        if not Validador.validar_cpf(value):
            raise serializers.ValidationError("CPF inválido.")

        cpf_formatado = Validador.formatar_cpf(value)
        
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.get('clinica_id'):
            raise serializers.ValidationError("Não foi possível identificar a clínica do usuário para validar o CPF.")
            
        clinica_id = request.user.get('clinica_id')

        # A query agora filtra por clinica_id, resolvendo o problema.
        query = Paciente.objects.filter(
            clinica_id=clinica_id, 
            cpf=cpf_formatado, 
            ativo=True
        )

        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("Este CPF já está em uso por outro paciente ativo nesta clínica.")

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

class MedicoSerializer(serializers.ModelSerializer):
    """Serializer simples para listar médicos para dropdowns."""
    class Meta:
        model = Usuario
        fields = ['id', 'nome_completo']


# ============================================
# SERIALIZER AGENDAMENTO
# ============================================

class AgendamentoSerializer(serializers.ModelSerializer):
    """Serializer para Agendamento"""
    
    paciente_nome = serializers.ReadOnlyField()
    paciente_cpf = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    servico_display = serializers.CharField(source='get_servico_display', read_only=True)
    
    paciente_id = serializers.IntegerField(source='paciente.id', read_only=True)
    medico_responsavel_nome = serializers.CharField(source='medico_responsavel.nome_completo', read_only=True, allow_null=True)
    
    class Meta:
        model = Agendamento
        fields = [
            'id', 'paciente', 'paciente_id', 'paciente_nome', 'paciente_cpf',
            'convenio', 'servico', 'servico_display', 'tipo', 'data', 'hora',
            'valor', 'observacoes', 'status', 'status_display',
            'medico_responsavel', 'medico_responsavel_nome',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ['id', 'paciente_nome', 'paciente_cpf', 'paciente_id', 'data_cadastro', 'data_atualizacao']
    
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
        if not self.instance and value < date.today():
            raise serializers.ValidationError("Não é possível agendar para datas passadas")
        return value
    
    def validate(self, data):
        """Validações gerais, incluindo verificação de disponibilidade por médico."""
        request = self.context.get('request')
        
        data_agendamento = data.get('data', getattr(self.instance, 'data', None))
        hora_agendamento = data.get('hora', getattr(self.instance, 'hora', None))
        
        medico_responsavel = data.get('medico_responsavel', getattr(self.instance, 'medico_responsavel', None))
        medico_id = medico_responsavel.id if medico_responsavel else None

        if request and hasattr(request, 'user') and data_agendamento and hora_agendamento:
            clinica_id = request.user.get('clinica_id')
            excluir_id = self.instance.id if self.instance else None
            
            if not Agendamento.verificar_disponibilidade(
                clinica_id, data_agendamento, hora_agendamento, medico_id, excluir_id
            ):
                nome_medico = medico_responsavel.nome_completo if medico_responsavel else "a clínica (sem médico específico)"
                raise serializers.ValidationError({
                    'hora': f"Horário indisponível. Já existe um agendamento para {nome_medico} em {data_agendamento.strftime('%d/%m/%Y')} às {hora_agendamento.strftime('%H:%M')}."
                })
        
        return data


class AgendamentoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de agendamentos"""
    
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    paciente_id = serializers.IntegerField(source='paciente.id', read_only=True)
    medico_responsavel_nome = serializers.CharField(source='medico_responsavel.nome_completo', read_only=True, allow_null=True)

    paciente_telefone = serializers.CharField(source='paciente.telefone_celular', read_only=True)
    paciente_sexo = serializers.CharField(source='paciente.get_sexo_display', read_only=True)
    paciente_idade = serializers.IntegerField(source='paciente.idade', read_only=True)

    class Meta:
        model = Agendamento
        fields = [
            'id', 
            'paciente_id',
            'paciente_nome', 
            'medico_responsavel_nome',
            'servico', 
            'tipo', 
            'data', 
            'hora',
            'valor', 
            'status', 
            'status_display',
            'convenio',
            'paciente_telefone',
            'paciente_sexo',
            'paciente_idade'
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
        # <<< INÍCIO DA CORREÇÃO >>>
        read_only_fields = [
            'id', 
            'clinica_id', # Adicionado aqui para ser gerenciado pelo backend
            'transcricao_completa', 'transcricao_ia', 
            'transcricao_medico', 'transcricao_paciente',
            'confianca_transcricao', 'tempo_processamento_transcricao',
            'data_inicio_atendimento', 'data_fim_atendimento',
            'data_cadastro', 'data_atualizacao'
        ]
        # <<< FIM DA CORREÇÃO >>>
    
    def validate_paciente(self, value):
        """Validar se paciente pertence à clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            if value.clinica_id != clinica_id:
                raise serializers.ValidationError("Paciente não pertence a esta clínica")
        return value
    
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
        # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
        # A lista base de campos somente leitura. 'interpretacao_ia' foi removida daqui.
        read_only_fields = [
            'id', 
            'clinica_id',
            'confianca_ia', 'fontes_consultadas',
            'tempo_processamento', 'erro_ia', 'tipo_exame_identificado_ia',
            'data_cadastro', 'data_atualizacao'
        ]
    
    def __init__(self, *args, **kwargs):
        """
        Construtor customizado para tornar campos somente leitura de forma dinâmica
        baseado na função do usuário.
        """
        super(ExameSerializer, self).__init__(*args, **kwargs)
        
        request = self.context.get('request')
        
        if request and hasattr(request, 'user') and request.user:
            funcao_usuario = request.user.get('funcao')
            
            # Garante que a lista de read_only_fields seja uma cópia para não afetar outras instâncias
            self.Meta.read_only_fields = list(self.Meta.read_only_fields)
            
            # Se a função for 'secretaria', adiciona 'interpretacao_ia' à lista de campos somente leitura
            if funcao_usuario == 'secretaria':
                if 'interpretacao_ia' not in self.Meta.read_only_fields:
                    self.Meta.read_only_fields.append('interpretacao_ia')
            # Garante que para outros perfis (médico/admin) o campo NÃO seja read_only
            elif 'interpretacao_ia' in self.Meta.read_only_fields:
                self.Meta.read_only_fields.remove('interpretacao_ia')
    # ▲▲▲ FIM DA CORREÇÃO ▲▲▲
    
    def validate_paciente(self, value):
        """Validar se paciente pertence à clínica"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            if value.clinica_id != clinica_id:
                raise serializers.ValidationError("Paciente não pertence a esta clínica")
        return value

class ExameListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de exames"""
    
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    tipo_exame_display = serializers.CharField(source='get_tipo_exame_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tem_interpretacao_ia = serializers.SerializerMethodField()
    revisado = serializers.BooleanField(source='revisado_por_medico', read_only=True)
    
    # <<< CAMPO ADICIONADO PARA CORREÇÃO >>>
    tipo_exame_identificado_pela_ia = serializers.CharField(source='tipo_exame_identificado_ia', read_only=True)

    class Meta:
        model = Exame
        fields = [
            'id', 'paciente_nome', 'tipo_exame', 'tipo_exame_display',
            'data_exame', 'data_resultado', 'status', 'status_display',
            'tem_interpretacao_ia', 'revisado', 'confianca_ia',
            'tipo_exame_identificado_pela_ia' # <<< ADICIONADO AQUI
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
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    
    class Meta:
        model = Receita
        fields = [
            'id', 'clinica_id', 'categoria', 'categoria_nome', 'agendamento', 'paciente', 'paciente_nome',
            'descricao', 'valor', 'data_vencimento', 'data_recebimento',
            'status', 'status_display', 'forma_pagamento', 'observacoes',
            'usuario_cadastro_id', 'usuario_cadastro_nome',
            'usuario_recebimento_id', 'usuario_recebimento_nome', 'data_operacao_recebimento',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ['id', 'data_cadastro', 'data_atualizacao']
    
    def validate_valor(self, value):
        """Validar valor"""
        if value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            data['clinica_id'] = clinica_id
            
            # Validar se paciente pertence à clínica
            if 'paciente' in data and data['paciente']:
                if data['paciente'].clinica_id != clinica_id:
                    raise serializers.ValidationError({
                        'paciente': 'Paciente não pertence a esta clínica'
                    })
            
            # Validar se categoria pertence à clínica
            if 'categoria' in data and data['categoria']:
                if data['categoria'].clinica_id != clinica_id:
                    raise serializers.ValidationError({
                        'categoria': 'Categoria não pertence a esta clínica'
                    })
        
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
            'data_recebimento', 'status', 'status_display', 'paciente_nome',
            'forma_pagamento'  # <-- CAMPO ADICIONADO
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
            'id', 'clinica_id', 'categoria', 'categoria_nome', 'descricao', 'valor',
            'data_vencimento', 'data_pagamento', 'status', 'status_display',
            'fornecedor', 'forma_pagamento', 'observacoes',
            'usuario_cadastro_id', 'usuario_cadastro_nome',
            'usuario_pagamento_id', 'usuario_pagamento_nome', 'data_operacao_pagamento',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ['id', 'data_cadastro', 'data_atualizacao']
    
    def validate_valor(self, value):
        """Validar valor"""
        if value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero")
        return value
    
    def validate(self, data):
        """Validações gerais"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            clinica_id = request.user.get('clinica_id')
            data['clinica_id'] = clinica_id
            
            # Validar se categoria pertence à clínica
            if 'categoria' in data and data['categoria']:
                if data['categoria'].clinica_id != clinica_id:
                    raise serializers.ValidationError({
                        'categoria': 'Categoria não pertence a esta clínica'
                    })
        
        return data

# ▼▼▼ SUBSTITUA A CLASSE 'DespesaListSerializer' PELA VERSÃO CORRIGIDA E COMPLETA ABAIXO ▼▼▼
class DespesaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de despesas"""
    
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Despesa
        fields = [
            'id', 'descricao', 'valor', 'categoria_nome', 'data_vencimento',
            'data_pagamento', 'status', 'status_display', 'fornecedor',
            'forma_pagamento'  # --- CAMPO CORRIGIDO E ADICIONADO AQUI ---
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
    
    # DENTRO da class PacienteViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        """
        Filtrar pacientes: super_admin vê todos, outros usuários veem apenas da sua clínica.
        VERSÃO CORRIGIDA: Permite que ações de detalhe (como reativar) encontrem pacientes inativos.
        """
        user = self.request.user
        clinica_id = user.get('clinica_id')

        # Se a ação for para um item específico (retrieve, update, reativar, etc.),
        # ou se for para listar os inativos, busca em TODOS os pacientes da clínica.
        if self.action not in ['list'] or self.request.path.endswith('/inativos/'):
            if user.get('funcao') == 'super_admin':
                return Paciente.objects.all()
            return Paciente.objects.filter(clinica_id=clinica_id) if clinica_id else Paciente.objects.none()

        # Para a ação 'list' (a lista principal), continua mostrando apenas os ativos.
        if user.get('funcao') == 'super_admin':
            queryset = Paciente.objects.filter(ativo=True)
        elif clinica_id is not None:
            queryset = Paciente.objects.filter(clinica_id=clinica_id, ativo=True)
        else:
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

    # Dentro da class PacienteViewSet(viewsets.ModelViewSet):

    @action(detail=True, methods=['post'], url_path='reativar')
    def reativar_paciente(self, request, pk=None):
        """
        Reativar um paciente inativo.
        VERSÃO CORRIGIDA: Busca o paciente inativo diretamente para evitar conflitos com get_queryset.
        """
        clinica_id = request.user.get('clinica_id')

        try:
            # Passo 1: Busca direta pelo paciente INATIVO que queremos reativar.
            paciente_para_reativar = Paciente.objects.get(pk=pk, clinica_id=clinica_id, ativo=False)
        
        except Paciente.DoesNotExist:
            # Se ele não for encontrado como inativo, algo está errado (talvez já esteja ativo).
            return Response({'erro': 'Paciente não encontrado na lista de inativos ou já está ativo.'}, status=status.HTTP_404_NOT_FOUND)

        # Passo 2: Agora, com o CPF do paciente inativo em mãos, fazemos a verificação de segurança.
        # Procuramos por QUALQUER OUTRO paciente que tenha o mesmo CPF e esteja ativo.
        paciente_ativo_conflitante = Paciente.objects.filter(
            cpf=paciente_para_reativar.cpf, 
            ativo=True,
            clinica_id=clinica_id
        ).exclude(pk=paciente_para_reativar.id).first() # Excluímos ele mesmo da busca

        if paciente_ativo_conflitante:
            # Se encontrarmos um conflitante, retornamos o erro.
            return Response(
                {'erro': f'Não é possível reativar. Já existe outro paciente ativo com o CPF {paciente_para_reativar.cpf} (ID: {paciente_ativo_conflitante.id}).'},
                status=status.HTTP_409_CONFLICT
            )

        # Passo 3: Se não houver conflito, podemos reativar o paciente com segurança.
        paciente_para_reativar.ativo = True
        paciente_para_reativar.save()
    
        # Retornamos os dados do paciente agora reativado.
        serializer = self.get_serializer(paciente_para_reativar)
        return Response(serializer.data)


    @action(detail=True, methods=['get'], url_path='historico_completo')
    def historico_completo(self, request, pk=None):
        """
        Retorna o histórico completo de consultas e documentos de um paciente.
        GET /api/pacientes/{id}/historico_completo/
        """
        paciente = self.get_object()
        paciente_data = PacienteSerializer(paciente).data
        
        historico = []
        
        # Busca todas as consultas do paciente, ordenadas da mais recente para a mais antiga
        consultas = paciente.consultas.all().order_by('-data_consulta')
        
        # Mapeamento dos campos de documento
        doc_map = {
            'anamnese': 'anamnese_documento',
            'evolucao': 'evolucao_medica',
            'prescricao': 'prescricao_documento',
            'atestado': 'atestado_medico',
            'relatorio': 'relatorio_medico',
        }
        
        for consulta in consultas:
            documentos_da_consulta = []
            
            # Verifica cada tipo de documento na consulta
            for tipo, campo in doc_map.items():
                conteudo = getattr(consulta, campo)
                if conteudo:
                    documentos_da_consulta.append({
                        'tipo': tipo,
                        'conteudo': conteudo
                    })
            
            historico.append({
                'consulta_id': consulta.id,
                'data_consulta': consulta.data_consulta.strftime('%d/%m/%Y às %H:%M'),
                'medico_responsavel': consulta.medico_responsavel or "Não informado",
                'status_display': consulta.get_status_display(),
                'documentos': documentos_da_consulta,
            })
            
        return Response({
            'paciente': paciente_data,
            'historico': historico
        })

# --- NOVO BLOCO DE CÓDIGO ---
class MedicoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de apenas leitura para listar os médicos de uma clínica.
    GET /api/medicos/
    """
    serializer_class = MedicoSerializer
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    pagination_class = None # Retorna todos os médicos, sem paginação

    def get_queryset(self):
        """Filtra usuários com função 'medico' da clínica do usuário logado."""
        clinica_id = self.request.user.get('clinica_id')
        if clinica_id:
            return Usuario.objects.filter(clinica_id=clinica_id, funcao='medico', status='ativo').order_by('nome_completo')
        return Usuario.objects.none()


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
    
    ordering = ['data', 'hora']
    
    def perform_create(self, serializer):
        """Injeta o clinica_id do usuário logado antes de salvar."""
        clinica_id = self.request.user.get('clinica_id')
        serializer.save(clinica_id=clinica_id)

    def get_queryset(self):
        """Filtrar agendamentos pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        
        # --- ALTERAÇÃO AQUI: Adiciona select_related para o médico ---
        queryset = Agendamento.objects.select_related('paciente', 'medico_responsavel').filter(clinica_id=clinica_id)
        
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
    
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescreve o método de exclusão para lidar com dependências.
        """
        instance = self.get_object()
        
        Consulta.objects.filter(agendamento=instance).delete()
        Receita.objects.filter(agendamento=instance).delete()
        
        self.perform_destroy(instance)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
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
    
    @action(detail=True, methods=['patch', 'options'], authentication_classes=[], permission_classes=[])
    def alterar_status(self, request, pk=None):
        """
        Alterar status do agendamento
        PATCH /api/agendamentos/{id}/alterar_status/
        Body: {"status": "Confirmado"}
        """
        if request.method == 'OPTIONS':
            return Response(status=200)
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'erro': 'Token não fornecido'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            import jwt
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
            clinica_id = payload.get('clinica_id')
        except:
            return Response({'erro': 'Token inválido ou expirado'}, status=401)
        
        try:
            agendamento = Agendamento.objects.get(id=pk, clinica_id=clinica_id)
        except Agendamento.DoesNotExist:
            return Response({'erro': 'Agendamento não encontrado'}, status=404)
        
        novo_status = request.data.get('status')
        
        if not novo_status:
            return Response({'erro': 'Status não fornecido'}, status=400)
        
        if novo_status not in dict(Agendamento.STATUS_CHOICES):
            return Response({'erro': 'Status inválido'}, status=400)
            
        status_antigo = agendamento.status
        
        if status_antigo == 'Realizado' and novo_status != 'Realizado':
            Receita.objects.filter(agendamento=agendamento).delete()
            print(f"INFO: Receita vinculada ao agendamento {agendamento.id} foi excluída devido à reversão de status.")
            
        agendamento.status = novo_status
        agendamento.save()
        
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
    - POST /api/consultas/{id}/salvar-audio/ - Salvar áudio da consulta
    - POST /api/consultas/{id}/transcrever-audio/ - Transcrever áudio salvo
    - POST /api/consultas/{id}/gerar-documento/ - Gerar documento médico
    - POST /api/consultas/{id}/salvar-documento/ - Salvar documento editado
    - POST /api/consultas/{id}/finalizar/ - Finalizar consulta
    """
    
    # --- INÍCIO DA CORREÇÃO ---
    # A permissão base é alterada para a mais permissiva necessária.
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove] 
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """
        Aplica permissões dinâmicas. Secretárias podem apenas listar e visualizar (leitura).
        Médicos e Admins podem realizar todas as ações.
        """
        # Ações seguras (leitura) são permitidas para Secretária e acima.
        if self.action in ['list', 'retrieve', 'listar_documentos']:
            permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
        # Todas as outras ações que modificam dados exigem permissão de Médico ou Admin.
        else:
            permission_classes = [IsAuthenticated, IsAdminOrMedico]
        
        return [permission() for permission in permission_classes]
    # --- FIM DA CORREÇÃO ---

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['paciente__nome_completo']
    ordering_fields = ['data_consulta']
    ordering = ['-data_consulta']
    
    def get_queryset(self):
        """Filtrar consultas pela clínica do usuário"""
        clinica_id = self.request.user.get('clinica_id')
        queryset = Consulta.objects.filter(clinica_id=clinica_id)
        
        paciente_id = self.request.query_params.get('paciente_id', None)
        status = self.request.query_params.get('status', None)
        data_inicial = self.request.query_params.get('data_inicial', None)
        data_final = self.request.query_params.get('data_final', None)
        agendamento_id = self.request.query_params.get('agendamento', None)
        
        if agendamento_id:
            queryset = queryset.filter(agendamento_id=agendamento_id)
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
    
    def perform_create(self, serializer):
        """Injeta o clinica_id do usuário logado antes de salvar."""
        clinica_id = self.request.user.get('clinica_id')
        agendamento = serializer.validated_data.get('agendamento')
        if agendamento:
            existente = Consulta.objects.filter(clinica_id=clinica_id, agendamento=agendamento).first()
            if existente:
                return
        serializer.save(clinica_id=clinica_id)
    
    @action(detail=False, methods=['get'], url_path='fila-hoje')
    def fila_hoje(self, request):
        """
        Retorna fila de atendimento de hoje, mostrando apenas agendamentos pendentes.
        """
        clinica_id = self.request.user.get('clinica_id')
        hoje = date.today()
        
        # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
        # O filtro de status foi alterado de status__in=['Agendado', 'Confirmado']
        # para buscar apenas status='Confirmado'.
        agendamentos_hoje = Agendamento.objects.filter(
            clinica_id=clinica_id,
            data=hoje,
            status='Confirmado'
        ).select_related('paciente').order_by('hora')
        # ▲▲▲ FIM DA CORREÇÃO ▲▲▲
        
        fila = []
        for agend in agendamentos_hoje:
            consulta_existente = Consulta.objects.filter(
                agendamento=agend,
                data_consulta__date=hoje
            ).first()
            
            if consulta_existente and consulta_existente.status in ['finalizada', 'cancelada', 'faltou']:
                continue

            pode_interagir = not consulta_existente or consulta_existente.status in ['agendada', 'confirmada', 'em_atendimento', 'aguardando_revisao']
            
            fila.append({
                'agendamento_id': agend.id,
                'paciente_id': agend.paciente.id,
                'paciente_nome': agend.paciente_nome,
                'paciente_cpf': agend.paciente_cpf,
                'paciente_sexo': agend.paciente.get_sexo_display(),
                'hora': agend.hora.strftime('%H:%M'),
                'tipo': agend.tipo,
                'convenio': agend.convenio,
                'observacoes': agend.observacoes,
                'consulta_id': consulta_existente.id if consulta_existente else None,
                'consulta_status': consulta_existente.status if consulta_existente else 'nao_iniciada',
                'pode_interagir': pode_interagir
            })
        
        return Response({
            'data': hoje.isoformat(),
            'total': len(fila),
            'fila': fila
        })
    
    @action(detail=True, methods=['post'], url_path='iniciar-atendimento')
    def iniciar_atendimento(self, request, pk=None):
        """
        Iniciar atendimento da consulta. NÃO altera o status do agendamento.
        """
        consulta = self.get_object()
        usuario = request.user.payload
        if consulta.status not in ['agendada', 'confirmada']:
            return Response({'erro': 'Consulta não pode ser iniciada neste status'}, status=400)
        try:
            medico = Usuario.objects.get(id=usuario.get('sub'), clinica_id=usuario.get('clinica_id'))
            medico_nome, medico_crm = medico.nome_completo, medico.crm or ''
        except Usuario.DoesNotExist:
            medico_nome, medico_crm = usuario.get('nome', ''), ''
        if not medico_nome.startswith('Dr.'): medico_nome = f"Dr. {medico_nome}"
        consulta.medico_responsavel, consulta.medico_crm = medico_nome, medico_crm
        consulta.iniciar_atendimento()
        serializer = ConsultaSerializer(consulta, context={'request': request})
        return Response({'mensagem': 'Atendimento iniciado', 'consulta': serializer.data})
        
    @action(detail=True, methods=['post'], url_path='salvar-audio')
    def salvar_audio(self, request, pk=None):
        """
        Apenas recebe e salva o áudio da consulta no banco de dados.
        """
        consulta = self.get_object()
        audio_base64 = request.data.get('audio_base64')
        if not audio_base64:
            return Response({'erro': 'Nenhum áudio fornecido.'}, status=status.HTTP_400_BAD_REQUEST)

        consulta.audio_consulta = audio_base64
        consulta.audio_formato = request.data.get('audio_formato', 'webm')
        consulta.status = 'gravando' 
        consulta.save(update_fields=['audio_consulta', 'audio_formato', 'status'])
        
        serializer = self.get_serializer(consulta)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='transcrever-audio')
    def transcrever_audio_action(self, request, pk=None):
        """
        Dispara a transcrição de uma consulta que JÁ POSSUI um áudio salvo.
        """
        consulta = self.get_object()
        if not consulta.audio_consulta:
            return Response({'erro': 'Nenhum áudio salvo nesta consulta para transcrever.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            resultado = transcrever_consulta_com_gemini(consulta.id)
            if not resultado.get('sucesso'):
                raise Exception(resultado.get('erro', 'Erro desconhecido na IA.'))

            consulta.refresh_from_db()
            serializer = self.get_serializer(consulta)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'erro': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='gerar-documento')
    def gerar_documento(self, request, pk=None):
        """
        Gerar documento médico (VERSÃO SÍNCRONA)
        """
        consulta = self.get_object()
        tipo = request.data.get('tipo')
        if not tipo:
            return Response({'erro': 'Tipo de documento não fornecido'}, status=400)
        if not consulta.medico_responsavel:
            return Response({'erro': 'Consulta sem médico responsável definido'}, status=400)
        
        resultado = gerar_documento_medico_sync(
            consulta.id,
            tipo,
            consulta.medico_responsavel,
            consulta.medico_crm or ''
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
            return Response({'erro': 'Erro ao gerar documento', 'detalhes': resultado['erro']}, status=500)
    
    @action(detail=True, methods=['post'], url_path='salvar-documento')
    def salvar_documento(self, request, pk=None):
        """ Salvar documento médico (após revisão/edição) """
        consulta = self.get_object()
        tipo = request.data.get('tipo')
        conteudo = request.data.get('conteudo')
        if not tipo or not conteudo:
            return Response({'erro': 'Tipo e conteúdo são obrigatórios'}, status=400)
        campo_map = {'atestado': 'atestado_medico', 'anamnese': 'anamnese_documento', 'evolucao': 'evolucao_medica', 'prescricao': 'prescricao_documento', 'relatorio': 'relatorio_medico'}
        setattr(consulta, campo_map.get(tipo), conteudo)
        if not consulta.documentos_gerados: consulta.documentos_gerados = []
        encontrado = False
        for i, doc in enumerate(consulta.documentos_gerados):
            if doc.get('tipo') == tipo:
                consulta.documentos_gerados[i] = {'tipo': tipo, 'data_geracao': timezone.now().isoformat(), 'editado': True, 'medico': consulta.medico_responsavel}
                encontrado = True
                break
        if not encontrado:
            consulta.documentos_gerados.append({'tipo': tipo, 'data_geracao': timezone.now().isoformat(), 'editado': True, 'medico': consulta.medico_responsavel})
        consulta.save()
        serializer = ConsultaSerializer(consulta, context={'request': request})
        return Response({'mensagem': 'Documento salvo com sucesso', 'consulta': serializer.data})
    
    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        """
        Finalizar consulta e ATUALIZAR status do agendamento.
        """
        consulta = self.get_object()
        if consulta.status == 'finalizada':
            return Response({'erro': 'Consulta já finalizada'}, status=400)
        
        consulta.finalizar_atendimento()
        
        if consulta.agendamento and consulta.agendamento.status != 'Realizado':
            consulta.agendamento.status = 'Realizado'
            consulta.agendamento.save(update_fields=['status'])
        
        serializer = ConsultaSerializer(consulta, context={'request': request})
        return Response({'mensagem': 'Consulta finalizada com sucesso', 'consulta': serializer.data})
    
    @action(detail=True, methods=['get'], url_path='documentos')
    def listar_documentos(self, request, pk=None):
        """ Listar todos os documentos da consulta """
        consulta = self.get_object()
        documentos = []
        
        campo_map = {
            'atestado_medico': 'atestado',
            'anamnese_documento': 'anamnese',
            'evolucao_medica': 'evolucao',
            'prescricao_documento': 'prescricao',
            'relatorio_medico': 'relatorio'
        }
        
        datas_geracao = {doc.get('tipo'): doc.get('data_geracao') for doc in consulta.documentos_gerados}

        for campo, tipo in campo_map.items():
            conteudo = getattr(consulta, campo)
            if conteudo:
                data_geracao_str = datas_geracao.get(tipo, consulta.data_atualizacao.isoformat())
                
                try:
                    from datetime import datetime
                    data_formatada = datetime.fromisoformat(data_geracao_str).strftime('%d/%m/%Y')
                except:
                    data_formatada = consulta.data_atualizacao.strftime('%d/%m/%Y')

                documentos.append({
                    'tipo': tipo,
                    'conteudo': conteudo,
                    'data_geracao': data_formatada
                })

        return Response({'consulta_id': consulta.id, 'documentos': documentos})


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
    
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove] 
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['paciente__nome_completo', 'tipo_exame']
    ordering_fields = ['data_exame']
    ordering = ['-data_exame']

    # --- INÍCIO DA CORREÇÃO ---
    def get_permissions(self):
        """
        Instancia e retorna a lista de permissões que esta view requer,
        aplicando permissões mais restritas para ações que modificam dados.
        """
        # Ações de listagem e visualização de detalhes são permitidas para Secretárias e acima.
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
        # Todas as outras ações (criar, editar, deletar, interpretar, etc.)
        # exigem permissão de Médico ou Administrador.
        else:
            permission_classes = [IsAuthenticated, IsAdminOrMedico]
        
        return [permission() for permission in permission_classes]
    # --- FIM DA CORREÇÃO ---
    
    def get_queryset(self):
        """Filtrar exames pela clínica do usuário."""
        clinica_id = self.request.user.get('clinica_id')
        queryset = Exame.objects.filter(clinica_id=clinica_id)
        
        paciente_id = self.request.query_params.get('paciente_id', None)
        status = self.request.query_params.get('status', None)
        tipo = self.request.query_params.get('tipo', None)
        interpretado_ia = self.request.query_params.get('interpretado_ia', None)
        
        if interpretado_ia is not None:
            if interpretado_ia.lower() == 'true':
                queryset = queryset.exclude(interpretacao_ia__isnull=True).exclude(interpretacao_ia__exact='')
            elif interpretado_ia.lower() == 'false':
                queryset = queryset.filter(Q(interpretacao_ia__isnull=True) | Q(interpretacao_ia__exact=''))
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        if status:
            queryset = queryset.filter(status=status)
        if tipo:
            queryset = queryset.filter(tipo_exame=tipo)
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return ExameListSerializer
        return ExameSerializer
    
    def perform_create(self, serializer):
        """Injeta o clinica_id do usuário logado antes de salvar."""
        clinica_id = self.request.user.get('clinica_id')
        serializer.save(clinica_id=clinica_id)
    
    @action(detail=False, methods=['post'], url_path='upload-ia')
    def upload_interpretar_ia(self, request):
        """
        Upload de arquivo de exame e interpretação automática por IA
        POST /api/exames/upload-ia/
        """
        from rest_framework.parsers import MultiPartParser, FormParser
        self.parser_classes = [MultiPartParser, FormParser]

        usuario_payload = request.user.payload
        clinica_id = usuario_payload.get('clinica_id')
        
        try:
            medico_logado = Usuario.objects.get(id=usuario_payload.get('sub'))
            usuario_nome = medico_logado.nome_completo
            usuario_crm = medico_logado.crm or ''
        except Usuario.DoesNotExist:
            usuario_nome = usuario_payload.get('nome', '')
            usuario_crm = ''
        
        paciente_id = request.data.get('paciente')
        if not paciente_id:
            return Response({'erro': 'paciente_id é obrigatório'}, status=400)
        
        try:
            paciente = Paciente.objects.get(id=paciente_id, clinica_id=clinica_id)
        except Paciente.DoesNotExist:
            return Response({'erro': 'Paciente não encontrado'}, status=404)
        
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response({'erro': 'Arquivo é obrigatório'}, status=400)
        
        arquivo_bytes = arquivo.read()
        arquivo_base64_str = base64.b64encode(arquivo_bytes).decode('utf-8')
        arquivo_nome = arquivo.name
        arquivo_tipo = arquivo.content_type
        
        arquivo_base64_completo = f"data:{arquivo_tipo};base64,{arquivo_base64_str}"
        
        exame = Exame.objects.create(
            clinica_id=clinica_id,
            paciente=paciente,
            tipo_exame=request.data.get('tipo_exame', 'outros'),
            data_exame=request.data.get('data_exame', date.today()),
            arquivo_exame=arquivo_base64_completo,
            arquivo_nome=arquivo_nome,
            arquivo_tipo=arquivo_tipo,
            medico_solicitante=request.data.get('medico_solicitante', usuario_nome),
            medico_solicitante_crm=request.data.get('medico_solicitante_crm', usuario_crm),
            observacoes=request.data.get('observacoes', ''),
            status='enviado_ia'
        )
        
        try:
            resultado = interpretar_exame_com_gemini(exame.id)
            
            if resultado['sucesso']:
                exame.refresh_from_db()
                serializer = ExameSerializer(exame, context={'request': request})
                return Response({
                    'mensagem': 'Exame interpretado com sucesso',
                    'exame': serializer.data,
                    'tempo_processamento': resultado['tempo_processamento']
                }, status=201)
            else:
                exame.delete()
                return Response({
                    'erro': 'Erro ao interpretar exame com IA',
                    'detalhes': resultado.get('erro', 'Erro desconhecido')
                }, status=500)
        except Exception as e:
            exame.delete()
            return Response({
                'erro': 'Erro crítico durante a chamada de interpretação',
                'detalhes': str(e)
            }, status=500)

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
        
        exame.revisado_por_medico = True
        exame.medico_revisor_nome = medico_nome
        exame.medico_revisor_crm = medico_crm
        exame.data_revisao = timezone.now()
        exame.observacoes_medico = request.data.get('observacoes_medico', '')
        exame.status = 'revisado_medico'
        
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
        clinica_id = self.request.user.get('clinica_id')
        
        exames = Exame.objects.filter(clinica_id=clinica_id)

        total = exames.count()
        interpretados_ia = exames.filter(status__in=['interpretado_ia', 'revisado_medico', 'finalizado']).count()
        revisados = exames.filter(revisado_por_medico=True).count()
        processando = exames.filter(status='processando_ia').count()
        erros = exames.filter(status='erro_ia').count()
        
        tempo_medio = exames.filter(
            tempo_processamento__isnull=False
        ).aggregate(media=models.Avg('tempo_processamento'))['media']
        
        confianca_media = exames.filter(
            confianca_ia__isnull=False
        ).aggregate(media=models.Avg('confianca_ia'))['media']
        
        taxa_revisao = (revisados / interpretados_ia * 100) if interpretados_ia > 0 else 0
        
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

# NO ARQUIVO: main.py
# ANTES DA CLASSE: DespesaViewSet
# DEPOIS DA CLASSE: CategoriaDespesaViewSet

# ============================================
# VIEWSET RECEITA
# ============================================

class ReceitaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Receitas
    """
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao']
    ordering_fields = ['data_vencimento', 'valor']
    ordering = ['-data_vencimento']
    
    def get_queryset(self):
        clinica_id = self.request.user.get('clinica_id')
        Receita.atualizar_status_vencidos(clinica_id)
        queryset = Receita.objects.select_related('categoria', 'paciente').filter(clinica_id=clinica_id)
        status = self.request.query_params.get('status', None)
        categoria_id = self.request.query_params.get('categoria_id', None)
        paciente_id = self.request.query_params.get('paciente_id', None)
        data_inicial = self.request.query_params.get('data_inicial', None)
        data_final = self.request.query_params.get('data_final', None)
        mes = self.request.query_params.get('mes', None)
        ano = self.request.query_params.get('ano', None)
        if status: queryset = queryset.filter(status=status)
        if categoria_id: queryset = queryset.filter(categoria_id=categoria_id)
        if paciente_id: queryset = queryset.filter(paciente_id=paciente_id)
        if data_inicial and data_final: queryset = queryset.filter(data_vencimento__range=[data_inicial, data_final])
        elif mes and ano: queryset = queryset.filter(data_vencimento__year=ano, data_vencimento__month=mes)
        elif ano: queryset = queryset.filter(data_vencimento__year=ano)
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return ReceitaListSerializer
        return ReceitaSerializer
    
    def perform_create(self, serializer):
        """Injeta dados do usuário na criação de uma receita."""
        user = self.request.user
        clinica_id = user.get('clinica_id')
        
        # Pega o status que está vindo do frontend
        status_receita = serializer.validated_data.get('status')
        
        # Dados de auditoria do CADASTRO (sempre preenchidos)
        usuario_cadastro_id = user.get('sub')
        usuario_cadastro_nome = user.get('nome')
        
        # Dados de auditoria do RECEBIMENTO (preenchidos condicionalmente)
        usuario_recebimento_id = None
        usuario_recebimento_nome = None
        data_operacao_recebimento = None
        
        # Se a receita já está sendo criada como "recebida"
        if status_receita == 'recebida':
            usuario_recebimento_id = user.get('sub')
            usuario_recebimento_nome = user.get('nome')
            data_operacao_recebimento = timezone.now()

        # Salva o objeto no banco de dados injetando os campos de auditoria
        serializer.save(
            clinica_id=clinica_id,
            usuario_cadastro_id=usuario_cadastro_id,
            usuario_cadastro_nome=usuario_cadastro_nome,
            usuario_recebimento_id=usuario_recebimento_id,
            usuario_recebimento_nome=usuario_recebimento_nome,
            data_operacao_recebimento=data_operacao_recebimento
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Atualizar parcialmente uma receita (usado para marcar como recebida)
        """
        instance = self.get_object()
        
        # Se está marcando como recebida, registrar auditoria
        if 'status' in request.data and request.data['status'] == 'recebida':
            user = request.user
            instance.status = 'recebida'
            instance.data_recebimento = request.data.get('data_recebimento', date.today())
            instance.forma_pagamento = request.data.get('forma_pagamento', instance.forma_pagamento)
            
            # Auditoria
            instance.usuario_recebimento_id = user.get('sub')
            instance.usuario_recebimento_nome = user.get('nome')
            instance.data_operacao_recebimento = timezone.now()
            
            instance.save(update_fields=[
                'status', 
                'data_recebimento', 
                'forma_pagamento',
                'usuario_recebimento_id', 
                'usuario_recebimento_nome',
                'data_operacao_recebimento'
            ])
            
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        # Para outras atualizações, usar o método padrão
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def receber(self, request, pk=None):
        receita = self.get_object()
        data_recebimento = request.data.get('data_recebimento', date.today())
        forma_pagamento = request.data.get('forma_pagamento')
        if not forma_pagamento: return Response({'erro': 'Forma de pagamento não fornecida'}, status=400)
        receita.marcar_como_recebida(data_recebimento, forma_pagamento)
        serializer = ReceitaSerializer(receita, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def receber_de_agendamento(self, request):
        agendamento_id = request.data.get('agendamento_id')
        forma_pagamento = request.data.get('forma_pagamento')
        if not agendamento_id or not forma_pagamento: return Response({'erro': 'Dados incompletos'}, status=400)
        
        # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
        user = self.request.user
        clinica_id = user.get('clinica_id')
        
        try: agendamento = Agendamento.objects.get(id=agendamento_id, clinica_id=clinica_id)
        except Agendamento.DoesNotExist: return Response({'erro': 'Agendamento não encontrado'}, status=404)
        
        if agendamento.status != 'Realizado': return Response({'erro': 'Agendamento deve estar com status "Realizado"'}, status=400)
        if not agendamento.valor or agendamento.valor <= 0: return Response({'erro': 'Agendamento não possui valor definido'}, status=400)
        if Receita.objects.filter(agendamento=agendamento).exists(): return Response({'erro': 'Já existe receita para este agendamento'}, status=400)
        
        categoria = None
        if agendamento.servico == 'Consulta': categoria = CategoriaReceita.objects.filter(clinica_id=clinica_id, nome='Consultas').first()
        elif agendamento.servico == 'Exame': categoria = CategoriaReceita.objects.filter(clinica_id=clinica_id, nome='Exames').first()

        # Captura os dados do usuário logado que está realizando a ação
        usuario_id = user.get('sub')
        usuario_nome = user.get('nome')

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
            observacoes=f"Recebimento de {agendamento.tipo} - {agendamento.data}",
            
            # Preenche os campos de auditoria de cadastro e recebimento com os dados do usuário atual
            usuario_cadastro_id=usuario_id,
            usuario_cadastro_nome=usuario_nome,
            usuario_recebimento_id=usuario_id,
            usuario_recebimento_nome=usuario_nome,
            data_operacao_recebimento=timezone.now()
        )
        # ▲▲▲ FIM DA CORREÇÃO ▲▲▲
        
        serializer = ReceitaSerializer(receita, context={'request': request})
        return Response(serializer.data, status=201)
    
    @action(detail=False, methods=['get'])
    def agendamentos_pendentes(self, request):
        clinica_id = request.user.get('clinica_id')
        agendamentos = Agendamento.objects.filter(clinica_id=clinica_id, status='Realizado', valor__gt=0)
        pendentes = []
        for agend in agendamentos:
            if not Receita.objects.filter(agendamento=agend).exists(): pendentes.append(AgendamentoSerializer(agend, context={'request': request}).data)
        return Response({'agendamentos': pendentes, 'total': len(pendentes)})

# ============================================
# VIEWSET DESPESA
# ============================================

class DespesaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Despesas
    """
    permission_classes = [IsAuthenticated, IsSecretariaOrAbove]
    authentication_classes = [JWTAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao', 'fornecedor']
    ordering_fields = ['data_vencimento', 'valor']
    ordering = ['-data_vencimento']
    
    def get_queryset(self):
        clinica_id = self.request.user.get('clinica_id')
        Despesa.atualizar_status_vencidos(clinica_id)
        queryset = Despesa.objects.select_related('categoria').filter(clinica_id=clinica_id)
        status = self.request.query_params.get('status', None)
        categoria_id = self.request.query_params.get('categoria_id', None)
        data_inicial = self.request.query_params.get('data_inicial', None)
        data_final = self.request.query_params.get('data_final', None)
        mes = self.request.query_params.get('mes', None)
        ano = self.request.query_params.get('ano', None)
        if status: queryset = queryset.filter(status=status)
        if categoria_id: queryset = queryset.filter(categoria_id=categoria_id)
        if data_inicial and data_final: queryset = queryset.filter(data_vencimento__range=[data_inicial, data_final])
        elif mes and ano: queryset = queryset.filter(data_vencimento__year=ano, data_vencimento__month=mes)
        elif ano: queryset = queryset.filter(data_vencimento__year=ano)
        return queryset
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listagem"""
        if self.action == 'list':
            return DespesaListSerializer
        return DespesaSerializer

    def perform_create(self, serializer):
        """Injeta dados do usuário na criação de uma despesa."""
        user = self.request.user
        clinica_id = user.get('clinica_id')
        
        status_despesa = serializer.validated_data.get('status')
        
        usuario_cadastro_id = user.get('sub')
        usuario_cadastro_nome = user.get('nome')
        
        usuario_pagamento_id = None
        usuario_pagamento_nome = None
        data_operacao_pagamento = None
        
        if status_despesa == 'paga':
            usuario_pagamento_id = user.get('sub')
            usuario_pagamento_nome = user.get('nome')
            data_operacao_pagamento = timezone.now()

        serializer.save(
            clinica_id=clinica_id,
            usuario_cadastro_id=usuario_cadastro_id,
            usuario_cadastro_nome=usuario_cadastro_nome,
            usuario_pagamento_id=usuario_pagamento_id,
            usuario_pagamento_nome=usuario_pagamento_nome,
            data_operacao_pagamento=data_operacao_pagamento
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Atualizar parcialmente uma despesa (usado para marcar como paga)
        """
        instance = self.get_object()
        
        # Se está marcando como paga, registrar auditoria
        if 'status' in request.data and request.data['status'] == 'paga':
            user = request.user
            instance.status = 'paga'
            instance.data_pagamento = request.data.get('data_pagamento', date.today())
            instance.forma_pagamento = request.data.get('forma_pagamento', instance.forma_pagamento)
            
            # Auditoria
            instance.usuario_pagamento_id = user.get('sub')
            instance.usuario_pagamento_nome = user.get('nome')
            instance.data_operacao_pagamento = timezone.now()
            
            instance.save(update_fields=[
                'status', 
                'data_pagamento', 
                'forma_pagamento',
                'usuario_pagamento_id', 
                'usuario_pagamento_nome',
                'data_operacao_pagamento'
            ])
            
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        # Para outras atualizações, usar o método padrão
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def pagar(self, request, pk=None):
        despesa = self.get_object()
        data_pagamento = request.data.get('data_pagamento', date.today())
        forma_pagamento = request.data.get('forma_pagamento')
        if not forma_pagamento: return Response({'erro': 'Forma de pagamento não fornecida'}, status=400)
        despesa.marcar_como_paga(data_pagamento, forma_pagamento)
        serializer = DespesaSerializer(despesa, context={'request': request})
        return Response(serializer.data)

# ============================================
# VIEW DASHBOARD FINANCEIRO
# ============================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated, IsSecretariaOrAbove])
def dashboard_financeiro(request):
    """
    Dashboard com estatísticas financeiras, incluindo fechamento de caixa por forma de pagamento.
    GET /api/faturamento/dashboard/
    """
    clinica_id = request.user.get('clinica_id')
    
    Receita.atualizar_status_vencidos(clinica_id)
    Despesa.atualizar_status_vencidos(clinica_id)
    
    # --- INÍCIO DA LÓGICA DE FILTRO ATUALIZADA ---
    data_inicial_str = request.query_params.get('data_inicial')
    data_final_str = request.query_params.get('data_final')
    mes_str = request.query_params.get('mes')
    ano_str = request.query_params.get('ano')

    filtros_vencimento = {}
    filtros_efetivados_receita = {'status': 'recebida'}
    filtros_efetivados_despesa = {'status': 'paga'}

    if data_inicial_str and data_final_str:
        filtros_vencimento['data_vencimento__range'] = [data_inicial_str, data_final_str]
        filtros_efetivados_receita['data_recebimento__range'] = [data_inicial_str, data_final_str]
        filtros_efetivados_despesa['data_pagamento__range'] = [data_inicial_str, data_final_str]
    elif mes_str and ano_str:
        filtros_vencimento['data_vencimento__month'] = int(mes_str)
        filtros_vencimento['data_vencimento__year'] = int(ano_str)
        filtros_efetivados_receita['data_recebimento__month'] = int(mes_str)
        filtros_efetivados_receita['data_recebimento__year'] = int(ano_str)
        filtros_efetivados_despesa['data_pagamento__month'] = int(mes_str)
        filtros_efetivados_despesa['data_pagamento__year'] = int(ano_str)
    else:
        # Padrão: Mês atual se nenhum filtro for fornecido
        hoje = date.today()
        filtros_vencimento['data_vencimento__month'] = hoje.month
        filtros_vencimento['data_vencimento__year'] = hoje.year
        filtros_efetivados_receita['data_recebimento__month'] = hoje.month
        filtros_efetivados_receita['data_recebimento__year'] = hoje.year
        filtros_efetivados_despesa['data_pagamento__month'] = hoje.month
        filtros_efetivados_despesa['data_pagamento__year'] = hoje.year
    # --- FIM DA LÓGICA DE FILTRO ATUALIZADA ---

    receitas_periodo = Receita.objects.filter(clinica_id=clinica_id, **filtros_vencimento)
    despesas_periodo = Despesa.objects.filter(clinica_id=clinica_id, **filtros_vencimento)

    receitas_recebidas = Receita.objects.filter(clinica_id=clinica_id, **filtros_efetivados_receita).aggregate(total=Sum('valor'))['total'] or 0
    despesas_pagas = Despesa.objects.filter(clinica_id=clinica_id, **filtros_efetivados_despesa).aggregate(total=Sum('valor'))['total'] or 0
    
    receitas_a_receber = receitas_periodo.filter(status='a_receber').aggregate(total=Sum('valor'))['total'] or 0
    receitas_vencidas = receitas_periodo.filter(status='vencida').aggregate(total=Sum('valor'))['total'] or 0
    despesas_a_pagar = despesas_periodo.filter(status='a_pagar').aggregate(total=Sum('valor'))['total'] or 0
    despesas_vencidas = despesas_periodo.filter(status='vencida').aggregate(total=Sum('valor'))['total'] or 0
    
    lucro_liquido = float(receitas_recebidas) - float(despesas_pagas)
    
    total_geral_receitas = (receitas_recebidas or 0) + (receitas_a_receber or 0) + (receitas_vencidas or 0)
    total_geral_despesas = (despesas_pagas or 0) + (despesas_a_pagar or 0) + (despesas_vencidas or 0)
    previsao_mensal = float(total_geral_receitas) - float(total_geral_despesas)
    
    receitas_efetivadas_qs = Receita.objects.filter(clinica_id=clinica_id, **filtros_efetivados_receita)
    despesas_efetivadas_qs = Despesa.objects.filter(clinica_id=clinica_id, **filtros_efetivados_despesa)

    receitas_por_metodo = receitas_efetivadas_qs.values('forma_pagamento').annotate(total=Sum('valor'))
    despesas_por_metodo = despesas_efetivadas_qs.values('forma_pagamento').annotate(total=Sum('valor'))
    
    receitas_map = {item['forma_pagamento']: item['total'] for item in receitas_por_metodo if item['forma_pagamento']}
    despesas_map = {item['forma_pagamento']: item['total'] for item in despesas_por_metodo if item['forma_pagamento']}
    
    formas_pagamento = Receita.FORMA_PAGAMENTO_CHOICES
    fechamento_caixa = []
    total_saldo_caixa = 0

    todos_metodos = set(list(receitas_map.keys()) + list(despesas_map.keys()))
    metodos_display_map = {key: display for key, display in formas_pagamento}

    for metodo_key in sorted(list(todos_metodos)):
        receita = receitas_map.get(metodo_key, Decimal('0.0'))
        despesa = despesas_map.get(metodo_key, Decimal('0.0'))
        saldo = receita - despesa
        total_saldo_caixa += saldo
        
        fechamento_caixa.append({
            'metodo': metodos_display_map.get(metodo_key, metodo_key),
            'receitas': float(receita),
            'despesas': float(despesa),
            'saldo': float(saldo)
        })
    
    return Response({
        'receitas': {
            'recebidas': float(receitas_recebidas),
            'a_receber': float(receitas_a_receber),
            'vencidas': float(receitas_vencidas),
        },
        'despesas': {
            'pagas': float(despesas_pagas),
            'a_pagar': float(despesas_a_pagar),
            'vencidas': float(despesas_vencidas),
        },
        'lucro_liquido': lucro_liquido,
        'previsao_mensal': previsao_mensal,
        'fechamento_caixa': fechamento_caixa,
        'total_saldo_caixa': float(total_saldo_caixa)
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
    
    # --- INÍCIO DA CORREÇÃO ---
    # Acessando os dados do usuário diretamente do objeto 'user',
    # que já é o wrapper do payload do token.
    clinica_id = user.get('clinica_id')
    funcao = user.get('funcao')
    # --- FIM DA CORREÇÃO ---
    
    if funcao == 'super_admin':
        clinica_id_param = request.query_params.get('clinica_id')
        if clinica_id_param:
            clinica_id = int(clinica_id_param)
    
    if not clinica_id:
        return Response({'erro': 'Usuário sem clínica vinculada'}, status=400)
    
    try:
        clinica = Clinica.objects.get(id=clinica_id)
    except Clinica.DoesNotExist:
        return Response({'erro': 'Clínica não encontrada'}, status=404)
    
    # ============================================
    # 1. DADOS CADASTRAIS DA CLÍNICA
    # ============================================
    
    dados_clinica = {
        'id': clinica.id, 'nome': clinica.nome, 'cnpj': clinica.cnpj, 'status': clinica.status,
        'status_display': clinica.get_status_display(),
        'contato': {'telefone': clinica.telefone, 'email': clinica.email},
        'endereco': {
            'logradouro': clinica.logradouro, 'numero': clinica.numero, 'bairro': clinica.bairro,
            'cidade': clinica.cidade, 'estado': clinica.estado, 'cep': clinica.cep,
            'endereco_completo': f"{clinica.logradouro}, {clinica.numero} - {clinica.bairro}, {clinica.cidade}/{clinica.estado} - CEP: {clinica.cep}"
        },
        'responsavel': {
            'nome': clinica.responsavel_nome, 'cpf': clinica.responsavel_cpf,
            'telefone': clinica.responsavel_telefone, 'email': clinica.responsavel_email,
        },
        'datas': {
            'cadastro': clinica.data_cadastro, 'atualizacao': clinica.data_atualizacao,
            'dias_cadastrado': (timezone.now() - clinica.data_cadastro).days
        }
    }
    
    # ============================================
    # 2. USUÁRIOS DA CLÍNICA
    # ============================================
    
    usuarios = Usuario.objects.filter(clinica_id=clinica_id)
    usuarios_lista = [{'id': u.id, 'nome_completo': u.nome_completo, 'email': u.email, 'cpf': u.cpf, 'telefone': u.telefone_celular, 'funcao': u.funcao, 'funcao_display': u.get_funcao_display(), 'status': u.status, 'status_display': u.get_status_display(), 'crm': u.crm, 'especialidade': u.especialidade, 'last_login': u.last_login, 'data_cadastro': u.data_cadastro} for u in usuarios]
    usuarios_por_funcao = {'admin': usuarios.filter(funcao='admin').count(), 'medico': usuarios.filter(funcao='medico').count(), 'secretaria': usuarios.filter(funcao='secretaria').count()}
    usuarios_por_status = {'ativo': usuarios.filter(status='ativo').count(), 'inativo': usuarios.filter(status='inativo').count(), 'alerta': usuarios.filter(status='alerta').count()}
    
    # ============================================
    # 3. ESTATÍSTICAS GERAIS DO SISTEMA
    # ============================================
    
    total_pacientes = Paciente.objects.filter(clinica_id=clinica_id, ativo=True).count()
    pacientes_por_convenio = Paciente.objects.filter(clinica_id=clinica_id, ativo=True).values('convenio').annotate(total=Count('id')).order_by('-total')[:5]
    
    hoje = date.today()
    ano_atual = hoje.year
    mes_atual = hoje.month
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    
    def calcular_estatisticas_detalhadas(start_date, end_date):
        # Agendamentos
        ag_qs = Agendamento.objects.filter(clinica_id=clinica_id, data__range=[start_date, end_date])
        ag_stats = ag_qs.values('status').annotate(total=Count('id'))
        
        stats_dict = {item['status']: item['total'] for item in ag_stats}
        
        status_choices = Agendamento.STATUS_CHOICES
        detalhes_completos = [{'status': choice[0], 'total': stats_dict.get(choice[0], 0)} for choice in status_choices]
        
        # Documentos
        consultas_periodo = Consulta.objects.filter(clinica_id=clinica_id, data_atualizacao__date__range=[start_date, end_date])
        docs_gerados = 0
        docs_editados = 0
        for c in consultas_periodo:
            if c.atestado_medico: docs_gerados += 1
            if c.anamnese_documento: docs_gerados += 1
            if c.evolucao_medica: docs_gerados += 1
            if c.prescricao_documento: docs_gerados += 1
            if c.relatorio_medico: docs_gerados += 1
            
            if c.documentos_gerados:
                docs_editados += sum(1 for doc in c.documentos_gerados if doc.get('editado'))

        # Exames
        exames_gerados = Exame.objects.filter(clinica_id=clinica_id, data_cadastro__date__range=[start_date, end_date]).count()
        exames_editados = Exame.objects.filter(clinica_id=clinica_id, revisado_por_medico=True, data_revisao__date__range=[start_date, end_date]).count()

        return {
            'agendamentos': {
                'total': ag_qs.count(),
                'detalhes': detalhes_completos
            },
            'documentos': {
                'gerados': docs_gerados,
                'editados': docs_editados
            },
            'exames': {
                'gerados': exames_gerados,
                'editados': exames_editados
            }
        }

    estatisticas_detalhadas = {
        'diaria': calcular_estatisticas_detalhadas(hoje, hoje),
        'semanal': calcular_estatisticas_detalhadas(inicio_semana, inicio_semana + timedelta(days=6)),
        'mensal': calcular_estatisticas_detalhadas(date(ano_atual, mes_atual, 1), (date(ano_atual, mes_atual, 1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)),
        'anual': calcular_estatisticas_detalhadas(date(ano_atual, 1, 1), date(ano_atual, 12, 31))
    }

    total_consultas = Consulta.objects.filter(clinica_id=clinica_id).count()
    total_exames = Exame.objects.filter(clinica_id=clinica_id).count()
    
    # ============================================
    # 4. DADOS FINANCEIROS, MÉTRICAS E ALERTAS (sem alteração)
    # ============================================
    Receita.atualizar_status_vencidos(clinica_id)
    Despesa.atualizar_status_vencidos(clinica_id)
    receitas_mes = Receita.objects.filter(clinica_id=clinica_id, data_vencimento__year=ano_atual, data_vencimento__month=mes_atual)
    receitas_recebidas_mes = receitas_mes.filter(status='recebida').aggregate(total=Sum('valor'))['total'] or 0
    despesas_mes = Despesa.objects.filter(clinica_id=clinica_id, data_vencimento__year=ano_atual, data_vencimento__month=mes_atual)
    despesas_pagas_mes = despesas_mes.filter(status='paga').aggregate(total=Sum('valor'))['total'] or 0
    lucro_liquido_mes = float(receitas_recebidas_mes) - float(despesas_pagas_mes)
    total_transcricoes = Transcricao.objects.filter(clinica_id=clinica_id).count()
    
    # ============================================
    # MONTAR RESPOSTA COMPLETA
    # ============================================
    
    return Response({
        'clinica': dados_clinica,
        'usuarios': {'lista': usuarios_lista, 'total': usuarios.count(), 'ativos': usuarios.filter(status='ativo').count(), 'por_funcao': usuarios_por_funcao, 'por_status': usuarios_por_status},
        'estatisticas_gerais': {
            'pacientes': {'total': total_pacientes, 'top_convenios': list(pacientes_por_convenio)},
            'consultas': {'total': total_consultas},
            'exames': {'total': total_exames},
            'estatisticas_detalhadas': estatisticas_detalhadas,
        },
        'financeiro': {'mes_atual': {'lucro_liquido': lucro_liquido_mes}},
        'metricas_uso': {'transcricoes': {'total': total_transcricoes}},
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
    
    # 1. TOTAL DE PACIENTES CADASTRADOS
    total_pacientes = Paciente.objects.filter(
        clinica_id=clinica_id,
        ativo=True
    ).count()
    
    # 2. AGENDAMENTOS DE HOJE
    # --- ALTERAÇÃO AQUI: Adicionado .select_related('paciente', 'medico_responsavel') para otimização ---
    agendamentos_hoje = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data=hoje
    ).select_related('paciente', 'medico_responsavel').order_by('hora')
    
    total_agendamentos_hoje = agendamentos_hoje.count()
    
    # 3. PACIENTES PENDENTES DE HOJE
    agendamentos_pendentes_hoje = agendamentos_hoje.filter(
        status__in=['Agendado', 'Confirmado']
    )
    total_pendentes_hoje = agendamentos_pendentes_hoje.count()
    
    # 4. AGENDAMENTOS FUTUROS
    total_agendamentos_futuros = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gt=hoje,
        status__in=['Agendado', 'Confirmado']
    ).count()
    
    proximos_7_dias = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gt=hoje,
        data__lte=hoje + timedelta(days=7),
        status__in=['Agendado', 'Confirmado']
    ).count()
    
    proximos_30_dias = Agendamento.objects.filter(
        clinica_id=clinica_id,
        data__gt=hoje,
        data__lte=hoje + timedelta(days=30),
        status__in=['Agendado', 'Confirmado']
    ).count()
    
    # 5. LISTA DE ESPERA DE HOJE (HISTÓRICO)
    lista_espera_hoje = []
    
    for agendamento in agendamentos_hoje:
        tempo_espera_minutos = None
        status_atendimento = agendamento.status
        
        hora_agendamento = timezone.make_aware(
            datetime.combine(hoje, agendamento.hora)
        )
        
        if agora > hora_agendamento and status_atendimento in ['Agendado', 'Confirmado']:
            tempo_espera_segundos = (agora - hora_agendamento).total_seconds()
            tempo_espera_minutos = int(tempo_espera_segundos / 60)
        
        lista_espera_hoje.append({
            'id': agendamento.id,
            'paciente_id': agendamento.paciente.id,
            'paciente_nome': agendamento.paciente_nome,
            'paciente_cpf': agendamento.paciente_cpf,
            'paciente_sexo': agendamento.paciente.get_sexo_display(),
            'hora': agendamento.hora.strftime('%H:%M'),
            'servico': agendamento.servico,
            'tipo': agendamento.tipo,
            'status': agendamento.status,
            'status_display': agendamento.get_status_display(),
            'convenio': agendamento.convenio,
            'tempo_espera_minutos': tempo_espera_minutos,
            'observacoes': agendamento.observacoes,
            # --- NOVO CAMPO ADICIONADO ABAIXO ---
            'medico_responsavel_nome': agendamento.medico_responsavel.nome_completo if agendamento.medico_responsavel else None
        })
    
    # 6. CONSULTAS PENDENTES DE AÇÃO
    consultas_pendentes = Consulta.objects.filter(
        clinica_id=clinica_id,
        status__in=['agendada', 'confirmada', 'em_atendimento']
    ).select_related('paciente').order_by('data_consulta')[:20]
    
    consultas_pendentes_lista = []
    
    for consulta in consultas_pendentes:
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
    
    # 7. ESTATÍSTICAS RÁPIDAS ADICIONAIS
    atendimentos_realizados_hoje = agendamentos_hoje.filter(
        status='Realizado'
    ).count()
    
    faltas_hoje = agendamentos_hoje.filter(
        status='Faltou'
    ).count()
    
    cancelamentos_hoje = agendamentos_hoje.filter(
        status='Cancelado'
    ).count()
    
    if total_agendamentos_hoje > 0:
        taxa_comparecimento = (atendimentos_realizados_hoje / total_agendamentos_hoje) * 100
    else:
        taxa_comparecimento = 0
    
    receitas_pendentes = Receita.objects.filter(
        clinica_id=clinica_id,
        status__in=['a_receber', 'vencida'],
        data_vencimento__lte=hoje
    ).count()
    
    despesas_pendentes = Despesa.objects.filter(
        clinica_id=clinica_id,
        status__in=['a_pagar', 'vencida'],
        data_vencimento__lte=hoje
    ).count()
    
    exames_pendentes = Exame.objects.filter(
        clinica_id=clinica_id,
        status__in=['solicitado', 'agendado', 'realizado']
    ).count()
    
    # 8. RESUMO DA SEMANA
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
    
    # 9. PRÓXIMO AGENDAMENTO
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
    
    # 10. MONTAR RESPOSTA COMPLETA
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
@authentication_classes([]) # <<< ESTA LINHA É A CORREÇÃO. ELA GARANTE QUE A ROTA SEJA PÚBLICA.
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
router.register(r'medicos', MedicoViewSet, basename='medico')
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
@authentication_classes([JWTAuthentication])
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
            'mensagem': 'Usuário sem clínica vinculada ou token inválido.'
        }, status=400)
    
    try:
        popular_categorias_padrao(clinica_id)
        return Response({
            'sucesso': True,
            'mensagem': 'Categorias padrão de receitas e despesas foram criadas com sucesso para a sua clínica!'
        })
    except Exception as e:
        return Response({
            'sucesso': False,
            'mensagem': str(e)
        }, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminOrMedico])
def transcrever_audio_view(request):
    """
    Endpoint para transcrição de áudio geral.
    Recebe: {"audio_base64": "...", "audio_formato": "..."}
    Retorna: {"texto": "..."}
    """
    audio_base64 = request.data.get('audio_base64')
    audio_formato = request.data.get('audio_formato', 'webm')

    if not audio_base64:
        return Response({'erro': 'Nenhum áudio fornecido.'}, status=status.HTTP_400_BAD_REQUEST)

    resultado = transcrever_audio_geral_com_gemini(audio_base64, audio_formato)

    if resultado['sucesso']:
        return Response({'texto': resultado['texto']}, status=status.HTTP_200_OK)
    else:
        return Response({'erro': resultado['erro']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def auditoria_recente_view(request):
    """
    Retorna um log de eventos recentes para auditoria (Exames e Documentos).
    GET /api/auditoria/recente/
    """
    from django.db.models import Q
    from datetime import datetime
    from django.utils import timezone

    clinica_id = request.user.get('clinica_id')
    if not clinica_id:
        return Response({"erro": "Usuário sem clínica vinculada."}, status=400)

    limite_eventos = 40  # Aumentado para garantir captura de ambos os tipos
    eventos = []

    def to_aware_datetime(ts):
        if ts is None: return None
        if isinstance(ts, str):
            try:
                ts_str = ts.split('+')[0].split('Z')[0]
                dt_obj = datetime.fromisoformat(ts_str)
                return timezone.make_aware(dt_obj)
            except (ValueError, TypeError): return None
        if timezone.is_naive(ts): return timezone.make_aware(ts)
        return ts

    # 1. Exames Gerados (criados)
    exames_criados = Exame.objects.filter(
        clinica_id=clinica_id
    ).select_related('paciente').order_by('-data_cadastro')[:limite_eventos]
    for exame in exames_criados:
        ts = to_aware_datetime(exame.data_cadastro)
        if ts:
            # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
            # Prioriza o tipo identificado pela IA e usa o tipo manual como fallback.
            tipo_exame_display = exame.tipo_exame_identificado_ia or exame.get_tipo_exame_display()
            # ▲▲▲ FIM DA CORREÇÃO ▲▲▲

            eventos.append({
                'timestamp': ts, 'tipo_evento': 'Exame Gerado',
                'paciente_nome': exame.paciente.nome_completo if exame.paciente else 'N/A',
                'usuario_nome': exame.medico_solicitante or 'Sistema',
                'detalhes': f"Tipo: {tipo_exame_display}"
            })

    # 2. Exames Editados (revisados)
    exames_revisados = Exame.objects.filter(
        clinica_id=clinica_id, revisado_por_medico=True, data_revisao__isnull=False
    ).select_related('paciente').order_by('-data_revisao')[:limite_eventos]
    for exame in exames_revisados:
        ts = to_aware_datetime(exame.data_revisao)
        if ts:
            # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
            tipo_exame_display = exame.tipo_exame_identificado_ia or exame.get_tipo_exame_display()
            # ▲▲▲ FIM DA CORREÇÃO ▲▲▲

            eventos.append({
                'timestamp': ts, 'tipo_evento': 'Exame Editado',
                'paciente_nome': exame.paciente.nome_completo if exame.paciente else 'N/A',
                'usuario_nome': exame.medico_revisor_nome or 'Não identificado',
                'detalhes': f"Revisão do Laudo de {tipo_exame_display}"
            })

    # 3. Documentos Gerados/Editados (Lógica Simplificada e Corrigida)
    consultas_com_docs = Consulta.objects.filter(
        clinica_id=clinica_id
    ).select_related('paciente').order_by('-data_atualizacao')[:limite_eventos]
    
    doc_fields = {
        'atestado_medico': 'Atestado', 'anamnese_documento': 'Anamnese',
        'evolucao_medica': 'Evolução', 'prescricao_documento': 'Prescrição',
        'relatorio_medico': 'Relatório'
    }

    for consulta in consultas_com_docs:
        # Verifica se há algum documento nos campos de texto
        for field_name, doc_type in doc_fields.items():
            if getattr(consulta, field_name):
                ts = to_aware_datetime(consulta.data_atualizacao)
                if ts:
                    # Verifica se o documento foi editado (olhando o JSON)
                    editado = False
                    if isinstance(consulta.documentos_gerados, list):
                        for doc_json in consulta.documentos_gerados:
                            if doc_json.get('tipo') == doc_type.lower() and doc_json.get('editado'):
                                editado = True
                                break
                    
                    eventos.append({
                        'timestamp': ts,
                        'tipo_evento': 'Documento Editado' if editado else 'Documento Gerado',
                        'paciente_nome': consulta.paciente.nome_completo if consulta.paciente else 'N/A',
                        'usuario_nome': consulta.medico_responsavel or 'Sistema',
                        'detalhes': f"Tipo: {doc_type}"
                    })

    # Ordenar todos os eventos
    eventos_ordenados = sorted(eventos, key=lambda x: x['timestamp'], reverse=True)

    # Remover duplicatas e formatar
    eventos_finais = []
    vistos = set()
    limite_final = 20
    for evento in eventos_ordenados:
        if len(eventos_finais) >= limite_final * 2: # Limite para processamento
            break
        chave = (evento['timestamp'].strftime('%Y-%m-%d %H:%M'), evento['tipo_evento'], evento['paciente_nome'], evento['detalhes'])
        if chave not in vistos:
            eventos_finais.append({
                'data': evento['timestamp'].strftime('%d/%m/%Y'),
                'hora': evento['timestamp'].strftime('%H:%M'),
                'tipo_evento': evento['tipo_evento'],
                'paciente_nome': evento['paciente_nome'],
                'usuario_nome': evento['usuario_nome'],
                'detalhes': evento['detalhes']
            })
            vistos.add(chave)

    return Response(eventos_finais)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def auditoria_financeira_view(request):
    """
    Retorna auditoria financeira com receitas recebidas e despesas pagas
    GET /api/auditoria/financeira/?mes=10&ano=2025
    """
    try:
        # A importação precisa estar aqui para a função get_sort_key funcionar
        from datetime import datetime

        user = request.user
        clinica_id = user.get('clinica_id')
        
        if not clinica_id:
            return Response({'erro': 'Clínica não identificada'}, status=400)
        
        # Parâmetros opcionais de filtro
        mes = request.GET.get('mes')
        ano = request.GET.get('ano')
        
        # Query base para receitas recebidas
        receitas_query = Receita.objects.filter(
            clinica_id=clinica_id,
            status='recebida'
        ).select_related('categoria', 'paciente')
        
        # Query base para despesas pagas
        despesas_query = Despesa.objects.filter(
            clinica_id=clinica_id,
            status='paga'
        ).select_related('categoria')
        
        # Aplicar filtros se fornecidos
        if mes and ano:
            from django.db.models import Q
            receitas_query = receitas_query.filter(
                data_recebimento__month=int(mes),
                data_recebimento__year=int(ano)
            )
            despesas_query = despesas_query.filter(
                data_pagamento__month=int(mes),
                data_pagamento__year=int(ano)
            )
        
        # Ordenar por data
        receitas = receitas_query.order_by('-data_recebimento')[:100]
        despesas = despesas_query.order_by('-data_pagamento')[:100]
        
        # Montar lista de auditoria
        auditoria = []
        
        # Processar receitas
        for r in receitas:
            auditoria.append({
                'id': r.id,
                'tipo': 'receita',
                'tipo_display': 'Receita',
                'descricao': r.descricao,
                'categoria': r.categoria.nome if r.categoria else 'Sem categoria',
                'categoria_cor': r.categoria.cor if r.categoria else '#4CAF50',
                'valor': float(r.valor),
                'data_operacao': r.data_recebimento.strftime('%d/%m/%Y') if r.data_recebimento else 'N/A',
                'data_hora_operacao': r.data_operacao_recebimento.strftime('%d/%m/%Y às %H:%M') if r.data_operacao_recebimento else 'Não registrado',
                'forma_pagamento': r.forma_pagamento or 'Não informado',
                'usuario_id': r.usuario_recebimento_id,
                'usuario_nome': r.usuario_recebimento_nome or 'Não identificado',
                'paciente': r.paciente.nome_completo if r.paciente else 'N/A',
                'observacoes': r.observacoes or '',
            })
        
        # Processar despesas
        for d in despesas:
            auditoria.append({
                'id': d.id,
                'tipo': 'despesa',
                'tipo_display': 'Despesa',
                'descricao': d.descricao,
                'categoria': d.categoria.nome if d.categoria else 'Sem categoria',
                'categoria_cor': d.categoria.cor if d.categoria else '#F44336',
                'valor': -float(d.valor),
                'data_operacao': d.data_pagamento.strftime('%d/%m/%Y') if d.data_pagamento else 'N/A',
                'data_hora_operacao': d.data_operacao_pagamento.strftime('%d/%m/%Y às %H:%M') if d.data_operacao_pagamento else 'Não registrado',
                'forma_pagamento': d.forma_pagamento or 'Não informado',
                'usuario_id': d.usuario_pagamento_id,
                'usuario_nome': d.usuario_pagamento_nome or 'Não identificado',
                'fornecedor': d.fornecedor or 'N/A',
                'observacoes': d.observacoes or '',
            })
        
        # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
        # A função agora sempre retorna um objeto datetime, evitando o TypeError.
        def get_sort_key(item):
            data_str = item['data_hora_operacao']
            if data_str == 'Não registrado':
                # Retorna um objeto datetime real para comparação correta
                return datetime.min
            try:
                # Converte a string de data para um objeto datetime
                return datetime.strptime(data_str, '%d/%m/%Y às %H:%M')
            except (ValueError, TypeError):
                # Fallback para qualquer outro caso inesperado
                return datetime.min
        # ▲▲▲ FIM DA CORREÇÃO ▲▲▲

        auditoria_ordenada = sorted(auditoria, key=get_sort_key, reverse=True)
        
        # Calcular totais
        total_receitas = sum(item['valor'] for item in auditoria if item['tipo'] == 'receita')
        total_despesas = abs(sum(item['valor'] for item in auditoria if item['tipo'] == 'despesa'))
        saldo = total_receitas - total_despesas
        
        return Response({
            'auditoria': auditoria_ordenada,
            'total_itens': len(auditoria_ordenada),
            'resumo': {
                'total_receitas': total_receitas,
                'total_despesas': total_despesas,
                'saldo': saldo,
            }
        })
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERRO em auditoria_financeira_view:")
        print(f"Erro: {str(e)}")
        traceback.print_exc()
        return Response({'erro': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def auditoria_faturamento_view(request):
    """
    Retorna histórico de receitas recebidas e despesas pagas para auditoria
    GET /api/faturamento/auditoria/
    """
    try:
        user = request.user
        clinica_id = user.get('clinica_id')
        
        if not clinica_id:
            return Response({'erro': 'Clínica não identificada'}, status=400)
        
        # Buscar receitas recebidas
        receitas = Receita.objects.filter(
            clinica_id=clinica_id,
            status='recebida'
        ).select_related('categoria', 'paciente').order_by('-data_recebimento')[:100]
        
        # Buscar despesas pagas
        despesas = Despesa.objects.filter(
            clinica_id=clinica_id,
            status='paga'
        ).select_related('categoria').order_by('-data_pagamento')[:100]
        
        # Montar lista combinada
        historico = []
        
        for receita in receitas:
            historico.append({
                'id': receita.id,
                'tipo': 'receita',
                'tipo_display': 'Receita',
                'descricao': receita.descricao,
                'categoria': receita.categoria.nome if receita.categoria else 'Sem categoria',
                'valor': float(receita.valor),
                'data_operacao': receita.data_recebimento.strftime('%d/%m/%Y') if receita.data_recebimento else '',
                'data_hora_operacao': receita.data_operacao_recebimento.strftime('%d/%m/%Y %H:%M') if receita.data_operacao_recebimento else 'Não registrado',
                'forma_pagamento': receita.forma_pagamento or 'Não informado',
                'usuario_id': receita.usuario_recebimento_id,
                'usuario_nome': receita.usuario_recebimento_nome or 'Não registrado',
                'paciente': receita.paciente.nome_completo if receita.paciente else 'N/A',
            })
        
        for despesa in despesas:
            historico.append({
                'id': despesa.id,
                'tipo': 'despesa',
                'tipo_display': 'Despesa',
                'descricao': despesa.descricao,
                'categoria': despesa.categoria.nome if despesa.categoria else 'Sem categoria',
                'valor': float(despesa.valor),
                'data_operacao': despesa.data_pagamento.strftime('%d/%m/%Y') if despesa.data_pagamento else '',
                'data_hora_operacao': despesa.data_operacao_pagamento.strftime('%d/%m/%Y %H:%M') if despesa.data_operacao_pagamento else 'Não registrado',
                'forma_pagamento': despesa.forma_pagamento or 'Não informado',
                'usuario_id': despesa.usuario_pagamento_id,
                'usuario_nome': despesa.usuario_pagamento_nome or 'Não registrado',
                'fornecedor': despesa.fornecedor or 'N/A',
            })
        
        # Ordenar por data de operação (mais recentes primeiro)
        historico_ordenado = sorted(
            historico,
            key=lambda x: x['data_hora_operacao'] if x['data_hora_operacao'] != 'Não registrado' else '',
            reverse=True
        )
        
        return Response({
            'historico': historico_ordenado,
            'total_itens': len(historico_ordenado)
        })
        
    except Exception as e:
        return Response({'erro': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def definir_nova_senha_view(request):
    """
    Endpoint para o usuário definir sua nova senha.
    Requer e-mail, senha temporária e a nova senha.
    """
    email = request.data.get('email', '').lower()
    senha_temporaria = request.data.get('senha_temporaria')
    nova_senha = request.data.get('nova_senha')
    confirmacao_nova_senha = request.data.get('confirmacao_nova_senha')

    if not all([email, senha_temporaria, nova_senha, confirmacao_nova_senha]):
        return Response({'mensagem': 'Todos os campos são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

    if nova_senha != confirmacao_nova_senha:
        return Response({'mensagem': 'A nova senha e a confirmação não correspondem.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(nova_senha) < 8:
        return Response({'mensagem': 'A nova senha deve ter pelo menos 8 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return Response({'mensagem': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    # Verifica se a senha temporária fornecida está correta
    if not usuario.check_password(senha_temporaria):
        return Response({'mensagem': 'A senha temporária está incorreta.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Verifica se o usuário realmente precisa alterar a senha
    if not usuario.precisa_alterar_senha:
        return Response({'mensagem': 'Este usuário não precisa ou já alterou sua senha.'}, status=status.HTTP_400_BAD_REQUEST)

    # Define a nova senha e atualiza a flag
    usuario.set_password(nova_senha)
    usuario.precisa_alterar_senha = False
    usuario.save(update_fields=['password', 'precisa_alterar_senha'])

    return Response({'mensagem': 'Senha alterada com sucesso! Você já pode fazer o login com sua nova senha.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def esqueci_senha_view(request):
    """
    Endpoint para o fluxo de "esqueci minha senha".
    Gera uma nova senha temporária e a envia por e-mail.
    """
    email = request.data.get('email', '').lower()

    if not email:
        return Response({'mensagem': 'O campo de e-mail é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return Response({'mensagem': 'Se um usuário com este e-mail existir, um link de recuperação foi enviado.'}, status=status.HTTP_200_OK)
    
    alfabeto = string.ascii_letters + string.digits
    nova_senha_temporaria = ''.join(secrets.choice(alfabeto) for i in range(10))

    usuario.set_password(nova_senha_temporaria)
    usuario.precisa_alterar_senha = True
    usuario.save(update_fields=['password', 'precisa_alterar_senha'])

    # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
    # Agora passamos o contexto 'recuperacao' para a função de envio de e-mail.
    _enviar_email_nova_senha(usuario.email, nova_senha_temporaria, contexto="recuperacao")
    # ▲▲▲ FIM DA CORREÇÃO ▲▲▲

    return Response({'mensagem': 'Se um usuário com este e-mail existir, uma nova senha temporária foi enviada.'}, status=status.HTTP_200_OK)

def _gerar_dados_backup(clinica_id):
    """Função auxiliar para gerar o dicionário de dados do backup."""
    pacientes = Paciente.objects.filter(clinica_id=clinica_id)
    agendamentos = Agendamento.objects.filter(clinica_id=clinica_id)
    consultas = Consulta.objects.filter(clinica_id=clinica_id)
    exames = Exame.objects.filter(clinica_id=clinica_id)
    receitas = Receita.objects.filter(clinica_id=clinica_id)
    despesas = Despesa.objects.filter(clinica_id=clinica_id)
    cat_receitas = CategoriaReceita.objects.filter(clinica_id=clinica_id)
    cat_despesas = CategoriaDespesa.objects.filter(clinica_id=clinica_id)

    return {
        'version': '1.0',
        'timestamp': timezone.now().isoformat(),
        'clinica_id': clinica_id,
        'dados': {
            'categorias_receita': CategoriaReceitaSerializer(cat_receitas, many=True).data,
            'categorias_despesa': CategoriaDespesaSerializer(cat_despesas, many=True).data,
            'pacientes': PacienteSerializer(pacientes, many=True).data,
            'agendamentos': AgendamentoSerializer(agendamentos, many=True).data,
            'consultas': ConsultaSerializer(consultas, many=True).data,
            'exames': ExameSerializer(exames, many=True).data,
            'receitas': ReceitaSerializer(receitas, many=True).data,
            'despesas': DespesaSerializer(despesas, many=True).data,
        }
    }

def executar_backup_automatico():
    """Tarefa agendada para rodar backups automáticos."""
    print(f"[{timezone.now()}]  scheduler: Iniciando verificação de backups automáticos...")
    hoje = timezone.now().date()
    
    # Backup Diário
    clinicas_diario = Clinica.objects.filter(backup_frequencia='diario', status='ativo')
    for clinica in clinicas_diario:
        if not clinica.backup_ultimo_realizado or clinica.backup_ultimo_realizado.date() < hoje:
            print(f"  -> Executando backup DIÁRIO para clínica {clinica.id} - {clinica.nome}")
            _enviar_backup_por_email(clinica)

    # Backup Semanal (ex: rodar todo domingo)
    if hoje.weekday() == 6: # 6 = Domingo
        clinicas_semanal = Clinica.objects.filter(backup_frequencia='semanal', status='ativo')
        for clinica in clinicas_semanal:
             if not clinica.backup_ultimo_realizado or (hoje - clinica.backup_ultimo_realizado.date()).days >= 7:
                print(f"  -> Executando backup SEMANAL para clínica {clinica.id} - {clinica.nome}")
                _enviar_backup_por_email(clinica)

    # Backup Mensal (ex: rodar todo dia 1º)
    if hoje.day == 1:
        clinicas_mensal = Clinica.objects.filter(backup_frequencia='mensal', status='ativo')
        for clinica in clinicas_mensal:
            if not clinica.backup_ultimo_realizado or clinica.backup_ultimo_realizado.month != hoje.month:
                print(f"  -> Executando backup MENSAL para clínica {clinica.id} - {clinica.nome}")
                _enviar_backup_por_email(clinica)


def _enviar_backup_por_email(clinica):
    """Gera o backup, salva localmente e envia por e-mail."""
    if not clinica.backup_email_notificacao:
        print(f"    ! AVISO: Clínica {clinica.id} não tem e-mail de notificação configurado. Backup por e-mail abortado.")
        # Mesmo sem e-mail, vamos tentar salvar o backup local se a frequência não for manual
        if clinica.backup_frequencia != 'manual':
             pass # Continua para o salvamento local
        else:
             return

    try:
        backup_data = _gerar_dados_backup(clinica.id)
        backup_content = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        # ▼▼▼ NOVA LÓGICA DE SALVAMENTO LOCAL ADICIONADA AQUI ▼▼▼
        # Garante que o diretório de backups exista
        backup_dir = 'intellimed_backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Cria um nome de arquivo padronizado com timestamp completo
        filename = f"backup_intellimed_clinica_{clinica.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(backup_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            print(f"    ✓ Backup local da clínica {clinica.id} salvo em: {filepath}")
        except Exception as e:
            print(f"    ✗ ERRO CRÍTICO ao salvar backup local para clínica {clinica.id}: {e}")
            # Não continua se não conseguir salvar o arquivo
            return
        # ▲▲▲ FIM DA NOVA LÓGICA ▲▲▲

        # Enviar por e-mail (se houver e-mail configurado)
        if clinica.backup_email_notificacao:
            send_mail(
                subject=f'IntelliMed - Backup Automático da sua Clínica ({timezone.now().strftime("%d/%m/%Y")})',
                message=f'Olá,\n\nSegue em anexo o backup automático dos dados da sua clínica "{clinica.nome}".\n\nGuarde este arquivo em um local seguro.\n\nAtenciosamente,\nEquipe IntelliMed.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[clinica.backup_email_notificacao],
                fail_silently=False,
                html_message=f'<p>Olá,</p><p>Segue em anexo o backup automático dos dados da sua clínica "{clinica.nome}".</p><p>Guarde este arquivo em um local seguro.</p><p>Atenciosamente,<br>Equipe IntelliMed.</p>'
            ).attach(filename, backup_content, 'application/json')
            print(f"    ✓ Backup da clínica {clinica.id} enviado para {clinica.backup_email_notificacao}")
        
        # Atualiza a data do último backup
        clinica.backup_ultimo_realizado = timezone.now()
        clinica.save(update_fields=['backup_ultimo_realizado'])

    except Exception as e:
        print(f"    ✗ ERRO ao gerar ou enviar e-mail de backup para clínica {clinica.id}: {e}")


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrMedico])
def backup_restaurar_view(request):
    """
    Restaurar dados a partir de arquivo de backup JSON
    POST /api/backup/restaurar/
    """
    try:
        # DEBUG: Ver o que chegou
        print(f"\n🔍 DEBUG RESTAURAÇÃO:")
        print(f"   - request.FILES: {request.FILES}")
        print(f"   - request.FILES.keys(): {list(request.FILES.keys())}")
        print(f"   - request.data: {request.data.keys() if hasattr(request.data, 'keys') else 'N/A'}")
        print(f"   - Content-Type: {request.content_type}")
        
        if 'backup_file' not in request.FILES:
            print(f"   ❌ ERRO: 'backup_file' não está em request.FILES")
            print(f"   📋 Chaves disponíveis: {list(request.FILES.keys())}")
            return Response({'erro': 'Nenhum arquivo enviado'}, status=400)
        
        arquivo = request.FILES['backup_file']

        print(f"   ✅ Arquivo recebido: {arquivo.name}")
        
        if not arquivo.name.endswith('.json'):
            print(f"   ❌ ERRO: Arquivo não é JSON: {arquivo.name}")
            return Response({'erro': 'Apenas arquivos JSON'}, status=400)
        
        try:
            conteudo = arquivo.read().decode('utf-8')
            print(f"   ✅ Arquivo lido: {len(conteudo)} caracteres")
            dados = json.loads(conteudo)
            print(f"   ✅ JSON parseado: {dados.keys()}")
        except Exception as e:
            print(f"   ❌ ERRO ao parsear JSON: {e}")
            return Response({'erro': 'Arquivo JSON inválido'}, status=400)
        
        if 'clinica_id' not in dados or 'timestamp' not in dados:
            print(f"   ❌ ERRO: Estrutura inválida. Chaves: {dados.keys()}")
            return Response({'erro': 'Estrutura de backup inválida'}, status=400)
        
        clinica_id = request.user.get('clinica_id')
        print(f"   ✅ Clínica do usuário: {clinica_id}")
        
        if not clinica_id:
            print(f"   ❌ ERRO: Usuário sem clínica")
            return Response({'erro': 'Usuário sem clínica'}, status=403)
        
        print(f"   🚀 Iniciando restauração...")
        
        from django.db import transaction
        
        with transaction.atomic():
            # Limpar dados existentes
            Despesa.objects.filter(clinica_id=clinica_id).delete()
            Receita.objects.filter(clinica_id=clinica_id).delete()
            CategoriaDespesa.objects.filter(clinica_id=clinica_id).delete()
            CategoriaReceita.objects.filter(clinica_id=clinica_id).delete()
            Transcricao.objects.filter(clinica_id=clinica_id).delete()
            Exame.objects.filter(clinica_id=clinica_id).delete()
            Consulta.objects.filter(clinica_id=clinica_id).delete()
            Agendamento.objects.filter(clinica_id=clinica_id).delete()
            Paciente.objects.filter(clinica_id=clinica_id).delete()
            
            id_map = {
                'categorias_receita': {},
                'categorias_despesa': {},
                'pacientes': {},
                'agendamentos': {},
                'consultas': {}
            }
            
            dados_backup = dados.get('dados', {})

            # Restaurar categorias de receita
            for cat in dados_backup.get('categorias_receita', []):
                old_id = cat.pop('id')
                cat.pop('clinica_id', None)
                cat.pop('data_cadastro', None)
                nova_cat = CategoriaReceita.objects.create(clinica_id=clinica_id, **cat)
                id_map['categorias_receita'][old_id] = nova_cat.id
            
            # Restaurar categorias de despesa
            for cat in dados_backup.get('categorias_despesa', []):
                old_id = cat.pop('id')
                cat.pop('clinica_id', None)
                cat.pop('data_cadastro', None)
                nova_cat = CategoriaDespesa.objects.create(clinica_id=clinica_id, **cat)
                id_map['categorias_despesa'][old_id] = nova_cat.id
            
            # Restaurar pacientes
            for paciente in dados_backup.get('pacientes', []):
                old_id = paciente.pop('id')
                paciente.pop('clinica_id', None)
                campos_a_remover = ['idade', 'endereco_completo', 'sexo_display', 'convenio_display', 'data_cadastro', 'data_atualizacao']
                for campo in campos_a_remover:
                    paciente.pop(campo, None)
                novo_paciente = Paciente.objects.create(clinica_id=clinica_id, **paciente)
                id_map['pacientes'][old_id] = novo_paciente.id
            
            # Restaurar agendamentos
            for agendamento in dados_backup.get('agendamentos', []):
                old_id = agendamento.pop('id')
                agendamento.pop('clinica_id', None)
                campos_a_remover = ['status_display', 'servico_display', 'paciente_nome', 'paciente_cpf', 'paciente_id', 'data_cadastro', 'data_atualizacao']
                for campo in campos_a_remover:
                    agendamento.pop(campo, None)
                paciente_old_id = agendamento.pop('paciente', None)
                agendamento['paciente_id'] = id_map['pacientes'].get(paciente_old_id)
                if agendamento['paciente_id']:
                    novo_agendamento = Agendamento.objects.create(clinica_id=clinica_id, **agendamento)
                    id_map['agendamentos'][old_id] = novo_agendamento.id
            
            # Restaurar consultas
            for consulta in dados_backup.get('consultas', []):
                old_id = consulta.pop('id')
                consulta.pop('clinica_id', None)
                paciente_old_id = consulta.pop('paciente', None)
                agendamento_old_id = consulta.pop('agendamento', None)
                consulta['paciente_id'] = id_map['pacientes'].get(paciente_old_id)
                if agendamento_old_id:
                    consulta['agendamento_id'] = id_map['agendamentos'].get(agendamento_old_id)
                campos_a_remover = ['tipo_consulta_display', 'status_display', 'paciente_nome', 'paciente_cpf', 'data_cadastro', 'data_atualizacao', 'data_inicio_atendimento', 'data_fim_atendimento']
                for campo in campos_a_remover:
                    consulta.pop(campo, None)
                if consulta['paciente_id']:
                    nova_consulta = Consulta.objects.create(clinica_id=clinica_id, **consulta)
                    id_map['consultas'][old_id] = nova_consulta.id
            
            # Restaurar exames
            for exame in dados_backup.get('exames', []):
                exame.pop('id', None)
                exame.pop('clinica_id', None)
                paciente_old_id = exame.pop('paciente', None)
                consulta_old_id = exame.pop('consulta', None)
                exame['paciente_id'] = id_map['pacientes'].get(paciente_old_id)
                if consulta_old_id:
                    exame['consulta_id'] = id_map['consultas'].get(consulta_old_id)
                campos_a_remover = ['tipo_exame_display', 'status_display', 'paciente_nome', 'data_cadastro', 'data_atualizacao', 'data_revisao']
                for campo in campos_a_remover:
                    exame.pop(campo, None)
                if exame['paciente_id']:
                    Exame.objects.create(clinica_id=clinica_id, **exame)
            
            # Restaurar receitas
            for receita in dados_backup.get('receitas', []):
                receita.pop('id', None)
                receita.pop('clinica_id', None)
                paciente_old_id = receita.pop('paciente', None)
                if paciente_old_id:
                    receita['paciente_id'] = id_map['pacientes'].get(paciente_old_id)
                categoria_old_id = receita.pop('categoria', None)
                if categoria_old_id:
                    receita['categoria_id'] = id_map['categorias_receita'].get(categoria_old_id)
                agendamento_old_id = receita.pop('agendamento', None)
                if agendamento_old_id:
                    receita['agendamento_id'] = id_map['agendamentos'].get(agendamento_old_id)
                
                # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
                campos_a_remover = ['data_cadastro', 'data_atualizacao', 'paciente_nome', 'categoria_nome', 'status_display']
                for campo in campos_a_remover:
                    receita.pop(campo, None)
                # ▲▲▲ FIM DA CORREÇÃO ▲▲▲
                
                Receita.objects.create(clinica_id=clinica_id, **receita)
            
            # Restaurar despesas
            for despesa in dados_backup.get('despesas', []):
                despesa.pop('id', None)
                despesa.pop('clinica_id', None)
                categoria_old_id = despesa.pop('categoria', None)
                if categoria_old_id:
                    despesa['categoria_id'] = id_map['categorias_despesa'].get(categoria_old_id)
                
                # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
                campos_a_remover = ['data_cadastro', 'data_atualizacao', 'categoria_nome', 'status_display']
                for campo in campos_a_remover:
                    despesa.pop(campo, None)
                # ▲▲▲ FIM DA CORREÇÃO ▲▲▲

                Despesa.objects.create(clinica_id=clinica_id, **despesa)
        
        return Response({
            'mensagem': 'Backup restaurado com sucesso!',
            'data_backup': dados.get('timestamp'),
            'resumo': {
                'pacientes': len(id_map['pacientes']),
                'agendamentos': len(id_map['agendamentos']),
                'consultas': len(id_map['consultas']),
                'exames': len(dados_backup.get('exames', [])),
                'receitas': len(dados_backup.get('receitas', [])),
                'despesas': len(dados_backup.get('despesas', []))
            }
        }, status=200)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'erro': f'Erro ao restaurar: {str(e)}'}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrMedico])
def backup_criar_view(request):
    """Cria e retorna um backup JSON dos dados da clínica para download manual."""
    user = request.user
    clinica_id = user.get('clinica_id')
    if not clinica_id:
        return Response({'erro': 'Usuário não vinculado a uma clínica.'}, status=400)

    backup_data = _gerar_dados_backup(clinica_id)
    
    response = JsonResponse(backup_data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    filename = f"backup_intellimed_clinica_{clinica_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@api_view(['POST', 'GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrMedico])
def backup_configurar_view(request):
    """
    GET: Retorna as configurações de backup da clínica.
    POST: Salva as novas configurações de backup da clínica.
    """
    user = request.user
    clinica_id = user.get('clinica_id')
    
    try:
        clinica = Clinica.objects.get(id=clinica_id)
    except Clinica.DoesNotExist:
        return Response({'erro': 'Clínica não encontrada.'}, status=404)

    if request.method == 'GET':
        serializer = ClinicaSerializer(clinica)
        return Response({
            'backup_frequencia': serializer.data.get('backup_frequencia'),
            'backup_email_notificacao': serializer.data.get('backup_email_notificacao'),
            'backup_ultimo_realizado': serializer.data.get('backup_ultimo_realizado'),
        })

    if request.method == 'POST':
        frequencia = request.data.get('frequencia')
        email = request.data.get('email_notificacao')
        
        frequencias_validas = [choice[0] for choice in Clinica.BACKUP_FREQUENCIA_CHOICES]
        if frequencia not in frequencias_validas:
            return Response({'erro': 'Frequência de backup inválida.'}, status=400)
            
        clinica.backup_frequencia = frequencia
        if email:
            clinica.backup_email_notificacao = email
        
        clinica.save()
        return Response({'mensagem': 'Configurações de backup salvas com sucesso!'})

def _perform_restore_from_data(clinica_id, dados_backup):
    """
    Função auxiliar que contém a lógica de restauração a partir de um dicionário de dados.
    Esta função é transacional e segura.
    """
    with transaction.atomic():
        # Função interna para filtrar apenas campos válidos do modelo
        def get_valid_fields(model, data_dict):
            valid_field_names = {f.name for f in model._meta.get_fields()}
            return {key: value for key, value in data_dict.items() if key in valid_field_names}

        # Limpar dados existentes
        Despesa.objects.filter(clinica_id=clinica_id).delete()
        Receita.objects.filter(clinica_id=clinica_id).delete()
        CategoriaDespesa.objects.filter(clinica_id=clinica_id).delete()
        CategoriaReceita.objects.filter(clinica_id=clinica_id).delete()
        Transcricao.objects.filter(clinica_id=clinica_id).delete()
        Exame.objects.filter(clinica_id=clinica_id).delete()
        Consulta.objects.filter(clinica_id=clinica_id).delete()
        Agendamento.objects.filter(clinica_id=clinica_id).delete()
        Paciente.objects.filter(clinica_id=clinica_id).delete()
        
        id_map = {
            'categorias_receita': {}, 'categorias_despesa': {}, 'pacientes': {},
            'agendamentos': {}, 'consultas': {}
        }
        
        for cat in dados_backup.get('categorias_receita', []):
            old_id = cat.pop('id')
            valid_data = get_valid_fields(CategoriaReceita, cat)
            nova_cat = CategoriaReceita.objects.create(clinica_id=clinica_id, **valid_data)
            id_map['categorias_receita'][old_id] = nova_cat.id
        
        for cat in dados_backup.get('categorias_despesa', []):
            old_id = cat.pop('id')
            valid_data = get_valid_fields(CategoriaDespesa, cat)
            nova_cat = CategoriaDespesa.objects.create(clinica_id=clinica_id, **valid_data)
            id_map['categorias_despesa'][old_id] = nova_cat.id
        
        for paciente_data in dados_backup.get('pacientes', []):
            old_id = paciente_data.pop('id')
            valid_data = get_valid_fields(Paciente, paciente_data)
            novo_paciente = Paciente.objects.create(clinica_id=clinica_id, **valid_data)
            id_map['pacientes'][old_id] = novo_paciente.id
        
        for agendamento_data in dados_backup.get('agendamentos', []):
            old_id = agendamento_data.pop('id')
            agendamento_data['paciente_id'] = id_map['pacientes'].get(agendamento_data.pop('paciente'))
            if agendamento_data.get('paciente_id'):
                valid_data = get_valid_fields(Agendamento, agendamento_data)
                novo_agendamento = Agendamento.objects.create(clinica_id=clinica_id, **valid_data)
                id_map['agendamentos'][old_id] = novo_agendamento.id
        
        for consulta_data in dados_backup.get('consultas', []):
            old_id = consulta_data.pop('id')
            consulta_data['paciente_id'] = id_map['pacientes'].get(consulta_data.pop('paciente'))
            if consulta_data.get('agendamento'):
                consulta_data['agendamento_id'] = id_map['agendamentos'].get(consulta_data.pop('agendamento'))
            if consulta_data.get('paciente_id'):
                valid_data = get_valid_fields(Consulta, consulta_data)
                nova_consulta = Consulta.objects.create(clinica_id=clinica_id, **valid_data)
                id_map['consultas'][old_id] = nova_consulta.id

        for exame_data in dados_backup.get('exames', []):
            old_id = exame_data.pop('id')
            exame_data['paciente_id'] = id_map['pacientes'].get(exame_data.pop('paciente'))
            if exame_data.get('consulta'):
                exame_data['consulta_id'] = id_map['consultas'].get(exame_data.pop('consulta'))
            if exame_data.get('paciente_id'):
                valid_data = get_valid_fields(Exame, exame_data)
                Exame.objects.create(clinica_id=clinica_id, **valid_data)

        for receita_data in dados_backup.get('receitas', []):
            old_id = receita_data.pop('id')
            if receita_data.get('paciente'):
                 receita_data['paciente_id'] = id_map['pacientes'].get(receita_data.pop('paciente'))
            if receita_data.get('categoria'):
                receita_data['categoria_id'] = id_map['categorias_receita'].get(receita_data.pop('categoria'))
            if receita_data.get('agendamento'):
                receita_data['agendamento_id'] = id_map['agendamentos'].get(receita_data.pop('agendamento'))
            valid_data = get_valid_fields(Receita, receita_data)
            Receita.objects.create(clinica_id=clinica_id, **valid_data)
            
        for despesa_data in dados_backup.get('despesas', []):
            old_id = despesa_data.pop('id')
            if despesa_data.get('categoria'):
                despesa_data['categoria_id'] = id_map['categorias_despesa'].get(despesa_data.pop('categoria'))
            valid_data = get_valid_fields(Despesa, despesa_data)
            Despesa.objects.create(clinica_id=clinica_id, **valid_data)
        
        return {
            'pacientes': len(id_map['pacientes']), 'agendamentos': len(id_map['agendamentos']),
            'consultas': len(id_map['consultas']), 'exames': len(dados_backup.get('exames', [])),
            'receitas': len(dados_backup.get('receitas', [])), 'despesas': len(dados_backup.get('despesas', []))
        }

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrMedico])
def backup_historico_view(request):
    """Lista os backups automáticos disponíveis no servidor para a clínica."""
    clinica_id = request.user.get('clinica_id')
    backup_dir = 'intellimed_backups'
    historico = []

    if not os.path.exists(backup_dir):
        return Response([])

    try:
        for filename in os.listdir(backup_dir):
            if filename.startswith(f"backup_intellimed_clinica_{clinica_id}_") and filename.endswith(".json"):
                try:
                    timestamp_str = filename.split('_')[-1].replace('.json', '')
                    dt_obj = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                    historico.append({
                        'filename': filename,
                        'timestamp': dt_obj.strftime('%d/%m/%Y às %H:%M:%S')
                    })
                except (ValueError, IndexError):
                    continue
        
        historico.sort(key=lambda x: datetime.strptime(x['timestamp'], '%d/%m/%Y às %H:%M:%S'), reverse=True)
        
        return Response(historico)
    except Exception as e:
        return Response({'erro': f'Erro ao listar backups: {str(e)}'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrMedico])
def backup_restaurar_automatico_view(request):
    """Restaura um backup específico a partir da lista de automáticos."""
    clinica_id = request.user.get('clinica_id')
    filename = request.data.get('filename')

    if not filename:
        return Response({'erro': 'Nome do arquivo de backup não fornecido.'}, status=400)

    if '..' in filename or '/' in filename or '\\' in filename:
        return Response({'erro': 'Nome de arquivo inválido.'}, status=400)
    if not filename.startswith(f"backup_intellimed_clinica_{clinica_id}_"):
        return Response({'erro': 'Acesso negado. Este backup não pertence à sua clínica.'}, status=403)

    backup_dir = 'intellimed_backups'
    filepath = os.path.join(backup_dir, filename)

    if not os.path.exists(filepath):
        return Response({'erro': 'Arquivo de backup não encontrado no servidor.'}, status=404)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        if dados.get('clinica_id') != clinica_id:
            return Response({'erro': 'Inconsistência de dados: O ID da clínica no arquivo não corresponde.'}, status=400)

        resumo = _perform_restore_from_data(clinica_id, dados.get('dados', {}))
        
        return Response({
            'mensagem': f'Backup de {dados.get("timestamp")} restaurado com sucesso!',
            'resumo': resumo
        }, status=200)

    except Exception as e:
        return Response({'erro': f'Erro crítico durante a restauração: {str(e)}'}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrMedico])
def estatisticas_medico_view(request):
    """
    Endpoint completo para estatísticas de rendimento de um médico.
    """
    try:
        medico_id = request.query_params.get('medico_id')
        if not medico_id:
            return Response({'erro': 'O parâmetro medico_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        clinica_id = request.user.get('clinica_id')
        medico = Usuario.objects.get(id=medico_id, clinica_id=clinica_id, funcao='medico')
        
        periodo = request.query_params.get('periodo', 'mes')
        hoje = date.today()
        
        if periodo == 'dia':
            start_date, end_date = hoje, hoje
        elif periodo == 'semana':
            start_date = hoje - timedelta(days=hoje.weekday())
            end_date = start_date + timedelta(days=6)
        elif periodo == 'bimestre':
            current_quarter = (hoje.month - 1) // 2
            start_month = current_quarter * 2 + 1
            start_date = date(hoje.year, start_month, 1)
            end_month = start_month + 1
            end_date = (date(hoje.year, end_month, 1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        elif periodo == 'trimestre':
            current_quarter = (hoje.month - 1) // 3
            start_month = current_quarter * 3 + 1
            start_date = date(hoje.year, start_month, 1)
            end_month = start_month + 2
            end_date = (date(hoje.year, end_month, 1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        elif periodo == 'semestre':
            start_month = 1 if hoje.month <= 6 else 7
            start_date = date(hoje.year, start_month, 1)
            end_date = date(hoje.year, start_month + 5, 1)
            end_date = (end_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        elif periodo == 'ano':
            start_date, end_date = date(hoje.year, 1, 1), date(hoje.year, 12, 31)
        else: # Mês (padrão)
            start_date = hoje.replace(day=1)
            end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        # --- CÁLCULOS ---
        agendamentos = Agendamento.objects.filter(medico_responsavel=medico, data__range=[start_date, end_date])
        consultas_realizadas = Consulta.objects.filter(medico_responsavel=medico.nome_completo, data_consulta__date__range=[start_date, end_date], status='finalizada')
        
        # 1. Atendimentos
        atendimentos_stats = agendamentos.values('status').annotate(total=Count('id'))
        atendimentos_map = {item['status']: item['total'] for item in atendimentos_stats}
        
        # 2. Duração Média
        duracao_media_dict = consultas_realizadas.aggregate(media=models.Avg('duracao_minutos'))
        duracao_media = duracao_media_dict['media'] or 0

        # 3. Faturamento
        agendamentos_realizados_ids = agendamentos.filter(status='Realizado').values_list('id', flat=True)
        receitas = Receita.objects.filter(agendamento_id__in=agendamentos_realizados_ids, status='recebida')
        
        faturamento_total = receitas.aggregate(total=Sum('valor'))['total'] or 0
        faturamento_por_convenio = list(receitas.values('agendamento__convenio').annotate(total=Sum('valor')).order_by('-total'))
        faturamento_por_forma_pgto = list(receitas.values('forma_pagamento').annotate(total=Sum('valor')).order_by('-total'))

        # Monta a resposta
        resposta = {
            'medico': {'id': medico.id, 'nome': medico.nome_completo},
            'periodo': {'tipo': periodo, 'inicio': start_date.strftime('%d/%m/%Y'), 'fim': end_date.strftime('%d/%m/%Y')},
            'estatisticas': {
                'atendimentos': {
                    'realizados': atendimentos_map.get('Realizado', 0),
                    'faltas': atendimentos_map.get('Faltou', 0),
                    'cancelados': atendimentos_map.get('Cancelado', 0),
                    'por_convenio': list(agendamentos.filter(status='Realizado').values('convenio').annotate(total=Count('id')).order_by('-total'))
                },
                'desempenho': {
                    'duracao_media_minutos': round(duracao_media, 1)
                },
                'faturamento': {
                    'total': float(faturamento_total),
                    'por_convenio': [{'convenio': item['agendamento__convenio'], 'total': float(item['total'])} for item in faturamento_por_convenio],
                    'por_forma_pagamento': [{'forma_pagamento': item['forma_pagamento'], 'total': float(item['total'])} for item in faturamento_por_forma_pgto]
                }
            }
        }
        return Response(resposta)
    except Usuario.DoesNotExist:
        return Response({'erro': 'Médico não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'erro': f'Ocorreu um erro: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================
# URLS
# ============================================

urlpatterns = [
    # Autenticação
    path('login', login_view, name='login'),
    path('register', register_view, name='register'),
    
    # ▼▼▼ NOVAS ROTAS ADICIONADAS AQUI ▼▼▼
    path('api/definir-nova-senha/', definir_nova_senha_view, name='definir-nova-senha'),
    path('api/esqueci-senha/', esqueci_senha_view, name='esqueci-senha'),
    # ▲▲▲ FIM DAS NOVAS ROTAS ▲▲▲

    # API REST (com autenticação JWT)
    path('api/', include(router.urls)),
    
    # Dashboards
    path('api/dashboard/', dashboard_principal, name='dashboard-principal'), 
    path('api/faturamento/dashboard/', dashboard_financeiro, name='dashboard-financeiro'),
    path('api/dados-clinica/', dados_clinica_completo, name='dados-clinica'),

    path('api/faturamento/auditoria/', auditoria_faturamento_view, name='auditoria_faturamento'),

    path('api/estatisticas/medico/', estatisticas_medico_view, name='estatisticas-medico'),

    # Rotas de Backup
    path('api/backup/criar/', backup_criar_view, name='backup-criar'),
    path('api/backup/restaurar/', backup_restaurar_view, name='backup-restaurar'),
    path('api/backup/configuracao/', backup_configurar_view, name='backup-configurar'),
    path('api/backup/historico/', backup_historico_view, name='backup-historico'),
    path('api/backup/restaurar-automatico/', backup_restaurar_automatico_view, name='backup-restaurar-automatico'),

    # IA - Termos de uso e Funções Utilitárias
    path('api/exames/termos-uso-ia/', termos_uso_ia, name='termos-uso-ia'),
    path('api/transcrever-audio/', transcrever_audio_view, name='transcrever-audio'), 

    # Health check
    path('api/health/', lambda request: JsonResponse({'status': 'ok'}), name='health'),
    path('api/auditoria/recente/', auditoria_recente_view, name='auditoria-recente'), 
    path('api/auditoria/financeira/', auditoria_financeira_view, name='auditoria-financeira'),
    
    # ROTA DE SETUP
    path('api/setup/', setup_clinica, name='setup-clinica'),
]

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
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================

# ============================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================

def criar_tabelas_customizadas():
    """
    Cria todas as tabelas customizadas do sistema usando connection.schema_editor()
    """
    from django.db import connection
    
    print("📦 Criando tabelas customizadas do IntelliMed...")
    
    with connection.schema_editor() as schema_editor:
        # Lista de todos os models que precisam ter tabelas criadas
        models_para_criar = [
            Clinica,
            Usuario,
            Paciente,
            Agendamento,
            Consulta,
            Exame,
            CategoriaReceita,
            CategoriaDespesa,
            Receita,
            Despesa,
            Transcricao,
        ]
        
        for model in models_para_criar:
            try:
                # Verifica se a tabela já existe
                table_name = model._meta.db_table
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                    existe = cursor.fetchone()
                
                if not existe:
                    schema_editor.create_model(model)
                    print(f"   ✅ Tabela '{table_name}' criada")
                else:
                    print(f"   ⏭️  Tabela '{table_name}' já existe")
                    
            except Exception as e:
                print(f"   ⚠️  Erro ao criar tabela {model._meta.db_table}: {e}")
    
    print("✅ Tabelas customizadas criadas com sucesso!\n")


def inicializar_banco():
    """
    Cria as tabelas do banco de dados e popula com dados iniciais
    """
    from django.core.management import execute_from_command_line
    import sys
    
    print("\n" + "="*70)
    print("INICIALIZANDO BANCO DE DADOS")
    print("="*70 + "\n")
    
    # Criar tabelas do Django (auth, contenttypes)
    print("📦 Criando tabelas do Django (auth, contenttypes)...")
    sys.argv = ['manage.py', 'migrate', '--run-syncdb']
    execute_from_command_line(sys.argv)
    print("✅ Tabelas Django criadas!\n")
    
    # Criar tabelas customizadas (nossos models)
    criar_tabelas_customizadas()
    
    # Verificar se já existe super admin
    try:
        super_admin = Usuario.objects.filter(email='superadmin@intellimed.com').first()
        
        if not super_admin:
            print("👤 Criando Super Admin padrão...")
            super_admin = Usuario(
            clinica=None,
            nome_completo='Super Administrador',
            email='superadmin@intellimed.com',
            cpf='123.456.789-09',  # ← CPF VÁLIDO
            data_nascimento='1990-01-01',
            telefone_celular='(00) 00000-0000',
            funcao='super_admin',
            status='ativo'
        )
            super_admin.set_password('superadmin123')
            super_admin.save()
            print("✅ Super Admin criado com sucesso!")
            print(f"   Email: superadmin@intellimed.com")
            print(f"   Senha: superadmin123\n")
        else:
            print("✅ Super Admin já existe no banco de dados\n")
            
    except Exception as e:
        print(f"⚠️  Erro ao criar Super Admin: {e}\n")
        import traceback
        traceback.print_exc()
    
    print("="*70)
    print("✅ BANCO DE DADOS INICIALIZADO COM SUCESSO!")
    print("="*70 + "\n")


def popular_categorias_padrao(clinica_id):
    """
    Popula categorias padrão de receitas e despesas para uma nova clínica
    """
    try:
        # Categorias de Receita padrão
        categorias_receita = [
            {'nome': 'Consultas', 'descricao': 'Receitas de consultas médicas', 'cor': '#4CAF50'},
            {'nome': 'Exames', 'descricao': 'Receitas de exames realizados', 'cor': '#2196F3'},
            {'nome': 'Procedimentos', 'descricao': 'Receitas de procedimentos médicos', 'cor': '#FF9800'},
            {'nome': 'Convênios', 'descricao': 'Repasses de convênios médicos', 'cor': '#9C27B0'},
            {'nome': 'Particulares', 'descricao': 'Atendimentos particulares', 'cor': '#00BCD4'},
        ]
        
        for cat_data in categorias_receita:
            CategoriaReceita.objects.get_or_create(
                clinica_id=clinica_id,
                nome=cat_data['nome'],
                defaults={
                    'descricao': cat_data['descricao'],
                    'cor': cat_data['cor'],
                    'ativo': True
                }
            )
        
        # Categorias de Despesa padrão
        categorias_despesa = [
            {'nome': 'Salários', 'descricao': 'Folha de pagamento', 'cor': '#F44336'},
            {'nome': 'Aluguel', 'descricao': 'Aluguel do imóvel', 'cor': '#E91E63'},
            {'nome': 'Material Médico', 'descricao': 'Materiais e equipamentos médicos', 'cor': '#9C27B0'},
            {'nome': 'Limpeza', 'descricao': 'Produtos e serviços de limpeza', 'cor': '#673AB7'},
            {'nome': 'Telefonia/Internet', 'descricao': 'Contas de telefone e internet', 'cor': '#3F51B5'},
            {'nome': 'Energia Elétrica', 'descricao': 'Conta de luz', 'cor': '#FF9800'},
            {'nome': 'Água', 'descricao': 'Conta de água', 'cor': '#00BCD4'},
            {'nome': 'Marketing', 'descricao': 'Despesas com divulgação', 'cor': '#4CAF50'},
        ]
        
        for cat_data in categorias_despesa:
            CategoriaDespesa.objects.get_or_create(
                clinica_id=clinica_id,
                nome=cat_data['nome'],
                defaults={
                    'descricao': cat_data['descricao'],
                    'cor': cat_data['cor'],
                    'ativo': True
                }
            )
        
        print(f"✅ Categorias padrão criadas para clínica ID {clinica_id}")
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao criar categorias padrão: {e}")
        return False

def popular_categorias_padrao(clinica_id):
    """
    Popula categorias padrão de receitas e despesas para uma nova clínica
    """
    try:
        # Categorias de Receita padrão
        categorias_receita = [
            {'nome': 'Consultas', 'descricao': 'Receitas de consultas médicas', 'cor': '#4CAF50'},
            {'nome': 'Exames', 'descricao': 'Receitas de exames realizados', 'cor': '#2196F3'},
            {'nome': 'Procedimentos', 'descricao': 'Receitas de procedimentos médicos', 'cor': '#FF9800'},
            {'nome': 'Convênios', 'descricao': 'Repasses de convênios médicos', 'cor': '#9C27B0'},
            {'nome': 'Particulares', 'descricao': 'Atendimentos particulares', 'cor': '#00BCD4'},
        ]
        
        for cat_data in categorias_receita:
            CategoriaReceita.objects.get_or_create(
                clinica_id=clinica_id,
                nome=cat_data['nome'],
                defaults={
                    'descricao': cat_data['descricao'],
                    'cor': cat_data['cor'],
                    'ativo': True
                }
            )
        
        # Categorias de Despesa padrão
        categorias_despesa = [
            {'nome': 'Salários', 'descricao': 'Folha de pagamento', 'cor': '#F44336'},
            {'nome': 'Aluguel', 'descricao': 'Aluguel do imóvel', 'cor': '#E91E63'},
            {'nome': 'Material Médico', 'descricao': 'Materiais e equipamentos médicos', 'cor': '#9C27B0'},
            {'nome': 'Limpeza', 'descricao': 'Produtos e serviços de limpeza', 'cor': '#673AB7'},
            {'nome': 'Telefonia/Internet', 'descricao': 'Contas de telefone e internet', 'cor': '#3F51B5'},
            {'nome': 'Energia Elétrica', 'descricao': 'Conta de luz', 'cor': '#FF9800'},
            {'nome': 'Água', 'descricao': 'Conta de água', 'cor': '#00BCD4'},
            {'nome': 'Marketing', 'descricao': 'Despesas com divulgação', 'cor': '#4CAF50'},
        ]
        
        for cat_data in categorias_despesa:
            CategoriaDespesa.objects.get_or_create(
                clinica_id=clinica_id,
                nome=cat_data['nome'],
                defaults={
                    'descricao': cat_data['descricao'],
                    'cor': cat_data['cor'],
                    'ativo': True
                }
            )
        
        print(f"✅ Categorias padrão criadas para clínica ID {clinica_id}")
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao criar categorias padrão: {e}")
        return False
    

# ============================================
# PONTO DE ENTRADA
# ============================================


if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    import sys
    
    import sqlite3
    import os
    
    db_existe = os.path.exists(Config.DATABASE_NAME)
    precisa_inicializar = False
    
    if not db_existe:
        print("⚠️  Banco de dados não encontrado. Será criado automaticamente.")
        precisa_inicializar = True
    else:
        try:
            conn = sqlite3.connect(Config.DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_apscheduler_djangojob';")
            result = cursor.fetchone()
            conn.close()
            if not result:
                print("⚠️  Tabelas do agendador não encontradas.")
                precisa_inicializar = True
        except:
            precisa_inicializar = True
    
    if precisa_inicializar:
        inicializar_banco()
    
    # ▼▼▼ LÓGICA DE INICIALIZAÇÃO DO AGENDADOR ATUALIZADA AQUI ▼▼▼
    try:
        print("\n" + "="*70)
        # Imports movidos para dentro da função para evitar erro de Apps not loaded
        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore
        print("⚙️  INICIANDO AGENDADOR DE TAREFAS (APScheduler)")
        # Imports movidos para evitar erro de Apps not loaded
        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore
        
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # Remove a tarefa antiga se já existir, para evitar duplicatas ao reiniciar o servidor
        if scheduler.get_job('backup_automatico_diario'):
            scheduler.remove_job('backup_automatico_diario')
            print("   - Tarefa de backup antiga removida para reconfiguração.")

        # Adiciona a tarefa para rodar todos os dias às 3 da manhã.
        scheduler.add_job(
            executar_backup_automatico,
            trigger='cron',
            hour=3,
            minute=0,
            id='backup_automatico_diario',
            max_instances=1,
            replace_existing=True,
        )
        
        scheduler.start()
        print("   ✅ Agendador iniciado. Verificação de backups agendada para as 03:00.")
        print("="*70)
    except Exception as e:
        print(f"   ❌ Falha ao iniciar o agendador: {e}")
    # ▲▲▲ FIM DA LÓGICA DO AGENDADOR ▲▲▲

    print("\n" + "="*70)
    print("INTELLIMED - BACKEND API")
    print(f"\n🚀 Servidor iniciando na porta {Config.PORT}...")
    
    sys.argv = ['manage.py', 'runserver', f'{Config.HOST}:{Config.PORT}', '--noreload']
    execute_from_command_line(sys.argv)
