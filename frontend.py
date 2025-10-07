"""
IntelliMed - Frontend Django
Interface Web para Sistema de Gestão de Clínicas
Arquivo Único com Templates Embutidos
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Configuração Django
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.middleware.csrf import get_token

# ============================================
# CONFIGURAÇÕES
# ============================================

class Config:
    """Configurações do Frontend"""
    
    # Backend API
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
    
    # Servidor Frontend
    HOST = '0.0.0.0'
    PORT = 3000
    
    # Debug
    DEBUG = True
    
    # Session
    SESSION_COOKIE_AGE = 86400  # 24 horas


# Configurar Django
if not settings.configured:
    settings.configure(
        DEBUG=Config.DEBUG,
        SECRET_KEY='frontend-secret-key-change-in-production',
        ALLOWED_HOSTS=['*'],
        
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
        ],
        
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': False,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.messages.context_processors.messages',
                ],
                'string_if_invalid': '',
            },
        }],
        
        # Session
        SESSION_ENGINE='django.contrib.sessions.backends.db',
        SESSION_COOKIE_AGE=Config.SESSION_COOKIE_AGE,
        
        # Database para sessions
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'frontend_sessions.db',
            }
        },
        
        ROOT_URLCONF='__main__',
    )
    
    django.setup()

# ============================================
# TEMPLATES HTML
# ============================================

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IntelliMed - Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .login-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            max-width: 400px;
            width: 100%;
        }
        
        .login-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        
        .login-header h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .login-header p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .login-body {
            padding: 40px 30px;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 14px;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 15px;
            transition: all 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn-login {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn-login:active {
            transform: translateY(0);
        }
        
        .btn-login:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .alert {
            padding: 12px 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .alert-error {
            background-color: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
        
        .alert-success {
            background-color: #efe;
            color: #3c3;
            border: 1px solid #cfc;
        }
        
        .remember-me {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .remember-me input {
            width: auto;
            margin-right: 8px;
        }
        
        .remember-me label {
            font-size: 14px;
            color: #666;
            cursor: pointer;
        }
        
        .dev-login {
            margin-top: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 10px;
            border: 2px dashed #ddd;
        }
        
        .dev-login p {
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .btn-dev {
            width: 100%;
            padding: 10px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            margin-bottom: 8px;
        }
        
        .btn-dev:hover {
            background: #45a049;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin-top: 10px;
            color: #667eea;
            font-size: 14px;
        }
        
        .loading.active {
            display: block;
        }
        
        @media (max-width: 480px) {
            .login-header h1 {
                font-size: 24px;
            }
            
            .login-body {
                padding: 30px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>intelliMed</h1>
            <p>Sistema de Gestão de Clínicas</p>
        </div>
        
        <div class="login-body">
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-{{ message.tags }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
            
            <form method="POST" action="{% url 'login' %}" id="loginForm">
                {% csrf_token %}
                
                <div class="form-group">
                    <label for="email">Email</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        placeholder="seu@email.com"
                        required
                        value="{{ email_saved }}"
                    >
                </div>
                
                <div class="form-group">
                    <label for="password">Senha</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        placeholder="••••••••"
                        required
                    >
                </div>
                
                <div class="remember-me">
                    <input type="checkbox" id="remember" name="remember" {{ remember_checked }}>
                    <label for="remember">Lembrar minhas credenciais</label>
                </div>
                
                <button type="submit" class="btn-login" id="btnLogin">
                    Entrar
                </button>
                
                <div class="loading" id="loading">
                    Autenticando...
                </div>
            </form>
            
            <!-- Apenas em desenvolvimento -->
            {% if debug %}
            <div class="dev-login">
                <p>🔧 DEV MODE - Login Rápido</p>
                <button class="btn-dev" onclick="quickLogin('superadmin@intellimed.com', 'superadmin123')">
                    Login como Super Admin
                </button>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        const form = document.getElementById('loginForm');
        const btnLogin = document.getElementById('btnLogin');
        const loading = document.getElementById('loading');
        
        form.addEventListener('submit', function() {
            btnLogin.disabled = true;
            btnLogin.textContent = 'Entrando...';
            loading.classList.add('active');
        });
        
        // Quick login para desenvolvimento
        function quickLogin(email, password) {
            document.getElementById('email').value = email;
            document.getElementById('password').value = password;
            form.submit();
        }
        
        // Salvar email no localStorage se "lembrar" estiver marcado
        const rememberCheckbox = document.getElementById('remember');
        const emailInput = document.getElementById('email');
        
        // Carregar email salvo
        const savedEmail = localStorage.getItem('intellimed_email');
        if (savedEmail) {
            emailInput.value = savedEmail;
            rememberCheckbox.checked = true;
        }
        
        // Salvar ao fazer login
        form.addEventListener('submit', function() {
            if (rememberCheckbox.checked) {
                localStorage.setItem('intellimed_email', emailInput.value);
            } else {
                localStorage.removeItem('intellimed_email');
            }
        });
    </script>
</body>
</html>
"""

# ============================================
# TEMPLATE DASHBOARD COM MENU LATERAL
# ============================================

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - intelliMed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            display: flex;
            min-height: 100vh;
        }
        
        /* MENU LATERAL */
        .sidebar {
            width: 260px;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
            left: 0;
            top: 0;
            box-shadow: 4px 0 10px rgba(0,0,0,0.1);
        }
        
        .sidebar-header {
            padding: 30px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .sidebar-header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .sidebar-header p {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .user-info {
            padding: 20px;
            background: rgba(0,0,0,0.1);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .user-info strong {
            display: block;
            font-size: 14px;
            margin-bottom: 3px;
        }
        
        .user-info small {
            font-size: 12px;
            opacity: 0.7;
        }
        
        .menu {
            flex: 1;
            padding: 20px 0;
        }
        
        .menu-item {
            display: flex;
            align-items: center;
            padding: 14px 25px;
            color: white;
            text-decoration: none;
            transition: all 0.3s;
            font-size: 15px;
            border-left: 3px solid transparent;
        }
        
        .menu-item:hover {
            background: rgba(255,255,255,0.1);
            border-left-color: white;
        }
        
        .menu-item.active {
            background: rgba(255,255,255,0.15);
            border-left-color: white;
            font-weight: 600;
        }
        
        .menu-item-icon {
            width: 20px;
            margin-right: 12px;
            font-size: 18px;
        }
        
        .sidebar-footer {
            padding: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .btn-logout {
            display: block;
            width: 100%;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-logout:hover {
            background: rgba(0,0,0,0.3);
        }
        
        /* CONTEÚDO PRINCIPAL */
        .main-content {
            margin-left: 260px;
            flex: 1;
            padding: 30px;
            width: calc(100% - 260px);
        }
        
        .header {
            background: white;
            padding: 25px 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }
        
        .header h2 {
            font-size: 28px;
            color: #333;
            margin-bottom: 8px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .content-area {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-height: 500px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }
        
        .empty-state {
            text-align: center;
            color: #999;
        }
        
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
        
        .empty-state h3 {
            font-size: 20px;
            color: #666;
            margin-bottom: 10px;
        }
        
        .empty-state p {
            font-size: 14px;
            color: #999;
        }
        
        /* RESPONSIVO */
        @media (max-width: 768px) {
            .sidebar {
                width: 70px;
            }
            
            .sidebar-header h1 {
                font-size: 18px;
            }
            
            .sidebar-header p,
            .user-info,
            .menu-item span {
                display: none;
            }
            
            .menu-item {
                justify-content: center;
                padding: 14px;
            }
            
            .menu-item-icon {
                margin-right: 0;
            }
            
            .main-content {
                margin-left: 70px;
                width: calc(100% - 70px);
            }
        }
    </style>
</head>
<body>
    <!-- MENU LATERAL -->
    <div class="sidebar">
        <div class="sidebar-header">
            <h1>intelliMed</h1>
            <p>Gestão de Clínicas</p>
        </div>
        
        <div class="user-info">
            <strong>{{ user.nome_completo }}</strong>
            <small>{{ user.funcao_display }}</small>
        </div>
        
        <nav class="menu">
            <a href="{% url 'dashboard' %}" class="menu-item active">
                <span class="menu-item-icon">🏠</span>
                <span>Home</span>
            </a>
            <a href="{% url 'pacientes' %}" class="menu-item">
                <span class="menu-item-icon">👥</span>
                <span>Pacientes</span>
            </a>
            <a href="{% url 'agendamentos' %}" class="menu-item">
                <span class="menu-item-icon">📅</span>
                <span>Agendamentos</span>
            </a>
            <a href="{% url 'consultas' %}" class="menu-item">
                <span class="menu-item-icon">🩺</span>
                <span>Consultas</span>
            </a>
            <a href="{% url 'exames' %}" class="menu-item">
                <span class="menu-item-icon">🔬</span>
                <span>Exames IA</span>
            </a>
            <a href="{% url 'faturamento' %}" class="menu-item">
                <span class="menu-item-icon">💰</span>
                <span>Faturamento</span>
            </a>
            <a href="{% url 'informacoes' %}" class="menu-item">
                <span class="menu-item-icon">ℹ️</span>
                <span>Informações</span>
            </a>
        </nav>
        
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">
                ⬅️ Sair
            </a>
        </div>
    </div>
    
    <!-- CONTEÚDO PRINCIPAL -->
    <div class="main-content">
        <div class="header">
            <h2>{{ page_title }}</h2>
            <p>{{ page_description }}</p>
        </div>
        
        <div class="content-area">
            {{ content }}
        </div>
    </div>
    
    <script>
        // Marcar item ativo no menu
        const currentPath = window.location.pathname;
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
            }
        });
    </script>
</body>
</html>
"""

# ============================================
# TEMPLATE PÁGINA DE PACIENTES
# ============================================

PACIENTES_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestão de Pacientes - intelliMed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            display: flex;
            min-height: 100vh;
        }
        
        /* MENU LATERAL (mesmo do dashboard) */
        .sidebar {
            width: 260px;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
            left: 0;
            top: 0;
            box-shadow: 4px 0 10px rgba(0,0,0,0.1);
        }
        
        .sidebar-header {
            padding: 30px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .sidebar-header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .sidebar-header p {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .user-info {
            padding: 20px;
            background: rgba(0,0,0,0.1);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .user-info strong {
            display: block;
            font-size: 14px;
            margin-bottom: 3px;
        }
        
        .user-info small {
            font-size: 12px;
            opacity: 0.7;
        }
        
        .menu {
            flex: 1;
            padding: 20px 0;
        }
        
        .menu-item {
            display: flex;
            align-items: center;
            padding: 14px 25px;
            color: white;
            text-decoration: none;
            transition: all 0.3s;
            font-size: 15px;
            border-left: 3px solid transparent;
        }
        
        .menu-item:hover {
            background: rgba(255,255,255,0.1);
            border-left-color: white;
        }
        
        .menu-item.active {
            background: rgba(255,255,255,0.15);
            border-left-color: white;
            font-weight: 600;
        }
        
        .menu-item-icon {
            width: 20px;
            margin-right: 12px;
            font-size: 18px;
        }
        
        .sidebar-footer {
            padding: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .btn-logout {
            display: block;
            width: 100%;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-logout:hover {
            background: rgba(0,0,0,0.3);
        }
        
        /* CONTEÚDO PRINCIPAL */
        .main-content {
            margin-left: 260px;
            flex: 1;
            padding: 30px;
            width: calc(100% - 260px);
        }
        
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        
        .page-title {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .page-title-icon {
            font-size: 36px;
        }
        
        .page-title h1 {
            font-size: 32px;
            color: #333;
        }
        
        .header-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn-secondary {
            background: white;
            color: #555;
            border: 2px solid #ddd;
        }
        
        .btn-secondary:hover {
            background: #f5f5f5;
            border-color: #ccc;
        }

        .count-indicator {
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            background-color: #e3f2fd;
            color: #1976d2;
            border: 2px solid #bbdefb;
            white-space: nowrap;
        }
        
        /* BUSCA */
        .search-box {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }
        
        .search-input {
            width: 100%;
            padding: 14px 20px 14px 45px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 15px;
            transition: all 0.3s;
            background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="%23999" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>');
            background-repeat: no-repeat;
            background-position: 15px center;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* LISTA DE PACIENTES */
        .pacientes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
        }
        
        .paciente-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: all 0.3s;
            border: 2px solid transparent;
            display: flex;
            flex-direction: column;
        }
        
        .paciente-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.12);
            border-color: #667eea;
        }
        
        .paciente-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .paciente-avatar {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            color: white;
            font-weight: 700;
        }
        
        .paciente-info {
            flex: 1;
        }
        
        .paciente-nome {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 4px;
        }
        
        .paciente-cpf {
            font-size: 13px;
            color: #999;
        }
        
        .paciente-detalhes {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .paciente-detalhe {
            font-size: 13px;
        }
        
        .paciente-detalhe strong {
            display: block;
            color: #666;
            margin-bottom: 3px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .paciente-detalhe span {
            color: #333;
            font-weight: 600;
        }
        
        .paciente-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: auto; /* Empurra os botões para o final do card */
            padding-top: 15px; /* Adiciona espaço acima dos botões */
        }
        
        .btn-action {
            flex: 1;
            min-width: 100px;
            padding: 8px 12px;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            font-weight: 500;
        }
        
        .btn-historico { background: #e3f2fd; color: #1976d2; }
        .btn-historico:hover { background: #1976d2; color: white; }
        .btn-exames { background: #fff3e0; color: #f57c00; }
        .btn-exames:hover { background: #f57c00; color: white; }
        .btn-visualizar { background: #e8f5e9; color: #388e3c; }
        .btn-visualizar:hover { background: #388e3c; color: white; }
        .btn-editar { background: #f3e5f5; color: #7b1fa2; }
        .btn-editar:hover { background: #7b1fa2; color: white; }
        .btn-deletar { background: #ffebee; color: #c62828; }
        .btn-deletar:hover { background: #c62828; color: white; }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
        
        /* ESTILOS DA PAGINAÇÃO */
        .pagination {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 30px;
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .pagination .btn {
            padding: 10px 20px;
        }
        .pagination .page-info {
            color: #666;
            font-size: 14px;
            font-weight: 500;
        }

        .alert-container {
            position: fixed; top: 20px; right: 20px; z-index: 1000;
        }
        .alert {
            padding: 15px 20px; border-radius: 8px; margin-bottom: 10px; font-size: 14px; min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .alert-error { background: #c62828; color: white; }
        .alert-success { background: #2e7d32; color: white; }
    </style>
</head>
<body>
    <!-- MENU LATERAL -->
    <div class="sidebar">
        <div class="sidebar-header">
            <h1>intelliMed</h1>
            <p>Gestão de Clínicas</p>
        </div>
        
        <div class="user-info">
            <strong>{{ user.nome_completo }}</strong>
            <small>{{ user.funcao_display }}</small>
        </div>
        
        <nav class="menu">
            <a href="/dashboard/" class="menu-item">
                <span class="menu-item-icon">🏠</span>
                <span>Home</span>
            </a>
            <a href="/pacientes/" class="menu-item active">
                <span class="menu-item-icon">👥</span>
                <span>Pacientes</span>
            </a>
            <a href="/agendamentos/" class="menu-item">
                <span class="menu-item-icon">📅</span>
                <span>Agendamentos</span>
            </a>
            <a href="/consultas/" class="menu-item">
                <span class="menu-item-icon">🩺</span>
                <span>Consultas</span>
            </a>
            <a href="/exames/" class="menu-item">
                <span class="menu-item-icon">🔬</span>
                <span>Exames IA</span>
            </a>
            <a href="/faturamento/" class="menu-item">
                <span class="menu-item-icon">💰</span>
                <span>Faturamento</span>
            </a>
            <a href="/informacoes/" class="menu-item">
                <span class="menu-item-icon">ℹ️</span>
                <span>Informações</span>
            </a>
        </nav>
        
        <div class="sidebar-footer">
            <a href="/logout/" class="btn-logout">
                ⬅️ Sair
            </a>
        </div>
    </div>
    
    <!-- CONTEÚDO PRINCIPAL -->
    <div class="main-content">
        <div class="page-header">
            <div class="page-title">
                <span class="page-title-icon">👥</span>
                <h1>Gestão de Pacientes</h1>
            </div>
            <div class="header-actions">
                <span class="count-indicator">Total: {{ pagination.count }}</span>
                <a href="/pacientes/inativos/" class="btn btn-secondary">🗑️ Ver Inativos</a>
                <button class="btn btn-secondary" onclick="location.reload()">🔄 Atualizar</button>
                <a href="/pacientes/novo/" class="btn btn-primary">➕ Novo Paciente</a>
            </div>
        </div>
        
        <div class="search-box">
            <input 
                type="text" 
                class="search-input" 
                placeholder="🔍 Buscar paciente (nome ou CPF)"
                id="searchInput"
                oninput="formatAndFilter(this)"
            >
        </div>
        
        <div class="pacientes-grid" id="pacientesGrid">
            {{ pacientes_html }}
        </div>

        <!-- SEÇÃO DE PAGINAÇÃO -->
        {% if pagination.total_pages > 1 %}
        <div class="pagination">
            {% if pagination.previous_url %}
                <a href="?page={{ pagination.current_page|add:"-1" }}" class="btn btn-secondary">&laquo; Anterior</a>
            {% else %}
                <span class="btn btn-secondary" style="opacity:0.5; cursor: not-allowed;">&laquo; Anterior</span>
            {% endif %}
            
            <span class="page-info">
                Página {{ pagination.current_page }} de {{ pagination.total_pages }}
            </span>

            {% if pagination.next_url %}
                <a href="?page={{ pagination.current_page|add:"1" }}" class="btn btn-secondary">Próxima &raquo;</a>
            {% else %}
                <span class="btn btn-secondary" style="opacity:0.5; cursor: not-allowed;">Próxima &raquo;</span>
            {% endif %}
        </div>
        {% endif %}
    </div>
    
    <div class="alert-container">
    {% if messages %}
        {% for message in messages %}
            <div class="alert alert-{{ message.tags }}">{{ message }}</div>
        {% endfor %}
    {% endif %}
    </div>
    
    <script>
        function formatAndFilter(input) {
            let originalValue = input.value;
            // Verifica se o usuário está tentando digitar um CPF (começa com número)
            if (/^\\d/.test(originalValue.replace(/[.-]/g, ''))) {
                let numbers = originalValue.replace(/\\D/g, '');
                if (numbers.length > 0) {
                    numbers = numbers.substring(0, 11);
                    let formatted = numbers;
                    if (numbers.length > 9) {
                        formatted = numbers.replace(/(\\d{3})(\\d{3})(\\d{3})(\\d{2})/, "$1.$2.$3-$4");
                    } else if (numbers.length > 6) {
                        formatted = numbers.replace(/(\\d{3})(\\d{3})(\\d{1,3})/, "$1.$2.$3");
                    } else if (numbers.length > 3) {
                        formatted = numbers.replace(/(\\d{3})(\\d{1,3})/, "$1.$2");
                    }
                    input.value = formatted;
                }
            }
            // Chama a função de filtro após qualquer alteração
            filtrarPacientes();
        }

        function filtrarPacientes() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const cards = document.querySelectorAll('.paciente-card');
            
            cards.forEach(card => {
                const nome = card.querySelector('.paciente-nome').textContent.toLowerCase();
                const cpf = card.querySelector('.paciente-cpf').textContent.toLowerCase();
                
                if (nome.includes(filter) || cpf.includes(filter)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        
        function confirmarDeletar(id, nome) {
            if (confirm(`Tem certeza que deseja arquivar o paciente ${nome}? Esta ação pode ser revertida.`)) {
                window.location.href = `/pacientes/${id}/deletar/`;
            }
        }

        // Fazer as mensagens desaparecerem após alguns segundos
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert-container .alert');
            alerts.forEach(alert => {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            });
        }, 5000);
    </script>
</body>
</html>
"""

# ============================================
# TEMPLATE FORMULÁRIO NOVO PACIENTE
# ============================================

NOVO_PACIENTE_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novo Paciente - intelliMed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            display: flex;
            min-height: 100vh;
        }
        
        /* SIDEBAR (mesmo das outras páginas) */
        .sidebar {
            width: 260px;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
            left: 0;
            top: 0;
            box-shadow: 4px 0 10px rgba(0,0,0,0.1);
        }
        
        .sidebar-header {
            padding: 30px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .sidebar-header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .sidebar-header p {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .user-info {
            padding: 20px;
            background: rgba(0,0,0,0.1);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .user-info strong {
            display: block;
            font-size: 14px;
            margin-bottom: 3px;
        }
        
        .user-info small {
            font-size: 12px;
            opacity: 0.7;
        }
        
        .menu {
            flex: 1;
            padding: 20px 0;
        }
        
        .menu-item {
            display: flex;
            align-items: center;
            padding: 14px 25px;
            color: white;
            text-decoration: none;
            transition: all 0.3s;
            font-size: 15px;
            border-left: 3px solid transparent;
        }
        
        .menu-item:hover {
            background: rgba(255,255,255,0.1);
            border-left-color: white;
        }
        
        .menu-item.active {
            background: rgba(255,255,255,0.15);
            border-left-color: white;
            font-weight: 600;
        }
        
        .menu-item-icon {
            width: 20px;
            margin-right: 12px;
            font-size: 18px;
        }
        
        .sidebar-footer {
            padding: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .btn-logout {
            display: block;
            width: 100%;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        /* CONTEÚDO */
        .main-content {
            margin-left: 260px;
            flex: 1;
            padding: 30px;
            width: calc(100% - 260px);
        }
        
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        
        .page-title {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .page-title-icon {
            font-size: 36px;
        }
        
        .page-title h1 {
            font-size: 32px;
            color: #333;
        }
        
        .form-container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            max-width: 900px;
        }
        
        .form-section {
            margin-bottom: 35px;
        }
        
        .form-section-title {
            font-size: 18px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        
        .form-grid-full {
            grid-column: 1 / -1;
        }
        
        .form-group {
            margin-bottom: 0;
        }
        
        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 14px;
        }
        
        .form-group label .required {
            color: #c62828;
            margin-left: 3px;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 15px;
            transition: all 0.3s;
        }
        
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .form-actions {
            display: flex;
            gap: 15px;
            justify-content: flex-end;
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid #f0f0f0;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn-secondary {
            background: #e0e0e0;
            color: #666;
        }
        
        .btn-secondary:hover {
            background: #d0d0d0;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .alert-error {
            background: #ffebee;
            color: #c62828;
            border: 1px solid #ffcdd2;
        }
        
        .alert-success {
            background: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #c8e6c9;
        }
    </style>
</head>
<body>
    <!-- SIDEBAR -->
    <div class="sidebar">
        <div class="sidebar-header">
            <h1>intelliMed</h1>
            <p>Gestão de Clínicas</p>
        </div>
        
        <div class="user-info">
            <strong>{{ user.nome_completo }}</strong>
            <small>{{ user.funcao_display }}</small>
        </div>
        
        <nav class="menu">
            <a href="/dashboard/" class="menu-item">
                <span class="menu-item-icon">🏠</span>
                <span>Home</span>
            </a>
            <a href="/pacientes/" class="menu-item active">
                <span class="menu-item-icon">👥</span>
                <span>Pacientes</span>
            </a>
            <a href="/agendamentos/" class="menu-item">
                <span class="menu-item-icon">📅</span>
                <span>Agendamentos</span>
            </a>
            <a href="/consultas/" class="menu-item">
                <span class="menu-item-icon">🩺</span>
                <span>Consultas</span>
            </a>
            <a href="/exames/" class="menu-item">
                <span class="menu-item-icon">🔬</span>
                <span>Exames IA</span>
            </a>
            <a href="/faturamento/" class="menu-item">
                <span class="menu-item-icon">💰</span>
                <span>Faturamento</span>
            </a>
            <a href="/informacoes/" class="menu-item">
                <span class="menu-item-icon">ℹ️</span>
                <span>Informações</span>
            </a>
        </nav>
        
        <div class="sidebar-footer">
            <a href="/logout/" class="btn-logout">
                ⬅️ Sair
            </a>
        </div>
    </div>
    
    <!-- CONTEÚDO -->
    <div class="main-content">
        <div class="page-header">
            <div class="page-title">
                <span class="page-title-icon">➕</span>
                <h1>Novo Paciente</h1>
            </div>
        </div>
        
        <div class="form-container">
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-{{ message.tags }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
            
            <form method="POST" action="/pacientes/novo/">
                {% csrf_token %}
                
                <!-- DADOS PESSOAIS -->
                <div class="form-section">
                    <h2 class="form-section-title">📋 Dados Pessoais</h2>
                    <div class="form-grid">
                        <div class="form-group form-grid-full">
                            <label>Nome Completo <span class="required">*</span></label>
                            <input type="text" name="nome_completo" required>
                        </div>
                        
                        <div class="form-group">
                            <label>CPF <span class="required">*</span></label>
                            <input type="text" name="cpf" required placeholder="000.000.000-00" maxlength="14">
                        </div>
                        
                        <div class="form-group">
                            <label>Data de Nascimento <span class="required">*</span></label>
                            <input type="date" name="data_nascimento" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Sexo <span class="required">*</span></label>
                            <select name="sexo" required>
                                <option value="">Selecione</option>
                                <option value="M">Masculino</option>
                                <option value="F">Feminino</option>
                                <option value="O">Outro</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Convênio <span class="required">*</span></label>
                            <select name="convenio" required>
                                <option value="">Selecione um convênio</option>
                                <option value="PARTICULAR">Particular</option>
                                <option value="SUS">SUS</option>
                                <option value="UNIMED">Unimed</option>
                                <option value="BRADESCO SAUDE">Bradesco Saúde</option>
                                <option value="SULAMERICA">SulAmérica</option>
                                <option value="AMIL">Amil</option>
                                <option value="HAPVIDA">Hapvida</option>
                                <option value="NOTREDAME INTERMEDICA">NotreDame Intermédica</option>
                                <option value="PREVENT SENIOR">Prevent Senior</option>
                                <option value="OUTRO">Outro</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Profissão</label>
                            <input type="text" name="profissao">
                        </div>
                    </div>
                </div>
                
                <!-- CONTATO -->
                <div class="form-section">
                    <h2 class="form-section-title">📞 Dados de Contato</h2>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Telefone Celular <span class="required">*</span></label>
                            <input type="text" name="telefone_celular" required placeholder="(00) 00000-0000" maxlength="15">
                        </div>
                        
                        <div class="form-group">
                            <label>Telefone Fixo</label>
                            <input type="text" name="telefone_fixo" placeholder="(00) 0000-0000" maxlength="14">
                        </div>
                        
                        <div class="form-group form-grid-full">
                            <label>E-mail</label>
                            <input type="email" name="email">
                        </div>
                    </div>
                </div>
                
                <!-- ENDEREÇO -->
                <div class="form-section">
                    <h2 class="form-section-title">📍 Endereço</h2>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>CEP</label>
                            <input type="text" name="cep" placeholder="00000-000" maxlength="9">
                        </div>
                        
                        <div class="form-group form-grid-full">
                            <label>Logradouro</label>
                            <input type="text" name="logradouro" placeholder="Rua, Avenida, etc">
                        </div>
                        
                        <div class="form-group">
                            <label>Número</label>
                            <input type="text" name="numero">
                        </div>
                        
                        <div class="form-group">
                            <label>Bairro</label>
                            <input type="text" name="bairro">
                        </div>
                        
                        <div class="form-group">
                            <label>Cidade</label>
                            <input type="text" name="cidade">
                        </div>
                        
                        <div class="form-group">
                            <label>UF</label>
                            <select name="estado">
                                <option value="">Selecione</option>
                                <option value="AC">AC</option>
                                <option value="AL">AL</option>
                                <option value="AP">AP</option>
                                <option value="AM">AM</option>
                                <option value="BA">BA</option>
                                <option value="CE">CE</option>
                                <option value="DF">DF</option>
                                <option value="ES">ES</option>
                                <option value="GO">GO</option>
                                <option value="MA">MA</option>
                                <option value="MT">MT</option>
                                <option value="MS">MS</option>
                                <option value="MG">MG</option>
                                <option value="PA">PA</option>
                                <option value="PB">PB</option>
                                <option value="PR">PR</option>
                                <option value="PE">PE</option>
                                <option value="PI">PI</option>
                                <option value="RJ">RJ</option>
                                <option value="RN">RN</option>
                                <option value="RS">RS</option>
                                <option value="RO">RO</option>
                                <option value="RR">RR</option>
                                <option value="SC">SC</option>
                                <option value="SP">SP</option>
                                <option value="SE">SE</option>
                                <option value="TO">TO</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="form-actions">
                    <a href="/pacientes/" class="btn btn-secondary">Cancelar</a>
                    <button type="submit" class="btn btn-primary">💾 Salvar Paciente</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        // Máscaras de input
        document.querySelector('[name="cpf"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            e.target.value = value;
        });
        
        document.querySelector('[name="telefone_celular"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/^(\d{2})(\d)/g, '($1) $2');
            value = value.replace(/(\d)(\d{4})$/, '$1-$2');
            e.target.value = value;
        });
        
        document.querySelector('[name="telefone_fixo"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/^(\d{2})(\d)/g, '($1) $2');
            value = value.replace(/(\d)(\d{4})$/, '$1-$2');
            e.target.value = value;
        });
        
        document.querySelector('[name="cep"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/^(\d{5})(\d)/, '$1-$2');
            e.target.value = value;
        });
    </script>
</body>
</html>
"""

# ============================================
# TEMPLATE VISUALIZAR PACIENTE
# ============================================

PACIENTE_VISUALIZAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detalhes do Paciente - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; }
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; transition: all 0.3s; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; width: calc(100% - 260px); }
        .page-header { margin-bottom: 30px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .details-container { background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .section-title { font-size: 18px; font-weight: 600; color: #667eea; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; }
        .info-grid { display: grid; grid-template-columns: 200px 1fr; gap: 15px; margin-bottom: 25px; }
        .info-grid .label { font-weight: 600; color: #666; }
        .info-grid .value { color: #333; }
        .btn-secondary { padding: 12px 30px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; background: #e0e0e0; color: #666; text-decoration: none; display: inline-block; margin-top: 20px; }
        .list-group { list-style: none; padding: 0; }
        .list-group-item { background: #f9f9f9; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span><span>Home</span></a>
            <a href="/pacientes/" class="menu-item active"><span class="menu-item-icon">👥</span><span>Pacientes</span></a>
        </nav>
    </div>
    <div class="main-content">
        <div class="page-header"><div class="page-title"><h1>{{ paciente.nome_completo }}</h1></div></div>
        <div class="details-container">
            <div class="form-section">
                <h2 class="section-title">📋 Dados Pessoais</h2>
                <div class="info-grid">
                    <div class="label">CPF:</div><div class="value">{{ paciente.cpf }}</div>
                    <div class="label">Data de Nascimento:</div><div class="value">{{ paciente.data_nascimento }} ({{ paciente.idade }} anos)</div>
                    <div class="label">Sexo:</div><div class="value">{{ paciente.sexo_display }}</div>
                    <div class="label">Convênio:</div><div class="value">{{ paciente.convenio_display }}</div>
                    <div class="label">Profissão:</div><div class="value">{{ paciente.profissao }}</div>
                </div>
            </div>
            <div class="form-section">
                <h2 class="section-title">📞 Contato</h2>
                <div class="info-grid">
                    <div class="label">Celular:</div><div class="value">{{ paciente.telefone_celular }}</div>
                    <div class="label">E-mail:</div><div class="value">{{ paciente.email }}</div>
                </div>
            </div>
            <div class="form-section">
                <h2 class="section-title">📍 Endereço</h2>
                <div class="value">{{ paciente.endereco_completo }}</div>
            </div>
            <div class="form-section">
                <h2 class="section-title">🕐 Histórico Recente de Consultas ({{ total_consultas }})</h2>
                {% if consultas %}
                    <ul class="list-group">
                    {% for consulta in consultas %}
                        <li class="list-group-item">{{ consulta.data_consulta }} - {{ consulta.tipo_consulta }} - Status: {{ consulta.status_display }}</li>
                    {% endfor %}
                    </ul>
                {% else %}
                    <p>Nenhuma consulta encontrada.</p>
                {% endif %}
            </div>
            <div class="form-section">
                <h2 class="section-title">🔬 Histórico Recente de Exames ({{ total_exames }})</h2>
                 {% if exames %}
                    <ul class="list-group">
                    {% for exame in exames %}
                        <li class="list-group-item">{{ exame.data_exame }} - {{ exame.tipo_exame_display }} - Status: {{ exame.status_display }}</li>
                    {% endfor %}
                    </ul>
                {% else %}
                    <p>Nenhum exame encontrado.</p>
                {% endif %}
            </div>
            <a href="/pacientes/" class="btn-secondary">Voltar</a>
        </div>
    </div>
</body>
</html>
"""

# ============================================
# TEMPLATE EDITAR PACIENTE
# ============================================

EDITAR_PACIENTE_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Paciente - intelliMed</title>
    <!-- Estilos são os mesmos do formulário de novo paciente -->
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; min-height: 100vh; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; display: flex; flex-direction: column; position: fixed; height: 100vh; left: 0; top: 0; box-shadow: 4px 0 10px rgba(0,0,0,0.1); }
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; width: calc(100% - 260px); }
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 30px;}
        .form-container { background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 900px; }
        .form-section-title { font-size: 18px; font-weight: 600; color: #667eea; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; }
        .form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .form-grid-full { grid-column: 1 / -1; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-weight: 600; margin-bottom: 8px; color: #333; font-size: 14px; }
        .form-group label .required { color: #c62828; margin-left: 3px; }
        .form-group input, .form-group select { width: 100%; padding: 12px 15px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; }
        .form-group input:read-only { background: #f5f5f5; color: #999; cursor: not-allowed; }
        .form-actions { display: flex; gap: 15px; justify-content: flex-end; margin-top: 30px; padding-top: 30px; border-top: 2px solid #f0f0f0; }
        .btn { padding: 12px 30px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; text-decoration: none; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-secondary { background: #e0e0e0; color: #666; }
        .alert { padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }
        .alert-error { background: #ffebee; color: #c62828; }
    </style>
</head>
<body>
    <div class="sidebar"> <!-- Conteúdo do Sidebar --> </div>
    <div class="main-content">
        <div class="page-header"><h1>✏️ Editar Paciente</h1></div>
        <div class="form-container">
            {% if messages %}{% for message in messages %}<div class="alert alert-error">{{ message }}</div>{% endfor %}{% endif %}
            <form method="POST">
                {% csrf_token %}

                <!-- ****** CORREÇÃO: ADICIONAR CAMPOS OCULTOS ****** -->
                <input type="hidden" name="clinica_id" value="{{ paciente.clinica_id }}">

                <h2 class="form-section-title">📋 Dados Pessoais</h2>
                <div class="form-grid">
                    <div class="form-group form-grid-full">
                        <label>Nome Completo <span class="required">*</span></label>
                        <input type="text" name="nome_completo" value="{{ paciente.nome_completo }}" required>
                    </div>
                    <div class="form-group">
                        <label>CPF (não pode ser alterado)</label>
                        <!-- ****** CORREÇÃO: MUDAR DE disabled PARA readonly ****** -->
                        <input type="text" name="cpf" value="{{ paciente.cpf }}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Data de Nascimento <span class="required">*</span></label>
                        <input type="date" name="data_nascimento" value="{{ paciente.data_nascimento }}" required>
                    </div>
                    <div class="form-group">
                        <label>Sexo <span class="required">*</span></label>
                        <select name="sexo" required>
                            <option value="M" {% if paciente.sexo == 'M' %}selected{% endif %}>Masculino</option>
                            <option value="F" {% if paciente.sexo == 'F' %}selected{% endif %}>Feminino</option>
                            <option value="O" {% if paciente.sexo == 'O' %}selected{% endif %}>Outro</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Convênio <span class="required">*</span></label>
                        <select name="convenio" required>
                            <option value="PARTICULAR" {% if paciente.convenio == 'PARTICULAR' %}selected{% endif %}>Particular</option>
                            <option value="SUS" {% if paciente.convenio == 'SUS' %}selected{% endif %}>SUS</option>
                            <option value="UNIMED" {% if paciente.convenio == 'UNIMED' %}selected{% endif %}>Unimed</option>
                            <option value="BRADESCO SAUDE" {% if paciente.convenio == 'BRADESCO SAUDE' %}selected{% endif %}>Bradesco Saúde</option>
                            <option value="SULAMERICA" {% if paciente.convenio == 'SULAMERICA' %}selected{% endif %}>SulAmérica</option>
                            <option value="AMIL" {% if paciente.convenio == 'AMIL' %}selected{% endif %}>Amil</option>
                            <option value="HAPVIDA" {% if paciente.convenio == 'HAPVIDA' %}selected{% endif %}>Hapvida</option>
                            <option value="NOTREDAME INTERMEDICA" {% if paciente.convenio == 'NOTREDAME INTERMEDICA' %}selected{% endif %}>NotreDame Intermédica</option>
                            <option value="PREVENT SENIOR" {% if paciente.convenio == 'PREVENT SENIOR' %}selected{% endif %}>Prevent Senior</option>
                            <option value="OUTRO" {% if paciente.convenio == 'OUTRO' %}selected{% endif %}>Outro</option>
                        </select>
                    </div>
                    <div class="form-group form-grid-full">
                        <label>Profissão</label>
                        <input type="text" name="profissao" value="{{ paciente.profissao }}">
                    </div>
                </div>

                <h2 class="form-section-title" style="margin-top:20px;">📞 Dados de Contato</h2>
                <div class="form-grid">
                    <div class="form-group">
                        <label>Telefone Celular <span class="required">*</span></label>
                        <input type="text" name="telefone_celular" value="{{ paciente.telefone_celular }}" required>
                    </div>
                    <div class="form-group">
                        <label>Telefone Fixo</label>
                        <input type="text" name="telefone_fixo" value="{{ paciente.telefone_fixo }}">
                    </div>
                    <div class="form-group form-grid-full">
                        <label>E-mail</label>
                        <input type="email" name="email" value="{{ paciente.email }}">
                    </div>
                </div>

                <h2 class="form-section-title" style="margin-top:20px;">📍 Endereço</h2>
                <div class="form-grid">
                    <div class="form-group">
                        <label>CEP</label>
                        <input type="text" name="cep" value="{{ paciente.cep }}">
                    </div>
                    <div class="form-group form-grid-full">
                        <label>Logradouro</label>
                        <input type="text" name="logradouro" value="{{ paciente.logradouro }}">
                    </div>
                    <div class="form-group">
                        <label>Número</label>
                        <input type="text" name="numero" value="{{ paciente.numero }}">
                    </div>
                    <div class="form-group">
                        <label>Complemento</label>
                        <input type="text" name="complemento" value="{{ paciente.complemento }}">
                    </div>
                    <div class="form-group">
                        <label>Bairro</label>
                        <input type="text" name="bairro" value="{{ paciente.bairro }}">
                    </div>
                    <div class="form-group">
                        <label>Cidade</label>
                        <input type="text" name="cidade" value="{{ paciente.cidade }}">
                    </div>
                    <div class="form-group">
                        <label>UF</label>
                        <input type="text" name="estado" value="{{ paciente.estado }}" maxlength="2">
                    </div>
                </div>

                <div class="form-actions">
                    <a href="/pacientes/" class="btn btn-secondary">Cancelar</a>
                    <button type="submit" class="btn btn-primary">💾 Salvar Alterações</button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
"""

INATIVOS_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <title>Pacientes Inativos - intelliMed</title>
    <!-- Estilos omitidos para brevidade, são os mesmos da página de pacientes -->
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; }
        /* ... outros estilos ... */
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .table-container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #f0f0f0; }
        th { font-weight: 600; color: #666; }
        .btn { padding: 8px 16px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; text-decoration: none; }
        .btn-success { background: #e8f5e9; color: #2e7d32; }
        .btn-secondary { background: #f5f5f5; color: #666; }
    </style>
</head>
<body>
    <div class="sidebar"> <!-- Coloque seu sidebar aqui --> </div>
    <div class="main-content">
        <div class="page-header">
            <div class="page-title"><h1>🗑️ Pacientes Inativos (Arquivados)</h1></div>
            <a href="/pacientes/" class="btn btn-secondary">Voltar para Pacientes Ativos</a>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Nome Completo</th>
                        <th>CPF</th>
                        <th>Data de Nascimento</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
                    {% if inativos %}
                        {% for paciente in inativos %}
                        <tr>
                            <td>{{ paciente.nome_completo }}</td>
                            <td>{{ paciente.cpf }}</td>
                            <td>{{ paciente.data_nascimento }}</td>
                            <td>
                                <form method="POST" action="/pacientes/{{ paciente.id }}/reativar/" style="display:inline;">
                                    {% csrf_token %}
                                    <button type="submit" class="btn btn-success">Reativar</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr><td colspan="4" style="text-align:center; padding: 40px;">Nenhum paciente inativo encontrado.</td></tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# ============================================
# TEMPLATES PARA AGENDAMENTOS
# ============================================

AGENDAMENTOS_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Gestão de Agendamentos - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; margin: 0; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; margin: 0; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item:hover { background: rgba(255,255,255,0.1); }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; border: none; cursor: pointer; box-sizing: border-box; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .header-actions, .filter-bar { display: flex; gap: 10px; align-items: center; }
        .filter-bar { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .filter-bar input, .filter-bar select { padding: 10px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        .btn { padding: 10px 20px; border-radius: 8px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; }
        .btn-primary { background: #667eea; color: white; }
        .btn-danger { background: #c62828; color: white; }
        .btn-secondary { background: white; color: #555; border: 2px solid #ddd; }
        .agendamentos-list { display: flex; flex-direction: column; gap: 15px; }
        .agendamento-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 20px; }
        .agendamento-card-data { text-align: center; padding-right: 20px; border-right: 1px solid #f0f0f0; }
        .agendamento-card-data .dia { font-size: 28px; font-weight: 700; color: #667eea; }
        .agendamento-card-data .mes { font-size: 14px; color: #666; text-transform: uppercase; }
        .agendamento-card-info { flex-grow: 1; }
        .agendamento-card-info strong { font-size: 18px; color: #333; display: block; margin-bottom: 2px; }
        .agendamento-card-info p { font-size: 14px; color: #777; margin: 0; }
        .agendamento-card-info .convenio-info { font-size: 12px; color: #555; margin-top: 5px; }
        .status-select { border: none; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: 700; cursor: pointer; -webkit-appearance: none; -moz-appearance: none; appearance: none; }
        .status-Agendado { background: #e3f2fd; color: #1565c0; }
        .status-Confirmado { background: #e8f5e9; color: #2e7d32; }
        .status-Realizado { background: #ede7f6; color: #4527a0; }
        .status-Cancelado { background: #ffebee; color: #c62828; }
        .status-Faltou { background: #fffde7; color: #f9a825; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span>🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span>👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item active"><span>📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span>🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span>🔬</span> <span>Exames IA</span></a>
            <a href="/faturamento/" class="menu-item"><span>💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span>ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer"><a href="/logout/" class="btn-logout">Sair</a></div>
    </div>
    <div class="main-content">
        <div class="page-header">
            <div class="page-title"><h1>📅 Gestão de Agendamentos</h1></div>
            <div class="header-actions">
                <button onclick="location.reload()" class="btn btn-secondary">🔄 Atualizar</button>
                <a href="/agendamentos/novo/" class="btn btn-primary">➕ Novo Agendamento</a>
            </div>
        </div>
        <div class="filter-bar">
            <span>Filtrar por:</span>
            <input type="date" id="filter-data" onchange="applyFilters()" value="{{ filter_date }}">
            <select id="filter-periodo" onchange="applyFilters()">
                <option value="dia" {% if filter_periodo == 'dia' %}selected{% endif %}>Ver Dia</option>
                <option value="semana" {% if filter_periodo == 'semana' %}selected{% endif %}>Ver Semana</option>
                <option value="mes" {% if filter_periodo == 'mes' %}selected{% endif %}>Ver Mês</option>
            </select>
            <input type="text" id="search-paciente" placeholder="Buscar por paciente..." onkeyup="applyFilters()" value="{{ search_term }}">
        </div>
        <div class="agendamentos-list">
            {{ agendamentos_html }}
        </div>
    </div>
    <script>
        function applyFilters() {
            const data = document.getElementById('filter-data').value;
            const periodo = document.getElementById('filter-periodo').value;
            const search = document.getElementById('search-paciente').value;
            window.location.href = `/agendamentos/?data=${data}&periodo=${periodo}&search=${search}`;
        }
        
        function updateStatus(agendamentoId, selectElement) {
            const novoStatus = selectElement.value;
            const jwtToken = "{{ token }}";
            const csrfToken = "{{ csrf_token }}";
            const backendUrl = "{{ backend_url }}";
            
            const url = `${backendUrl}/api/agendamentos/${agendamentoId}/alterar_status/`;

            fetch(url, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'Authorization': `Bearer ${jwtToken}`
                },
                body: JSON.stringify({ status: novoStatus })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.detail || 'Erro do servidor') });
                }
                return response.json();
            })
            .then(data => {
                if (data.id) {
                    selectElement.className = `status-select status-${data.status}`;
                } else {
                    throw new Error('Resposta inválida do servidor.');
                }
            })
            .catch(error => {
                alert(`Erro ao atualizar status: ${error.message}`);
                location.reload();
            });
        }
    </script>
</body>
</html>
"""

# ============================================
# TEMPLATE FORMULÁRIO AGENDAMENTO (CORRIGIDO)
# ============================================
# No frontend.py

AGENDAMENTO_FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ form_title }} - intelliMed</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; margin: 0; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; margin: 0; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .form-container { max-width: 800px; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; font-weight: 600; margin-bottom: 8px; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; }
        .form-actions { display: flex; justify-content: flex-end; gap: 15px; margin-top: 20px; }
        .btn { padding: 12px 30px; border-radius: 8px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #e0e0e0; color: #666; }
    </style>
</head>
<body>
    <div class="sidebar"> <!-- Seu menu lateral aqui --> </div>
    <div class="main-content">
        <h1>{{ form_title }}</h1>
        <div class="form-container">
            <form method="POST">
                {% csrf_token %}
                <div class="form-group">
                    <label>Paciente <span style="color:red;">*</span></label>
                    <select name="paciente" required>
                        <option value="">Selecione um paciente</option>
                        {% for p in pacientes %}
                        <option value="{{ p.id }}" {% if p.id == agendamento.paciente %}selected{% endif %}>{{ p.nome_completo }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-grid">
                    <div class="form-group">
                        <label>Serviço <span style="color:red;">*</span></label>
                        <select name="servico" required>
                            <option value="">Selecione...</option>
                            <option value="Consulta|Primeira Consulta" {% if agendamento.servico == 'Consulta' and agendamento.tipo == 'Primeira Consulta' %}selected{% endif %}>Primeira Consulta</option>
                            <option value="Consulta|Revisão" {% if agendamento.servico == 'Consulta' and agendamento.tipo == 'Revisão' %}selected{% endif %}>Retorno / Revisão</option>
                            <option value="Exame|Exame" {% if agendamento.servico == 'Exame' %}selected{% endif %}>Exame</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Convênio <span style="color:red;">*</span></label>
                        <select name="convenio" required>
                            <option value="">Selecione o convênio</option>
                            <option value="PARTICULAR" {% if agendamento.convenio == 'PARTICULAR' %}selected{% endif %}>Particular</option>
                            <option value="SUS" {% if agendamento.convenio == 'SUS' %}selected{% endif %}>SUS</option>
                            <option value="UNIMED" {% if agendamento.convenio == 'UNIMED' %}selected{% endif %}>Unimed</option>
                            <option value="BRADESCO SAUDE" {% if agendamento.convenio == 'BRADESCO SAUDE' %}selected{% endif %}>Bradesco Saúde</option>
                            <option value="SULAMERICA" {% if agendamento.convenio == 'SULAMERICA' %}selected{% endif %}>SulAmérica</option>
                            <option value="AMIL" {% if agendamento.convenio == 'AMIL' %}selected{% endif %}>Amil</option>
                            <option value="HAPVIDA" {% if agendamento.convenio == 'HAPVIDA' %}selected{% endif %}>Hapvida</option>
                            <option value="NOTREDAME INTERMEDICA" {% if agendamento.convenio == 'NOTREDAME INTERMEDICA' %}selected{% endif %}>NotreDame Intermédica</option>
                            <option value="PREVENT SENIOR" {% if agendamento.convenio == 'PREVENT SENIOR' %}selected{% endif %}>Prevent Senior</option>
                            <option value="OUTRO" {% if agendamento.convenio == 'OUTRO' %}selected{% endif %}>Outro</option>
                        </select>
                    </div>
                </div>
                <div class="form-grid">
                    <div class="form-group">
                        <label>Data <span style="color:red;">*</span></label>
                        <input type="date" name="data" value="{{ agendamento.data }}" required>
                    </div>
                    <div class="form-group">
                        <label>Horário <span style="color:red;">*</span></label>
                        <input type="time" name="hora" value="{{ agendamento.hora }}" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Valor (R$)</label>
                    <input type="number" step="0.01" name="valor" value="{{ agendamento.valor }}">
                </div>
                <div class="form-group">
                    <label>Observações</label>
                    <textarea name="observacoes" rows="4">{{ agendamento.observacoes }}</textarea>
                </div>
                <div class="form-actions">
                    <a href="/agendamentos/" class="btn btn-secondary">Cancelar</a>
                    <button type="submit" class="btn btn-primary">Salvar</button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
"""
# ============================================
# TEMPLATES PLACEHOLDER
# ============================================

PLACEHOLDER_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ page_title }} - intelliMed</title>
    <!-- Estilos omitidos para brevidade -->
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .content-area { background: white; padding: 40px; border-radius: 12px; text-align: center; color: #999; }
        .content-area h1 { font-size: 24px; color: #333; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="sidebar"><!-- Sidebar --></div>
    <div class="main-content">
        <div class="content-area">
            <h1>🚧 {{ page_title }} 🚧</h1>
            <p>Esta página está em desenvolvimento.</p>
            <br>
            <a href="/pacientes/">Voltar para Pacientes</a>
        </div>
    </div>
</body>
</html>
"""

# ============================================
# VIEWS
# ============================================

def login_view(request):
    """Página de login"""
    
    # Se já está logado, redireciona para dashboard
    if request.session.get('token'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        # Chamar API de login do backend
        try:
            print(f"\n🔍 DEBUG: Tentando login em {Config.BACKEND_URL}/login")
            print(f"📧 Email: {email}")
            
            response = requests.post(
                f'{Config.BACKEND_URL}/login',
                json={'email': email, 'password': password},
                timeout=10
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response Text: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Salvar token e informações do usuário na sessão
                request.session['token'] = data['access_token']
                request.session['user'] = data['user_info']
                
                # Se marcou "lembrar", estende a sessão
                if remember:
                    request.session.set_expiry(2592000)  # 30 dias
                else:
                    request.session.set_expiry(86400)  # 24 horas
                
                messages.success(request, f'Bem-vindo, {data["user_info"]["nome_completo"]}!')
                return redirect('dashboard')
            else:
                try:
                    error_data = response.json()
                    messages.error(request, error_data.get('mensagem', 'Email ou senha incorretos'))
                except:
                    messages.error(request, 'Erro ao processar resposta do servidor')
        
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Erro: Não foi possível conectar ao servidor backend')
            print("❌ ConnectionError: Backend não está acessível")
        except requests.exceptions.Timeout:
            messages.error(request, 'Erro: Tempo de conexão esgotado')
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')
            print(f"❌ Exception: {e}")
    
    # Renderizar template (SEMPRE retorna HttpResponse)
    from django.template import Template, RequestContext
    
    template = Template(LOGIN_TEMPLATE)
    context = RequestContext(request, {
        'messages': messages.get_messages(request),
        'debug': Config.DEBUG,
        'email_saved': '',
        'remember_checked': ''
    })
    
    return HttpResponse(template.render(context))

def logout_view(request):
    """Logout - limpa sessão"""
    request.session.flush()
    messages.success(request, 'Logout realizado com sucesso')
    return redirect('login')

def dashboard_view(request):
    """Dashboard principal"""
    
    # Verificar se está logado
    if not request.session.get('token'):
        return redirect('login')
    
    user = request.session.get('user', {})
    
    # Traduzir função para português
    funcoes_pt = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'medico': 'Médico',
        'secretaria': 'Secretária'
    }
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    
    # Conteúdo da página (vazio por enquanto)
    content_html = """
        <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <h3>Dashboard em Desenvolvimento</h3>
            <p>Em breve você terá acesso a estatísticas e indicadores da sua clínica.</p>
        </div>
    """
    
    # Renderizar template
    from django.template import Template, Context
    
    template = Template(DASHBOARD_TEMPLATE)
    context = Context({
        'user': user,
        'page_title': 'Dashboard',
        'page_description': 'Visão geral da sua clínica',
        'content': content_html
    })
    
    return HttpResponse(template.render(context))

def pacientes_view(request):
    """Página de gestão de pacientes com paginação."""
    
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    user = request.session.get('user', {})
    
    # Traduzir função para português
    funcoes_pt = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'medico': 'Médico',
        'secretaria': 'Secretária'
    }
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))

    # Pega o número da página da URL, o padrão é 1
    page = request.GET.get('page', '1')
    
    html_parts = []
    pagination = {}
    
    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/',
            headers={'Authorization': f'Bearer {token}'},
            params={'page': page}, # Envia o número da página para a API
            timeout=10
        )
        response.raise_for_status() # Lança erro para status 4xx/5xx
        
        data = response.json()
        pacientes = data.get('results', [])
        
        # Lógica de Paginação
        count = data.get('count', 0)
        page_size = 20 # O mesmo valor que você definiu no PAGE_SIZE do backend
        total_pages = (count + page_size - 1) // page_size if page_size > 0 else 1

        pagination = {
            'next_url': data.get('next'),
            'previous_url': data.get('previous'),
            'count': count,
            'current_page': int(page),
            'total_pages': total_pages
        }

        if pacientes:
            for paciente in pacientes:
                nome_partes = paciente.get('nome_completo', '').split()
                iniciais = (nome_partes[0][0] + (nome_partes[-1][0] if len(nome_partes) > 1 else '')).upper()
                
                idade = '-'
                if paciente.get('data_nascimento'):
                    try:
                        data_nasc = datetime.strptime(paciente['data_nascimento'], '%Y-%m-%d')
                        idade = (datetime.now() - data_nasc).days // 365
                    except (ValueError, TypeError):
                        idade = '-'

                html_parts.append(f"""
                <div class="paciente-card">
                    <div class="paciente-header">
                        <div class="paciente-avatar">{iniciais}</div>
                        <div class="paciente-info">
                            <div class="paciente-nome">{paciente.get('nome_completo', 'N/A')}</div>
                            <div class="paciente-cpf">CPF: {paciente.get('cpf', 'N/A')}</div>
                        </div>
                    </div>
                    
                    <div class="paciente-detalhes">
                        <div class="paciente-detalhe">
                            <strong>Idade</strong>
                            <span>{idade} anos</span>
                        </div>
                        <div class="paciente-detalhe">
                            <strong>Convênio</strong>
                            <span>{paciente.get('convenio', 'N/A')}</span>
                        </div>
                        <div class="paciente-detalhe">
                            <strong>Telefone</strong>
                            <span>{paciente.get('telefone_celular', 'N/A')}</span>
                        </div>
                        <div class="paciente-detalhe">
                            <strong>Cidade</strong>
                            <span>{paciente.get('cidade', 'N/A')}/{paciente.get('estado', 'N/A')}</span>
                        </div>
                    </div>
                    
                    <div class="paciente-actions">
                        <a href="/pacientes/{paciente['id']}/historico/" class="btn-action btn-historico">🕐 Histórico</a>
                        
                        <!-- ****** CORREÇÃO AQUI ****** -->
                        <a href="/pacientes/{paciente['id']}/exames/" class="btn-action btn-exames">🔬 Exames</a>

                        <a href="/pacientes/{paciente['id']}/visualizar/" class="btn-action btn-visualizar">👁️ Ver</a>
                        <a href="/pacientes/{paciente['id']}/editar/" class="btn-action btn-editar">✏️ Editar</a>
                        <button onclick="confirmarDeletar({paciente['id']}, '{paciente['nome_completo']}')" class="btn-action btn-deletar">🗑️ Arquivar</button>
                    </div>
                </div>
                """)
        else:
            # Se não houver pacientes na página atual (mas pode haver em outras)
            if pagination.get('count', 0) > 0:
                 html_parts.append("""<p style="grid-column: 1/-1;">Não há pacientes nesta página.</p>""")
            else:
                html_parts.append("""
                <div style="grid-column: 1/-1;">
                    <div class="empty-state">
                        <div class="empty-state-icon">👥</div>
                        <h3>Nenhum paciente cadastrado</h3>
                        <p>Clique em "Novo Paciente" para cadastrar o primeiro.</p>
                    </div>
                </div>
                """)
            
    except Exception as e:
        messages.error(request, f"Erro ao carregar pacientes: {e}")
        html_parts.append(f"""
        <div style="grid-column: 1/-1;" class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <h3>Erro ao conectar com o servidor</h3>
            <p>Verifique se o backend está rodando e tente novamente.</p>
        </div>
        """)

    pacientes_html = "".join(html_parts)
    
    from django.template import Template, RequestContext
    from django.utils.safestring import mark_safe
    
    template = Template(PACIENTES_TEMPLATE)
    context = RequestContext(request, {
        'user': user,
        'pacientes_html': mark_safe(pacientes_html),
        'pagination': pagination
    })
    
    return HttpResponse(template.render(context))

def novo_paciente_view(request):
    """Formulário de cadastro de novo paciente"""
    
    # Verificar se está logado
    if not request.session.get('token'):
        return redirect('login')
    
    user = request.session.get('user', {})
    token = request.session.get('token')
    
    # Traduzir função
    funcoes_pt = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'medico': 'Médico',
        'secretaria': 'Secretária'
    }
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    
    if request.method == 'POST':
        # Coletar dados do formulário
        clinica_id = user.get('clinica_id')
        
        # Se for super_admin sem clínica, mostrar erro
        if not clinica_id and user.get('funcao') != 'super_admin':
            messages.error(request, 'Erro: Usuário sem clínica vinculada')
            return redirect('pacientes')
        
        dados_paciente = {
            'nome_completo': request.POST.get('nome_completo'),
            'cpf': request.POST.get('cpf').replace('.', '').replace('-', ''),  # Remover formatação
            'data_nascimento': request.POST.get('data_nascimento'),
            'sexo': request.POST.get('sexo'),  # ← ADICIONAR
            'convenio': request.POST.get('convenio') or '',
            'profissao': request.POST.get('profissao', ''),
            'telefone_celular': request.POST.get('telefone_celular'),
            'telefone_fixo': request.POST.get('telefone_fixo', ''),
            'email': request.POST.get('email', ''),
            'cep': request.POST.get('cep', ''),
            'logradouro': request.POST.get('logradouro', ''),
            'numero': request.POST.get('numero', ''),
            'bairro': request.POST.get('bairro', ''),
            'cidade': request.POST.get('cidade', ''),
            'estado': request.POST.get('estado', ''),
        }
        
        # Adicionar clinica_id apenas se não for super_admin
        if clinica_id:
            dados_paciente['clinica_id'] = clinica_id
        
        # Enviar para a API
        try:
            print(f"\n🔍 DEBUG FRONTEND - CRIAR PACIENTE:")
            print(f"Token: {token[:50]}...")
            print(f"Dados enviados: {dados_paciente}")
            
            response = requests.post(
                f'{Config.BACKEND_URL}/api/pacientes/',
                headers={'Authorization': f'Bearer {token}'},
                json=dados_paciente,
                timeout=10
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
            if response.status_code == 201:
                messages.success(request, 'Paciente cadastrado com sucesso!')
                return redirect('pacientes')
            else:
                error_data = response.json()
                error_msg = error_data.get('mensagem', error_data)
                messages.error(request, f"Erro ao cadastrar: {error_msg}")
                print(f"❌ Erro completo: {error_data}")
        
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Erro ao conectar com o servidor')
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')
            print(f"❌ Exception: {e}")

    # Renderizar formulário
    from django.template import Template, RequestContext
    
    template = Template(NOVO_PACIENTE_TEMPLATE)
    context = RequestContext(request, {
        'user': user,
        'messages': messages.get_messages(request)
    })
    
    return HttpResponse(template.render(context))

def paciente_deletar_view(request, paciente_id):
    """Deleta um paciente"""
    if not request.session.get('token'):
        return redirect('login')
    
    token = request.session.get('token')
    
    try:
        response = requests.delete(
            f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 204:
            messages.success(request, 'Paciente deletado com sucesso!')
        else:
            messages.error(request, 'Erro ao deletar paciente.')
            
    except Exception as e:
        messages.error(request, f'Erro de conexão: {str(e)}')
        
    return redirect('pacientes')

def paciente_visualizar_view(request, paciente_id):
    """Página para visualizar detalhes completos de um paciente"""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/completo/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        response.raise_for_status()  # Isso vai gerar um erro para status 4xx ou 5xx
        
        data = response.json()
        
        # ****** CORREÇÃO DA DATA DE NASCIMENTO ******
        # Pega a data de nascimento do paciente (que vem como 'AAAA-MM-DD')
        if data.get('paciente') and data['paciente'].get('data_nascimento'):
            data_nasc_str = data['paciente']['data_nascimento']
            try:
                # Converte a string para um objeto de data
                data_nasc_obj = datetime.strptime(data_nasc_str, '%Y-%m-%d')
                # Formata o objeto de data para o formato 'DD/MM/AAAA' e atualiza o dicionário
                data['paciente']['data_nascimento'] = data_nasc_obj.strftime('%d/%m/%Y')
            except ValueError:
                # Se a data já estiver em outro formato por algum motivo, não quebra a página
                pass 
        # ***********************************************

        from django.template import Template, RequestContext
        template = Template(PACIENTE_VISUALIZAR_TEMPLATE)
        context = RequestContext(request, data)
        return HttpResponse(template.render(context))

    except requests.exceptions.HTTPError as e:
        messages.error(request, f"Paciente não encontrado ou sem permissão (Erro: {e.response.status_code}).")
        return redirect('pacientes')
    except Exception as e:
        messages.error(request, f'Erro ao carregar dados do paciente: {str(e)}')
        return redirect('pacientes')

def paciente_editar_view(request, paciente_id):
    """Página para editar um paciente"""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    api_url = f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/'

    if request.method == 'POST':
        # Coleta TODOS os dados do formulário para enviar à API
        dados_paciente = {
            # ****** CORREÇÃO: Coletar todos os campos do POST ******
            'clinica_id': request.POST.get('clinica_id'),
            'cpf': request.POST.get('cpf'),
            'nome_completo': request.POST.get('nome_completo'),
            'data_nascimento': request.POST.get('data_nascimento'),
            'sexo': request.POST.get('sexo'),
            'convenio': request.POST.get('convenio'),
            'profissao': request.POST.get('profissao', ''),
            'telefone_celular': request.POST.get('telefone_celular'),
            'telefone_fixo': request.POST.get('telefone_fixo', ''),
            'email': request.POST.get('email', ''),
            'cep': request.POST.get('cep', ''),
            'logradouro': request.POST.get('logradouro', ''),
            'numero': request.POST.get('numero', ''),
            'complemento': request.POST.get('complemento', ''),
            'bairro': request.POST.get('bairro', ''),
            'cidade': request.POST.get('cidade', ''),
            'estado': request.POST.get('estado', ''),
        }
        
        try:
            response = requests.put(api_url, headers={'Authorization': f'Bearer {token}'}, json=dados_paciente)
            response.raise_for_status()
            
            messages.success(request, 'Paciente atualizado com sucesso!')
            return redirect('pacientes')
        except requests.exceptions.HTTPError as e:
            messages.error(request, f'Erro ao atualizar: {e.response.text}')
        except Exception as e:
            messages.error(request, f'Erro de conexão: {str(e)}')
            
        # Se houve erro, recarrega a página de edição para mostrar a mensagem
        return redirect('paciente_editar', paciente_id=paciente_id)

    # Lógica GET (continua a mesma)
    try:
        response = requests.get(api_url, headers={'Authorization': f'Bearer {token}'})
        response.raise_for_status()
        
        paciente = response.json()
        
        from django.template import Template, RequestContext
        template = Template(EDITAR_PACIENTE_TEMPLATE)
        context = RequestContext(request, {
            'paciente': paciente
        })
        return HttpResponse(template.render(context))

    except requests.exceptions.HTTPError as e:
        messages.error(request, f"Paciente não encontrado ou sem permissão (Erro: {e.response.status_code}).")
        return redirect('pacientes')
    except Exception as e:
        messages.error(request, f'Erro ao carregar paciente para edição: {str(e)}')
        return redirect('pacientes')

def pacientes_inativos_view(request):
    """Página para listar e reativar pacientes inativos."""
    if not request.session.get('token'):
        return redirect('login')
    
    token = request.session.get('token')
    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/inativos/',
            headers={'Authorization': f'Bearer {token}'}
        )
        inativos = response.json() if response.status_code == 200 else []
        
        from django.template import Template, RequestContext
        template = Template(INATIVOS_TEMPLATE)
        context = RequestContext(request, {'inativos': inativos})
        return HttpResponse(template.render(context))
        
    except Exception as e:
        messages.error(request, f"Erro ao buscar pacientes inativos: {e}")
        return redirect('pacientes')

@require_http_methods(["POST"])
def paciente_reativar_view(request, paciente_id):
    """Processa a reativação de um paciente."""
    if not request.session.get('token'):
        return redirect('login')
        
    token = request.session.get('token')
    try:
        response = requests.post(
            f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/reativar/',
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code == 200:
            messages.success(request, "Paciente reativado com sucesso!")
        else:
            error_data = response.json()
            messages.error(request, f"Erro ao reativar: {error_data.get('erro', 'Erro desconhecido')}")
        
    except Exception as e:
        messages.error(request, f"Erro de conexão: {e}")

    return redirect('pacientes')

# Views de placeholder para funcionalidades futuras
def placeholder_view(request, paciente_id, page_title="Em Desenvolvimento"):
    from django.template import Template, Context
    template = Template(PLACEHOLDER_TEMPLATE)
    context = Context({'page_title': page_title})
    return HttpResponse(template.render(context))

def paciente_historico_view(request, paciente_id):
    return placeholder_view(request, paciente_id, page_title="Histórico do Paciente")

def paciente_exames_view(request, paciente_id):
    return placeholder_view(request, paciente_id, page_title="Exames do Paciente")

# No frontend.py

def agendamentos_view(request):
    """Página de gestão de agendamentos"""
    from datetime import date, datetime, timedelta

    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))

    params = {}
    search_term = request.GET.get('search', '')
    if search_term:
        params['search'] = search_term

    filter_date_str = request.GET.get('data', date.today().isoformat())
    filter_periodo = request.GET.get('periodo', 'dia')
    
    try:
        filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        filter_date = date.today()
        filter_date_str = filter_date.isoformat()

    if filter_periodo == 'dia':
        params['data_inicial'] = filter_date.isoformat()
    elif filter_periodo == 'semana':
        start_of_week = filter_date - timedelta(days=filter_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        params['data_inicial'] = start_of_week.isoformat()
        params['data_final'] = end_of_week.isoformat()
    elif filter_periodo == 'mes':
        params['mes'] = filter_date.month
        params['ano'] = filter_date.year
        
    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/agendamentos/',
            headers={'Authorization': f'Bearer {token}'},
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        agendamentos = data.get('results', data)
        
        csrf_token = get_token(request)

        html_parts = []
        if agendamentos:
            status_options = ['Agendado', 'Confirmado', 'Realizado', 'Cancelado', 'Faltou']

            for ag in agendamentos:
                data_obj = datetime.strptime(ag['data'], '%Y-%m-%d')
                
                options_html = ""
                for option in status_options:
                    selected = "selected" if ag['status'] == option else ""
                    options_html += f'<option value="{option}" {selected}>{option}</option>'
                
                html_parts.append(f"""
                <div class="agendamento-card" id="agendamento-card-{ag['id']}">
                    <div class="agendamento-card-data">
                        <div class="dia">{data_obj.strftime('%d')}</div>
                        <div class="mes">{data_obj.strftime('%b').upper()}</div>
                    </div>
                    <div class="agendamento-card-info">
                        <strong>{ag['paciente_nome']}</strong>
                        <p>{ag.get('tipo', 'Agendamento')} às {ag.get('hora', '')[:5]}</p>
                        <p class="convenio-info">Convênio: <strong>{ag.get('convenio', 'N/A')}</strong></p>
                    </div>
                    <div class="agendamento-card-status">
                        <select name="status" class="status-select status-{ag['status']}" onchange="updateStatus({ag['id']}, this)">
                            {options_html}
                        </select>
                    </div>
                    <div class="header-actions">
                        <a href="/agendamentos/{ag['id']}/editar/" class="btn btn-secondary">Editar</a>
                        <form method="POST" action="/agendamentos/{ag['id']}/deletar/" onsubmit="return confirm('Tem certeza que deseja excluir este agendamento?');" style="display:inline;">
                            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                            <button type="submit" class="btn btn-danger">Excluir</button>
                        </form>
                    </div>
                </div>
                """)
        else:
            html_parts.append("<p style='text-align:center; padding: 20px;'>Nenhum agendamento encontrado para os filtros selecionados.</p>")
        
        agendamentos_html = "".join(html_parts)

    except Exception as e:
        messages.error(request, f"Erro ao buscar agendamentos: {e}")
        agendamentos_html = f"<p style='text-align:center; padding: 20px;'>Ocorreu um erro ao carregar os agendamentos.</p>"

    from django.template import Template, RequestContext
    from django.utils.safestring import mark_safe
    template = Template(AGENDAMENTOS_TEMPLATE)
    context = RequestContext(request, {
        'user': user,
        'agendamentos_html': mark_safe(agendamentos_html),
        'filter_date': filter_date_str,
        'filter_periodo': filter_periodo,
        'search_term': search_term,
        'token': token,
        'backend_url': Config.BACKEND_URL,
        'csrf_token': csrf_token
    })
    return HttpResponse(template.render(context))

def agendamento_form_view(request, agendamento_id=None):
    """View para criar ou editar um agendamento."""
    token = request.session.get('token')
    if not token:
        return redirect('login')
        
    # ****** PEGAMOS O 'user' DA SESSÃO AQUI ******
    user = request.session.get('user', {})

    # Buscar lista de pacientes para o dropdown
    pacientes = []
    try:
        pac_res = requests.get(f'{Config.BACKEND_URL}/api/pacientes/?page_size=1000', headers={'Authorization': f'Bearer {token}'})
        if pac_res.status_code == 200:
            pacientes = pac_res.json().get('results', pac_res.json())
    except Exception as e:
        messages.error(request, f"Erro ao carregar lista de pacientes: {e}")

    agendamento_data = {}
    form_title = "Novo Agendamento"
    api_url = f'{Config.BACKEND_URL}/api/agendamentos/'
    http_method = requests.post

    if agendamento_id:
        form_title = "Editar Agendamento"
        api_url = f'{Config.BACKEND_URL}/api/agendamentos/{agendamento_id}/'
        http_method = requests.put
        try:
            response = requests.get(api_url, headers={'Authorization': f'Bearer {token}'})
            if response.status_code == 200:
                agendamento_data = response.json()
        except Exception as e:
            messages.error(request, f"Erro ao carregar dados do agendamento: {e}")

    if request.method == 'POST':
        servico_tipo = request.POST.get('servico', '|')
        servico, tipo = (servico_tipo.split('|') + [None])[:2]
        
        payload = {
            'paciente': request.POST.get('paciente'),
            'servico': servico,
            'tipo': tipo,
            'convenio': request.POST.get('convenio'),
            'data': request.POST.get('data'),
            'hora': request.POST.get('hora'),
            'valor': request.POST.get('valor') or None,
            'observacoes': request.POST.get('observacoes', ''),
            
            # ****** AQUI ESTÁ A CORREÇÃO DEFINITIVA ******
            # Adiciona o ID da clínica do usuário logado ao payload
            'clinica_id': user.get('clinica_id')
        }
        try:
            response = http_method(api_url, headers={'Authorization': f'Bearer {token}'}, json=payload)
            response.raise_for_status()
            messages.success(request, "Agendamento salvo com sucesso!")
            return redirect('agendamentos')
        except requests.exceptions.HTTPError as e:
            try:
                error_details = e.response.json()
                error_message = "; ".join([f"{k}: {v[0]}" for k, v in error_details.items()])
                messages.error(request, f"Erro de validação: {error_message}")
            except json.JSONDecodeError:
                messages.error(request, f"Erro ao salvar: {e.response.text}")
        except Exception as e:
            messages.error(request, f"Erro ao salvar agendamento: {e}")

    from django.template import Template, RequestContext
    template = Template(AGENDAMENTO_FORM_TEMPLATE)
    context = RequestContext(request, {
        'form_title': form_title,
        'pacientes': pacientes,
        'agendamento': agendamento_data,
        'user': user # Garante que o menu sempre tenha os dados do usuário
    })
    return HttpResponse(template.render(context))

@require_http_methods(["POST"])
def agendamento_deletar_view(request, agendamento_id):
    """Processa a exclusão de um agendamento."""
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    try:
        response = requests.delete(
            f'{Config.BACKEND_URL}/api/agendamentos/{agendamento_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        messages.success(request, "Agendamento excluído com sucesso.")
    except Exception as e:
        messages.error(request, f"Erro ao excluir agendamento: {e}")

    return redirect('agendamentos')

# ============================================
# URLS
# ============================================

urlpatterns = [
    path('', login_view, name='login'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Pacientes
    path('pacientes/', pacientes_view, name='pacientes'),
    path('pacientes/novo/', novo_paciente_view, name='novo_paciente'),
    path('pacientes/inativos/', pacientes_inativos_view, name='pacientes_inativos'),
    path('pacientes/<int:paciente_id>/reativar/', paciente_reativar_view, name='paciente_reativar'),
    path('pacientes/<int:paciente_id>/visualizar/', paciente_visualizar_view, name='paciente_visualizar'),
    path('pacientes/<int:paciente_id>/editar/', paciente_editar_view, name='paciente_editar'),
    path('pacientes/<int:paciente_id>/deletar/', paciente_deletar_view, name='paciente_deletar'),
    path('pacientes/<int:paciente_id>/historico/', paciente_historico_view, name='paciente_historico'),
    path('pacientes/<int:paciente_id>/exames/', paciente_exames_view, name='paciente_exames'),
    
    # Agendamentos (NOVAS ROTAS)
    path('agendamentos/', agendamentos_view, name='agendamentos'),
    path('agendamentos/novo/', agendamento_form_view, name='agendamento_novo'),
    path('agendamentos/<int:agendamento_id>/editar/', agendamento_form_view, name='agendamento_editar'),
    path('agendamentos/<int:agendamento_id>/deletar/', agendamento_deletar_view, name='agendamento_deletar'),
    
    # Rotas restantes
    path('consultas/', dashboard_view, name='consultas'),
    path('exames/', dashboard_view, name='exames'),
    path('faturamento/', dashboard_view, name='faturamento'),
    path('informacoes/', dashboard_view, name='informacoes'),
]

# ============================================
# INICIALIZAÇÃO
# ============================================

def run_server():
    """Iniciar servidor frontend"""
    
    print("="*70)
    print("INTELLIMED - FRONTEND WEB")
    print("Interface de Usuário Django")
    print("="*70)
    
    # Criar banco de sessões
    print("\nInicializando banco de sessões...")
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
    
    print("\n" + "="*70)
    print("FRONTEND INICIADO")
    print("="*70)
    print(f"\n🌐 Acesse: http://localhost:{Config.PORT}")
    print(f"🔗 Backend: {Config.BACKEND_URL}")
    print("\n📝 CREDENCIAIS PADRÃO:")
    print("  Email: superadmin@intellimed.com")
    print("  Senha: superadmin123")
    print("\nPressione CTRL+C para parar\n")
    
    # Rodar servidor
    sys.argv = ['manage.py', 'runserver', f'{Config.HOST}:{Config.PORT}', '--noreload']
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    run_server()