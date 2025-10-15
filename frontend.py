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
        
        /* --- Sidebar (Estilo Padrão) --- */
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; display: flex; flex-direction: column; position: fixed; height: 100vh; }
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; transition: all 0.3s; }
        .menu-item:hover { background: rgba(255,255,255,0.1); }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; border: none; cursor: pointer; }

        /* --- Conteúdo Principal --- */
        .main-content { margin-left: 260px; flex: 1; padding: 30px; width: calc(100% - 260px); }
        .page-header h2 { font-size: 28px; color: #333; margin-bottom: 8px; }
        .page-header p { color: #666; font-size: 14px; margin-bottom: 30px; }
        
        /* --- Grid de Cards Superiores --- */
        .stats-grid-home { display: grid; grid-template-columns: repeat(4, 1fr); gap: 25px; margin-bottom: 30px; }
        .stat-card-home { background: white; padding: 25px; border-radius: 12px; border: 2px solid #e0e0e0; transition: all 0.3s; }
        .stat-card-home:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
        .card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
        .card-header .icon { font-size: 18px; }
        .card-header .title { font-size: 14px; font-weight: 600; color: #555; text-transform: uppercase; }
        .card-body .number { font-size: 48px; font-weight: 700; margin-bottom: 5px; }
        .card-body .description { font-size: 13px; color: #777; }
        .stat-card-home.border-gray .number { color: #555; }
        .stat-card-home.border-green { border-color: #4CAF50; }
        .stat-card-home.border-green .number { color: #4CAF50; }
        .stat-card-home.border-red { border-color: #f44336; }
        .stat-card-home.border-red .number { color: #f44336; }

        /* --- Colunas do Dashboard --- */
        .dashboard-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: start; }
        .dashboard-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .dashboard-card-title { font-size: 20px; color: #333; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; }
        
        .list-container { max-height: 400px; overflow-y: auto; }
        .list-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 5px; border-bottom: 1px solid #f5f5f5; }
        .list-item:last-child { border-bottom: none; }
        .list-item-info strong { display: block; font-size: 15px; color: #333; }
        .list-item-info span { font-size: 13px; color: #777; }
        .empty-list { text-align: center; padding: 40px 10px; color: #999; font-size: 14px; }
        
        /* <<< INÍCIO DA ALTERAÇÃO: Reutilizando estilo do seletor de Agendamentos >>> */
        .status-select { 
            border: none; padding: 8px 12px; border-radius: 20px; font-size: 13px; font-weight: 700; cursor: pointer; 
            -webkit-appearance: none; -moz-appearance: none; appearance: none; transition: all 0.3s ease;
        }
        .status-select:hover { transform: scale(1.05); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
        .status-Agendado { background: #FFF9C4; color: #F57F17; border: 2px solid #FBC02D; }
        .status-Confirmado { background: #FFCDD2; color: #C62828; border: 2px solid #E53935; }
        .status-Realizado { background: #C8E6C9; color: #2E7D32; border: 2px solid #43A047; }
        .status-Cancelado { background: #E0E0E0; color: #616161; border: 2px solid #9E9E9E; }
        .status-Faltou { background: #BBDEFB; color: #1565C0; border: 2px solid #1976D2; }
        /* <<< FIM DA ALTERAÇÃO >>> */

        .status-badge-pill { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 2px solid; }
        .pill-Agendado { background-color: rgba(255, 249, 196, 0.5); color: #F57F17; border-color: #FBC02D; }
        .pill-Confirmado { background-color: rgba(255, 205, 210, 0.5); color: #C62828; border-color: #E53935; }
        .pill-Realizado { background-color: rgba(200, 230, 201, 0.5); color: #2E7D32; border-color: #43A047; }
        .pill-Cancelado { background-color: rgba(224, 224, 224, 0.5); color: #616161; border-color: #9E9E9E; }
        .pill-Faltou { background-color: rgba(187, 222, 251, 0.5); color: #1565C0; border-color: #1976D2; }

        .priority-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .priority-alta { background-color: #f44336; }
        .priority-media { background-color: #ff9800; }
        .priority-baixa { background-color: #4caf50; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="{% url 'dashboard' %}" class="menu-item active"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="{% url 'pacientes' %}" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="{% url 'agendamentos' %}" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="{% url 'consultas' %}" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="{% url 'exames' %}" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames IA</span></a>
            <a href="{% url 'faturamento' %}" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="{% url 'informacoes' %}" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    
    <div class="main-content">
        <div class="page-header">
            <h2>{{ page_title }}</h2>
            <p>Olá, {{ user.nome_completo }}. Aqui está um resumo da sua clínica hoje.</p>
        </div>
        
        {% if error_message %}
            <div style="background-color: #ffebee; color: #c62828; padding: 20px; border-radius: 8px;">
                <strong>Erro:</strong> {{ error_message }}
            </div>
        {% else %}
            <div class="stats-grid-home">
                <div class="stat-card-home border-gray">
                    <div class="card-header"><span class="icon">👥</span><h3 class="title">Pacientes</h3></div>
                    <div class="card-body">
                        <p class="number">{{ data.resumo_principal.total_pacientes|default:"0" }}</p>
                        <p class="description">Total de pacientes</p>
                    </div>
                </div>
                
                <div class="stat-card-home border-green">
                    <div class="card-header"><span class="icon">📅</span><h3 class="title">Hoje</h3></div>
                    <div class="card-body">
                        <p class="number">{{ total_hoje_validos|default:"0" }}</p>
                        <p class="description">Agendamentos hoje</p>
                    </div>
                </div>
                
                <div class="stat-card-home border-red">
                    <div class="card-header"><span class="icon">⏰</span><h3 class="title">Pendentes</h3></div>
                    <div class="card-body">
                        <p class="number">{{ data.resumo_principal.pendentes_hoje|default:"0" }}</p>
                        <p class="description">Consultas pendentes</p>
                    </div>
                </div>
                
                <div class="stat-card-home border-gray">
                    <div class="card-header"><span class="icon">🗓️</span><h3 class="title">Futuros</h3></div>
                    <div class="card-body">
                        <p class="number">{{ data.resumo_principal.agendamentos_futuros|default:"0" }}</p>
                        <p class="description">Agendamentos futuros</p>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-columns">
                <div class="dashboard-card">
                    <!-- <<< ALTERAÇÃO DO TÍTULO >>> -->
                    <h3 class="dashboard-card-title">Fila de Atendimentos de Hoje</h3>
                    <div class="list-container">
                        {% for ag in data.lista_espera_hoje %}
                            <div class="list-item">
                                <div class="list-item-info">
                                    <strong>{{ ag.hora }} - {{ ag.paciente_nome }}</strong>
                                    <span>{{ ag.servico }} - {{ ag.tipo }}</span>
                                </div>
                                <!-- <<< INÍCIO DA ALTERAÇÃO: Troca de span para select >>> -->
                                <select name="status" class="status-select status-{{ ag.status }}" onchange="updateStatus({{ ag.id }}, this)">
                                    <option value="Agendado" {% if ag.status == 'Agendado' %}selected{% endif %}>Agendado</option>
                                    <option value="Confirmado" {% if ag.status == 'Confirmado' %}selected{% endif %}>Confirmado</option>
                                    <option value="Realizado" {% if ag.status == 'Realizado' %}selected{% endif %}>Realizado</option>
                                    <option value="Cancelado" {% if ag.status == 'Cancelado' %}selected{% endif %}>Cancelado</option>
                                    <option value="Faltou" {% if ag.status == 'Faltou' %}selected{% endif %}>Faltou</option>
                                </select>
                                <!-- <<< FIM DA ALTERAÇÃO >>> -->
                            </div>
                        {% empty %}
                            <div class="empty-list">Nenhum paciente agendado para hoje.</div>
                        {% endfor %}
                    </div>
                </div>

                <div class="dashboard-card">
                    <h3 class="dashboard-card-title">Consultas Pendentes de Ação</h3>
                    <div class="list-container">
                        {% for consulta in data.consultas_pendentes.lista %}
                            <div class="list-item">
                                <div class="list-item-info">
                                    <strong>{{ consulta.paciente_nome }}</strong>
                                    <span><span class="priority-dot priority-{{ consulta.prioridade }}"></span>{{ consulta.tempo_status }}</span>
                                </div>
                                <span class="status-badge-pill pill-{{ consulta.status }}">{{ consulta.status_display }}</span>
                            </div>
                        {% empty %}
                            <div class="empty-list">Nenhuma consulta pendente de ação.</div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
        {% endif %}
    </div>

    <!-- <<< ADIÇÃO DO SCRIPT JAVASCRIPT >>> -->
    <script>
        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 20px; right: 20px; padding: 15px 20px;
                background: ${type === 'success' ? '#4CAF50' : '#f44336'};
                color: white; border-radius: 5px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 10000; font-weight: 600;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            setTimeout(() => {
                notification.style.transition = 'opacity 0.5s';
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 500);
            }, 3000);
        }

        function updateStatus(agendamentoId, selectElement) {
            const novoStatus = selectElement.value;
            const originalStatus = selectElement.getAttribute('data-original-status');
            selectElement.disabled = true;
            selectElement.style.opacity = '0.5';
            
            const token = "{{ token }}";
            const backendUrl = "{{ backend_url }}";
            const url = `${backendUrl}/api/agendamentos/${agendamentoId}/alterar_status/`;

            fetch(url, {
                method: 'PATCH',
                headers: { 
                    'Content-Type': 'application/json', 
                    'Authorization': `Bearer ${token}` 
                },
                body: JSON.stringify({ status: novoStatus })
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401) {
                        alert('❌ Sessão expirada. Faça login novamente.');
                        window.location.href = '/login/';
                        return Promise.reject('Sessão expirada');
                    }
                    return response.json().then(err => { throw new Error(err.detail || err.erro || 'Erro desconhecido'); });
                }
                return response.json();
            })
            .then(data => {
                if (data && data.id) {
                    selectElement.className = `status-select status-${data.status}`;
                    selectElement.setAttribute('data-original-status', data.status);
                    showNotification('Status atualizado com sucesso!', 'success');
                    // Recarrega a página para refletir as mudanças no faturamento, se houver.
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    throw new Error('Resposta inválida do servidor');
                }
            })
            .catch(error => {
                console.error('❌ Erro:', error);
                showNotification(`Erro ao atualizar: ${error.message}`, 'error');
                selectElement.value = originalStatus; // Reverte a mudança visual em caso de erro
                selectElement.className = `status-select status-${originalStatus}`;
            })
            .finally(() => {
                selectElement.disabled = false;
                selectElement.style.opacity = '1';
            });
        }

        // Adiciona o status original como um atributo para poder reverter em caso de erro
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.status-select').forEach(select => {
                select.setAttribute('data-original-status', select.value);
            });
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            display: flex;
            min-height: 100vh;
        }
        
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
        
        /* <<< INÍCIO DA ALTERAÇÃO DE ESTILO >>> */
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 25px; /* Efeito pílula */
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
            border-radius: 25px; /* Efeito pílula */
            font-size: 14px;
            font-weight: 600;
            background-color: #e3f2fd;
            color: #1976d2;
            border: 2px solid #bbdefb;
            white-space: nowrap;
        }
        /* <<< FIM DA ALTERAÇÃO DE ESTILO >>> */
        
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
            margin-top: auto;
            padding-top: 15px;
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
                <span>Exames iA</span>
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
    
    <div class="main-content">
        <div class="page-header">
            <div class="page-title">
                <span class="page-title-icon">👥</span>
                <h1>Gestão de Pacientes</h1>
            </div>
            <!-- <<< INÍCIO DA ALTERAÇÃO DOS BOTÕES >>> -->
            <div class="header-actions">
                <span class="count-indicator">Total: {{ pagination.count }}</span>
                <a href="/pacientes/inativos/" class="btn btn-secondary">Ver Inativos</a>
                <button class="btn btn-secondary" onclick="location.reload()">Atualizar</button>
                <a href="/pacientes/novo/" class="btn btn-primary">Novo Paciente</a>
            </div>
            <!-- <<< FIM DA ALTERAÇÃO DOS BOTÕES >>> -->
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            display: flex;
            min-height: 100vh;
        }
        
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
        
        /* <<< INÍCIO DA ALTERAÇÃO DE ESTILO >>> */
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 25px; /* Efeito Pílula */
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.2);
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-secondary {
            background: #e0e0e0;
            color: #666;
        }
        .btn-secondary:hover {
            background: #d0d0d0;
            box-shadow: none;
        }
        /* <<< FIM DA ALTERAÇÃO DE ESTILO >>> */
        
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
                <span>Exames iA</span>
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
                                <option value="AC">AC</option><option value="AL">AL</option><option value="AP">AP</option><option value="AM">AM</option>
                                <option value="BA">BA</option><option value="CE">CE</option><option value="DF">DF</option><option value="ES">ES</option>
                                <option value="GO">GO</option><option value="MA">MA</option><option value="MT">MT</option><option value="MS">MS</option>
                                <option value="MG">MG</option><option value="PA">PA</option><option value="PB">PB</option><option value="PR">PR</option>
                                <option value="PE">PE</option><option value="PI">PI</option><option value="RJ">RJ</option><option value="RN">RN</option>
                                <option value="RS">RS</option><option value="RO">RO</option><option value="RR">RR</option><option value="SC">SC</option>
                                <option value="SP">SP</option><option value="SE">SE</option><option value="TO">TO</option>
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
        document.querySelector('[name="cpf"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            value = value.replace(/(\\d{3})(\\d)/, '$1.$2');
            value = value.replace(/(\\d{3})(\\d)/, '$1.$2');
            value = value.replace(/(\\d{3})(\\d{1,2})$/, '$1-$2');
            e.target.value = value;
        });
        document.querySelector('[name="telefone_celular"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            value = value.replace(/^(\\d{2})(\\d)/g, '($1) $2');
            value = value.replace(/(\\d)(\\d{4})$/, '$1-$2');
            e.target.value = value;
        });
        document.querySelector('[name="telefone_fixo"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            value = value.replace(/^(\\d{2})(\\d)/g, '($1) $2');
            value = value.replace(/(\\d)(\\d{4})$/, '$1-$2');
            e.target.value = value;
        });
        document.querySelector('[name="cep"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            value = value.replace(/^(\\d{5})(\\d)/, '$1-$2');
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
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        
        /* <<< ESTILOS DO MENU LATERAL ADICIONADOS >>> */
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; }

        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .table-container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #f0f0f0; }
        th { font-weight: 600; color: #666; }
        
        /* <<< ESTILOS DOS BOTÕES ALTERADOS >>> */
        .btn { 
            padding: 8px 16px; 
            border: none; 
            border-radius: 20px; /* Efeito pílula */
            font-weight: 600; 
            cursor: pointer; 
            text-decoration: none;
            transition: all 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .btn-success { background: #e8f5e9; color: #2e7d32; }
        .btn-primary { background: rgba(86, 105, 211, 0.8); color: white; padding: 10px 22px; } /* Cor azul escura */
    </style>
</head>
<body>
    <!-- <<< MENU LATERAL COMPLETO ADICIONADO >>> -->
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item active"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>

    <div class="main-content">
        <div class="page-header">
            <div class="page-title"><h1>🗑️ Pacientes Inativos (Arquivados)</h1></div>
            <!-- <<< BOTÃO "VOLTAR" ATUALIZADO >>> -->
            <a href="/pacientes/" class="btn btn-primary">Voltar</a>
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

PACIENTE_EXAMES_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Exames do Paciente - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; padding: 30px 20px; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; }
        
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .page-title p { color: #666; font-size: 16px; margin-top: 5px; }
        .btn { padding: 10px 20px; border-radius: 20px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; }
        .btn-primary { background: rgba(86, 105, 211, 0.8); color: white; }

        .columns-container { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: start; }
        .card-section { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        .section-header h2 { font-size: 20px; color: #333; }
        
        .exame-item { border-bottom: 1px solid #f0f0f0; padding: 12px 5px; }
        .exame-item:last-child { border-bottom: none; }
        .exame-info { display: flex; justify-content: space-between; align-items: center; }
        .exame-info strong { font-size: 14px; color: #333; }
        .exame-info span { font-size: 12px; color: #666; }
        .exame-actions a { margin-left: 10px; text-decoration: none; font-size: 13px; font-weight: 500; }
        .exame-actions .view-link { color: #007bff; }
        .exame-actions .edit-link { color: #ffc107; }
        .exame-actions .delete-link { color: #dc3545; }
        
        .empty-list { text-align: center; padding: 30px; color: #999; }
        
        .form-exame-geral { margin-top: 20px; padding-top: 20px; border-top: 2px dashed #eee; }
        .form-exame-geral .form-group { margin-bottom: 15px; }
        .form-exame-geral label { font-weight: 600; font-size: 13px; margin-bottom: 5px; display: block; }
        .form-exame-geral select, .form-exame-geral textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 14px;
        }
        .form-exame-geral textarea { resize: vertical; min-height: 120px; }

        .dictation-controls { display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
        #btn-ditar-exame { background: #f0f0f0; border: 1px solid #ccc; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 20px; }
        #btn-ditar-exame.recording { background: #ffebee; color: #dc3545; border-color: #dc3545; animation: pulse 1.5s infinite; }
        #ditar-status { font-size: 13px; color: #666; font-weight: 500; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); } 100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); } }

    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item active"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <div class="page-header">
            <div class="page-title">
                <h1>🔬 Exames do Paciente</h1>
                <p>{{ paciente.nome_completo }}</p>
            </div>
            <a href="/pacientes/" class="btn btn-primary">Voltar</a>
        </div>

        <div class="columns-container">
            <div class="card-section">
                <div class="section-header">
                    <h2>Exames iA</h2>
                </div>
                <div class="exames-list">
                    {% for exame in exames_ia %}
                        <div class="exame-item">
                            <div class="exame-info">
                                <div>
                                    <strong>{{ exame.tipo_exame_identificado_pela_ia|default:exame.tipo_exame_display }}</strong>
                                    <span>{{ exame.data_exame_formatada }}</span>
                                </div>
                                <div class="exame-actions">
                                    <a href="/exames/{{ exame.id }}/visualizar/" class="view-link">Ver Laudo</a>
                                </div>
                            </div>
                        </div>
                    {% empty %}
                        <p class="empty-list">Nenhum exame analisado pela iA para este paciente.</p>
                    {% endfor %}
                </div>
            </div>

            <div class="card-section">
                <div class="section-header">
                    <h2>Exames Gerais</h2>
                </div>
                <div class="exames-list">
                    {% for exame in exames_gerais %}
                        <div class="exame-item">
                            <div class="exame-info">
                                <div>
                                    <strong>{{ exame.tipo_exame_display }}</strong>
                                    <span>{{ exame.data_exame_formatada }}</span>
                                </div>
                                <div class="exame-actions">
                                    <a href="{% url 'exame_geral_visualizar' paciente_id=paciente.id exame_id=exame.id %}" class="view-link">Ver</a>
                                    <a href="{% url 'exame_geral_editar' paciente_id=paciente.id exame_id=exame.id %}" class="edit-link">Editar</a>
                                    <a href="{% url 'exame_geral_deletar' paciente_id=paciente.id exame_id=exame.id %}" onclick="return confirm('Tem certeza que deseja excluir este exame?')" class="delete-link">Deletar</a>
                                </div>
                            </div>
                        </div>
                    {% empty %}
                        <p class="empty-list">Nenhum exame geral cadastrado.</p>
                    {% endfor %}
                </div>

                <div class="form-exame-geral">
                    <form method="POST">
                        {% csrf_token %}
                        <h3>Lançar Novo Exame Geral</h3>
                        <div class="form-group">
                            <label for="tipo_exame">Tipo de Exame</label>
                            <select name="tipo_exame" required>
                                <option value="hemograma">Hemograma</option>
                                <option value="glicemia">Glicemia de Jejum</option>
                                <option value="colesterol_total">Colesterol Total e Frações</option>
                                <option value="urinalise">Urinálise (EAS)</option>
                                <option value="gasometria">Gasometria Arterial</option>
                                <option value="raio_x">Raio-X</option>
                                <option value="ultrassonografia">Ultrassonografia</option>
                                <option value="tomografia">Tomografia Computadorizada</option>
                                <option value="ressonancia">Ressonância Magnética</option>
                                <option value="eletrocardiograma">Eletrocardiograma (ECG)</option>
                                <option value="ecocardiograma">Ecocardiograma</option>
                                <option value="endoscopia">Endoscopia Digestiva Alta</option>
                                <option value="colonoscopia">Colonoscopia</option>
                                <option value="mamografia">Mamografia</option>
                                <option value="densitometria">Densitometria Óssea</option>
                                <option value="espirometria">Espirometria</option>
                                <option value="outros">Outros</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="resultado">Resultado / Observações</label>
                            <div class="dictation-controls">
                                <button type="button" id="btn-ditar-exame" title="Ditar resultado do exame">🎤</button>
                                <span id="ditar-status">Clique no microfone para ditar o resultado</span>
                            </div>
                            <textarea id="resultado-textarea" name="resultado" required placeholder="Digite ou dite aqui o resultado do exame..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Salvar Exame</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const btnDitar = document.getElementById('btn-ditar-exame');
            const ditarStatus = document.getElementById('ditar-status');
            const resultadoTextarea = document.getElementById('resultado-textarea');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            let isRecording = false;
            let mediaRecorder;
            let audioChunks = [];

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                btnDitar.disabled = true;
                ditarStatus.textContent = "Gravação de áudio não é suportada neste navegador.";
                return;
            }

            btnDitar.addEventListener('click', () => {
                if (isRecording) {
                    stopRecording();
                } else {
                    startRecording();
                }
            });

            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    isRecording = true;
                    audioChunks = [];
                    mediaRecorder = new MediaRecorder(stream);

                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64String = reader.result.split(',')[1];
                            sendAudioForTranscription(base64String);
                        };
                        reader.readAsDataURL(audioBlob);
                    };

                    mediaRecorder.start();
                    updateUIRecording(true);
                } catch (err) {
                    console.error("Erro ao acessar microfone:", err);
                    ditarStatus.textContent = "Erro: Permissão para microfone negada.";
                    ditarStatus.style.color = '#dc3545';
                }
            }

            function stopRecording() {
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                    mediaRecorder.stop();
                }
                isRecording = false;
                updateUIRecording(false);
            }

            function updateUIRecording(isRec) {
                if (isRec) {
                    btnDitar.classList.add('recording');
                    btnDitar.innerHTML = '🛑';
                    ditarStatus.textContent = "Gravando... Clique para parar.";
                    ditarStatus.style.color = '#dc3545';
                } else {
                    btnDitar.classList.remove('recording');
                    btnDitar.innerHTML = '🎤';
                    ditarStatus.textContent = "Processando transcrição...";
                    ditarStatus.style.color = '#007bff';
                }
            }

            async function sendAudioForTranscription(base64String) {
                try {
                    // <<< INÍCIO DA CORREÇÃO >>>
                    const backendUrl = '{{ BACKEND_URL }}';
                    const response = await fetch(`${backendUrl}/api/transcrever-audio/`, {
                    // <<< FIM DA CORREÇÃO >>>
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                            'Authorization': `Bearer {{ token }}`
                        },
                        body: JSON.stringify({
                            audio_base64: base64String,
                            audio_formato: 'webm'
                        })
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.erro || 'Erro no servidor');
                    }

                    const data = await response.json();
                    resultadoTextarea.value = data.texto;
                    ditarStatus.textContent = "Transcrição concluída! Clique para ditar novamente.";
                    ditarStatus.style.color = '#28a745';

                } catch (err) {
                    console.error("Erro na transcrição:", err);
                    ditarStatus.textContent = `Erro: ${err.message}. Tente novamente.`;
                    ditarStatus.style.color = '#dc3545';
                } finally {
                    btnDitar.innerHTML = '🎤';
                    btnDitar.classList.remove('recording');
                }
            }
        });
    </script>
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
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; margin: 0; }
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
        .btn { padding: 10px 20px; border-radius: 20px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: all 0.2s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .btn-primary { background: rgba(86, 105, 211, 0.8); color: white; }
        .btn-primary:hover { background: rgba(86, 105, 211, 1); }
        .btn-secondary { background: rgba(108, 117, 125, 0.15); color: #495057; }
        .btn-secondary:hover { background: rgba(108, 117, 125, 0.25); }
        .agendamentos-list { display: flex; flex-direction: column; gap: 15px; }
        .agendamento-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 20px; }
        .agendamento-card-data { text-align: center; padding-right: 20px; border-right: 1px solid #f0f0f0; }
        .agendamento-card-data .dia { font-size: 28px; font-weight: 700; color: #667eea; }
        .agendamento-card-data .mes { font-size: 14px; color: #666; text-transform: uppercase; }
        .agendamento-card-info { flex-grow: 1; }
        .agendamento-card-info strong { font-size: 18px; color: #333; display: block; margin-bottom: 2px; }
        .agendamento-card-info p { font-size: 14px; color: #777; margin: 0; }
        .status-select { border: none; padding: 8px 12px; border-radius: 20px; font-size: 13px; font-weight: 700; cursor: pointer; -webkit-appearance: none; -moz-appearance: none; appearance: none; transition: all 0.3s ease; }
        .status-select:hover { transform: scale(1.05); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
        .status-Agendado { background: #FFF9C4; color: #F57F17; border: 2px solid #FBC02D; }
        .status-Confirmado { background: #FFCDD2; color: #C62828; border: 2px solid #E53935; }
        .status-Realizado { background: #C8E6C9; color: #2E7D32; border: 2px solid #43A047; }
        .status-Cancelado { background: #E0E0E0; color: #616161; border: 2px solid #9E9E9E; }
        .status-Faltou { background: #BBDEFB; color: #1565C0; border: 2px solid #1976D2; }
        .actions-dropdown { position: relative; }
        .actions-btn { background: transparent; border: none; color: #667eea; border-radius: 8px; width: 40px; height: 40px; cursor: pointer; transition: color 0.2s, background-color 0.2s; display: flex; align-items: center; justify-content: center; }
        .actions-btn:hover { background-color: rgba(102, 126, 234, 0.1); color: #5a67d8; }
        .dropdown-menu { display: none; position: absolute; right: 0; top: 110%; background: white; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 10; min-width: 150px; overflow: hidden; }
        .dropdown-menu.show { display: block; }
        .dropdown-item { display: block; padding: 12px 15px; color: #333; text-decoration: none; font-size: 14px; }
        .dropdown-item:hover { background: #f5f5f5; }
        .dropdown-item-danger { color: #c62828; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item active"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer"><a href="/logout/" class="btn-logout">Sair</a></div>
    </div>
    <div class="main-content">
        <div class="page-header">
            <div class="page-title"><h1>📅 Gestão de Agendamentos</h1></div>
            <div class="header-actions">
                <button onclick="location.reload()" class="btn btn-secondary">Atualizar</button>
                <a href="/agendamentos/novo/" class="btn btn-primary">Novo Agendamento</a>
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
            <input type="text" id="search-paciente" placeholder="🔍 Buscar por nome ou CPF do paciente..." oninput="handleAgendamentoSearch(this)" value="{{ search_term }}">
        </div>
        <div class="agendamentos-list">
            {{ agendamentos_html }}
        </div>
    </div>
    <script>
        let searchTimeout;

        function handleAgendamentoSearch(input) {
            let originalValue = input.value;
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
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                applyFilters();
            }, 400);
        }

        function applyFilters() {
            const data = document.getElementById('filter-data').value;
            const periodo = document.getElementById('filter-periodo').value;
            const search = document.getElementById('search-paciente').value;
            const params = new URLSearchParams();
            if (data) params.append('data', data);
            if (periodo) params.append('periodo', periodo);
            if (search) params.append('search', search);
            window.location.href = `/agendamentos/?${params.toString()}`;
        }
        
        function updateStatus(agendamentoId, selectElement) {
            const novoStatus = selectElement.value;
            const originalStatus = selectElement.getAttribute('data-original-status');
            selectElement.disabled = true;
            selectElement.style.opacity = '0.5';
            const token = "{{ token }}";
            const backendUrl = "{{ backend_url }}";
            const url = `${backendUrl}/api/agendamentos/${agendamentoId}/alterar_status/`;
            fetch(url, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ status: novoStatus })
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401) {
                        alert('❌ Sessão expirada. Faça login novamente.');
                        window.location.href = '/login/';
                        return Promise.reject('Sessão expirada');
                    }
                    return response.json().then(err => { throw new Error(err.detail || err.erro || 'Erro desconhecido'); });
                }
                return response.json();
            })
            .then(data => {
                if (data && data.id) {
                    selectElement.className = `status-select status-${data.status}`;
                    selectElement.setAttribute('data-original-status', data.status);
                    showNotification('Status atualizado com sucesso!', 'success');
                } else {
                    throw new Error('Resposta inválida');
                }
            })
            .catch(error => {
                console.error('❌ Erro:', error);
                alert(`Erro ao atualizar: ${error.message}`);
                selectElement.value = originalStatus;
            })
            .finally(() => {
                selectElement.disabled = false;
                selectElement.style.opacity = '1';
            });
        }
        
        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 20px; right: 20px; padding: 15px 20px;
                background: ${type === 'success' ? '#4CAF50' : '#f44336'};
                color: white; border-radius: 5px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 10000; font-weight: 600;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 3000);
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.status-select').forEach(select => {
                select.setAttribute('data-original-status', select.value);
            });
        });

        document.addEventListener('click', function(event) {
            const target = event.target.closest('.actions-btn');
            if (target) {
                const dropdownId = target.getAttribute('data-dropdown-id');
                const dropdown = document.getElementById(dropdownId);
                document.querySelectorAll('.dropdown-menu.show').forEach(openDropdown => {
                    if (openDropdown !== dropdown) {
                        openDropdown.classList.remove('show');
                    }
                });
                dropdown.classList.toggle('show');
            } else {
                if (!event.target.closest('.actions-dropdown')) {
                    document.querySelectorAll('.dropdown-menu.show').forEach(openDropdown => {
                        openDropdown.classList.remove('show');
                    });
                }
            }
        });

        function confirmDelete(agendamentoId) {
            if (confirm('Tem certeza que deseja excluir este agendamento? Esta ação não pode ser desfeita.')) {
                // Remove o formulário se já existir
                const existingForm = document.getElementById('delete-form-' + agendamentoId);
                if (existingForm) {
                    existingForm.submit();
                }
            }
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
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .form-container { max-width: 800px; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; font-weight: 600; margin-bottom: 8px; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; }
        .form-actions { display: flex; justify-content: flex-end; gap: 15px; margin-top: 20px; }
        
        /* <<< INÍCIO DA ALTERAÇÃO DE ESTILO >>> */
        .btn { 
            padding: 12px 30px; 
            border-radius: 25px; /* Efeito Pílula */
            font-weight: 600; 
            text-decoration: none; 
            border: none; 
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #e0e0e0; color: #666; }
        /* <<< FIM DA ALTERAÇÃO DE ESTILO >>> */

        .hidden-field { display: none; }
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
                        <select name="servico" id="servico-select" required>
                            <option value="">Selecione...</option>
                            <option value="Consulta" {% if agendamento.servico == 'Consulta' %}selected{% endif %}>Consulta</option>
                            <option value="Exame" {% if agendamento.servico == 'Exame' %}selected{% endif %}>Exame</option>
                        </select>
                    </div>
                    
                    <div class="form-group hidden-field" id="tipo-consulta-field">
                        <label>Tipo de Consulta <span style="color:red;">*</span></label>
                        <select name="tipo_consulta">
                            <option value="Primeira Consulta" {% if agendamento.tipo == 'Primeira Consulta' %}selected{% endif %}>Primeira Consulta</option>
                            <option value="Revisão" {% if agendamento.tipo == 'Revisão' %}selected{% endif %}>Retorno / Revisão</option>
                            <option value="Consulta de Urgência" {% if agendamento.tipo == 'Consulta de Urgência' %}selected{% endif %}>Urgência</option>
                        </select>
                    </div>

                    <div class="form-group hidden-field" id="tipo-exame-field">
                        <label>Tipo de Exame <span style="color:red;">*</span></label>
                        <select name="tipo_exame">
                            <option value="Eletrocardiograma" {% if agendamento.tipo == 'Eletrocardiograma' %}selected{% endif %}>Eletrocardiograma</option>
                            <option value="Ecocardiograma" {% if agendamento.tipo == 'Ecocardiograma' %}selected{% endif %}>Ecocardiograma</option>
                            <option value="Radiografia" {% if agendamento.tipo == 'Radiografia' %}selected{% endif %}>Radiografia</option>
                            <option value="Ultrassonografia" {% if agendamento.tipo == 'Ultrassonografia' %}selected{% endif %}>Ultrassonografia</option>
                            <option value="Holter" {% if agendamento.tipo == 'Holter' %}selected{% endif %}>Holter 24h</option>
                            <option value="Mapa de pressão" {% if agendamento.tipo == 'Mapa de pressão' %}selected{% endif %}>MAPA 24h</option>
                            <option value="Espirometria" {% if agendamento.tipo == 'Espirometria' %}selected{% endif %}>Espirometria</option>
                            <option value="Outro" {% if agendamento.tipo == 'Outro' %}selected{% endif %}>Outro</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label>Convênio <span style="color:red;">*</span></label>
                    <select name="convenio" required>
                        <option value="">Selecione...</option>
                        <option value="PARTICULAR" {% if agendamento.convenio == 'PARTICULAR' %}selected{% endif %}>Particular</option>
                        <option value="UNIMED" {% if agendamento.convenio == 'UNIMED' %}selected{% endif %}>Unimed</option>
                    </select>
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

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const servicoSelect = document.getElementById('servico-select');
            const tipoConsultaField = document.getElementById('tipo-consulta-field');
            const tipoExameField = document.getElementById('tipo-exame-field');

            function toggleFields() {
                const selectedService = servicoSelect.value;
                if (selectedService === 'Consulta') {
                    tipoConsultaField.classList.remove('hidden-field');
                    tipoExameField.classList.add('hidden-field');
                } else if (selectedService === 'Exame') {
                    tipoConsultaField.classList.add('hidden-field');
                    tipoExameField.classList.remove('hidden-field');
                } else {
                    tipoConsultaField.classList.add('hidden-field');
                    tipoExameField.classList.add('hidden-field');
                }
            }

            servicoSelect.addEventListener('change', toggleFields);
            toggleFields();
        });
    </script>
</body>
</html>
"""

AGENDAMENTO_VISUALIZAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Visualizar Agendamento - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 20px; }
        .details-container { background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 900px; }
        .section-title { font-size: 20px; font-weight: 600; color: #667eea; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; }
        .info-grid { display: grid; grid-template-columns: 200px 1fr; gap: 15px; margin-bottom: 30px; }
        .info-grid .label { font-weight: 600; color: #666; font-size: 14px; }
        .info-grid .value { color: #333; font-size: 15px; }
        .obs-box { background: #f9f9f9; border: 1px solid #eee; padding: 15px; border-radius: 8px; min-height: 80px; }
        .btn-secondary { padding: 12px 30px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; background: #e0e0e0; color: #666; text-decoration: none; display: inline-block; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <!-- O menu lateral pode ser incluído aqui como nas outras páginas -->
    </div>
    <div class="main-content">
        <div class="page-header"><h1>👁️ Detalhes do Agendamento</h1></div>
        <div class="details-container">
            <h2 class="section-title">Dados do Paciente</h2>
            <div class="info-grid">
                <div class="label">Nome Completo:</div><div class="value">{{ agendamento.paciente_nome }}</div>
                <div class="label">CPF:</div><div class="value">{{ agendamento.paciente_cpf }}</div>
                <div class="label">Idade:</div><div class="value">{{ agendamento.paciente_detalhes.idade }} anos</div>
                <div class="label">Sexo:</div><div class="value">{{ agendamento.paciente_detalhes.sexo_display }}</div>
                <div class="label">Telefone:</div><div class="value">{{ agendamento.paciente_detalhes.telefone_celular }}</div>
            </div>

            <h2 class="section-title">Informações do Agendamento</h2>
            <div class="info-grid">
                <div class="label">Data:</div><div class="value">{{ agendamento.data }}</div>
                <div class="label">Horário:</div><div class="value">{{ agendamento.hora }}</div>
                <div class="label">Serviço:</div><div class="value">{{ agendamento.servico }}</div>
                <div class="label">Tipo:</div><div class="value">{{ agendamento.tipo }}</div>
                <div class="label">Convênio:</div><div class="value">{{ agendamento.convenio }}</div>
                <div class="label">Valor:</div><div class="value">R$ {{ agendamento.valor }}</div>
                <div class="label">Status Atual:</div><div class="value">{{ agendamento.status_display }}</div>
            </div>

            <h2 class="section-title">Observações</h2>
            <div class="info-grid">
                <div class="value obs-box">
                    {{ agendamento.observacoes|default:"Nenhuma observação registrada." }}
                </div>
            </div>

            <a href="/agendamentos/" class="btn btn-secondary">Voltar para a Lista</a>
        </div>
    </div>
</body>
</html>
"""

FATURAMENTO_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Gestão Financeira - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; padding: 30px 20px; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; border: none; cursor: pointer; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 20px; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .stat-card h3 { font-size: 14px; color: #666; margin-bottom: 10px; font-weight: 600; text-transform: uppercase; }
        .stat-card .amount { font-size: 28px; font-weight: 700; }
        .text-success { color: #2e7d32; }
        .text-danger { color: #c62828; }
        .text-warning { color: #f57c00; }
        .text-info { color: #0277bd; }
        .text-primary { color: #5a67d8; }

        .actions-bar { display: flex; justify-content: space-between; align-items: center; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .actions-group { display: flex; align-items: center; gap: 10px; }
        .btn { padding: 10px 20px; border-radius: 8px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: all 0.2s; }
        
        /* <<< INÍCIO DAS ALTERAÇÕES DE ESTILO DOS BOTÕES DE AÇÃO >>> */
        .btn-success {
            background: rgba(76, 175, 80, 0.15); /* Verde com transparência */
            color: #2e7d32; /* Texto verde escuro */
            border-radius: 20px; /* Formato de pílula */
        }
        .btn-success:hover {
            background: rgba(76, 175, 80, 0.25);
            transform: translateY(-2px);
        }
        .btn-danger {
            background: rgba(244, 67, 54, 0.15); /* Vermelho com transparência */
            color: #c62828; /* Texto vermelho escuro */
            border-radius: 20px; /* Formato de pílula */
        }
        .btn-danger:hover {
            background: rgba(244, 67, 54, 0.25);
            transform: translateY(-2px);
        }
        /* <<< FIM DAS ALTERAÇÕES DE ESTILO DOS BOTÕES DE AÇÃO >>> */

        .filter-group { 
            display: flex; 
            align-items: center; 
            gap: 10px; 
        }
        .filter-group span {
            color: #555;
            font-weight: 600;
            font-size: 14px;
            padding-right: 5px;
        }
        .filter-group .btn-filter {
            background: #667eea;
            border: none;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .filter-group .btn-filter:hover {
            background-color: #5a67d8;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .filter-group .btn-filter.active {
            background-color: #434190;
            font-weight: 700;
        }

        .columns-container { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: start; }
        .launch-section { background: white; padding: 20px; border-radius: 12px; }
        .section-header { margin-bottom: 20px; }
        .section-header h2 { font-size: 22px; color: #333; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { 
            padding: 12px 8px; text-align: left; 
            border-bottom: 1px solid #f0f0f0;
            vertical-align: middle;
        }
        th { font-weight: 600; color: #666; font-size: 11px; text-transform: uppercase; }
        td { font-size: 13px; color: #333; }
        
        .truncate-text {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100px;
        }
        td:first-child { max-width: 150px; }

        .status-badge { display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: 700; text-align: center; white-space: nowrap; }
        .status-recebida, .status-paga { background-color: #e8f5e9; color: #2e7d32; }
        .status-a_receber, .status-a_pagar { background-color: #fff3e0; color: #f57c00; }
        .status-vencida { background-color: #ffebee; color: #c62828; }
        
        .actions-dropdown { position: relative; }
        .actions-btn { background: transparent; border: none; color: #667eea; border-radius: 8px; width: 35px; height: 35px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .actions-btn:hover { background-color: rgba(102, 126, 234, 0.1); }
        .dropdown-menu { display: none; position: absolute; right: 0; top: 100%; background: white; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 10; min-width: 150px; overflow: hidden; }
        .dropdown-menu.show { display: block; }
        .dropdown-item { display: block; width: 100%; padding: 10px 15px; color: #333; text-decoration: none; font-size: 14px; background: none; border: none; text-align: left; cursor: pointer; }
        .dropdown-item:hover { background: #f5f5f5; }
        .dropdown-item-danger { color: #c62828; }
        
        .pendentes-section { background: #fffde7; border: 1px solid #fff59d; padding: 20px; border-radius: 12px; margin-bottom: 30px; }
        .pendentes-section h2 { color: #f57f17; }
        .pendentes-section table td, .pendentes-section table th { border-color: #fff9c4; }
        .pendentes-form { display: flex; align-items: center; gap: 10px; }
        .pendentes-form select { padding: 8px; border-radius: 6px; border: 1px solid #ccc; }
        .pendentes-form button { padding: 8px 16px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames IA</span></a>
            <a href="/faturamento/" class="menu-item active"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">
                ⬅️ Sair
            </a>
        </div>
    </div>
    <div class="main-content">
        <div class="page-header"><h1>💰 Gestão Financeira</h1></div>
        
        <div class="stats-grid">
            <div class="stat-card"><h3>Receitas Recebidas</h3><div class="amount text-success">R$ {{ dashboard_data.receitas.recebidas|default:'0.00' }}</div></div>
            <div class="stat-card"><h3>Receitas a Receber</h3><div class="amount text-warning">R$ {{ dashboard_data.receitas.a_receber|default:'0.00' }}</div></div>
            <div class="stat-card"><h3>Despesas Pagas</h3><div class="amount text-info">R$ {{ dashboard_data.despesas.pagas|default:'0.00' }}</div></div>
            <div class="stat-card"><h3>Despesas a Pagar</h3><div class="amount text-danger">R$ {{ dashboard_data.despesas.a_pagar|default:'0.00' }}</div></div>
            <div class="stat-card"><h3>Lucro Líquido</h3><div class="amount text-primary">R$ {{ dashboard_data.lucro_liquido|default:'0.00' }}</div></div>
        </div>

        <div class="actions-bar">
            <div class="filter-group">
                <span>Período:</span>
                <button class="btn btn-filter" id="filter-today">Hoje</button>
                <button class="btn btn-filter" id="filter-week">Semanal</button>
                <button class="btn btn-filter" id="filter-month">Mensal</button>
                <button class="btn btn-filter" id="filter-year">Anual</button>
            </div>
            <!-- <<< INÍCIO DAS ALTERAÇÕES NO HTML DOS BOTÕES DE AÇÃO >>> -->
            <div class="actions-group">
                <a href="{% url 'receita_nova' %}" class="btn btn-success">Nova Receita</a>
                <a href="{% url 'despesa_nova' %}" class="btn btn-danger">Nova Despesa</a>
            </div>
            <!-- <<< FIM DAS ALTERAÇÕES NO HTML DOS BOTÕES DE AÇÃO >>> -->
        </div>

        {% if agendamentos_pendentes %}
        <div class="pendentes-section">
            <div class="section-header">
                <h2>🔔 Atendimentos Pendentes de Recebimento</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Paciente</th>
                        <th>Serviço</th>
                        <th>Data</th>
                        <th>Valor</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
                    {% for ag in agendamentos_pendentes %}
                    <tr>
                        <td>{{ ag.paciente_nome }}</td>
                        <td>{{ ag.servico }}</td>
                        <td>{{ ag.data }}</td>
                        <td class="text-success">R$ {{ ag.valor }}</td>
                        <td>
                            <form method="POST" action="/faturamento/receber-agendamento/{{ ag.id }}/" class="pendentes-form">
                                {% csrf_token %}
                                <select name="forma_pagamento" required>
                                    <option value="Dinheiro">Dinheiro</option>
                                    <option value="PIX">PIX</option>
                                    <option value="Cartão de Débito">Débito</option>
                                    <option value="Cartão de Crédito">Crédito</option>
                                </select>
                                <button type="submit" class="btn btn-success">Receber</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <div class="columns-container">
            <div class="launch-section">
                <div class="section-header"><h2>Receitas</h2></div>
                <table>
                    <thead><tr><th>Descrição</th><th>Valor</th><th>Categoria</th><th>Vencimento</th><th>Status</th><th>Ações</th></tr></thead>
                    <tbody>
                        {% if receitas_html %}{{ receitas_html }}{% else %}<tr><td colspan="6" style="text-align:center; padding: 20px;">Nenhuma receita encontrada.</td></tr>{% endif %}
                    </tbody>
                </table>
            </div>

            <div class="launch-section">
                <div class="section-header"><h2>Despesas</h2></div>
                <table>
                    <thead><tr><th>Descrição</th><th>Valor</th><th>Categoria</th><th>Vencimento</th><th>Status</th><th>Ações</th></tr></thead>
                    <tbody>
                        {% if despesas_html %}{{ despesas_html }}{% else %}<tr><td colspan="6" style="text-align:center; padding: 20px;">Nenhuma despesa encontrada.</td></tr>{% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            function navigateWithFilter(params) {
                const url = new URL(window.location.href);
                url.search = new URLSearchParams(params).toString();
                window.location.href = url.toString();
            }

            document.getElementById('filter-week').addEventListener('click', () => {
                const today = new Date();
                const dayOfWeek = today.getDay();
                const startOfWeek = new Date(today);
                startOfWeek.setDate(today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1));

                const endOfWeek = new Date(startOfWeek);
                endOfWeek.setDate(startOfWeek.getDate() + 6);
                
                const startDateStr = startOfWeek.toISOString().slice(0, 10);
                const endDateStr = endOfWeek.toISOString().slice(0, 10);
                
                navigateWithFilter({ data_inicial: startDateStr, data_final: endDateStr });
            });

            document.getElementById('filter-today').addEventListener('click', () => {
                const todayStr = new Date().toISOString().slice(0, 10);
                navigateWithFilter({ data_inicial: todayStr, data_final: todayStr });
            });

            document.getElementById('filter-month').addEventListener('click', () => {
                const d = new Date();
                const startDateStr = new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
                const endDateStr = new Date(d.getFullYear(), d.getMonth() + 1, 0).toISOString().slice(0, 10);
                navigateWithFilter({ data_inicial: startDateStr, data_final: endDateStr });
            });
            
            document.getElementById('filter-year').addEventListener('click', () => {
                const y = new Date().getFullYear();
                navigateWithFilter({ data_inicial: `${y}-01-01`, data_final: `${y}-12-31` });
            });

            document.addEventListener('click', function(event) {
                const isActionsButton = event.target.closest('.actions-btn');
                document.querySelectorAll('.dropdown-menu.show').forEach(openDropdown => {
                    if (!isActionsButton || openDropdown.id !== isActionsButton.getAttribute('data-dropdown-id')) {
                        openDropdown.classList.remove('show');
                    }
                });
                if (isActionsButton) {
                    const dropdownId = isActionsButton.getAttribute('data-dropdown-id');
                    document.getElementById(dropdownId).classList.toggle('show');
                }
            });
        });
    </script>
</body>
</html>
"""

FATURAMENTO_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Gestão Financeira - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; padding: 30px 20px; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; border: none; cursor: pointer; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 20px; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .stat-card h3 { font-size: 14px; color: #666; margin-bottom: 10px; font-weight: 600; text-transform: uppercase; }
        .stat-card .amount { font-size: 28px; font-weight: 700; }
        .text-success { color: #2e7d32; }
        .text-danger { color: #c62828; }
        .text-warning { color: #f57c00; }
        .text-info { color: #0277bd; }
        .text-primary { color: #5a67d8; }

        .card-receitas {
            background: rgba(76, 175, 80, 0.1);
            border: 1px solid rgba(76, 175, 80, 0.2);
        }
        .card-despesas {
            background: rgba(244, 67, 54, 0.1);
            border: 1px solid rgba(244, 67, 54, 0.2);
        }
        .card-lucro {
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.2);
        }

        .actions-bar { display: flex; justify-content: space-between; align-items: center; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .actions-group { display: flex; align-items: center; gap: 10px; }
        .btn { padding: 10px 20px; border-radius: 8px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: all 0.2s; }
        
        .btn-success {
            background: rgba(76, 175, 80, 0.15);
            color: #2e7d32;
            border-radius: 20px;
        }
        .btn-success:hover {
            background: rgba(76, 175, 80, 0.25);
            transform: translateY(-2px);
        }
        .btn-danger {
            background: rgba(244, 67, 54, 0.15);
            color: #c62828;
            border-radius: 20px;
        }
        .btn-danger:hover {
            background: rgba(244, 67, 54, 0.25);
            transform: translateY(-2px);
        }

        .filter-group { 
            display: flex; 
            align-items: center; 
            gap: 10px; 
        }
        .filter-group span {
            color: #555;
            font-weight: 600;
            font-size: 14px;
            padding-right: 5px;
        }
        .filter-group .btn-filter {
            background: rgba(102, 126, 234, 0.15);
            border: none;
            color: #434190;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .filter-group .btn-filter:hover {
            background-color: rgba(102, 126, 234, 0.25);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        /* <<< ESTILO ADICIONADO PARA O BOTÃO ATIVO >>> */
        .filter-group .btn-filter.active {
            background-color: #434190;
            color: white;
            font-weight: 700;
        }

        .columns-container { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: start; }
        .launch-section { background: white; padding: 20px; border-radius: 12px; }
        .section-header { margin-bottom: 20px; }
        .section-header h2 { font-size: 22px; color: #333; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { 
            padding: 12px 8px; text-align: left; 
            border-bottom: 1px solid #f0f0f0;
            vertical-align: middle;
        }
        th { font-weight: 600; color: #666; font-size: 11px; text-transform: uppercase; }
        td { font-size: 13px; color: #333; }
        
        .truncate-text {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100px;
        }
        td:first-child { max-width: 150px; }

        .status-badge { display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: 700; text-align: center; white-space: nowrap; }
        .status-recebida, .status-paga { background-color: #e8f5e9; color: #2e7d32; }
        .status-a_receber, .status-a_pagar { background-color: #fff3e0; color: #f57c00; }
        .status-vencida { background-color: #ffebee; color: #c62828; }
        
        .actions-dropdown { position: relative; }
        .actions-btn { background: transparent; border: none; color: #667eea; border-radius: 8px; width: 35px; height: 35px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .actions-btn:hover { background-color: rgba(102, 126, 234, 0.1); }
        .dropdown-menu { display: none; position: absolute; right: 0; top: 100%; background: white; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 10; min-width: 150px; overflow: hidden; }
        .dropdown-menu.show { display: block; }
        .dropdown-item { display: block; width: 100%; padding: 10px 15px; color: #333; text-decoration: none; font-size: 14px; background: none; border: none; text-align: left; cursor: pointer; }
        .dropdown-item:hover { background: #f5f5f5; }
        .dropdown-item-danger { color: #c62828; }
        
        .pendentes-section { background: #fffde7; border: 1px solid #fff59d; padding: 20px; border-radius: 12px; margin-bottom: 30px; }
        .pendentes-section h2 { color: #f57f17; }
        .pendentes-section table td, .pendentes-section table th { border-color: #fff9c4; }
        .pendentes-form { display: flex; align-items: center; gap: 10px; }
        .pendentes-form select { padding: 8px; border-radius: 6px; border: 1px solid #ccc; }
        .pendentes-form button { padding: 8px 16px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item active"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">
                ⬅️ Sair
            </a>
        </div>
    </div>
    <div class="main-content">
        <div class="page-header"><h1>💰 Gestão Financeira</h1></div>
        
        <div class="stats-grid">
            <div class="stat-card card-receitas"><h3>Receitas Recebidas</h3><div class="amount text-success">R$ {{ dashboard_data.receitas.recebidas|default:'0.00' }}</div></div>
            <div class="stat-card"><h3>Receitas a Receber</h3><div class="amount text-success">R$ {{ dashboard_data.receitas.a_receber|default:'0.00' }}</div></div>
            <div class="stat-card"><h3>Receitas Vencidas</h3><div class="amount text-success">R$ {{ dashboard_data.receitas.vencidas|default:'0.00' }}</div></div>
            <div class="stat-card card-despesas"><h3>Despesas Pagas</h3><div class="amount text-danger">R$ {{ dashboard_data.despesas.pagas|default:'0.00' }}</div></div>
            
            <div class="stat-card"><h3>Despesas a Pagar</h3><div class="amount text-danger">R$ {{ dashboard_data.despesas.a_pagar|default:'0.00' }}</div></div>
            <div class="stat-card"><h3>Despesas Vencidas</h3><div class="amount text-danger">R$ {{ dashboard_data.despesas.vencidas|default:'0.00' }}</div></div>
            <div class="stat-card card-lucro">
                <h3>Lucro Líquido</h3>
                {% if dashboard_data.lucro_liquido >= 0 %}
                    <div class="amount text-success">R$ {{ dashboard_data.lucro_liquido|default:'0.00' }}</div>
                {% else %}
                    <div class="amount text-danger">R$ {{ dashboard_data.lucro_liquido|default:'0.00' }}</div>
                {% endif %}
            </div>
        </div>

        <div class="actions-bar">
            <div class="filter-group">
                <span>Período:</span>
                <!-- <<< ADIÇÃO DA LÓGICA DE CLASSE 'active' >>> -->
                <button class="btn btn-filter {% if filtro_ativo == 'hoje' %}active{% endif %}" id="filter-today">Hoje</button>
                <button class="btn btn-filter {% if filtro_ativo == 'semana' %}active{% endif %}" id="filter-week">Semanal</button>
                <button class="btn btn-filter {% if filtro_ativo == 'mes' %}active{% endif %}" id="filter-month">Mensal</button>
                <button class="btn btn-filter {% if filtro_ativo == 'ano' %}active{% endif %}" id="filter-year">Anual</button>
            </div>
            <div class="actions-group">
                <a href="{% url 'receita_nova' %}" class="btn btn-success">Nova Receita</a>
                <a href="{% url 'despesa_nova' %}" class="btn btn-danger">Nova Despesa</a>
            </div>
        </div>

        {% if agendamentos_pendentes %}
        <div class="pendentes-section">
            <div class="section-header">
                <h2>🔔 Atendimentos Pendentes de Recebimento</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Paciente</th>
                        <th>Serviço</th>
                        <th>Data</th>
                        <th>Valor</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
                    {% for ag in agendamentos_pendentes %}
                    <tr>
                        <td>{{ ag.paciente_nome }}</td>
                        <td>{{ ag.servico }}</td>
                        <td>{{ ag.data }}</td>
                        <td class="text-success">R$ {{ ag.valor }}</td>
                        <td>
                            <form method="POST" action="/faturamento/receber-agendamento/{{ ag.id }}/" class="pendentes-form">
                                {% csrf_token %}
                                <select name="forma_pagamento" required>
                                    <option value="Dinheiro">Dinheiro</option>
                                    <option value="PIX">PIX</option>
                                    <option value="Cartão de Débito">Débito</option>
                                    <option value="Cartão de Crédito">Crédito</option>
                                </select>
                                <button type="submit" class="btn btn-success">Receber</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <div class="columns-container">
            <div class="launch-section">
                <div class="section-header"><h2>Receitas</h2></div>
                <table>
                    <thead><tr><th>Descrição</th><th>Valor</th><th>Categoria</th><th>Vencimento</th><th>Status</th><th>Ações</th></tr></thead>
                    <tbody>
                        {% if receitas_html %}{{ receitas_html }}{% else %}<tr><td colspan="6" style="text-align:center; padding: 20px;">Nenhuma receita encontrada.</td></tr>{% endif %}
                    </tbody>
                </table>
            </div>

            <div class="launch-section">
                <div class="section-header"><h2>Despesas</h2></div>
                <table>
                    <thead><tr><th>Descrição</th><th>Valor</th><th>Categoria</th><th>Vencimento</th><th>Status</th><th>Ações</th></tr></thead>
                    <tbody>
                        {% if despesas_html %}{{ despesas_html }}{% else %}<tr><td colspan="6" style="text-align:center; padding: 20px;">Nenhuma despesa encontrada.</td></tr>{% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            function navigateWithFilter(params) {
                const url = new URL(window.location.href);
                url.search = new URLSearchParams(params).toString();
                window.location.href = url.toString();
            }

            document.getElementById('filter-week').addEventListener('click', () => {
                const today = new Date();
                const dayOfWeek = today.getDay();
                const startOfWeek = new Date(today);
                startOfWeek.setDate(today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1));

                const endOfWeek = new Date(startOfWeek);
                endOfWeek.setDate(startOfWeek.getDate() + 6);
                
                const startDateStr = startOfWeek.toISOString().slice(0, 10);
                const endDateStr = endOfWeek.toISOString().slice(0, 10);
                
                navigateWithFilter({ data_inicial: startDateStr, data_final: endDateStr });
            });

            document.getElementById('filter-today').addEventListener('click', () => {
                const todayStr = new Date().toISOString().slice(0, 10);
                navigateWithFilter({ data_inicial: todayStr, data_final: todayStr });
            });

            document.getElementById('filter-month').addEventListener('click', () => {
                const d = new Date();
                const startDateStr = new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
                const endDateStr = new Date(d.getFullYear(), d.getMonth() + 1, 0).toISOString().slice(0, 10);
                navigateWithFilter({ data_inicial: startDateStr, data_final: endDateStr });
            });
            
            document.getElementById('filter-year').addEventListener('click', () => {
                const y = new Date().getFullYear();
                navigateWithFilter({ data_inicial: `${y}-01-01`, data_final: `${y}-12-31` });
            });

            document.addEventListener('click', function(event) {
                const isActionsButton = event.target.closest('.actions-btn');
                document.querySelectorAll('.dropdown-menu.show').forEach(openDropdown => {
                    if (!isActionsButton || openDropdown.id !== isActionsButton.getAttribute('data-dropdown-id')) {
                        openDropdown.classList.remove('show');
                    }
                });
                if (isActionsButton) {
                    const dropdownId = isActionsButton.getAttribute('data-dropdown-id');
                    document.getElementById(dropdownId).classList.toggle('show');
                }
            });
        });
    </script>
</body>
</html>
"""

LANCAMENTO_VISUALIZAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ form_title }} - intelliMed</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f5f7fa; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .container { background: white; padding: 40px; border-radius: 12px; max-width: 700px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-bottom: 30px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; }
        .info-grid { display: grid; grid-template-columns: 200px 1fr; gap: 15px; margin-bottom: 25px; }
        .info-grid .label { font-weight: 600; color: #666; font-size: 14px; }
        .info-grid .value { color: #333; font-size: 15px; }
        .btn-secondary { display: inline-block; padding: 12px 30px; background: #e0e0e0; color: #666; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ form_title }}</h1>
        <div class="info-grid">
            <div class="label">Descrição:</div><div class="value">{{ lancamento.descricao }}</div>
            <div class="label">Valor:</div><div class="value">R$ {{ lancamento.valor }}</div>
            <div class="label">Categoria:</div><div class="value">{{ lancamento.categoria_nome|default:"Sem Categoria" }}</div>
            <div class="label">Data de Vencimento:</div><div class="value">{{ lancamento.data_vencimento }}</div>
            <div class="label">Status:</div><div class="value">{{ lancamento.status_display }}</div>
            {% if lancamento.data_recebimento %}
            <div class="label">Data de Recebimento:</div><div class="value">{{ lancamento.data_recebimento }}</div>
            {% endif %}
            {% if lancamento.data_pagamento %}
            <div class="label">Data de Pagamento:</div><div class="value">{{ lancamento.data_pagamento }}</div>
            {% endif %}
        </div>
        <a href="/faturamento/" class="btn-secondary">Voltar</a>
    </div>
</body>
</html>
"""

SETUP_RESULTADO_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Resultado da Configuração - intelliMed</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f5f7fa; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .container { background: white; padding: 40px; border-radius: 12px; text-align: center; max-width: 600px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .success h1 { color: #2e7d32; }
        .error h1 { color: #c62828; }
        p { color: #333; font-size: 16px; margin: 20px 0; }
        a { display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container {{ status }}">
        <h1>{{ titulo }}</h1>
        <p>{{ mensagem }}</p>
        <a href="/faturamento/">Voltar para a Gestão Financeira</a>
    </div>
</body>
</html>
"""

INFORMACOES_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informações da Clínica - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; padding: 30px 20px; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; border: none; cursor: pointer; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 30px; }
        
        .info-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; }
        .info-section { grid-column: span 3; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .info-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; }
        
        .section-title { font-size: 22px; color: #333; margin-bottom: 25px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; }
        
        .info-card h3 { font-size: 14px; color: #666; margin-bottom: 10px; font-weight: 600; text-transform: uppercase; }
        .info-card .number { font-size: 36px; font-weight: 700; color: #667eea; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
        th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        td { font-size: 14px; color: #333; }

        .status-dot {
            height: 12px;
            width: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: blinker 1.5s linear infinite;
        }
        .status-dot.online { background-color: #4CAF50; }
        .status-dot.offline { background-color: #f44336; animation: none; }

        @keyframes blinker {  
            50% { opacity: 0.3; }
        }

        .stats-table td { font-weight: 600; }
        .stats-table td:first-child { color: #555; font-weight: 500; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames IA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item active"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <div class="page-header"><h1>ℹ️ Informações da Clínica</h1></div>
        
        {% if error_message %}
            <div class="info-section" style="background-color: #ffebee; color: #c62828;">
                <h2>Erro ao Carregar Dados</h2>
                <p>{{ error_message }}</p>
            </div>
        {% else %}
            <div class="info-container">
                <div class="info-card">
                    <h3>Usuários Cadastrados</h3>
                    <p class="number">{{ data.usuarios.total|default:"-" }}</p>
                </div>
                <div class="info-card">
                    <h3>Pacientes Ativos</h3>
                    <p class="number">{{ data.estatisticas_gerais.pacientes.total|default:"-" }}</p>
                </div>
                <div class="info-card">
                    <h3>Pacientes Arquivados</h3>
                    <p class="number">{{ total_inativos|default:"-" }}</p>
                </div>

                <div class="info-section">
                    <h2 class="section-title">👥 Usuários do Sistema</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Nome</th>
                                <th>Função</th>
                                <th>Email</th>
                                <th>Último Login</th>
                            </tr>
                        </thead>
                        <tbody>
                        {% for usuario in data.usuarios.lista %}
                            <tr>
                                <td>
                                    {% if usuario.status == 'ativo' %}
                                        <span class="status-dot online" title="Ativo"></span> Ativo
                                    {% else %}
                                        <span class="status-dot offline" title="Inativo"></span> Inativo
                                    {% endif %}
                                </td>
                                <td>{{ usuario.nome_completo }}</td>
                                <td>{{ usuario.funcao_display }}</td>
                                <td>{{ usuario.email }}</td>
                                <td>{{ usuario.last_login|default:"Nunca" }}</td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="5" style="text-align: center;">Nenhum usuário encontrado.</td></tr>
                        {% endfor %}
                        </tbody>
                    </table>
                </div>

                <div class="info-section">
                    <h2 class="section-title">📅 Estatísticas de Agendamentos (Mês Atual)</h2>
                    <table class="stats-table">
                        <tbody>
                            <tr><td>Total de Agendamentos no Mês</td><td>{{ data.estatisticas_gerais.agendamentos.mes_atual|default:0 }}</td></tr>
                            {% for stat in data.estatisticas_gerais.agendamentos.por_status %}
                                <tr><td>Total de {{ stat.status }}</td><td>{{ stat.total }}</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    <p style="font-size: 12px; color: #888; margin-top: 15px;">Nota: Estatísticas detalhadas para outros períodos (semanal, anual) serão adicionadas em breve.</p>
                </div>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

EXAMES_IA_TERMOS_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Aviso Importante - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; padding: 30px 20px; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .terms-container { max-width: 900px; margin: auto; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .terms-header { padding: 30px; background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); color: white; border-top-left-radius: 12px; border-top-right-radius: 12px; }
        .terms-header h1 { font-size: 24px; margin-bottom: 10px; }
        .terms-body { padding: 30px; font-size: 16px; line-height: 1.7; color: #333; }
        .terms-body p { margin-bottom: 15px; }
        .terms-footer { padding: 20px 30px; text-align: right; }
        
        /* <<< INÍCIO DAS ALTERAÇÕES DE ESTILO >>> */
        .btn { 
            padding: 12px 30px; 
            border-radius: 25px; /* Efeito Pílula */
            font-weight: 600; 
            text-decoration: none; 
            border: none; 
            cursor: pointer; 
            transition: all 0.2s; 
        }
        .btn-primary { 
            background: rgba(76, 175, 80, 0.8); /* Verde com transparência */
            color: white; 
        }
        .btn-primary:hover {
            background: rgba(76, 175, 80, 1); /* Verde opaco no hover */
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        /* <<< FIM DAS ALTERAÇÕES DE ESTILO >>> */

    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
             <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item active"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <div class="terms-container">
            <div class="terms-header">
                <!-- <<< ALTERAÇÃO NO TEXTO DO TÍTULO >>> -->
                <h1>⚠️ Aviso Importante sobre o Uso da iA</h1>
            </div>
            <div class="terms-body">
                <p>A ferramenta de Análise Inteligente de Exames utiliza inteligência artificial para fornecer uma interpretação preliminar e de apoio diagnóstico.</p>
                <p><strong>Ela NÃO substitui a avaliação, o julgamento clínico e a responsabilidade final de um profissional de saúde qualificado.</strong></p>
                <p>Toda interpretação gerada pela iA deve ser rigorosamente revisada, validada e, se necessário, corrigida por um médico antes de ser utilizada para qualquer decisão clínica.</p>
            </div>
            <div class="terms-footer">
                <form action="{% url 'exames_analise' %}" method="get">
                    <!-- <<< ALTERAÇÃO NO TEXTO DO BOTÃO >>> -->
                    <button type="submit" class="btn btn-primary">Concordar e Continuar</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

EXAMES_IA_PRINCIPAL_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Análise de Exames - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 30px; }
        
        .upload-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 700px; margin: 0 auto 40px auto; }
        .upload-card h2 { font-size: 20px; color: #333; margin-bottom: 25px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; font-weight: 600; margin-bottom: 8px; color: #333; }
        .form-group select, .form-group input { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; }
        #file-upload-area { border: 2px dashed #ccc; border-radius: 8px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.3s; }
        #file-upload-area:hover { border-color: #667eea; background: #f9f9ff; }
        #file-info { margin-top: 15px; font-size: 14px; color: #555; }
        .btn { padding: 12px 30px; border-radius: 8px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: all 0.2s; }
        
        .btn-primary { 
            background: rgba(102, 126, 234, 0.8);
            color: white;
            border-radius: 25px;
        }
        .btn-primary:hover {
            background: rgba(102, 126, 234, 1);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .btn-primary:disabled { background: #aaa; cursor: not-allowed; transform: none; box-shadow: none;}
        .loading-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; }
        .loading-overlay.show { display: flex; }
        .spinner { border: 8px solid #f3f3f3; border-top: 8px solid #667eea; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite; }
        .loading-text { margin-top: 20px; font-size: 16px; color: #333; font-weight: 600; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .history-section { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid #f0f0f0; }
        th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        .alert { padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .alert-success { background: #e8f5e9; color: #2e7d32; }
        .alert-error { background: #ffebee; color: #c62828; }

        .action-link { 
            text-decoration: none; 
            padding: 5px 10px; 
            border-radius: 5px; 
            font-size: 13px; 
            margin-right: 5px;
        }
        .link-view { background-color: #e3f2fd; color: #0d47a1; }
        .link-delete { background-color: #ffebee; color: #b71c1c; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
             <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item active"><span class="menu-item-icon">🔬</span> <span>Exames IA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <div class="page-header"><h1>🔬 Análise Inteligente de Exames</h1></div>
        
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">{{ message }}</div>
            {% endfor %}
        {% endif %}

        <div class="upload-card">
            <h2>Novo Envio para Análise</h2>
            <form id="uploadForm" method="POST" action="{% url 'exames_analise' %}" enctype="multipart/form-data">
                {% csrf_token %}
                <div class="form-group">
                    <label for="paciente">1. Selecione o Paciente</label>
                    <select name="paciente_id" id="paciente" required>
                        <option value="">Selecione...</option>
                        {% for p in pacientes %}
                            <option value="{{ p.id }}">{{ p.nome_completo }} (CPF: {{ p.cpf }})</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>2. Envie o Arquivo do Exame</label>
                    <div id="file-upload-area">
                        <input type="file" name="arquivo" id="arquivo" accept="image/*,.pdf" style="display: none;" required>
                        <!-- <<< AQUI ESTÁ A ALTERAÇÃO DO TEXTO >>> -->
                        <p><strong>Clique para selecionar</strong></p>
                        <p id="file-info"></p>
                    </div>
                </div>
                <button type="submit" id="submitBtn" class="btn btn-primary" style="width: 100%;">Analisar Exame com iA</button>
            </form>
        </div>
        
        <div class="history-section">
            <h2>Histórico de Análises</h2>
            <table>
                <thead>
                    <tr><th>Paciente</th><th>Tipo do Exame</th><th>Data</th><th>Status</th><th>Ações</th></tr>
                </thead>
                <tbody>
                    {% for exame in exames %}
                    <tr>
                        <td>{{ exame.paciente_nome }}</td>
                        <td>{{ exame.tipo_exame_display }}</td>
                        <td>{{ exame.data_exame }}</td>
                        <td>{{ exame.status_display }}</td>
                        <td>
                            <a href="/exames/{{ exame.id }}/visualizar/" class="action-link link-view">Ver Laudo</a>
                            <a href="/exames/{{ exame.id }}/deletar/" onclick="return confirm('Tem certeza que deseja excluir este exame e seu laudo? Esta ação não pode ser desfeita.')" class="action-link link-delete">Deletar</a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr><td colspan="5" style="text-align:center; padding: 20px;">Nenhum exame analisado ainda.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
        <p class="loading-text">Analisando exame... Este processo pode levar alguns segundos.</p>
    </div>
    <script>
        const uploadArea = document.getElementById('file-upload-area');
        const fileInput = document.getElementById('arquivo');
        const fileInfo = document.getElementById('file-info');
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const loadingOverlay = document.getElementById('loadingOverlay');

        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                fileInfo.textContent = `Arquivo selecionado: ${fileInput.files[0].name}`;
            } else {
                fileInfo.textContent = '';
            }
        });

        form.addEventListener('submit', (e) => {
            if (form.getAttribute('action') !== "{% url 'exames_analise' %}") {
                form.setAttribute('action', "{% url 'exames_analise' %}");
            }
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando...';
            loadingOverlay.classList.add('show');
        });
    </script>
</body>
</html>
"""

EXAME_VISUALIZAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Laudo do Exame - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header { padding: 30px 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; }
        
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; margin-bottom: 3px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; border: none; cursor: pointer; }

        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .header-actions { display: flex; gap: 10px; }
        .btn { 
            padding: 10px 22px; 
            border-radius: 20px;
            font-weight: 600; 
            text-decoration: none; 
            border: none; 
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .btn-secondary { background: rgba(108, 117, 125, 0.15); color: #495057; }
        .btn-edit { background: rgba(255, 193, 7, 0.15); color: #b08800; }
        .btn-print { background: rgba(0, 123, 255, 0.15); color: #0056b3; }
        
        .laudo-container { display: flex; gap: 30px; align-items: flex-start; }
        .laudo-content { flex: 2; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .laudo-header { padding: 20px; border-bottom: 1px solid #eee; }
        .laudo-header h2 { font-size: 20px; color: #333; margin-bottom: 5px; }
        .laudo-header p { font-size: 14px; color: #666; }
        .laudo-body { padding: 20px; }
        #laudo-texto, #laudo-editor {
            width: 100%;
            white-space: pre-wrap; 
            font-family: 'Courier New', Courier, monospace; 
            font-size: 13px; 
            line-height: 1.6; 
            color: #333; 
            background: #fdfdfd;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #eee;
        }
        #laudo-editor {
            display: none;
            min-height: 600px;
            resize: vertical;
        }
        #btn-salvar-edicao {
            display: none;
            margin-top: 15px;
        }
        
        .info-sidebar { flex: 1; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 20px; }
        .info-title { font-size: 18px; color: #333; margin-bottom: 15px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        .info-item { margin-bottom: 12px; }
        .info-item label { display: block; font-size: 12px; font-weight: 600; color: #666; margin-bottom: 3px; }
        .info-item p { font-size: 14px; color: #333; }
        .badge { display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: 700; }
        .badge-success { background: #e8f5e9; color: #2e7d32; }
        .badge-warning { background: #fff8e1; color: #f57c00; }

        @media print {
            body {
                background: #fff;
            }
            .sidebar, .page-header, .info-sidebar {
                display: none;
            }
            .main-content {
                margin-left: 0;
                padding: 0;
                width: 100%;
            }
            .laudo-container, .laudo-content {
                box-shadow: none;
                border: none;
                padding: 0;
                margin: 0;
                width: 100%;
            }
            .laudo-body {
                padding: 0;
            }
            #laudo-texto, #laudo-editor {
                border: none;
                padding: 0;
                background: #fff;
                font-size: 12pt;
                font-family: 'Times New Roman', Times, serif;
            }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info">
            <strong>{{ user.nome_completo }}</strong>
            <small>{{ user.funcao_display }}</small>
        </div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item active"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <div class="page-header">
            <!-- <<< AQUI ESTÁ A ALTERAÇÃO NO TÍTULO >>> -->
            <div class="page-title"><h1>🔬 Laudo do Exame (iA)</h1></div>
            <div class="header-actions">
                <a href="{% url 'exames_analise' %}" class="btn btn-secondary">Voltar</a>
                <button id="btn-editar-laudo" class="btn btn-edit">✏️ Editar Laudo</button>
                <button onclick="window.print()" class="btn btn-print">🖨️ Imprimir</button>
            </div>
        </div>

        {% if error_message %}
            <div style="background: #ffebee; color: #c62828; padding: 20px; border-radius: 8px;">{{ error_message }}</div>
        {% else %}
            <div class="laudo-container">
                <div class="laudo-content">
                    <div class="laudo-header">
                        <h2>{{ exame.tipo_exame_identificado_ia|default:"Laudo de Exame" }}</h2>
                        <p>Análise gerada por Inteligência Artificial</p>
                    </div>
                    <div class="laudo-body">
                        <div id="laudo-texto">{{ exame.interpretacao_ia|default:"Conteúdo do laudo não disponível." }}</div>
                        <form id="form-edicao" method="POST">
                            {% csrf_token %}
                            <textarea id="laudo-editor" name="laudo_editado">{{ exame.interpretacao_ia }}</textarea>
                            <button type="submit" id="btn-salvar-edicao" class="btn btn-print">💾 Salvar Alterações</button>
                        </form>
                    </div>
                </div>
                <div class="info-sidebar">
                    <h3 class="info-title">Detalhes do Exame</h3>
                    <div class="info-item">
                        <label>Paciente</label>
                        <p>{{ exame.paciente_nome }}</p>
                    </div>
                    <div class="info-item">
                        <label>Data do Exame</label>
                        <p>{{ exame.data_exame }}</p>
                    </div>
                    <div class="info-item">
                        <label>ID do Exame</label>
                        <p>#{{ exame.id }}</p>
                    </div>
                    <div class="info-item">
                        <label>Status</label>
                        <p><span class="badge badge-success">{{ exame.status_display }}</span></p>
                    </div>
                    <div class="info-item">
                        <label>Confiança da iA</label>
                        <p><span class="badge badge-warning">{{ exame.confianca_ia|floatformat:2 }}%</span></p>
                    </div>
                    <div class="info-item">
                        <label>Revisão Médica</label>
                        <p>{{ exame.revisado_por_medico|yesno:"Sim,Requer Revisão" }}</p>
                    </div>
                </div>
            </div>
        {% endif %}
    </div>

    <script>
        document.getElementById('btn-editar-laudo').addEventListener('click', function() {
            document.getElementById('laudo-texto').style.display = 'none';
            document.getElementById('laudo-editor').style.display = 'block';
            document.getElementById('btn-salvar-edicao').style.display = 'block';
            this.style.display = 'none';
        });
    </script>
</body>
</html>
"""

EXAME_GERAL_VISUALIZAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Detalhes do Exame Geral - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; padding: 30px 20px; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .btn { padding: 10px 20px; border-radius: 20px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; }
        .btn-primary { background: rgba(86, 105, 211, 0.8); color: white; }
        
        .details-container { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 800px; }
        .section-title { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; }
        .info-grid { display: grid; grid-template-columns: 150px 1fr; gap: 10px; margin-bottom: 25px; font-size: 15px; }
        .info-grid .label { font-weight: 600; color: #666; }
        .info-grid .value { color: #333; }
        
        /* <<< INÍCIO DA CORREÇÃO DE ESTILO >>> */
        .resultado-box { 
            background: #f9f9f9; 
            padding: 15px; 
            border-radius: 8px; 
            border: 1px solid #eee; 
        }
        .resultado-box pre {
            white-space: pre-wrap; /* Mantém quebras de linha e espaços */
            word-wrap: break-word; /* Quebra palavras longas */
            font-family: 'Courier New', Courier, monospace; /* Garante fonte monoespaçada */
            font-size: 14px; /* Tamanho de fonte consistente */
            line-height: 1.6;
            margin: 0; /* Remove margem padrão da tag <pre> */
        }
        /* <<< FIM DA CORREÇÃO DE ESTILO >>> */
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item active"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
    </div>
    <div class="main-content">
        <div class="page-header">
            <div class="page-title"><h1>Detalhes do Exame Geral</h1></div>
            <a href="{% url 'paciente_exames' paciente.id %}" class="btn btn-primary">Voltar</a>
        </div>

        <div class="details-container">
            <h2 class="section-title">Informações do Exame</h2>
            <div class="info-grid">
                <div class="label">Paciente:</div><div class="value">{{ paciente.nome_completo }}</div>
                <div class="label">Tipo de Exame:</div><div class="value">{{ exame.tipo_exame_display }}</div>
                <div class="label">Data do Exame:</div><div class="value">{{ exame.data_exame_formatada }}</div>
                <div class="label">Status:</div><div class="value">{{ exame.status_display }}</div>
            </div>
            
            <h2 class="section-title">Resultado / Observações</h2>
            <div class="resultado-box">
                <!-- <<< ALTERAÇÃO PARA USAR A TAG <pre> >>> -->
                <pre>{{ exame.resultado_original|default:"Nenhum resultado registrado." }}</pre>
            </div>
        </div>
    </div>
</body>
</html>
"""

EXAME_GERAL_EDITAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Editar Exame Geral - intelliMed</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 20px; }
        .form-container { max-width: 800px; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; font-weight: 600; margin-bottom: 8px; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        .form-group input[readonly], .form-group select[disabled] { background: #f5f5f5; cursor: not-allowed; }
        .form-actions { display: flex; justify-content: flex-end; gap: 15px; margin-top: 20px; }
        .btn { padding: 12px 30px; border-radius: 25px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-secondary { background: #e0e0e0; color: #666; }
    </style>
</head>
<body>
    <div class="sidebar"><!-- Seu menu lateral aqui --></div>
    <div class="main-content">
        <h1>✏️ Editar Exame Geral</h1>
        <div class="form-container">
            <form method="POST">
                {% csrf_token %}
                <div class="form-group">
                    <label>Paciente</label>
                    <input type="text" value="{{ exame.paciente_nome }}" readonly>
                </div>
                <div class="form-group">
                    <label for="tipo_exame">Tipo de Exame</label>
                    <select name="tipo_exame" required>
                        <option value="hemograma" {% if exame.tipo_exame == 'hemograma' %}selected{% endif %}>Hemograma</option>
                        <option value="glicemia" {% if exame.tipo_exame == 'glicemia' %}selected{% endif %}>Glicemia de Jejum</option>
                        <option value="colesterol_total" {% if exame.tipo_exame == 'colesterol_total' %}selected{% endif %}>Colesterol Total e Frações</option>
                        <option value="urinalise" {% if exame.tipo_exame == 'urinalise' %}selected{% endif %}>Urinálise (EAS)</option>
                        <option value="gasometria" {% if exame.tipo_exame == 'gasometria' %}selected{% endif %}>Gasometria Arterial</option>
                        <option value="raio_x" {% if exame.tipo_exame == 'raio_x' %}selected{% endif %}>Raio-X</option>
                        <option value="ultrassonografia" {% if exame.tipo_exame == 'ultrassonografia' %}selected{% endif %}>Ultrassonografia</option>
                        <option value="tomografia" {% if exame.tipo_exame == 'tomografia' %}selected{% endif %}>Tomografia Computadorizada</option>
                        <option value="ressonancia" {% if exame.tipo_exame == 'ressonancia' %}selected{% endif %}>Ressonância Magnética</option>
                        <option value="eletrocardiograma" {% if exame.tipo_exame == 'eletrocardiograma' %}selected{% endif %}>Eletrocardiograma (ECG)</option>
                        <option value="ecocardiograma" {% if exame.tipo_exame == 'ecocardiograma' %}selected{% endif %}>Ecocardiograma</option>
                        <option value="endoscopia" {% if exame.tipo_exame == 'endoscopia' %}selected{% endif %}>Endoscopia Digestiva Alta</option>
                        <option value="colonoscopia" {% if exame.tipo_exame == 'colonoscopia' %}selected{% endif %}>Colonoscopia</option>
                        <option value="mamografia" {% if exame.tipo_exame == 'mamografia' %}selected{% endif %}>Mamografia</option>
                        <option value="densitometria" {% if exame.tipo_exame == 'densitometria' %}selected{% endif %}>Densitometria Óssea</option>
                        <option value="espirometria" {% if exame.tipo_exame == 'espirometria' %}selected{% endif %}>Espirometria</option>
                        <option value="outros" {% if exame.tipo_exame == 'outros' %}selected{% endif %}>Outros</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="data_exame">Data do Exame</label>
                    <input type="date" name="data_exame" value="{{ exame.data_exame }}" required>
                </div>
                <div class="form-group">
                    <label for="resultado_original">Resultado / Observações</label>
                    <textarea name="resultado_original" required rows="10">{{ exame.resultado_original }}</textarea>
                </div>
                <div class="form-actions">
                    <a href="{% url 'paciente_exames' paciente_id=exame.paciente %}" class="btn btn-secondary">Cancelar</a>
                    <button type="submit" class="btn btn-primary">Salvar Alterações</button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
"""


CONSULTAS_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Fila de Atendimento - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; padding: 30px 20px; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; }
        
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .page-title p { font-size: 14px; color: #666; }
        .btn-refresh { padding: 10px 20px; border-radius: 20px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; background: rgba(108, 117, 125, 0.15); color: #495057; }

        .fila-container { display: flex; flex-direction: column; gap: 15px; }
        .fila-item {
            background: white; border-radius: 12px; padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex;
            align-items: center; gap: 20px; transition: all 0.2s;
        }
        .fila-item:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.1); }
        .item-horario { font-size: 18px; font-weight: 700; color: #667eea; width: 70px; }
        .item-info { flex-grow: 1; }
        .item-info strong { font-size: 18px; color: #333; display: block; }
        .item-info p { font-size: 14px; color: #777; margin: 2px 0 0; }
        
        .btn-fila { padding: 12px 25px; border-radius: 25px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; }
        .btn-iniciar { background: #28a745; color: white; }
        .btn-continuar { background: #007bff; color: white; }
        .btn-fila:disabled { background: #6c757d; cursor: not-allowed; color: #ccc; }
        
        .empty-list { text-align: center; padding: 50px; background: white; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item active"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <div class="page-header">
            <div class="page-title">
                <h1>Fila de Atendimento</h1>
                <p>Pacientes agendados para hoje: {{ data.data }}</p>
            </div>
            <button onclick="location.reload()" class="btn-refresh">Atualizar</button>
        </div>

        {% if error_message %}
            <div style="background: #ffebee; color: #c62828; padding: 20px; border-radius: 8px;">{{ error_message }}</div>
        {% else %}
            <div class="fila-container">
                {% for item in data.fila %}
                    <div class="fila-item">
                        <div class="item-horario">{{ item.hora }}</div>
                        <div class="item-info">
                            <strong>{{ item.paciente_nome }}</strong>
                            <p>{{ item.tipo }} • {{ item.convenio }}</p>
                        </div>
                        <div class="item-actions">
                            <!-- ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼ -->
                            {% if item.consulta_status == 'em_atendimento' or item.consulta_status == 'aguardando_revisao' %}
                                <a href="{% url 'continuar_consulta' item.consulta_id %}" class="btn-fila btn-continuar">Continuar Atendimento</a>
                            {% elif item.pode_interagir %}
                                <form method="POST" action="/consultas/iniciar/{{ item.agendamento_id }}/">
                                    {% csrf_token %}
                                    <button type="submit" class="btn-fila btn-iniciar">Iniciar Atendimento</button>
                                </form>
                            {% else %}
                                <button class="btn-fila" disabled>{{ item.consulta_status|capfirst|default:"Concluído" }}</button>
                            {% endif %}
                            <!-- ▲▲▲ FIM DA CORREÇÃO ▲▲▲ -->
                        </div>
                    </div>
                {% empty %}
                    <div class="empty-list">
                        <h3>Nenhum paciente na fila para hoje.</h3>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# NO ARQUIVO: frontend.py

WORKSPACE_CONSULTA_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Consulta em Andamento - intelliMed</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; display: flex; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .sidebar-header h1 { font-size: 28px; font-weight: 700; padding: 30px 20px; }
        .user-info { padding: 20px; background: rgba(0,0,0,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .user-info strong { display: block; font-size: 14px; }
        .user-info small { font-size: 12px; opacity: 0.7; }
        .menu { flex: 1; padding: 20px 0; }
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .workspace-header { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .workspace-header h1 { font-size: 24px; color: #333; margin: 0; }
        .workspace-header p { color: #666; margin: 5px 0 0; }
        .timer { font-size: 22px; font-weight: 700; color: #007bff; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
        .card-title { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 15px; }
        .btn-rec { width: 60px; height: 60px; border-radius: 50%; border: 4px solid #ccc; background: #f0f0f0; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 28px; transition: all 0.2s; }
        .btn-rec.recording { background: #dc3545; border-color: #ffcdd2; color: white; animation: pulse-rec 1.5s infinite; }
        #recording-status { font-weight: 600; color: #666; }
        @keyframes pulse-rec { 0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(220, 53, 69, 0); } 100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); } }
        #transcription-output { max-height: 300px; overflow-y: auto; background: #f9f9f9; border-radius: 8px; padding: 15px; border: 1px solid #eee; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace; line-height: 1.6; }
        .final-actions { text-align: right; margin-top: 20px; }
        .btn { padding: 12px 30px; border-radius: 25px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        #document-generation-card { display: none; }
        .doc-buttons { display: flex; flex-wrap: wrap; gap: 10px; }
        .btn-doc { background: #e7e9fd; color: #434190; border: 1px solid #c9cfff; padding: 10px 15px; font-size: 14px; font-weight: 600; cursor: pointer;}
        .btn-doc:hover { background: #d9dcfd; }
        .btn-doc:disabled { background: #eee; color: #aaa; cursor: not-allowed; }
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: none; align-items: center; justify-content: center; z-index: 1000; }
        .modal-content { background: white; padding: 30px; border-radius: 12px; width: 90%; max-width: 800px; max-height: 90vh; display: flex; flex-direction: column; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .modal-title { font-size: 22px; }
        .modal-close { font-size: 24px; cursor: pointer; border: none; background: none; }
        .modal-body { flex: 1; overflow-y: auto; }
        .modal-body textarea { width: 100%; min-height: 400px; border-radius: 8px; border: 1px solid #ccc; padding: 15px; font-family: 'Courier New', Courier, monospace; font-size: 14px; }
        .modal-footer { text-align: right; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header"><h1>intelliMed</h1></div>
        <div class="user-info"><strong>{{ user.nome_completo }}</strong><small>{{ user.funcao_display }}</small></div>
        <nav class="menu">
            <a href="/dashboard/" class="menu-item"><span class="menu-item-icon">🏠</span> <span>Home</span></a>
            <a href="/pacientes/" class="menu-item"><span class="menu-item-icon">👥</span> <span>Pacientes</span></a>
            <a href="/agendamentos/" class="menu-item"><span class="menu-item-icon">📅</span> <span>Agendamentos</span></a>
            <a href="/consultas/" class="menu-item active"><span class="menu-item-icon">🩺</span> <span>Consultas</span></a>
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames iA</span></a>
            <a href="/faturamento/" class="menu-item"><span class="menu-item-icon">💰</span> <span>Faturamento</span></a>
            <a href="/informacoes/" class="menu-item"><span class="menu-item-icon">ℹ️</span> <span>Informações</span></a>
        </nav>
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <div class="workspace-header">
            <div>
                <h1>Consulta em Andamento</h1>
                <p>Paciente: <strong>{{ consulta.paciente_nome }}</strong> (ID: #{{ consulta.id }})</p>
            </div>
            <div id="timer" class="timer">00:00:00</div>
        </div>

        <div class="card">
            <h2 class="card-title">1. Gravação da Consulta</h2>
            <div style="display: flex; align-items: center; gap: 20px;">
                <button id="btn-rec" class="btn-rec" title="Iniciar Gravação">🎤</button>
                <div id="recording-status">Clique no microfone para iniciar a gravação</div>
            </div>
        </div>

        <div class="card">
            <h2 class="card-title">2. Transcrição iA</h2>
            <button id="btn-transcrever" class="btn btn-primary" style="display: none; margin-bottom: 15px; cursor: pointer;">🤖 Transcrever com iA</button>
            <div id="transcription-output">
                <p style="color: #999; text-align: center;">Aguardando gravação ser finalizada...</p>
            </div>
        </div>

        <div class="card" id="document-generation-card">
            <h2 class="card-title">3. Gerar Documentos</h2>
            <div class="doc-buttons">
                <button class="btn btn-doc" onclick="generateDocument('anamnese')">Anamnese</button>
                <button class="btn btn-doc" onclick="generateDocument('evolucao')">Evolução Médica</button>
                <button class="btn btn-doc" onclick="generateDocument('prescricao')">Prescrição Médica</button>
                <button class="btn btn-doc" onclick="generateDocument('atestado')">Atestado Médico</button>
                <button class="btn btn-doc" onclick="generateDocument('relatorio')">Relatório Completo</button>
            </div>
        </div>

        <div class="final-actions">
            <a href="/consultas/" class="btn btn-secondary">Finalizar Consulta</a>
        </div>
    </div>

    <div class="modal-overlay" id="document-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modal-title" class="modal-title"></h2>
                <button class="modal-close" onclick="closeModal()">×</button>
            </div>
            <div class="modal-body"><textarea id="modal-textarea"></textarea></div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button id="modal-save-btn" class="btn btn-primary">Salvar Documento</button>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const btnRec = document.getElementById('btn-rec');
            const btnTranscrever = document.getElementById('btn-transcrever');
            const recStatus = document.getElementById('recording-status');
            const transcriptionOutput = document.getElementById('transcription-output');
            const timerDisplay = document.getElementById('timer');
            const documentCard = document.getElementById('document-generation-card');
            
            let isRecording = false;
            let mediaRecorder;
            let audioChunks = [];
            let timerInterval;
            let seconds = 0;

            btnRec.addEventListener('click', () => {
                if (isRecording) stopRecording();
                else startRecording();
            });

            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    isRecording = true;
                    audioChunks = [];
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64String = reader.result.split(',')[1];
                            sendAudioToBackend(base64String);
                        };
                        reader.readAsDataURL(audioBlob);
                    };
                    mediaRecorder.start();
                    startTimer();
                    updateUIRecording(true);
                } catch (err) {
                    recStatus.textContent = "Erro ao acessar microfone: " + err.message;
                    recStatus.style.color = '#dc3545';
                }
            }

            function stopRecording() {
                if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
                isRecording = false;
                stopTimer();
                updateUIRecording(false);
            }

            function updateUIRecording(isRec) {
                if (isRec) {
                    btnRec.classList.add('recording');
                    btnRec.innerHTML = '⏹️';
                    recStatus.textContent = "Gravando... Clique para parar.";
                    recStatus.style.color = '#dc3545';
                } else {
                    btnRec.classList.remove('recording');
                    btnRec.innerHTML = '...';
                    recStatus.textContent = "Processando áudio para salvar...";
                    recStatus.style.color = '#007bff';
                    btnRec.disabled = true;
                }
            }
            
            function startTimer() {
                seconds = 0;
                timerInterval = setInterval(() => {
                    seconds++;
                    const h = String(Math.floor(seconds / 3600)).padStart(2, '0');
                    const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
                    const s = String(seconds % 60).padStart(2, '0');
                    timerDisplay.textContent = `${h}:${m}:${s}`;
                }, 1000);
            }
            function stopTimer() { clearInterval(timerInterval); }

            async function sendAudioToBackend(base64String) {
                const backendUrl = '{{ BACKEND_URL }}';
                const consultaId = '{{ consulta.id }}';
                try {
                    const response = await fetch(`${backendUrl}/api/consultas/${consultaId}/salvar-audio/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer {{ token }}` },
                        body: JSON.stringify({ audio_base64: base64String, audio_formato: 'webm' })
                    });
                    if (!response.ok) throw new Error('Falha ao salvar o áudio.');
                    
                    recStatus.textContent = "Áudio salvo com sucesso! Clique em 'Transcrever' para continuar.";
                    recStatus.style.color = '#28a745';
                    btnTranscrever.style.display = 'block';
                    btnRec.disabled = false;
                    btnRec.innerHTML = '🎤';

                } catch (err) {
                    recStatus.textContent = `Erro ao salvar áudio: ${err.message}`;
                    recStatus.style.color = '#dc3545';
                    btnRec.disabled = false;
                    btnRec.innerHTML = '🎤';
                }
            }

            btnTranscrever.addEventListener('click', async () => {
                btnTranscrever.disabled = true;
                btnTranscrever.textContent = 'Transcrevendo...';
                transcriptionOutput.textContent = 'Processando...';
                recStatus.textContent = "Aguarde, a iA está trabalhando...";
                recStatus.style.color = '#007bff';

                const backendUrl = '{{ BACKEND_URL }}';
                const consultaId = '{{ consulta.id }}';
                try {
                    const response = await fetch(`${backendUrl}/api/consultas/${consultaId}/transcrever-audio/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer {{ token }}` }
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.erro || `Erro ${response.status}`);
                    }

                    const data = await response.json();
                    transcriptionOutput.textContent = data.transcricao_ia || "Transcrição finalizada, mas sem conteúdo.";
                    recStatus.textContent = "Transcrição Concluída!";
                    recStatus.style.color = '#28a745';
                    documentCard.style.display = 'block';
                    btnTranscrever.style.display = 'none';
                
                } catch (err) {
                    recStatus.textContent = `Erro na transcrição: ${err.message}`;
                    recStatus.style.color = '#dc3545';
                    btnTranscrever.disabled = false;
                    btnTranscrever.textContent = '🤖 Transcrever com iA';
                }
            });

            window.generateDocument = async function(tipo) {
                const btn = document.querySelector(`.btn-doc[onclick="generateDocument('${tipo}')"]`);
                const originalText = btn.textContent;
                btn.textContent = 'Gerando...';
                btn.disabled = true;
                const backendUrl = '{{ BACKEND_URL }}', consultaId = '{{ consulta.id }}', token = '{{ token }}';
                try {
                    const response = await fetch(`${backendUrl}/api/consultas/${consultaId}/gerar-documento/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                        body: JSON.stringify({ tipo: tipo })
                    });
                    if (!response.ok) throw new Error('Falha ao gerar o documento.');
                    const data = await response.json();
                    showModal(tipo, data.documento.conteudo);
                } catch (error) { alert(error.message); } 
                finally { btn.textContent = originalText; btn.disabled = false; }
            }

            window.showModal = function(tipo, conteudo) {
                document.getElementById('modal-title').textContent = `Revisar ${tipo.charAt(0).toUpperCase() + tipo.slice(1)}`;
                document.getElementById('modal-textarea').value = conteudo;
                document.getElementById('modal-save-btn').onclick = () => saveDocument(tipo);
                document.getElementById('document-modal').style.display = 'flex';
            }

            window.closeModal = function() { document.getElementById('document-modal').style.display = 'none'; }

            window.saveDocument = async function(tipo) {
                const saveBtn = document.getElementById('modal-save-btn');
                saveBtn.textContent = 'Salvando...';
                saveBtn.disabled = true;
                const conteudo = document.getElementById('modal-textarea').value;
                const backendUrl = '{{ BACKEND_URL }}', consultaId = '{{ consulta.id }}', token = '{{ token }}';
                try {
                    const response = await fetch(`${backendUrl}/api/consultas/${consultaId}/salvar-documento/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                        body: JSON.stringify({ tipo: tipo, conteudo: conteudo, editado: true })
                    });
                    if (!response.ok) throw new Error('Falha ao salvar o documento.');
                    alert('Documento salvo com sucesso!');
                    closeModal();
                } catch(error) { alert(error.message); } 
                finally { saveBtn.textContent = 'Salvar Documento'; saveBtn.disabled = false; }
            }
        });
    </script>
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
    """Dashboard principal com cards de resumo."""
    
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    user = request.session.get('user', {})
    funcoes_pt = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'medico': 'Médico',
        'secretaria': 'Secretária'
    }
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    
    if user.get('funcao') == 'medico':
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    page_title = user.get('clinica_nome', 'Dashboard')
    
    context = {
        'user': user,
        'data': {},
        'total_hoje_validos': 0,
        'error_message': None,
        'page_title': page_title,
        'token': token,  # <<< ADICIONADO para o JavaScript
        'backend_url': Config.BACKEND_URL, # <<< ADICIONADO para o JavaScript
    }
    
    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/dashboard/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        context['data'] = data
        
        agendamentos_do_dia = data.get('lista_espera_hoje', [])
        total_bruto = len(agendamentos_do_dia)
        cancelados = sum(1 for ag in agendamentos_do_dia if ag.get('status') == 'Cancelado')
        context['total_hoje_validos'] = total_bruto - cancelados
        
    except requests.exceptions.HTTPError as e:
        context['error_message'] = f"Não foi possível carregar os dados do dashboard. (Erro {e.response.status_code})"
    except requests.exceptions.RequestException as e:
        context['error_message'] = f"Erro de conexão com o servidor: {e}"
    except Exception as e:
        context['error_message'] = f"Ocorreu um erro inesperado: {e}"
    
    from django.template import Template, RequestContext
    template = Template(DASHBOARD_TEMPLATE)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

def pacientes_view(request):
    """Página de gestão de pacientes com paginação."""
    
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    user = request.session.get('user', {})
    
    funcoes_pt = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'medico': 'Médico',
        'secretaria': 'Secretária'
    }
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))

    # Adiciona "Dr." ao nome se o usuário for médico
    if user.get('funcao') == 'medico':
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    page = request.GET.get('page', '1')
    
    html_parts = []
    pagination = {}
    
    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/',
            headers={'Authorization': f'Bearer {token}'},
            params={'page': page},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        pacientes = data.get('results', [])
        
        count = data.get('count', 0)
        page_size = 20
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
                        <a href="/pacientes/{paciente['id']}/exames/" class="btn-action btn-exames">🔬 Exames</a>
                        <a href="/pacientes/{paciente['id']}/visualizar/" class="btn-action btn-visualizar">👁️ Ver</a>
                        <a href="/pacientes/{paciente['id']}/editar/" class="btn-action btn-editar">✏️ Editar</a>
                        <button onclick="confirmarDeletar({paciente['id']}, '{paciente['nome_completo']}')" class="btn-action btn-deletar">🗑️ Arquivar</button>
                    </div>
                </div>
                """)
        else:
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
    
    # <<< LÓGICA DO USUÁRIO ADICIONADA >>>
    user = request.session.get('user', {})
    funcoes_pt = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'medico': 'Médico',
        'secretaria': 'Secretária'
    }
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/inativos/',
            headers={'Authorization': f'Bearer {token}'}
        )
        inativos = response.json() if response.status_code == 200 else []
        
        from django.template import Template, RequestContext
        template = Template(INATIVOS_TEMPLATE)
        # <<< 'user' ADICIONADO AO CONTEXTO >>>
        context = RequestContext(request, {'inativos': inativos, 'user': user})
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
def placeholder_view(request, page_title="Em Desenvolvimento"):
    # <<< INÍCIO DA CORREÇÃO >>>
    user = request.session.get('user', {})
    funcoes_pt = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'medico': 'Médico',
        'secretaria': 'Secretária'
    }
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"
    
    from django.template import Template, RequestContext
    template = Template(PLACEHOLDER_TEMPLATE)
    context = RequestContext(request, {'page_title': page_title, 'user': user})
    return HttpResponse(template.render(context))
    # <<< FIM DA CORREÇÃO >>>

def paciente_historico_view(request, paciente_id):
    # <<< ALTERAÇÃO PARA CHAMAR A FUNÇÃO CORRETA >>>
    return placeholder_view(request, page_title=f"Histórico do Paciente #{paciente_id}")

def paciente_exames_view(request, paciente_id):
    """Página para visualizar e adicionar exames de um paciente específico."""
    from datetime import date, datetime

    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    context = {
        'user': user,
        'paciente': {},
        'exames_ia': [],
        'exames_gerais': [],
        'error_message': None,
        'token': token, # Adicionado para o JS
        'BACKEND_URL': Config.BACKEND_URL # <<< ADICIONADO PARA O JS
    }

    if request.method == 'POST':
        try:
            payload = {
                "paciente": paciente_id,
                "tipo_exame": request.POST.get("tipo_exame"),
                "data_exame": date.today().isoformat(),
                "resultado_original": request.POST.get("resultado"),
                "status": "finalizado"
            }
            response = requests.post(
                f'{Config.BACKEND_URL}/api/exames/',
                headers={'Authorization': f'Bearer {token}'},
                json=payload
            )
            response.raise_for_status()
            messages.success(request, "Exame geral salvo com sucesso!")
        except Exception as e:
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', str(error_data))
                messages.error(request, f"Erro ao salvar exame geral: {error_detail}")
            except:
                messages.error(request, f"Erro ao salvar exame geral: {e}")
        
        return redirect('paciente_exames', paciente_id=paciente_id)

    try:
        paciente_response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        paciente_response.raise_for_status()
        context['paciente'] = paciente_response.json()

        exames_response = requests.get(
            f'{Config.BACKEND_URL}/api/exames/?paciente_id={paciente_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        exames_response.raise_for_status()
        todos_exames = exames_response.json().get('results', [])

        for exame in todos_exames:
            try:
                data_obj = datetime.strptime(exame['data_exame'], '%Y-%m-%d')
                exame['data_exame_formatada'] = data_obj.strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                exame['data_exame_formatada'] = exame['data_exame']

            if exame.get('tem_interpretacao_ia'):
                context['exames_ia'].append(exame)
            else:
                context['exames_gerais'].append(exame)

    except Exception as e:
        context['error_message'] = f"Erro ao carregar dados do paciente ou exames: {e}"

    from django.template import Template, RequestContext
    template = Template(PACIENTE_EXAMES_TEMPLATE)
    context['messages'] = messages.get_messages(request)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

def agendamentos_view(request):
    """Página de gestão de agendamentos (otimizada para uma única requisição)"""
    from datetime import date, datetime, timedelta

    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))

    # Adiciona "Dr." ao nome se o usuário for médico
    if user.get('funcao') == 'medico':
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

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
                options_html = "".join([f'<option value="{opt}" {"selected" if ag["status"] == opt else ""}>{opt}</option>' for opt in status_options])
                
                convenio = ag.get('convenio', 'N/A')
                telefone = ag.get('paciente_telefone', 'N/A')
                sexo = ag.get('paciente_sexo', 'N/A')
                idade = ag.get('paciente_idade', 'N/A')

                html_parts.append(f"""
                <div class="agendamento-card" id="agendamento-card-{ag['id']}">
                    <div class="agendamento-card-data">
                        <div class="dia">{data_obj.strftime('%d')}</div>
                        <div class="mes">{data_obj.strftime('%b').upper()}</div>
                    </div>
                    <div class="agendamento-card-info">
                        <strong>{ag['paciente_nome']}</strong>
                        <p style="margin: 2px 0;">{ag.get('tipo', 'Agendamento')} às {ag.get('hora', '')[:5]}</p>
                        <p style="font-size: 11px; color: #666; margin: 2px 0;">
                            <span style="margin-right: 10px;">📋 {convenio}</span>
                            <span style="margin-right: 10px;">📞 {telefone}</span>
                            <span style="margin-right: 10px;">👤 {sexo}</span>
                            <span>🎂 {idade} anos</span>
                        </p>
                    </div>
                    <div class="agendamento-card-status">
                        <select name="status" class="status-select status-{ag['status']}" onchange="updateStatus({ag['id']}, this)">
                            {options_html}
                        </select>
                    </div>
                    <div class="actions-dropdown">
                        <button class="actions-btn" data-dropdown-id="dropdown-{ag['id']}">
                            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                                <path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61-.25-1.17-.59-1.69-.98l-2.49-1c-.23-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24-.42-.12-.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59-1.69-.98l2.49 1c.23.09.49 0 .61-.22l2 3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/>
                            </svg>
                        </button>
                        <div id="dropdown-{ag['id']}" class="dropdown-menu">
                            <a href="/agendamentos/{ag['id']}/visualizar/" class="dropdown-item">👁️ Visualizar</a>
                            <a href="/agendamentos/{ag['id']}/editar/" class="dropdown-item">✏️ Editar</a>
                            <a href="#" onclick="confirmDelete({ag['id']}); return false;" class="dropdown-item dropdown-item-danger">🗑️ Excluir</a>
                        </div>
                    </div>
                    <form id="delete-form-{ag['id']}" method="POST" action="/agendamentos/{ag['id']}/deletar/" style="display:none;">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                    </form>
                </div>
                """)
        else:
            html_parts.append("<p style='text-align:center; padding: 20px;'>Nenhum agendamento encontrado.</p>")
        
        agendamentos_html = "".join(html_parts)

    except Exception as e:
        messages.error(request, f"Erro ao buscar agendamentos: {e}")
        agendamentos_html = "<p style='text-align:center; padding: 20px;'>Erro ao carregar agendamentos.</p>"

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
    })
    return HttpResponse(template.render(context))

def agendamento_visualizar_view(request, agendamento_id):
    """Página para visualizar todos os detalhes de um agendamento."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))

    try:
        # 1. Buscar os dados do agendamento específico
        agendamento_url = f'{Config.BACKEND_URL}/api/agendamentos/{agendamento_id}/'
        response = requests.get(agendamento_url, headers={'Authorization': f'Bearer {token}'}, timeout=10)
        response.raise_for_status()
        agendamento_data = response.json()

        # 2. Buscar dados complementares do paciente (como idade)
        paciente_id = agendamento_data.get('paciente')
        if paciente_id:
            paciente_url = f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/'
            pac_response = requests.get(paciente_url, headers={'Authorization': f'Bearer {token}'}, timeout=10)
            if pac_response.status_code == 200:
                # Adiciona os detalhes do paciente ao dicionário do agendamento
                agendamento_data['paciente_detalhes'] = pac_response.json()

        from django.template import Template, RequestContext
        template = Template(AGENDAMENTO_VISUALIZAR_TEMPLATE)
        context = RequestContext(request, {
            'user': user,
            'agendamento': agendamento_data,
        })
        return HttpResponse(template.render(context))

    except requests.exceptions.HTTPError as e:
        messages.error(request, f"Agendamento não encontrado ou sem permissão (Erro: {e.response.status_code}).")
        return redirect('agendamentos')
    except Exception as e:
        messages.error(request, f'Erro ao carregar dados do agendamento: {str(e)}')
        return redirect('agendamentos')

def agendamento_form_view(request, agendamento_id=None):
    """View para criar ou editar um agendamento."""
    token = request.session.get('token')
    if not token:
        return redirect('login')
        
    user = request.session.get('user', {})
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
        # Lógica corrigida para lidar com campos condicionais
        servico = request.POST.get('servico')
        tipo = ''
        if servico == 'Consulta':
            tipo = request.POST.get('tipo_consulta')
        elif servico == 'Exame':
            tipo = request.POST.get('tipo_exame')
        
        payload = {
            'paciente': request.POST.get('paciente'),
            'servico': servico,
            'tipo': tipo,
            'convenio': request.POST.get('convenio'),
            'data': request.POST.get('data'),
            'hora': request.POST.get('hora'),
            'valor': request.POST.get('valor') or None,
            'observacoes': request.POST.get('observacoes', ''),
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
        'user': user
    })
    return HttpResponse(template.render(context))

def agendamento_deletar_view(request, agendamento_id):
    """Processa a exclusão de um agendamento."""
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    try:
        # A URL agora aponta para o endpoint padrão de DELETE
        response = requests.delete(
            f'{Config.BACKEND_URL}/api/agendamentos/{agendamento_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        messages.success(request, "Agendamento excluído com sucesso.")
    except Exception as e:
        messages.error(request, f"Erro ao excluir agendamento: {e}")

    return redirect('agendamentos')

def faturamento_view(request):
    """Página de Gestão Financeira com dashboard e listas."""
    # <<< ADICIONE ESTA LINHA DE IMPORTAÇÃO >>>
    from datetime import date, datetime, timedelta

    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    
    if user.get('funcao') == 'medico':
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    params = {'data_inicial': request.GET.get('data_inicial'), 'data_final': request.GET.get('data_final')}
    params = {k: v for k, v in params.items() if v}

    dashboard_data, receitas, despesas = {}, [], []
    agendamentos_pendentes = []
    csrf_token = get_token(request)

    filtro_ativo = ''
    today_str = date.today().isoformat()
    if params.get('data_inicial') == today_str and params.get('data_final') == today_str:
        filtro_ativo = 'hoje'
    else:
        try:
            d_ini = datetime.strptime(params.get('data_inicial'), '%Y-%m-%d').date()
            d_fim = datetime.strptime(params.get('data_final'), '%Y-%m-%d').date()
            
            if d_ini.day == 1 and d_ini.month == 1 and d_fim.day == 31 and d_fim.month == 12:
                filtro_ativo = 'ano'
            elif d_ini.day == 1 and (d_fim + timedelta(days=1)).day == 1:
                filtro_ativo = 'mes'
            elif d_ini.weekday() == 0 and d_fim.weekday() == 6 and (d_fim - d_ini).days == 6:
                filtro_ativo = 'semana'
        except (ValueError, TypeError, KeyError):
            pass

    try:
        dash_response = requests.get(f'{Config.BACKEND_URL}/api/faturamento/dashboard/', headers={'Authorization': f'Bearer {token}'}, params=params)
        if dash_response.status_code == 200: dashboard_data = dash_response.json()

        rec_response = requests.get(f'{Config.BACKEND_URL}/api/faturamento/receitas/', headers={'Authorization': f'Bearer {token}'}, params=params)
        if rec_response.status_code == 200: receitas = rec_response.json().get('results', rec_response.json())

        desp_response = requests.get(f'{Config.BACKEND_URL}/api/faturamento/despesas/', headers={'Authorization': f'Bearer {token}'}, params=params)
        if desp_response.status_code == 200: despesas = desp_response.json().get('results', desp_response.json())
        
        pendentes_response = requests.get(f'{Config.BACKEND_URL}/api/faturamento/receitas/agendamentos_pendentes/', headers={'Authorization': f'Bearer {token}'})
        if pendentes_response.status_code == 200:
            agendamentos_pendentes = pendentes_response.json().get('agendamentos', [])

    except requests.RequestException as e:
        messages.error(request, f"Erro de comunicação: {e}")

    receitas_html = []
    for r in receitas:
        try: data_vencimento = datetime.strptime(r['data_vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except: data_vencimento = r['data_vencimento']

        receitas_html.append(f"""
        <tr>
            <td>{r['descricao']}</td>
            <td class="truncate-text text-success">R$ {r['valor']}</td>
            <td class="truncate-text">{r.get('categoria_nome', 'N/A')}</td>
            <td class="truncate-text">{data_vencimento}</td>
            <td><span class="status-badge status-{r['status']}">{r['status_display']}</span></td>
            <td>
                <div class="actions-dropdown">
                    <button class="actions-btn" data-dropdown-id="dropdown-receita-{r['id']}">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61-.25-1.17-.59-1.69-.98l-2.49-1c-.23-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19-.15-.24-.42-.12-.64l2 3.46c.12.22.39.3.61-.22l2.49-1c.52.4 1.08.73 1.69-.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59-1.69-.98l2.49 1c.23.09.49 0 .61-.22l2 3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>
                    </button>
                    <div id="dropdown-receita-{r['id']}" class="dropdown-menu">
                        <a href="/faturamento/receita/{r['id']}/visualizar/" class="dropdown-item">👁️ Visualizar</a>
                        <a href="/faturamento/receita/{r['id']}/editar/" class="dropdown-item">✏️ Editar</a>
                        <form method="POST" action="/faturamento/receita/{r['id']}/deletar/"><input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"><button type="submit" class="dropdown-item dropdown-item-danger" onclick="return confirm('Confirmar exclusão?')">🗑️ Excluir</button></form>
                    </div>
                </div>
            </td>
        </tr>
        """)

    despesas_html = []
    for d in despesas:
        try: data_vencimento = datetime.strptime(d['data_vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except: data_vencimento = d['data_vencimento']

        despesas_html.append(f"""
        <tr>
            <td>{d['descricao']}</td>
            <td class="truncate-text text-danger">R$ {d['valor']}</td>
            <td class="truncate-text">{d.get('categoria_nome', 'N/A')}</td>
            <td class="truncate-text">{data_vencimento}</td>
            <td><span class="status-badge status-{d['status']}">{d['status_display']}</span></td>
            <td>
                <div class="actions-dropdown">
                    <button class="actions-btn" data-dropdown-id="dropdown-despesa-{d['id']}">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61-.25-1.17-.59-1.69-.98l-2.49-1c-.23-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19-.15-.24-.42-.12-.64l2 3.46c.12.22.39.3.61-.22l2.49-1c.52.4 1.08.73 1.69-.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59-1.69-.98l2.49 1c.23.09.49 0 .61-.22l2 3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>
                    </button>
                    <div id="dropdown-despesa-{d['id']}" class="dropdown-menu">
                        <a href="/faturamento/despesa/{d['id']}/visualizar/" class="dropdown-item">👁️ Visualizar</a>
                        <a href="/faturamento/despesa/{d['id']}/editar/" class="dropdown-item">✏️ Editar</a>
                        <form method="POST" action="/faturamento/despesa/{d['id']}/deletar/"><input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"><button type="submit" class="dropdown-item dropdown-item-danger" onclick="return confirm('Confirmar exclusão?')">🗑️ Excluir</button></form>
                    </div>
                </div>
            </td>
        </tr>
        """)

    from django.template import Template, RequestContext
    from django.utils.safestring import mark_safe
    template = Template(FATURAMENTO_TEMPLATE)
    context = RequestContext(request, {
        'user': user,
        'dashboard_data': dashboard_data,
        'receitas_html': mark_safe("".join(receitas_html)),
        'despesas_html': mark_safe("".join(despesas_html)),
        'filter_params': params,
        'agendamentos_pendentes': agendamentos_pendentes,
        'filtro_ativo': filtro_ativo,
    })
    return HttpResponse(template.render(context))

def informacoes_view(request):
    """Página com informações e estatísticas da clínica."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    
    # Adiciona "Dr." ao nome se o usuário for médico
    if user.get('funcao') == 'medico':
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    context = {
        'user': user,
        'data': {},
        'total_inativos': 0,
        'error_message': None
    }

    try:
        # Requisição principal para dados consolidados
        response_dados = requests.get(
            f'{Config.BACKEND_URL}/api/dados-clinica/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        response_dados.raise_for_status()
        context['data'] = response_dados.json()

        # Requisição secundária para buscar o total de pacientes inativos
        response_inativos = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/inativos/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        response_inativos.raise_for_status()
        # A resposta é uma lista, então contamos o tamanho dela
        context['total_inativos'] = len(response_inativos.json())

    except requests.exceptions.HTTPError as e:
        context['error_message'] = f"Não foi possível carregar os dados. (Erro {e.response.status_code})"
    except requests.exceptions.RequestException as e:
        context['error_message'] = f"Erro de conexão com o servidor: {e}"
    except Exception as e:
        context['error_message'] = f"Ocorreu um erro inesperado: {e}"
        
    from django.template import Template, RequestContext
    template = Template(INFORMACOES_TEMPLATE)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

def exames_view(request):
    """View que SEMPRE mostra a página de aviso/termos de uso."""
    if not request.session.get('token'):
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    from django.template import Template, RequestContext
    template = Template(EXAMES_IA_TERMOS_TEMPLATE)
    context = RequestContext(request, {'user': user})
    return HttpResponse(template.render(context))

def exame_visualizar_view(request, exame_id):
    """Página para visualizar e editar o laudo de um exame específico."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    # <<< INÍCIO DA CORREÇÃO >>>
    user = request.session.get('user', {})
    funcoes_pt = {
        'super_admin': 'Super Administrador',
        'admin': 'Administrador',
        'medico': 'Médico',
        'secretaria': 'Secretária'
    }
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"
    # <<< FIM DA CORREÇÃO >>>

    context = {'user': user, 'error_message': None, 'exame': {}}
    api_url = f'{Config.BACKEND_URL}/api/exames/{exame_id}/'

    if request.method == 'POST':
        laudo_editado = request.POST.get('laudo_editado')
        if not laudo_editado:
            messages.error(request, "O conteúdo do laudo não pode estar vazio.")
            return redirect('exame_visualizar', exame_id=exame_id)
        
        try:
            get_response = requests.get(api_url, headers={'Authorization': f'Bearer {token}'})
            get_response.raise_for_status()
            exame_data = get_response.json()
            
            exame_data['interpretacao_ia'] = laudo_editado
            
            put_response = requests.put(api_url, headers={'Authorization': f'Bearer {token}'}, json=exame_data)
            put_response.raise_for_status()
            
            messages.success(request, "Laudo atualizado com sucesso!")
            return redirect('exame_visualizar', exame_id=exame_id)

        except Exception as e:
            messages.error(request, f"Erro ao salvar o laudo: {e}")
            return redirect('exame_visualizar', exame_id=exame_id)

    try:
        response = requests.get(api_url, headers={'Authorization': f'Bearer {token}'}, timeout=10)
        response.raise_for_status()
        
        exame_data = response.json()
        
        if 'confianca_ia' in exame_data and exame_data['confianca_ia'] is not None:
            exame_data['confianca_ia'] = exame_data['confianca_ia'] * 100

        context['exame'] = exame_data
        
    except requests.exceptions.HTTPError as e:
        context['error_message'] = f"Exame não encontrado ou sem permissão (Erro: {e.response.status_code})."
    except Exception as e:
        context['error_message'] = f'Erro ao carregar dados do exame: {str(e)}'
    
    from django.template import Template, RequestContext
    template = Template(EXAME_VISUALIZAR_TEMPLATE)
    context['messages'] = messages.get_messages(request)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

def exame_geral_visualizar_view(request, paciente_id, exame_id):
    """Página para visualizar detalhes de um exame geral (manual)."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    context = {'user': user, 'error_message': None, 'exame': {}, 'paciente': {}}

    try:
        # Busca o exame específico. Usamos o serializer completo (não o de lista)
        exame_response = requests.get(
            f'{Config.BACKEND_URL}/api/exames/{exame_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        exame_response.raise_for_status()
        exame_data = exame_response.json()
        
        # Formata a data
        try:
            data_obj = datetime.strptime(exame_data['data_exame'], '%Y-%m-%d')
            exame_data['data_exame_formatada'] = data_obj.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            exame_data['data_exame_formatada'] = exame_data['data_exame']

        context['exame'] = exame_data
        
        # Busca os dados do paciente para o link de "Voltar"
        paciente_response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        paciente_response.raise_for_status()
        context['paciente'] = paciente_response.json()
        
    except Exception as e:
        context['error_message'] = f"Erro ao carregar dados: {e}"

    from django.template import Template, RequestContext
    template = Template(EXAME_GERAL_VISUALIZAR_TEMPLATE)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

def exame_geral_editar_view(request, paciente_id, exame_id):
    """Página para editar um exame geral."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    api_url = f'{Config.BACKEND_URL}/api/exames/{exame_id}/'

    if request.method == 'POST':
        try:
            payload = {
                "paciente": paciente_id,
                "tipo_exame": request.POST.get("tipo_exame"),
                "data_exame": request.POST.get("data_exame"),
                "resultado_original": request.POST.get("resultado_original"),
            }
            response = requests.put(api_url, headers={'Authorization': f'Bearer {token}'}, json=payload)
            response.raise_for_status()
            messages.success(request, "Exame geral atualizado com sucesso!")
            return redirect('paciente_exames', paciente_id=paciente_id)
        except Exception as e:
            messages.error(request, f"Erro ao atualizar o exame: {e}")
            return redirect('exame_geral_editar', paciente_id=paciente_id, exame_id=exame_id)

    # Lógica GET
    try:
        response = requests.get(api_url, headers={'Authorization': f'Bearer {token}'})
        response.raise_for_status()
        exame_data = response.json()
        
        from django.template import Template, RequestContext
        template = Template(EXAME_GERAL_EDITAR_TEMPLATE)
        context = RequestContext(request, {'exame': exame_data})
        return HttpResponse(template.render(context))
    except Exception as e:
        messages.error(request, f"Erro ao carregar o exame para edição: {e}")
        return redirect('paciente_exames', paciente_id=paciente_id)

def exame_geral_deletar_view(request, paciente_id, exame_id):
    """Processa a exclusão de um exame geral."""
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    try:
        response = requests.delete(
            f'{Config.BACKEND_URL}/api/exames/{exame_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        messages.success(request, "Exame geral excluído com sucesso.")
    except Exception as e:
        messages.error(request, f"Erro ao excluir o exame: {e}")
        
    return redirect('paciente_exames', paciente_id=paciente_id)

def exame_deletar_view(request, exame_id):
    """Processa a exclusão de um exame."""
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    try:
        response = requests.delete(
            f'{Config.BACKEND_URL}/api/exames/{exame_id}/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        response.raise_for_status() # Lança um erro para status 4xx ou 5xx
        messages.success(request, "Exame e laudo excluídos com sucesso.")
        
    except requests.exceptions.HTTPError as e:
        messages.error(request, f"Erro ao excluir o exame (Erro: {e.response.status_code}).")
    except Exception as e:
        messages.error(request, f"Erro de conexão: {str(e)}")
        
    return redirect('exames_analise')

def exames_analise_view(request):
    """Página principal de análise e upload de exames."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    context = {'user': user, 'pacientes': [], 'exames': []}
    
    if request.method == 'POST':
        paciente_id = request.POST.get('paciente_id')
        arquivo = request.FILES.get('arquivo')

        if not paciente_id or not arquivo:
            messages.error(request, "É necessário selecionar um paciente e um arquivo.")
        else:
            try:
                tipo_exame = 'outros'
                
                files = {
                    'arquivo': (
                        arquivo.name,
                        arquivo.read(),
                        arquivo.content_type or 'application/octet-stream'
                    )
                }
                
                data = {
                    'paciente': paciente_id,
                    'tipo_exame': tipo_exame,
                    'observacoes': ''
                }
                
                headers = {
                    'Authorization': f'Bearer {token}'
                }
                
                response = requests.post(
                    f'{Config.BACKEND_URL}/api/exames/upload-ia/',
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=120
                )
                
                if response.status_code in [200, 201]:
                    resultado = response.json()
                    messages.success(request, "✅ Exame analisado com sucesso pela iA!")
                    
                    exame_resultado = resultado.get('exame', {})
                    if exame_resultado.get('id'):
                        return redirect('exame_visualizar', exame_id=exame_resultado['id'])
                    
                else:
                    response.raise_for_status() # Lança erro para ser pego abaixo
                    
            except requests.exceptions.HTTPError as http_err:
                try:
                    error_data = http_err.response.json()
                    error_detail = error_data.get('detail', error_data.get('erro', 'Dados inválidos'))
                    messages.error(request, f"❌ Erro na validação: {error_detail}")
                except json.JSONDecodeError:
                    messages.error(request, f"❌ Erro desconhecido do servidor: {http_err.response.status_code}")

            except requests.exceptions.Timeout:
                messages.error(request, "⏱️ Tempo limite excedido! O processamento com iA pode estar demorando.")
                
            except requests.exceptions.ConnectionError:
                messages.error(request, "🌐 Erro de conexão com o servidor. Verifique se o backend está rodando.")
                
            except Exception as e:
                messages.error(request, f"❌ Erro inesperado: {str(e)}")

    # --- LÓGICA GET ---
    try:
        pac_res = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/?page_size=1000', 
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        if pac_res.status_code == 200:
            data = pac_res.json()
            context['pacientes'] = data.get('results', data)

    except Exception as e:
        messages.error(request, f"Erro ao carregar lista de pacientes: {e}")

    try:
        # <<< INÍCIO DA CORREÇÃO >>>
        # Adicionar o parâmetro de filtro na URL da requisição
        params = {'interpretado_ia': 'true'}
        exames_res = requests.get(
            f'{Config.BACKEND_URL}/api/exames/', 
            headers={'Authorization': f'Bearer {token}'},
            params=params, # Passa os parâmetros de filtro
            timeout=10
        )
        # <<< FIM DA CORREÇÃO >>>

        if exames_res.status_code == 200:
            data = exames_res.json()
            context['exames'] = data.get('results', data)
            
    except Exception as e:
        print(f"⚠️ Erro ao carregar histórico de exames: {e}")

    from django.template import Template, RequestContext
    template = Template(EXAMES_IA_PRINCIPAL_TEMPLATE)
    context['messages'] = messages.get_messages(request)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

def receber_agendamento_view(request, agendamento_id):
    """Processa o recebimento de um agendamento, criando uma nova receita."""
    token = request.session.get('token')
    if not token:
        return redirect('login')
        
    if request.method == 'POST':
        forma_pagamento = request.POST.get('forma_pagamento')
        if not forma_pagamento:
            messages.error(request, "Forma de pagamento não selecionada.")
            return redirect('faturamento')
            
        payload = {
            'agendamento_id': agendamento_id,
            'forma_pagamento': forma_pagamento
        }
        
        try:
            response = requests.post(
                f'{Config.BACKEND_URL}/api/faturamento/receitas/receber_de_agendamento/',
                headers={'Authorization': f'Bearer {token}'},
                json=payload
            )
            response.raise_for_status()
            messages.success(request, "Recebimento registrado com sucesso!")
            
        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                messages.error(request, f"Erro ao registrar recebimento: {error_data.get('erro', 'Detalhes não fornecidos.')}")
            except:
                messages.error(request, f"Erro no servidor: {e.response.status_code}")
        except Exception as e:
            messages.error(request, f"Erro de conexão: {e}")
            
    return redirect('faturamento')

def lancamento_form_view(request, tipo_lancamento, lancamento_id=None):
    """View para criar ou editar uma Receita ou Despesa."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    
    # Define os endpoints e o título com base no tipo (receita ou despesa)
    if tipo_lancamento == 'receita':
        form_title = "Nova Receita"
        api_base_url = f'{Config.BACKEND_URL}/api/faturamento/receitas/'
        api_categorias_url = f'{Config.BACKEND_URL}/api/faturamento/categorias/receitas/'
    else:
        form_title = "Nova Despesa"
        api_base_url = f'{Config.BACKEND_URL}/api/faturamento/despesas/'
        api_categorias_url = f'{Config.BACKEND_URL}/api/faturamento/categorias/despesas/'

    # Busca as categorias para o dropdown do formulário
    categorias = []
    try:
        cat_res = requests.get(api_categorias_url, headers={'Authorization': f'Bearer {token}'})
        if cat_res.status_code == 200:
            categorias = cat_res.json().get('results', cat_res.json())
    except Exception as e:
        messages.error(request, f"Erro ao carregar categorias: {e}")

    lancamento_data = {}
    http_method = requests.post
    api_url = api_base_url

    if lancamento_id:
        form_title = f"Editar {tipo_lancamento.capitalize()}"
        api_url = f'{api_base_url}{lancamento_id}/'
        http_method = requests.put
        try:
            response = requests.get(api_url, headers={'Authorization': f'Bearer {token}'})
            if response.status_code == 200:
                lancamento_data = response.json()
        except Exception as e:
            messages.error(request, f"Erro ao carregar dados do lançamento: {e}")

    if request.method == 'POST':
        payload = {
            'descricao': request.POST.get('descricao'),
            'valor': request.POST.get('valor'),
            'categoria': request.POST.get('categoria') or None,
            'data_vencimento': request.POST.get('data_vencimento'),
            'status': request.POST.get('status', 'a_pagar' if tipo_lancamento == 'despesa' else 'a_receber'),
            'clinica_id': user.get('clinica_id')
        }
        
        # Campos adicionais se existirem
        if 'data_pagamento' in request.POST:
             payload['data_pagamento'] = request.POST.get('data_pagamento') or None
        if 'data_recebimento' in request.POST:
             payload['data_recebimento'] = request.POST.get('data_recebimento') or None

        try:
            response = http_method(api_url, headers={'Authorization': f'Bearer {token}'}, json=payload)
            response.raise_for_status()
            messages.success(request, f"{tipo_lancamento.capitalize()} salva com sucesso!")
            return redirect('faturamento')
        except requests.exceptions.HTTPError as e:
            error_details = e.response.json()
            messages.error(request, f"Erro de validação: {error_details}")
        except Exception as e:
            messages.error(request, f"Erro ao salvar: {e}")

    from django.template import Template, RequestContext
    template = Template(LANCAMENTO_FORM_TEMPLATE)
    context = RequestContext(request, {
        'form_title': form_title,
        'tipo_lancamento': tipo_lancamento,
        'lancamento': lancamento_data,
        'categorias': categorias,
        'user': user
    })
    return HttpResponse(template.render(context))

def lancamento_visualizar_view(request, tipo_lancamento, lancamento_id):
    """Página para visualizar todos os detalhes de uma receita ou despesa."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    
    if tipo_lancamento == 'receita':
        form_title = "Detalhes da Receita"
        api_url = f'{Config.BACKEND_URL}/api/faturamento/receitas/{lancamento_id}/'
    else:
        form_title = "Detalhes da Despesa"
        api_url = f'{Config.BACKEND_URL}/api/faturamento/despesas/{lancamento_id}/'

    try:
        response = requests.get(api_url, headers={'Authorization': f'Bearer {token}'}, timeout=10)
        response.raise_for_status()
        lancamento_data = response.json()

        from django.template import Template, RequestContext
        template = Template(LANCAMENTO_VISUALIZAR_TEMPLATE)
        context = RequestContext(request, {
            'user': user,
            'lancamento': lancamento_data,
            'form_title': form_title
        })
        return HttpResponse(template.render(context))

    except requests.RequestException as e:
        messages.error(request, f'Erro ao carregar detalhes do lançamento: {e}')
        return redirect('faturamento')

def lancamento_deletar_view(request, tipo_lancamento, lancamento_id):
    """Processa a exclusão de uma receita ou despesa."""
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    if tipo_lancamento == 'receita':
        api_url = f'{Config.BACKEND_URL}/api/faturamento/receitas/{lancamento_id}/'
    else:
        api_url = f'{Config.BACKEND_URL}/api/faturamento/despesas/{lancamento_id}/'

    try:
        response = requests.delete(api_url, headers={'Authorization': f'Bearer {token}'})
        response.raise_for_status()
        messages.success(request, f"{tipo_lancamento.capitalize()} excluída com sucesso.")
    except Exception as e:
        messages.error(request, f"Erro ao excluir lançamento: {e}")

    return redirect('faturamento')

def setup_categorias_view(request):
    """View especial para popular as categorias padrão da clínica logada."""
    token = request.session.get('token')
    
    context = {
        'titulo': 'Erro de Autenticação',
        'mensagem': 'Você precisa estar logado para executar esta ação.',
        'status': 'error'
    }

    if token:
        try:
            response = requests.post(
                f'{Config.BACKEND_URL}/api/setup/',
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            data = response.json()

            if response.status_code == 200 and data.get('sucesso'):
                context = {
                    'titulo': 'Sucesso!',
                    'mensagem': data.get('mensagem', 'Categorias criadas com sucesso!'),
                    'status': 'success'
                }
            else:
                 context = {
                    'titulo': 'Ocorreu um Erro',
                    'mensagem': data.get('mensagem', 'Não foi possível criar as categorias. Verifique se o backend está no ar.'),
                    'status': 'error'
                }

        except requests.RequestException as e:
             context = {
                'titulo': 'Erro de Conexão',
                'mensagem': f"Não foi possível conectar ao servidor: {e}",
                'status': 'error'
            }
    
    from django.template import Template, RequestContext
    template = Template(SETUP_RESULTADO_TEMPLATE)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

def consultas_view(request):
    """Página que exibe a fila de atendimento do dia."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    context = {'user': user, 'data': {}, 'error_message': None}

    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/consultas/fila-hoje/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        response.raise_for_status()
        context['data'] = response.json()
        
        # Formatar a data para exibição
        if context['data'].get('data'):
            try:
                data_obj = datetime.strptime(context['data']['data'], '%Y-%m-%d')
                context['data']['data'] = data_obj.strftime('%d/%m/%Y')
            except ValueError:
                pass

    except requests.exceptions.RequestException as e:
        context['error_message'] = f"Erro ao carregar a fila de atendimento: {e}"

    from django.template import Template, RequestContext
    template = Template(CONSULTAS_TEMPLATE)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

def iniciar_consulta_view(request, agendamento_id):
    """Cria/busca uma consulta, inicia o atendimento e redireciona para o workspace."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    if request.method == 'POST':
        try:
            agendamento_response = requests.get(
                f'{Config.BACKEND_URL}/api/agendamentos/{agendamento_id}/',
                headers={'Authorization': f'Bearer {token}'}
            )
            agendamento_response.raise_for_status()
            agendamento_data = agendamento_response.json()
            
            paciente_id = agendamento_data.get('paciente')
            data_hora_agendamento = f"{agendamento_data.get('data')}T{agendamento_data.get('hora')}"

            # Payload agora não precisa mais do clinica_id
            payload = {
                "agendamento": agendamento_id,
                "paciente": paciente_id,
                "data_consulta": data_hora_agendamento,
                "tipo_consulta": "primeira_consulta"
            }
            response = requests.post(
                f'{Config.BACKEND_URL}/api/consultas/',
                headers={'Authorization': f'Bearer {token}'},
                json=payload,
                timeout=10
            )

            consulta_id = None
            
            if response.status_code == 201:
                consulta_criada = response.json()
                consulta_id = consulta_criada.get('id')
            elif response.status_code == 400:
                consulta_response = requests.get(
                    f'{Config.BACKEND_URL}/api/consultas/?agendamento={agendamento_id}', 
                    headers={'Authorization': f'Bearer {token}'}
                )
                consulta_response.raise_for_status()
                consulta_data = consulta_response.json().get('results', [])
                if consulta_data:
                    consulta_id = consulta_data[0]['id']
                else:
                    raise Exception(f"Erro ao criar consulta: {response.text}")
            else:
                response.raise_for_status()

            if not consulta_id:
                raise Exception("Não foi possível obter o ID da consulta.")

            iniciar_response = requests.post(
                f'{Config.BACKEND_URL}/api/consultas/{consulta_id}/iniciar-atendimento/',
                headers={'Authorization': f'Bearer {token}'}
            )
            if iniciar_response.status_code not in [200, 400]:
                iniciar_response.raise_for_status()

            messages.success(request, "Consulta iniciada com sucesso!")
            return redirect('workspace', consulta_id=consulta_id)

        except Exception as e:
            messages.error(request, f"Não foi possível iniciar o atendimento: {e}")
            return redirect('consultas')

    return redirect('consultas')

def continuar_consulta_view(request, consulta_id):
    """Redireciona diretamente para o workspace de uma consulta já iniciada."""
    if not request.session.get('token'):
        return redirect('login')
    
    # Simplesmente redireciona para a URL do workspace
    return redirect('workspace', consulta_id=consulta_id)

def workspace_view(request, consulta_id):
    """Página de atendimento da consulta (workspace)."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    context = {
        'user': user, 
        'consulta': {}, 
        'error_message': None,
        'token': token,
        'BACKEND_URL': Config.BACKEND_URL
    }

    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/consultas/{consulta_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        context['consulta'] = response.json()
        
    except Exception as e:
        context['error_message'] = f"Erro ao carregar dados da consulta: {e}"

    from django.template import Template, RequestContext
    template = Template(WORKSPACE_CONSULTA_TEMPLATE)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

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
    
    # Agendamentos
    path('agendamentos/', agendamentos_view, name='agendamentos'),
    path('agendamentos/novo/', agendamento_form_view, name='agendamento_novo'),
    path('agendamentos/<int:agendamento_id>/visualizar/', agendamento_visualizar_view, name='agendamento_visualizar'),
    path('agendamentos/<int:agendamento_id>/editar/', agendamento_form_view, name='agendamento_editar'),
    path('agendamentos/<int:agendamento_id>/deletar/', agendamento_deletar_view, name='agendamento_deletar'),
    
    # Faturamento
    path('faturamento/', faturamento_view, name='faturamento'),
    path('faturamento/receita/nova/', lancamento_form_view, {'tipo_lancamento': 'receita'}, name='receita_nova'),
    path('faturamento/despesa/nova/', lancamento_form_view, {'tipo_lancamento': 'despesa'}, name='despesa_nova'),
    path('faturamento/receber-agendamento/<int:agendamento_id>/', receber_agendamento_view, name='receber_agendamento'),
    path('faturamento/receita/<int:lancamento_id>/editar/', lancamento_form_view, {'tipo_lancamento': 'receita'}, name='receita_editar'),
    path('faturamento/receita/<int:lancamento_id>/visualizar/', lancamento_visualizar_view, {'tipo_lancamento': 'receita'}, name='receita_visualizar'),
    path('faturamento/receita/<int:lancamento_id>/deletar/', lancamento_deletar_view, {'tipo_lancamento': 'receita'}, name='receita_deletar'),
    path('faturamento/despesa/<int:lancamento_id>/editar/', lancamento_form_view, {'tipo_lancamento': 'despesa'}, name='despesa_editar'),
    path('faturamento/despesa/<int:lancamento_id>/visualizar/', lancamento_visualizar_view, {'tipo_lancamento': 'despesa'}, name='despesa_visualizar'),
    path('faturamento/despesa/<int:lancamento_id>/deletar/', lancamento_deletar_view, {'tipo_lancamento': 'despesa'}, name='despesa_deletar'),
    
    # Rota de Setup
    path('setup-categorias/', setup_categorias_view, name='setup_categorias'),
    
    # Rotas de Exames
    path('exames/', exames_view, name='exames'),
    path('exames/analise/', exames_analise_view, name='exames_analise'),
    path('exames/<int:exame_id>/visualizar/', exame_visualizar_view, name='exame_visualizar'),
    path('exames/<int:exame_id>/deletar/', exame_deletar_view, name='exame_deletar'),
    path('pacientes/<int:paciente_id>/exames-gerais/<int:exame_id>/', exame_geral_visualizar_view, name='exame_geral_visualizar'),
    path('pacientes/<int:paciente_id>/exames-gerais/<int:exame_id>/editar/', exame_geral_editar_view, name='exame_geral_editar'),
    path('pacientes/<int:paciente_id>/exames-gerais/<int:exame_id>/deletar/', exame_geral_deletar_view, name='exame_geral_deletar'),
    
    # Rotas de Consulta
    path('consultas/', consultas_view, name='consultas'),
    path('consultas/iniciar/<int:agendamento_id>/', iniciar_consulta_view, name='iniciar_consulta'),
    path('consultas/continuar/<int:consulta_id>/', continuar_consulta_view, name='continuar_consulta'),
    path('consultas/atendimento/<int:consulta_id>/', workspace_view, name='workspace'),
    
    path('informacoes/', informacoes_view, name='informacoes'),
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