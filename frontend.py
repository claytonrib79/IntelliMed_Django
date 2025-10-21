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

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def format_currency_brl(value):
    """Formata um número para o padrão de moeda brasileiro (R$ 1.234,56)."""
    if value is None:
        return "0,00"
    try:
        # Garante que o valor seja um float e formata com 2 casas decimais,
        # separador de milhar com ponto e decimal com vírgula.
        return f"{float(value):,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        return "0,00"

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
# TEMPLATE PARA DASHBOARD 
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

        .main-content { margin-left: 260px; flex: 1; padding: 30px; width: calc(100% - 260px); }
        .page-header h2 { font-size: 28px; color: #333; margin-bottom: 8px; }
        .page-header p { color: #666; font-size: 14px; margin-bottom: 30px; }
        
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

        .dashboard-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: start; }
        .dashboard-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .dashboard-card-title { font-size: 20px; color: #333; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        .dashboard-card-title select { font-size: 13px; padding: 5px 10px; border-radius: 6px; border: 1px solid #ccc; }
        
        .list-container { max-height: 400px; overflow-y: auto; }
        .list-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 5px; border-bottom: 1px solid #f5f5f5; }
        .list-item:last-child { border-bottom: none; }
        .list-item-info { flex-grow: 1; }
        .list-item-info strong { display: block; font-size: 15px; color: #333; }
        .list-item-info span { font-size: 13px; color: #777; }
        .empty-list { text-align: center; padding: 40px 10px; color: #999; font-size: 14px; }
        
        .status-select { border: none; padding: 8px 12px; border-radius: 20px; font-size: 13px; font-weight: 700; cursor: pointer; -webkit-appearance: none; -moz-appearance: none; appearance: none; transition: all 0.3s ease; }
        .status-select:hover { transform: scale(1.05); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
        .status-Agendado { background: #FFF9C4; color: #F57F17; border: 2px solid #FBC02D; }
        .status-Confirmado { background: #FFCDD2; color: #C62828; border: 2px solid #E53935; }
        .status-Realizado { background: #C8E6C9; color: #2E7D32; border: 2px solid #43A047; }
        .status-Cancelado { background: #E0E0E0; color: #616161; border: 2px solid #9E9E9E; }
        .status-Faltou { background: #BBDEFB; color: #1565C0; border: 2px solid #1976D2; }
        
        .status-badge-pill { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 2px solid; }
        .pill-atraso { background-color: rgba(244, 67, 54, 0.1); color: #c62828; border-color: #e57373; }
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
            <a href="/exames/" class="menu-item"><span class="menu-item-icon">🔬</span> <span>Exames IA</span></a>
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
                    <h3 class="dashboard-card-title">Fila de Atendimentos de Hoje</h3>
                    <div class="list-container">
                        {% for ag in data.lista_espera_hoje %}
                            <div class="list-item">
                                <div class="list-item-info">
                                    <strong>{{ ag.hora }} - {{ ag.paciente_nome }}</strong>
                                    <span>{{ ag.servico }} - {{ ag.tipo }}</span>
                                </div>
                                <select name="status" class="status-select status-{{ ag.status }}" onchange="updateStatus({{ ag.id }}, this)">
                                    <option value="Agendado" {% if ag.status == 'Agendado' %}selected{% endif %}>Agendado</option>
                                    <option value="Confirmado" {% if ag.status == 'Confirmado' %}selected{% endif %}>Confirmado</option>
                                    <option value="Realizado" {% if ag.status == 'Realizado' %}selected{% endif %}>Realizado</option>
                                    <option value="Cancelado" {% if ag.status == 'Cancelado' %}selected{% endif %}>Cancelado</option>
                                    <option value="Faltou" {% if ag.status == 'Faltou' %}selected{% endif %}>Faltou</option>
                                </select>
                            </div>
                        {% empty %}
                            <div class="empty-list">Nenhum paciente agendado para hoje.</div>
                        {% endfor %}
                    </div>
                </div>

                <div class="dashboard-card">
                    <div class="dashboard-card-title">
                        <h3>Monitor de Atrasos</h3>
                        <select id="filtro-atraso" onchange="filtrarAtrasos()">
                            <option value="15">Atraso > 0:15 h</option>
                            <option value="30" selected>Atraso > 0:30 h</option>
                            <option value="45">Atraso > 0:45 h</option>
                            <option value="60">Atraso > 1:00 h</option>
                            <option value="90">Atraso > 1:30 h</option>
                            <option value="120">Atraso > 2:00 h</option>
                            <option value="150">Atraso > 2:30 h</option>
                            <option value="180">Atraso > 3:00 h</option>
                        </select>
                    </div>
                    <div class="list-container" id="lista-atrasos-container">
                        <!-- Conteúdo gerado por JavaScript -->
                    </div>
                </div>
            </div>
            
        {% endif %}
    </div>

    <script>
        // ▼▼▼ INÍCIO DA ALTERAÇÃO ▼▼▼
        let listaEsperaHoje = [];
        let refreshInterval = null; // Variável para controlar o timer
        const REFRESH_INTERVAL_MS = 300000; // 5 minutos em milissegundos

        function startRefreshTimer() {
            // Limpa qualquer timer anterior para evitar múltiplos timers rodando
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
            // Inicia um novo timer
            refreshInterval = setInterval(() => {
                console.log('Atualizando dashboard automaticamente...');
                location.reload();
            }, REFRESH_INTERVAL_MS);
            console.log('Timer de atualização automática iniciado.');
        }

        function stopRefreshTimer() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
                console.log('Timer de atualização automática parado.');
            }
        }

        function handleVisibilityChange() {
            if (document.hidden) {
                // A página ficou inativa (usuário mudou de aba, etc.)
                stopRefreshTimer();
            } else {
                // A página voltou a ficar ativa
                startRefreshTimer();
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            try {
                listaEsperaHoje = JSON.parse('{{ lista_espera_json|safe }}');
            } catch (e) {
                console.error("Erro ao carregar dados da fila de espera:", e);
                listaEsperaHoje = [];
            }

            document.querySelectorAll('.status-select').forEach(select => {
                select.setAttribute('data-original-status', select.value);
            });

            filtrarAtrasos();

            // Inicia o timer de atualização pela primeira vez
            startRefreshTimer();

            // Adiciona o listener para a visibilidade da página
            document.addEventListener('visibilitychange', handleVisibilityChange);
        });
        // ▲▲▲ FIM DA ALTERAÇÃO ▲▲▲

        function filtrarAtrasos() {
            const filtroMinutos = parseInt(document.getElementById('filtro-atraso').value, 10);
            const container = document.getElementById('lista-atrasos-container');
            
            if (!Array.isArray(listaEsperaHoje)) {
                container.innerHTML = '<div class="empty-list">Erro ao carregar dados.</div>';
                return;
            }
            
            const pacientesAtrasados = listaEsperaHoje.filter(paciente => 
                paciente.status === 'Confirmado' &&
                paciente.tempo_espera_minutos !== null && 
                paciente.tempo_espera_minutos >= filtroMinutos
            );

            container.innerHTML = '';

            if (pacientesAtrasados.length > 0) {
                pacientesAtrasados.forEach(paciente => {
                    const itemHtml = `
                        <div class="list-item">
                            <div class="list-item-info">
                                <strong>${paciente.paciente_nome}</strong>
                                <span>Agendado para ${paciente.hora}</span>
                            </div>
                            <span class="status-badge-pill pill-atraso">${paciente.tempo_espera_minutos} min atrasado</span>
                        </div>
                    `;
                    container.insertAdjacentHTML('beforeend', itemHtml);
                });
            } else {
                container.innerHTML = '<div class="empty-list">Nenhum paciente atrasado com base no filtro selecionado.</div>';
            }
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
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    throw new Error('Resposta inválida do servidor');
                }
            })
            .catch(error => {
                console.error('❌ Erro:', error);
                showNotification(`Erro ao atualizar: ${error.message}`, 'error');
                selectElement.value = originalStatus;
                selectElement.className = `status-select status-${originalStatus}`;
            })
            .finally(() => {
                selectElement.disabled = false;
                selectElement.style.opacity = '1';
            });
        }
    </script>
</body>
</html>
"""

# ============================================
# TEMPLATE PARA PACIENTES
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
            <div class="header-actions">
                <span class="count-indicator">Total: {{ pagination.count }}</span>
                <a href="/pacientes/inativos/" class="btn btn-secondary">Ver Inativos</a>
                <button class="btn btn-secondary" onclick="location.reload()">Atualizar</button>
                <a href="/pacientes/novo/" class="btn btn-primary">Novo Paciente</a>
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
        
        <!-- ▼▼▼ CONTAINER PARA AS MENSAGENS ▼▼▼ -->
        <div class="alert-container">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
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

        // ▼▼▼ SCRIPT ADICIONADO PARA REMOVER ALERTAS AUTOMATICAMENTE ▼▼▼
        document.addEventListener('DOMContentLoaded', (event) => {
            setTimeout(() => {
                const alerts = document.querySelectorAll('.alert-container .alert');
                alerts.forEach(alert => {
                    // Adiciona uma classe para a transição de fade-out
                    alert.style.transition = 'opacity 0.5s ease';
                    alert.style.opacity = '0';
                    
                    // Remove o elemento do DOM após a transição
                    setTimeout(() => {
                        alert.remove();
                    }, 500); // 500ms é a duração da transição
                });
            }, 5000); // 5000ms = 5 segundos
        });
        // ▲▲▲ FIM DO SCRIPT ADICIONADO ▲▲▲
    </script>
</body>
</html>
"""

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

PACIENTE_VISUALIZAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detalhes do Paciente - intelliMed</title>
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
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; transition: all 0.3s; }
        .menu-item:hover { background: rgba(255,255,255,0.1); }
        .menu-item.active { background: rgba(255,255,255,0.15); border-left-color: white; font-weight: 600; }
        .menu-item-icon { width: 20px; margin-right: 12px; font-size: 18px; }
        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; width: calc(100% - 260px); }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .page-title h1 { font-size: 32px; color: #333; }
        .details-container { background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .section-title { font-size: 18px; font-weight: 600; color: #667eea; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; }
        .info-grid { display: grid; grid-template-columns: 200px 1fr; gap: 15px; margin-bottom: 25px; }
        .info-grid .label { font-weight: 600; color: #666; }
        .info-grid .value { color: #333; }
        .btn-secondary { padding: 12px 30px; border: none; border-radius: 25px; font-size: 15px; font-weight: 600; cursor: pointer; background: #e0e0e0; color: #666; text-decoration: none; display: inline-block; margin-top: 20px; }
        .list-group { list-style: none; padding: 0; }
        .list-group-item { background: #f9f9f9; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #eee; }
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
            <div class="page-title"><h1>{{ paciente.nome_completo }}</h1></div>
            <a href="/pacientes/" class="btn-secondary">Voltar</a>
        </div>
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
        </div>
    </div>
</body>
</html>
"""

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

HISTORICO_PACIENTE_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Histórico do Paciente - intelliMed</title>
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
        .btn-secondary { padding: 10px 20px; border-radius: 20px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; background: rgba(108, 117, 125, 0.15); color: #495057; }

        .timeline { display: flex; flex-direction: column; gap: 30px; }
        .consulta-card { background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .consulta-header { padding: 20px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; }
        .consulta-header h2 { font-size: 18px; color: #333; }
        .consulta-header span { font-size: 14px; color: #666; }
        .documentos-list { padding: 20px; display: flex; flex-direction: column; gap: 10px; }
        .documento-item { background: #f9f9f9; border: 1px solid #eee; border-radius: 8px; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
        .documento-item-name { font-weight: 600; color: #333; }
        .btn-doc-action { padding: 8px 15px; font-size: 13px; font-weight: 500; border-radius: 20px; border: none; cursor: pointer; }
        .btn-view-doc { background: #e0e0e0; color: #555; }
        .btn-print-doc { background: #e3f2fd; color: #1976d2; margin-left: 8px; }

        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: none; align-items: center; justify-content: center; z-index: 1000; }
        .modal-content { background: white; padding: 30px; border-radius: 12px; width: 90%; max-width: 800px; max-height: 90vh; display: flex; flex-direction: column; }
        .modal-body textarea { width: 100%; min-height: 400px; border-radius: 8px; border: 1px solid #ccc; padding: 15px; font-family: 'Courier New', monospace; }
        
        @media print {
            body * { visibility: hidden; }
            #print-area, #print-area * { visibility: visible; }
            #print-area { position: absolute; left: 0; top: 0; width: 100%; font-family: 'Times New Roman', Times, serif; font-size: 12pt; white-space: pre-wrap; }
        }
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
                <h1>🕐 Histórico do Paciente</h1>
                <p>{{ paciente.nome_completo }}</p>
            </div>
            <a href="/pacientes/" class="btn btn-secondary">Voltar</a>
        </div>

        <div class="timeline">
            {% for item in historico %}
                <div class="consulta-card">
                    <div class="consulta-header">
                        <h2>Consulta com {{ item.medico_responsavel }}</h2>
                        <span>{{ item.data_consulta }}</span>
                    </div>
                    <div class="documentos-list">
                        {% for doc in item.documentos %}
                            <div class="documento-item">
                                <span class="documento-item-name">{{ doc.tipo|capfirst }}</span>
                                <div class="documento-item-actions">
                                    <button class="btn-doc-action btn-view-doc" onclick="showDocumentModal(this)">Visualizar</button>
                                    <button class="btn-doc-action btn-print-doc" onclick="printDocument(this)">Imprimir</button>
                                </div>
                                <div class="document-content" style="display: none;">{{ doc.conteudo }}</div>
                            </div>
                        {% empty %}
                            <p style="text-align: center; color: #999;">Nenhum documento gerado para esta consulta.</p>
                        {% endfor %}
                    </div>
                </div>
            {% empty %}
                <div class="consulta-card" style="text-align: center; padding: 40px;">
                    <h2>Nenhum histórico de consulta encontrado.</h2>
                </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="modal-overlay" id="document-modal">
        <div class="modal-content">
            <div class="modal-header" style="justify-content: flex-end;">
                <button onclick="closeDocumentModal()">×</button>
            </div>
            <div class="modal-body"><textarea id="document-textarea" readonly></textarea></div>
        </div>
    </div>

    <script>
        function showDocumentModal(buttonElement) {
            const content = buttonElement.closest('.documento-item').querySelector('.document-content').textContent;
            document.getElementById('document-textarea').value = content;
            document.getElementById('document-modal').style.display = 'flex';
        }

        function closeDocumentModal() {
            document.getElementById('document-modal').style.display = 'none';
        }

        function printDocument(buttonElement) {
            const contentToPrint = buttonElement.closest('.documento-item').querySelector('.document-content').textContent;
            const printWindow = window.open('', '_blank');
            if (printWindow) {
                printWindow.document.write('<html><head><title>Imprimir</title><style>body { font-family: "Courier New", monospace; white-space: pre-wrap; margin: 20px; }</style></head><body>' + contentToPrint + '</body></html>');
                printWindow.document.close();
                printWindow.focus();
                printWindow.print();
                printWindow.onafterprint = () => printWindow.close();
            } else {
                alert('Por favor, habilite pop-ups para imprimir.');
            }
        }
    </script>
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
                                    <!-- ▼▼▼ LINK CORRIGIDO AQUI ▼▼▼ -->
                                    <a href="/exames/{{ exame.id }}/visualizar/?paciente_id={{ paciente.id }}" class="view-link">Ver Laudo</a>
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
                    // Tentar codec Opus (preferido pelo Gemini)
                    let options = { mimeType: 'audio/webm;codecs=opus' };

                    // Se não suportar Opus, tentar outros
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                        console.warn('Opus não suportado, tentando alternativas...');
                        options = { mimeType: 'audio/webm' };
                    }

                    mediaRecorder = new MediaRecorder(stream, options);
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
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
                    const backendUrl = '{{ BACKEND_URL }}';
                    const response = await fetch(`${backendUrl}/api/transcrever-audio/`, {
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

PACIENTE_EXAMES_SECRETARIA_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Visualizar Exames do Paciente - intelliMed</title>
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
        .btn-primary { background: rgba(108, 117, 125, 0.15); color: #495057; }

        .columns-container { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: start; }
        .card-section { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        .section-header h2 { font-size: 20px; color: #333; }
        
        .exame-item { border-bottom: 1px solid #f0f0f0; padding: 12px 5px; }
        .exame-item:last-child { border-bottom: none; }
        .exame-info { display: flex; justify-content: space-between; align-items: center; }
        .exame-info strong { font-size: 14px; color: #333; }
        .exame-info span { font-size: 12px; color: #666; }
        
        .exame-actions .action-link { 
            text-decoration: none; 
            padding: 8px 16px; 
            border-radius: 20px; 
            font-size: 13px; 
            font-weight: 500;
            background-color: #e3f2fd; 
            color: #1976d2; 
            white-space: nowrap;
        }
        
        .empty-list { text-align: center; padding: 30px; color: #999; }
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
                <div class="section-header"><h2>Exames iA</h2></div>
                <div class="exames-list">
                    {% for exame in exames_ia %}
                        <div class="exame-item">
                            <div class="exame-info">
                                <div>
                                    <strong>{{ exame.tipo_exame_identificado_pela_ia|default:exame.tipo_exame_display }}</strong>
                                    <span>{{ exame.data_exame_formatada }}</span>
                                </div>
                                <div class="exame-actions">
                                    <!-- --- INÍCIO DA CORREÇÃO (BOTÃO INALTERADO) --- -->
                                    <a href="/exames/{{ exame.id }}/visualizar/?paciente_id={{ paciente.id }}" class="action-link">🖨️ Ver/Imprimir</a>
                                    <!-- --- FIM DA CORREÇÃO --- -->
                                </div>
                            </div>
                        </div>
                    {% empty %}
                        <p class="empty-list">Nenhum exame analisado pela iA para este paciente.</p>
                    {% endfor %}
                </div>
            </div>

            <div class="card-section">
                <div class="section-header"><h2>Exames Gerais</h2></div>
                <div class="exames-list">
                    {% for exame in exames_gerais %}
                        <div class="exame-item">
                            <div class="exame-info">
                                <div>
                                    <strong>{{ exame.tipo_exame_display }}</strong>
                                    <span>{{ exame.data_exame_formatada }}</span>
                                </div>
                                <div class="exame-actions">
                                    <!-- --- INÍCIO DA CORREÇÃO (BOTÃO ALTERADO) --- -->
                                    <a href="{% url 'exame_geral_visualizar' paciente_id=paciente.id exame_id=exame.id %}" class="action-link">👁️ Ver</a>
                                    <!-- --- FIM DA CORREÇÃO --- -->
                                </div>
                            </div>
                        </div>
                    {% empty %}
                        <p class="empty-list">Nenhum exame geral cadastrado.</p>
                    {% endfor %}
                </div>
            </div>
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

AGENDAMENTO_FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ form_title }} - intelliMed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa; display: flex; margin: 0; }
        .sidebar { width: 260px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; position: fixed; height: 100vh; display: flex; flex-direction: column; }
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
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .form-container { max-width: 800px; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; font-weight: 600; margin-bottom: 8px; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; }
        .form-actions { display: flex; justify-content: flex-end; gap: 15px; margin-top: 20px; }
        
        .btn { padding: 12px 30px; border-radius: 25px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: all 0.2s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #e0e0e0; color: #666; }

        .hidden-field { display: none; }

        .searchable-select-container { position: relative; }
        #paciente-search-input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
        }
        #paciente-search-results {
            display: none;
            position: absolute;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            width: 100%;
            max-height: 200px;
            overflow-y: auto;
            z-index: 100;
            margin-top: 5px;
        }
        .search-result-item {
            padding: 10px;
            cursor: pointer;
        }
        .search-result-item:hover {
            background-color: #f0f0f0;
        }
        .search-result-item small {
            display: block;
            color: #777;
        }
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
        <div class="sidebar-footer">
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <h1>{{ form_title }}</h1>
        <div class="form-container">
            <form method="POST">
                {% csrf_token %}
                <div class="form-group">
                    <label>Paciente <span style="color:red;">*</span></label>
                    
                    <div class="searchable-select-container">
                        <input type="text" id="paciente-search-input" placeholder="Digite para buscar por nome ou CPF..." autocomplete="off">
                        <div id="paciente-search-results"></div>
                    </div>
                    <select name="paciente" id="paciente-select" required class="hidden-field">
                        <option value="">Selecione um paciente</option>
                        {% for p in pacientes %}
                        <option value="{{ p.id }}" data-cpf="{{ p.cpf }}" {% if p.id == agendamento.paciente %}selected{% endif %}>{{ p.nome_completo }}</option>
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
                        <option value="">Selecione um convênio</option>
                        <option value="PARTICULAR" {% if agendamento.convenio == 'PARTICULAR' %}selected{% endif %}>Particular</option>
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
            // Lógica para campos condicionais (serviço/tipo)
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

            // ▼▼▼ INÍCIO DO SCRIPT ATUALIZADO PARA DROPDOWN PESQUISÁVEL ▼▼▼
            const searchInput = document.getElementById('paciente-search-input');
            const resultsContainer = document.getElementById('paciente-search-results');
            const hiddenSelect = document.getElementById('paciente-select');
            const options = Array.from(hiddenSelect.options);

            const selectedOption = hiddenSelect.options[hiddenSelect.selectedIndex];
            if (selectedOption && selectedOption.value) {
                searchInput.value = selectedOption.text;
            }

            searchInput.addEventListener('input', function(e) {
                let originalValue = e.target.value;
                
                // Verifica se a entrada é primariamente numérica para formatar como CPF
                if (/^\\d{1,11}$/.test(originalValue.replace(/[.\\-]/g, ''))) {
                    let numbers = originalValue.replace(/\\D/g, '');
                    numbers = numbers.substring(0, 11);
                    let formatted = numbers;
                    if (numbers.length > 9) {
                        formatted = numbers.replace(/(\\d{3})(\\d{3})(\\d{3})(\\d{2})/, "$1.$2.$3-$4");
                    } else if (numbers.length > 6) {
                        formatted = numbers.replace(/(\\d{3})(\\d{3})(\\d{1,3})/, "$1.$2.$3");
                    } else if (numbers.length > 3) {
                        formatted = numbers.replace(/(\\d{3})(\\d{1,3})/, "$1.$2");
                    }
                    e.target.value = formatted;
                }
                
                filterAndDisplayResults();
            });
            
            function filterAndDisplayResults() {
                const searchTerm = searchInput.value.toLowerCase();
                resultsContainer.innerHTML = '';
                resultsContainer.style.display = 'block';

                if (searchTerm.length === 0) {
                    resultsContainer.style.display = 'none';
                    return;
                }

                const filteredOptions = options.filter(option => {
                    const nome = option.text.toLowerCase();
                    const cpf = option.dataset.cpf ? option.dataset.cpf.toLowerCase() : '';
                    return (nome.includes(searchTerm) || cpf.includes(searchTerm)) && option.value !== '';
                });

                filteredOptions.forEach(option => {
                    const item = document.createElement('div');
                    item.className = 'search-result-item';
                    item.innerHTML = `${option.text} <small>CPF: ${option.dataset.cpf || 'N/A'}</small>`;
                    item.dataset.value = option.value;
                    item.dataset.text = option.text;

                    item.addEventListener('click', () => {
                        searchInput.value = item.dataset.text;
                        hiddenSelect.value = item.dataset.value;
                        resultsContainer.style.display = 'none';
                    });

                    resultsContainer.appendChild(item);
                });
            }
            
            document.addEventListener('click', function(e) {
                if (!searchInput.contains(e.target)) {
                    resultsContainer.style.display = 'none';
                }
            });
            // ▲▲▲ FIM DO SCRIPT ATUALIZADO ▲▲▲
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
        
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .stat-card h3 { font-size: 14px; color: #666; margin-bottom: 10px; font-weight: 600; text-transform: uppercase; }
        .stat-card .amount { font-size: 28px; font-weight: 700; }
        .text-success { color: #2e7d32; }
        .text-danger { color: #c62828; }
        .text-warning { color: #f57c00; }
        .text-info { color: #0277bd; }
        .text-primary { color: #5a67d8; }

        .card-receitas { background: rgba(76, 175, 80, 0.1); border: 1px solid rgba(76, 175, 80, 0.2); }
        .card-despesas { background: rgba(244, 67, 54, 0.1); border: 1px solid rgba(244, 67, 54, 0.2); }
        .card-lucro { background: rgba(102, 126, 234, 0.1); border: 1px solid rgba(102, 126, 234, 0.2); }

        .actions-bar { display: flex; justify-content: space-between; align-items: center; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .actions-group { display: flex; align-items: center; gap: 10px; }
        .btn { padding: 10px 20px; border-radius: 8px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: all 0.2s; }
        
        .btn-success { background: rgba(76, 175, 80, 0.15); color: #2e7d32; border-radius: 20px; }
        .btn-success:hover { background: rgba(76, 175, 80, 0.25); transform: translateY(-2px); }
        .btn-danger { background: rgba(244, 67, 54, 0.15); color: #c62828; border-radius: 20px; }
        .btn-danger:hover { background: rgba(244, 67, 54, 0.25); transform: translateY(-2px); }

        .filter-group { display: flex; align-items: center; gap: 10px; }
        .filter-group span { color: #555; font-weight: 600; font-size: 14px; padding-right: 5px; }
        .filter-group .btn-filter { background: rgba(102, 126, 234, 0.15); border: none; color: #434190; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s; }
        .filter-group .btn-filter:hover { background-color: rgba(102, 126, 234, 0.25); transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .filter-group .btn-filter.active { background-color: #434190; color: white; font-weight: 700; }

        .columns-container { display: flex; flex-direction: column; gap: 30px; }

        .launch-section { background: white; padding: 20px; border-radius: 12px; }
        .section-header { margin-bottom: 20px; }
        .section-header h2 { font-size: 22px; color: #333; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 8px; text-align: left; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
        th { font-weight: 600; color: #666; font-size: 11px; text-transform: uppercase; }
        td { font-size: 13px; color: #333; }
        .truncate-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100px; }
        td:first-child { max-width: 150px; }

        .status-select { border: none; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; cursor: pointer; -webkit-appearance: none; -moz-appearance: none; appearance: none; transition: all 0.3s ease; border: 2px solid; }
        .status-select:hover { transform: scale(1.05); }
        .status-recebida, .status-paga { background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
        .status-a_receber, .status-a_pagar { background-color: #fff3e0; color: #f57c00; border-color: #ffcc80; }
        .status-vencida { background-color: #ffebee; color: #c62828; border-color: #ef9a9a; }
        
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

        .card-caixa { grid-column: 1 / -1; }
        .card-caixa .section-header { display: flex; justify-content: space-between; align-items: center; }
        .card-caixa table { margin-top: 10px; }
        .card-caixa table tfoot td { font-weight: bold; border-top: 2px solid #ccc; }
        
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5); display: none; align-items: center;
            justify-content: center; z-index: 1000;
        }
        .modal-overlay.show { display: flex; }
        .modal-content {
            background: white; padding: 30px; border-radius: 12px;
            width: 90%; max-width: 400px; box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        .modal-title { font-size: 20px; margin-bottom: 20px; color: #333; }
        .modal-body .form-group { margin-bottom: 20px; }
        .modal-body label { font-weight: 600; margin-bottom: 8px; display: block; }
        .modal-body select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ccc; }
        .modal-footer { margin-top: 30px; display: flex; justify-content: flex-end; gap: 10px; }
        .modal-footer .btn-modal { padding: 10px 25px; border-radius: 20px; }
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
            <div class="stat-card card-receitas"><h3>Receitas Recebidas</h3><div class="amount text-success">R$ {{ dashboard_data.receitas.recebidas }}</div></div>
            <div class="stat-card"><h3>Receitas a Receber</h3><div class="amount text-warning">R$ {{ dashboard_data.receitas.a_receber }}</div></div>
            <div class="stat-card"><h3>Receitas Vencidas</h3><div class="amount text-danger">R$ {{ dashboard_data.receitas.vencidas }}</div></div>
            <div class="stat-card card-despesas"><h3>Despesas Pagas</h3><div class="amount text-danger">R$ {{ dashboard_data.despesas.pagas }}</div></div>
            <div class="stat-card"><h3>Despesas a Pagar</h3><div class="amount text-warning">R$ {{ dashboard_data.despesas.a_pagar }}</div></div>
            <div class="stat-card"><h3>Despesas Vencidas</h3><div class="amount text-danger">R$ {{ dashboard_data.despesas.vencidas }}</div></div>
            <div class="stat-card card-lucro">
                <h3>Lucro Líquido</h3>
                {% if dashboard_data.lucro_liquido >= 0 %}
                    <div class="amount text-success">R$ {{ dashboard_data.lucro_liquido_formatado }}</div>
                {% else %}
                    <div class="amount text-danger">R$ {{ dashboard_data.lucro_liquido_formatado }}</div>
                {% endif %}
            </div>
            <div class="stat-card card-receitas">
                <h3>Previsão Mensal</h3>
                {% if dashboard_data.previsao_mensal >= 0 %}
                    <div class="amount text-success">R$ {{ dashboard_data.previsao_mensal_formatado }}</div>
                {% else %}
                    <div class="amount text-danger">R$ {{ dashboard_data.previsao_mensal_formatado }}</div>
                {% endif %}
            </div>
        </div>

        <div class="actions-bar">
            <div class="filter-group">
                <span>Período:</span>
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

        <div class="card-caixa launch-section">
            <div class="section-header">
                <h2>📊 Fechamento de Caixa do Período</h2>
                <div class="stat-card" style="padding: 10px; text-align: right;">
                    <h3>Saldo Total do Caixa</h3>
                    {% if dashboard_data.total_saldo_caixa >= 0 %}
                        <div class="amount text-success">R$ {{ dashboard_data.total_saldo_caixa_formatado }}</div>
                    {% else %}
                        <div class="amount text-danger">R$ {{ dashboard_data.total_saldo_caixa_formatado }}</div>
                    {% endif %}
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Modo de Pagamento</th>
                        <th style="text-align: right;">Total Recebido</th>
                        <th style="text-align: right;">Total Pago</th>
                        <th style="text-align: right;">Saldo</th>
                    </tr>
                </thead>
                <tbody>
                {% for item in dashboard_data.fechamento_caixa %}
                    <tr>
                        <td>{{ item.metodo }}</td>
                        <td style="text-align: right;" class="text-success">R$ {{ item.receitas_formatado }}</td>
                        <td style="text-align: right;" class="text-danger">R$ {{ item.despesas_formatado }}</td>
                        <td style="text-align: right; font-weight: bold;">
                            {% if item.saldo >= 0 %}
                                <span class="text-success">R$ {{ item.saldo_formatado }}</span>
                            {% else %}
                                <span class="text-danger">R$ {{ item.saldo_formatado }}</span>
                            {% endif %}
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="4" style="text-align: center; padding: 20px;">Nenhuma transação efetivada no período.</td></tr>
                {% endfor %}
                </tbody>
            </table>
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
        
        <div class="columns-container" style="margin-top: 30px;">
            <div class="launch-section">
                <div class="section-header"><h2>Receitas</h2></div>
                <table>
                    <thead><tr><th>Descrição</th><th>Valor</th><th>Categoria</th><th>Vencimento</th><th>Forma Pgto.</th><th>Status</th><th>Ações</th></tr></thead>
                    <tbody>
                        {% if receitas_html %}{{ receitas_html }}{% else %}<tr><td colspan="7" style="text-align:center; padding: 20px;">Nenhuma receita encontrada.</td></tr>{% endif %}
                    </tbody>
                </table>
            </div>

            <div class="launch-section">
                <div class="section-header"><h2>Despesas</h2></div>
                <table>
                    <thead><tr><th>Descrição</th><th>Valor</th><th>Categoria</th><th>Vencimento</th><th>Forma Pgto.</th><th>Status</th><th>Ações</th></tr></thead>
                    <tbody>
                        {% if despesas_html %}{{ despesas_html }}{% else %}<tr><td colspan="7" style="text-align:center; padding: 20px;">Nenhuma despesa encontrada.</td></tr>{% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="modal-overlay" id="payment-modal">
        <div class="modal-content">
            <h2 class="modal-title" id="modal-title">Confirmar Pagamento</h2>
            <div class="modal-body">
                <div class="form-group">
                    <label for="forma-pagamento-select">Selecione a Forma de Pagamento</label>
                    <select id="forma-pagamento-select">
                        <option value="Dinheiro">Dinheiro</option>
                        <option value="Cartão de Crédito">Cartão de Crédito</option>
                        <option value="Cartão de Débito">Cartão de Débito</option>
                        <option value="PIX">PIX</option>
                        <option value="Transferência Bancária">Transferência Bancária</option>
                        <option value="Boleto">Boleto</option>
                        <option value="Cheque">Cheque</option>
                        <option value="Convênio">Convênio</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary btn-modal" id="modal-cancel-btn">Cancelar</button>
                <button class="btn btn-primary btn-modal" id="modal-confirm-btn">Confirmar</button>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
            function getLocalDateAsString(date) {
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                // REMOVIDAS AS ASPAS INTERNAS
                return `${year}-${month}-${day}`;
            }
            // ▲▲▲ FIM DA CORREÇÃO ▲▲▲

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
                
                navigateWithFilter({ 
                    data_inicial: getLocalDateAsString(startOfWeek), 
                    data_final: getLocalDateAsString(endOfWeek) 
                });
            });

            document.getElementById('filter-today').addEventListener('click', () => {
                navigateWithFilter({ 
                    data_inicial: getLocalDateAsString(new Date()), 
                    data_final: getLocalDateAsString(new Date()) 
                });
            });

            document.getElementById('filter-month').addEventListener('click', () => {
                const d = new Date();
                const firstDay = new Date(d.getFullYear(), d.getMonth(), 1);
                const lastDay = new Date(d.getFullYear(), d.getMonth() + 1, 0);
                navigateWithFilter({ 
                    data_inicial: getLocalDateAsString(firstDay), 
                    data_final: getLocalDateAsString(lastDay) 
                });
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

            document.querySelectorAll('.status-select').forEach(select => {
                select.setAttribute('data-original-status', select.value);
            });
        });

        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 20px; right: 20px; padding: 15px 20px; z-index: 1000;
                background: ${type === 'success' ? '#4CAF50' : '#f44336'};
                color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            setTimeout(() => {
                notification.style.transition = 'opacity 0.5s';
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 500);
            }, 3000);
        }

        const modal = document.getElementById('payment-modal');
        const modalConfirmBtn = document.getElementById('modal-confirm-btn');
        const modalCancelBtn = document.getElementById('modal-cancel-btn');
        const formaPagamentoSelect = document.getElementById('forma-pagamento-select');
        let currentUpdateInfo = {};

        function showPaymentModal(tipo, id, novoStatus, selectElement) {
            currentUpdateInfo = { tipo, id, novoStatus, selectElement };
            document.getElementById('modal-title').textContent = `Confirmar ${tipo === 'receita' ? 'Recebimento' : 'Pagamento'}`;
            modal.classList.add('show');
        }

        modalCancelBtn.addEventListener('click', () => {
            const { selectElement } = currentUpdateInfo;
            selectElement.value = selectElement.getAttribute('data-original-status');
            modal.classList.remove('show');
        });

        modalConfirmBtn.addEventListener('click', () => {
            const { tipo, id, novoStatus, selectElement } = currentUpdateInfo;
            const formaPagamento = formaPagamentoSelect.value;
            
            const payload = {
                status: novoStatus,
                forma_pagamento: formaPagamento
            };
            
            sendUpdateRequest(tipo, id, payload, selectElement);
            modal.classList.remove('show');
        });

        function sendUpdateRequest(tipo, id, payload, selectElement) {
            selectElement.disabled = true;
            selectElement.style.opacity = '0.5';

            const url = `{{ backend_url }}/api/faturamento/${tipo}s/${id}/`;
            const token = "{{ token }}";

            fetch(url, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.detail || 'Erro desconhecido'); });
                }
                return response.json();
            })
            .then(data => {
                showNotification('Status atualizado com sucesso!', 'success');
                selectElement.className = `status-select status-${data.status}`;
                selectElement.setAttribute('data-original-status', data.status);
                setTimeout(() => { window.location.reload(); }, 1000);
            })
            .catch(error => {
                showNotification(`Erro: ${error.message}`, 'error');
                selectElement.value = selectElement.getAttribute('data-original-status');
            })
            .finally(() => {
                selectElement.disabled = false;
                selectElement.style.opacity = '1';
            });
        }
        
        function updateLancamentoStatus(tipo, id, selectElement) {
            const novoStatus = selectElement.value;
            const originalStatus = selectElement.getAttribute('data-original-status');
            
            if (novoStatus === originalStatus) return;

            if ((tipo === 'receita' && novoStatus === 'recebida') || (tipo === 'despesa' && novoStatus === 'paga')) {
                showPaymentModal(tipo, id, novoStatus, selectElement);
            } else {
                const payload = { status: novoStatus };
                sendUpdateRequest(tipo, id, payload, selectElement);
            }
        }
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

# NO ARQUIVO: frontend.py

# ▼▼▼ SUBSTITUA A VARIÁVEL 'LANCAMENTO_FORM_TEMPLATE' PELA VERSÃO ABAIXO ▼▼▼
LANCAMENTO_FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ form_title }} - intelliMed</title>
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
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 20px; }
        .form-container { max-width: 700px; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; font-weight: 600; margin-bottom: 8px; color: #333; }
        .form-group input, .form-group select { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        .form-actions { display: flex; justify-content: flex-end; gap: 15px; margin-top: 30px; }
        .btn { padding: 12px 30px; border-radius: 25px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #e0e0e0; color: #666; }

        /* ▼▼▼ ESTILOS DO ALERTA ADICIONADOS ▼▼▼ */
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
            <a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a>
        </div>
    </div>
    <div class="main-content">
        <!-- ▼▼▼ CONTAINER DE ALERTAS ADICIONADO AQUI ▼▼▼ -->
        <div class="alert-container">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
        </div>
        
        <div class="page-header"><h1>{{ form_title }}</h1></div>
        <div class="form-container">
            <form method="POST">
                {% csrf_token %}
                <div class="form-group">
                    <label for="descricao">Descrição</label>
                    <input type="text" name="descricao" value="{{ lancamento.descricao }}" required>
                </div>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="valor">Valor (R$)</label>
                        <input type="number" step="0.01" name="valor" value="{{ lancamento.valor }}" required>
                    </div>
                    <div class="form-group">
                        <label for="data_vencimento">Data de Vencimento</label>
                        <input type="date" name="data_vencimento" value="{{ lancamento.data_vencimento }}" required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="categoria">Categoria</label>
                    <select name="categoria">
                        <option value="">Sem Categoria</option>
                        {% for categoria in categorias %}
                            <option value="{{ categoria.id }}" {% if categoria.id == lancamento.categoria %}selected{% endif %}>
                                {{ categoria.nome }}
                            </option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label for="status">Status</label>
                        <select name="status" id="status-select" required>
                            {% if tipo_lancamento == 'receita' %}
                                <option value="a_receber" {% if lancamento.status == 'a_receber' %}selected{% endif %}>A Receber</option>
                                <option value="recebida" {% if lancamento.status == 'recebida' %}selected{% endif %}>Recebida</option>
                            {% else %}
                                <option value="a_pagar" {% if lancamento.status == 'a_pagar' %}selected{% endif %}>A Pagar</option>
                                <option value="paga" {% if lancamento.status == 'paga' %}selected{% endif %}>Paga</option>
                            {% endif %}
                        </select>
                    </div>
                </div>
                
                <div id="campos-pagamento-group" style="display: none;">
                    <div class="form-group">
                        {% if tipo_lancamento == 'receita' %}
                            <label for="data_recebimento">Data de Recebimento</label>
                            <input type="date" name="data_recebimento" value="{{ lancamento.data_recebimento }}">
                        {% else %}
                            <label for="data_pagamento">Data de Pagamento</label>
                            <input type="date" name="data_pagamento" value="{{ lancamento.data_pagamento }}">
                        {% endif %}
                    </div>
                    <div class="form-group">
                        <label for="forma_pagamento">Forma de Pagamento</label>
                        <select name="forma_pagamento">
                            <option value="">Selecione...</option>
                            <option value="Dinheiro" {% if lancamento.forma_pagamento == 'Dinheiro' %}selected{% endif %}>Dinheiro</option>
                            <option value="Cartão de Crédito" {% if lancamento.forma_pagamento == 'Cartão de Crédito' %}selected{% endif %}>Cartão de Crédito</option>
                            <option value="Cartão de Débito" {% if lancamento.forma_pagamento == 'Cartão de Débito' %}selected{% endif %}>Cartão de Débito</option>
                            <option value="PIX" {% if lancamento.forma_pagamento == 'PIX' %}selected{% endif %}>PIX</option>
                            <option value="Transferência Bancária" {% if lancamento.forma_pagamento == 'Transferência Bancária' %}selected{% endif %}>Transferência Bancária</option>
                            <option value="Boleto" {% if lancamento.forma_pagamento == 'Boleto' %}selected{% endif %}>Boleto</option>
                            <option value="Cheque" {% if lancamento.forma_pagamento == 'Cheque' %}selected{% endif %}>Cheque</option>
                            <option value="Convênio" {% if lancamento.forma_pagamento == 'Convênio' %}selected{% endif %}>Convênio</option>
                        </select>
                    </div>
                </div>

                <div class="form-actions">
                    <a href="/faturamento/" class="btn btn-secondary">Cancelar</a>
                    <button type="submit" class="btn btn-primary">Salvar</button>
                </div>
            </form>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const statusSelect = document.getElementById('status-select');
            const camposPagamentoGroup = document.getElementById('campos-pagamento-group');

            function toggleCamposPagamento() {
                if (statusSelect.value === 'paga' || statusSelect.value === 'recebida') {
                    camposPagamentoGroup.style.display = 'block';
                } else {
                    camposPagamentoGroup.style.display = 'none';
                }
            }
            toggleCamposPagamento();
            statusSelect.addEventListener('change', toggleCamposPagamento);
        });

        // ▼▼▼ SCRIPT DE AUTO-REMOÇÃO ADICIONADO AQUI ▼▼▼
        document.addEventListener('DOMContentLoaded', (event) => {
            setTimeout(() => {
                const alerts = document.querySelectorAll('.alert-container .alert');
                alerts.forEach(alert => {
                    alert.style.transition = 'opacity 0.5s ease';
                    alert.style.opacity = '0';
                    setTimeout(() => {
                        alert.remove();
                    }, 500);
                });
            }, 5000); // 5 segundos
        });
    </script>
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
        .btn-logout { display: block; width: 100%; padding: 12px; background: rgba(0,0,0,0.2); color: white; text-align: center; text-decoration: none; border-radius: 8px; border: none; cursor: pointer; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .page-header h1 { font-size: 32px; color: #333; margin-bottom: 30px; }
        .info-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; }
        .agendamentos-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
        .info-section { grid-column: span 3; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .agendamentos-section { grid-column: span 3; }
        .info-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; }
        .section-title { font-size: 22px; color: #333; margin-bottom: 25px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; }
        .info-card h3 { font-size: 14px; color: #666; margin-bottom: 10px; font-weight: 600; text-transform: uppercase; }
        .info-card .number { font-size: 36px; font-weight: 700; color: #667eea; }
        .stat-card-agendamento { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
        .stat-card-agendamento h3 { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 15px; }
        .stat-card-agendamento ul { list-style: none; padding: 0; font-size: 12px; color: #555; }
        .stat-card-agendamento li { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #f5f5f5; }
        .stat-card-agendamento li:last-child { border-bottom: none; }
        .stat-card-agendamento strong { color: #333; }
        .stat-card-agendamento hr { border: none; border-top: 1px dashed #ccc; margin: 10px 0; }
        .sub-title { font-weight: bold; font-size: 11px; text-transform: uppercase; color: #888; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
        th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        td { font-size: 14px; color: #333; }
        .status-dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; animation: blinker 1.5s linear infinite; }
        .status-dot.online { background-color: #4CAF50; }
        .status-dot.offline { background-color: #f44336; animation: none; }
        @keyframes blinker { 50% { opacity: 0.3; } }
        .historico-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; grid-column: span 3; }
        .historico-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
        .historico-card h3 { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 15px; }
        .log-list { max-height: 300px; overflow-y: auto; padding-right: 10px; }
        .log-item { display: grid; grid-template-columns: 80px 1fr; align-items: start; padding: 8px 0; border-bottom: 1px solid #f5f5f5; font-size: 12px; }
        .log-item:last-child { border-bottom: none; }
        .log-timestamp { color: #888; }
        .log-details { color: #333; }
        .log-details strong { color: #667eea; }
        .log-details .user { color: #764ba2; }
        .financeiro-card { grid-column: span 3; }
        .financeiro-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .financeiro-header h3 { font-size: 18px; margin: 0; }
        .financeiro-filters { display: flex; gap: 10px; }
        .financeiro-filters select { padding: 8px; border-radius: 6px; border: 1px solid #ccc; }
        .log-financeiro-item { display: grid; grid-template-columns: 80px 60px 1fr 100px 120px; align-items: start; padding: 8px 0; border-bottom: 1px solid #f5f5f5; font-size: 12px; }
        .log-financeiro-item .tipo-receita { color: #2e7d32; font-weight: bold; }
        .log-financeiro-item .tipo-despesa { color: #c62828; font-weight: bold; }
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
                <div class="info-card"><h3>Usuários Cadastrados</h3><p class="number">{{ data.usuarios.total|default:"-" }}</p></div>
                <div class="info-card"><h3>Pacientes Ativos</h3><p class="number">{{ data.estatisticas_gerais.pacientes.total|default:"-" }}</p></div>
                <div class="info-card"><h3>Pacientes Arquivados</h3><p class="number">{{ total_inativos|default:"-" }}</p></div>

                <div class="info-section agendamentos-section">
                    <h2 class="section-title">📊 Estatísticas</h2>
                    <div class="agendamentos-grid">
                        {% with stats=data.estatisticas_gerais.estatisticas_detalhadas.diaria %}
                        <div class="stat-card-agendamento">
                            <h3>Hoje</h3>
                            <p class="sub-title">Agendamentos</p><ul>{% for stat in stats.agendamentos.detalhes %}<li><span>{{ stat.status }}</span> <strong>{{ stat.total }}</strong></li>{% endfor %}</ul><hr>
                            <p class="sub-title">Documentos & Exames</p><ul><li><span>Docs Gerados</span> <strong>{{ stats.documentos.gerados|default:0 }}</strong></li><li><span>Docs Editados</span> <strong>{{ stats.documentos.editados|default:0 }}</strong></li><li><span>Exames Gerados</span> <strong>{{ stats.exames.gerados|default:0 }}</strong></li><li><span>Exames Editados</span> <strong>{{ stats.exames.editados|default:0 }}</strong></li></ul>
                        </div>
                        {% endwith %}
                        {% with stats=data.estatisticas_gerais.estatisticas_detalhadas.semanal %}
                        <div class="stat-card-agendamento">
                            <h3>Esta Semana</h3>
                            <p class="sub-title">Agendamentos</p><ul>{% for stat in stats.agendamentos.detalhes %}<li><span>{{ stat.status }}</span> <strong>{{ stat.total }}</strong></li>{% endfor %}</ul><hr>
                            <p class="sub-title">Documentos & Exames</p><ul><li><span>Docs Gerados</span> <strong>{{ stats.documentos.gerados|default:0 }}</strong></li><li><span>Docs Editados</span> <strong>{{ stats.documentos.editados|default:0 }}</strong></li><li><span>Exames Gerados</span> <strong>{{ stats.exames.gerados|default:0 }}</strong></li><li><span>Exames Editados</span> <strong>{{ stats.exames.editados|default:0 }}</strong></li></ul>
                        </div>
                        {% endwith %}
                        {% with stats=data.estatisticas_gerais.estatisticas_detalhadas.mensal %}
                        <div class="stat-card-agendamento">
                            <h3>Este Mês</h3>
                            <p class="sub-title">Agendamentos</p><ul>{% for stat in stats.agendamentos.detalhes %}<li><span>{{ stat.status }}</span> <strong>{{ stat.total }}</strong></li>{% endfor %}</ul><hr>
                            <p class="sub-title">Documentos & Exames</p><ul><li><span>Docs Gerados</span> <strong>{{ stats.documentos.gerados|default:0 }}</strong></li><li><span>Docs Editados</span> <strong>{{ stats.documentos.editados|default:0 }}</strong></li><li><span>Exames Gerados</span> <strong>{{ stats.exames.gerados|default:0 }}</strong></li><li><span>Exames Editados</span> <strong>{{ stats.exames.editados|default:0 }}</strong></li></ul>
                        </div>
                        {% endwith %}
                        {% with stats=data.estatisticas_gerais.estatisticas_detalhadas.anual %}
                        <div class="stat-card-agendamento">
                            <h3>Este Ano</h3>
                            <p class="sub-title">Agendamentos</p><ul>{% for stat in stats.agendamentos.detalhes %}<li><span>{{ stat.status }}</span> <strong>{{ stat.total }}</strong></li>{% endfor %}</ul><hr>
                            <p class="sub-title">Documentos & Exames</p><ul><li><span>Docs Gerados</span> <strong>{{ stats.documentos.gerados|default:0 }}</strong></li><li><span>Docs Editados</span> <strong>{{ stats.documentos.editados|default:0 }}</strong></li><li><span>Exames Gerados</span> <strong>{{ stats.exames.gerados|default:0 }}</strong></li><li><span>Exames Editados</span> <strong>{{ stats.exames.editados|default:0 }}</strong></li></ul>
                        </div>
                        {% endwith %}
                    </div>
                </div>

                <div class="historico-grid">
                    <div class="historico-card">
                        <h3>Tendências: Histórico de Exames</h3>
                        <div class="log-list">
                            {% for log in log_exames %}
                            <div class="log-item">
                                <div class="log-timestamp">{{ log.data }}<br>{{ log.hora }}</div>
                                <div class="log-details">
                                    <strong>{{ log.tipo_evento }}:</strong> {{ log.detalhes }}<br>
                                    Paciente: <strong>{{ log.paciente_nome }}</strong> | Por: <span class="user">{{ log.usuario_nome }}</span>
                                </div>
                            </div>
                            {% empty %}
                                <p style="text-align:center; color:#999; padding:20px 0;">Nenhum evento de exame recente.</p>
                            {% endfor %}
                        </div>
                    </div>
                    <div class="historico-card">
                        <h3>Tendências: Histórico de Documentos</h3>
                        <div class="log-list">
                            {% for log in log_documentos %}
                            <div class="log-item">
                                <div class="log-timestamp">{{ log.data }}<br>{{ log.hora }}</div>
                                <div class="log-details">
                                    <strong>{{ log.tipo_evento }}:</strong> {{ log.detalhes }}<br>
                                    Paciente: <strong>{{ log.paciente_nome }}</strong> | Por: <span class="user">{{ log.usuario_nome }}</span>
                                </div>
                            </div>
                            {% empty %}
                                <p style="text-align:center; color:#999; padding:20px 0;">Nenhum evento de documento recente.</p>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                
                <div class="info-section financeiro-card">
                    <div class="financeiro-header">
                        <h3>Tendência de Faturamento (Auditoria)</h3>
                        <div class="financeiro-filters">
                            <select id="filter-mes" onchange="applyFinanceFilter()">
                                {% for num, nome in meses_disponiveis %}
                                <option value="{{ num }}" {% if num == selected_mes %}selected{% endif %}>{{ nome }}</option>
                                {% endfor %}
                            </select>
                            <select id="filter-ano" onchange="applyFinanceFilter()">
                                {% for ano in anos_disponiveis %}
                                <option value="{{ ano }}" {% if ano == selected_ano %}selected{% endif %}>{{ ano }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="log-list">
                        <div class="log-financeiro-item" style="font-weight: bold; color: #666;">
                            <span>Data</span><span>Tipo</span><span>Descrição</span><span>Valor</span><span>Usuário</span>
                        </div>
                        {% for log in log_financeiro %}
                        <div class="log-financeiro-item">
                            <div class="log-timestamp">{{ log.data }}</div>
                            <div class="tipo-{{ log.tipo|lower }}">{{ log.tipo }}</div>
                            <div class="log-details">{{ log.descricao }}</div>
                            <div class="log-details">{{ log.valor_formatado }}</div>
                            <div class="log-details user">{{ log.usuario_nome }}</div>
                        </div>
                        {% empty %}
                            <p style="text-align:center; color:#999; padding:20px 0;">Nenhuma transação financeira efetivada no período selecionado.</p>
                        {% endfor %}
                    </div>
                </div>

                <div class="info-section">
                    <h2 class="section-title">👥 Usuários do Sistema</h2>
                    <table>
                        <thead><tr><th>Status</th><th>Nome</th><th>Função</th><th>Email</th><th>Último Login</th></tr></thead>
                        <tbody>
                        {% for usuario in data.usuarios.lista %}
                            <tr>
                                <td>{% if usuario.status == 'ativo' %}<span class="status-dot online"></span> Ativo{% else %}<span class="status-dot offline"></span> Inativo{% endif %}</td>
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
            </div>
        {% endif %}
    </div>

    <script>
        function applyFinanceFilter() {
            const mes = document.getElementById('filter-mes').value;
            const ano = document.getElementById('filter-ano').value;
            const url = new URL(window.location.href);
            url.searchParams.set('mes', mes);
            url.searchParams.set('ano', ano);
            window.location.href = url.toString();
        }
    </script>
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
        
        /* ▼▼▼ INÍCIO DOS NOVOS ESTILOS ▼▼▼ */
        .searchable-select-container { position: relative; }
        #paciente-search-input { font-size: 1rem; }
        #paciente-search-results {
            display: none;
            position: absolute;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            width: 100%;
            max-height: 200px;
            overflow-y: auto;
            z-index: 100;
            margin-top: 5px;
        }
        .search-result-item { padding: 10px; cursor: pointer; }
        .search-result-item:hover { background-color: #f0f0f0; }
        .search-result-item small { display: block; color: #777; }
        /* ▲▲▲ FIM DOS NOVOS ESTILOS ▲▲▲ */
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
                    <!-- ▼▼▼ INÍCIO DA ALTERAÇÃO HTML ▼▼▼ -->
                    <div class="searchable-select-container">
                        <input type="text" id="paciente-search-input" placeholder="Digite para buscar por nome ou CPF..." autocomplete="off">
                        <div id="paciente-search-results"></div>
                    </div>
                    <select name="paciente_id" id="paciente-select" required style="display: none;">
                        <option value="">Selecione...</option>
                        {% for p in pacientes %}
                            <option value="{{ p.id }}" data-cpf="{{ p.cpf }}">{{ p.nome_completo }}</option>
                        {% endfor %}
                    </select>
                    <!-- ▲▲▲ FIM DA ALTERAÇÃO HTML ▲▲▲ -->
                </div>
                <div class="form-group">
                    <label>2. Envie o Arquivo do Exame</label>
                    <div id="file-upload-area">
                        <input type="file" name="arquivo" id="arquivo" accept="image/*,.pdf" style="display: none;" required>
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

        // ▼▼▼ INÍCIO DO NOVO SCRIPT PARA DROPDOWN PESQUISÁVEL ▼▼▼
        document.addEventListener('DOMContentLoaded', function() {
            const searchInput = document.getElementById('paciente-search-input');
            const resultsContainer = document.getElementById('paciente-search-results');
            const hiddenSelect = document.getElementById('paciente-select');
            const options = Array.from(hiddenSelect.options);

            searchInput.addEventListener('input', function(e) {
                let originalValue = e.target.value;
                if (/^\\d{1,11}$/.test(originalValue.replace(/[.\\-]/g, ''))) {
                    let numbers = originalValue.replace(/\\D/g, '');
                    numbers = numbers.substring(0, 11);
                    let formatted = numbers;
                    if (numbers.length > 9) {
                        formatted = numbers.replace(/(\\d{3})(\\d{3})(\\d{3})(\\d{2})/, "$1.$2.$3-$4");
                    } else if (numbers.length > 6) {
                        formatted = numbers.replace(/(\\d{3})(\\d{3})(\\d{1,3})/, "$1.$2.$3");
                    } else if (numbers.length > 3) {
                        formatted = numbers.replace(/(\\d{3})(\\d{1,3})/, "$1.$2");
                    }
                    e.target.value = formatted;
                }
                filterAndDisplayResults();
            });

            function filterAndDisplayResults() {
                const searchTerm = searchInput.value.toLowerCase();
                resultsContainer.innerHTML = '';
                resultsContainer.style.display = 'block';

                if (searchTerm.length === 0) {
                    resultsContainer.style.display = 'none';
                    return;
                }

                const filteredOptions = options.filter(option => {
                    const nome = option.text.toLowerCase();
                    const cpf = option.dataset.cpf ? option.dataset.cpf.toLowerCase() : '';
                    return (nome.includes(searchTerm) || cpf.includes(searchTerm)) && option.value !== '';
                });

                filteredOptions.forEach(option => {
                    const item = document.createElement('div');
                    item.className = 'search-result-item';
                    item.innerHTML = `${option.text} <small>CPF: ${option.dataset.cpf || 'N/A'}</small>`;
                    item.dataset.value = option.value;
                    item.dataset.text = option.text;

                    item.addEventListener('click', () => {
                        searchInput.value = item.dataset.text;
                        hiddenSelect.value = item.dataset.value;
                        resultsContainer.style.display = 'none';
                    });

                    resultsContainer.appendChild(item);
                });
            }

            document.addEventListener('click', function(e) {
                if (searchInput && !searchInput.contains(e.target)) {
                    resultsContainer.style.display = 'none';
                }
            });
        });
        // ▲▲▲ FIM DO NOVO SCRIPT ▲▲▲
    </script>
</body>
</html>
"""

# NO ARQUIVO: frontend.py

# ▼▼▼ SUBSTITUA A VARIÁVEL 'EXAME_VISUALIZAR_TEMPLATE' INTEIRA POR ESTA VERSÃO SIMPLIFICADA E CORRIGIDA ▼▼▼
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
        .btn { padding: 10px 22px; border-radius: 20px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: all 0.2s; font-size: 14px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .btn-secondary { background: rgba(108, 117, 125, 0.15); color: #495057; }
        .btn-edit { background: rgba(255, 193, 7, 0.15); color: #b08800; }
        .btn-print { background: rgba(0, 123, 255, 0.15); color: #0056b3; }
        .laudo-container { display: flex; gap: 30px; align-items: flex-start; }
        .laudo-content { flex: 2; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .laudo-header { padding: 20px; border-bottom: 1px solid #eee; }
        .laudo-header h2 { font-size: 20px; color: #333; margin-bottom: 5px; }
        .laudo-header p { font-size: 14px; color: #666; }
        .laudo-body { padding: 20px; }
        #laudo-texto, #laudo-editor { width: 100%; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace; font-size: 13px; line-height: 1.6; color: #333; background: #fdfdfd; padding: 15px; border-radius: 8px; border: 1px solid #eee; }
        #laudo-editor { display: none; min-height: 600px; resize: vertical; }
        #btn-salvar-edicao { display: none; margin-top: 15px; }
        .info-sidebar { flex: 1; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 20px; }
        .info-title { font-size: 18px; color: #333; margin-bottom: 15px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        .info-item { margin-bottom: 12px; }
        .info-item label { display: block; font-size: 12px; font-weight: 600; color: #666; margin-bottom: 3px; }
        .info-item p { font-size: 14px; color: #333; }
        .badge { display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: 700; }
        .badge-success { background: #e8f5e9; color: #2e7d32; }
        .badge-warning { background: #fff8e1; color: #f57c00; }
        @media print { body * { visibility: hidden; } #print-area, #print-area * { visibility: visible; } #print-area { position: absolute; left: 0; top: 0; width: 100%; font-family: 'Times New Roman', Times, serif; font-size: 12pt; line-height: 1.5; white-space: pre-wrap; } }
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
        <div class="sidebar-footer"><a href="{% url 'logout' %}" class="btn-logout">⬅️ Sair</a></div>
    </div>
    <div class="main-content">
        <div class="page-header">
            <div class="page-title"><h1>🔬 Laudo do Exame (iA)</h1></div>
            <div class="header-actions">
                <!-- ▼▼▼ LÓGICA DO BOTÃO "VOLTAR" CORRIGIDA E SIMPLIFICADA ▼▼▼ -->
                {% if paciente_id_origem %}
                    <a href="/pacientes/{{ paciente_id_origem }}/exames/" class="btn btn-secondary">Voltar</a>
                {% else %}
                    <a href="{% url 'exames_analise' %}" class="btn btn-secondary">Voltar</a>
                {% endif %}
                {% if user.funcao != 'secretaria' %}<button id="btn-editar-laudo" class="btn btn-edit">✏️ Editar Laudo</button>{% endif %}
                <button onclick="printLaudo()" class="btn btn-print">🖨️ Imprimir</button>
            </div>
        </div>
        {% if error_message %}
            <div style="background: #ffebee; color: #c62828; padding: 20px; border-radius: 8px;">{{ error_message }}</div>
        {% else %}
            <div class="laudo-container">
                <div class="laudo-content">
                    <div class="laudo-header"><h2>{{ exame.tipo_exame_identificado_ia|default:"Laudo de Exame" }}</h2><p>Análise gerada por Inteligência Artificial</p></div>
                    <div class="laudo-body">
                        <div id="laudo-texto">{{ exame.interpretacao_ia|default:"Conteúdo do laudo não disponível." }}</div>
                        {% if user.funcao != 'secretaria' %}
                            <form id="form-edicao" method="POST">
                                {% csrf_token %}
                                <textarea id="laudo-editor" name="laudo_editado">{{ exame.interpretacao_ia }}</textarea>
                                <button type="submit" id="btn-salvar-edicao" class="btn btn-print">💾 Salvar Alterações</button>
                            </form>
                        {% endif %}
                    </div>
                </div>
                <div class="info-sidebar">
                    <h3 class="info-title">Detalhes do Exame</h3>
                    <div class="info-item"><label>Paciente</label><p>{{ exame.paciente_nome }}</p></div>
                    <div class="info-item"><label>Data do Exame</label><p>{{ exame.data_exame }}</p></div>
                    <div class="info-item"><label>ID do Exame</label><p>#{{ exame.id }}</p></div>
                    <div class="info-item"><label>Status</label><p><span class="badge badge-success">{{ exame.status_display }}</span></p></div>
                    <div class="info-item"><label>Confiança da iA</label><p><span class="badge badge-warning">{{ exame.confianca_ia|floatformat:2 }}%</span></p></div>
                    <div class="info-item"><label>Revisão Médica</label><p>{{ exame.revisado_por_medico|yesno:"Sim,Requer Revisão" }}</p></div>
                </div>
            </div>
        {% endif %}
    </div>
    <script>
        {% if user.funcao != 'secretaria' %}
            document.getElementById('btn-editar-laudo').addEventListener('click', function() {
                document.getElementById('laudo-texto').style.display = 'none';
                document.getElementById('laudo-editor').style.display = 'block';
                document.getElementById('btn-salvar-edicao').style.display = 'block';
                this.style.display = 'none';
            });
        {% endif %}
        function printLaudo() {
            const laudoTextoDiv = document.getElementById('laudo-texto');
            const laudoEditor = document.getElementById('laudo-editor');
            const isEditing = laudoEditor && laudoEditor.style.display !== 'none';
            const contentToPrint = isEditing ? laudoEditor.value : laudoTextoDiv.innerText;
            const printWindow = window.open('', '_blank', 'height=600,width=800');
            if (printWindow) {
                printWindow.document.write('<html><head><title>Imprimir Laudo</title>');
                printWindow.document.write('<style>body { font-family: "Courier New", monospace; white-space: pre-wrap; margin: 20px; font-size: 12pt; }</style>');
                printWindow.document.write('</head><body></body></html>');
                printWindow.document.body.innerText = contentToPrint;
                printWindow.document.close();
                printWindow.focus();
                printWindow.addEventListener('afterprint', () => { printWindow.close(); });
                printWindow.print();
            } else { alert('Por favor, habilite pop-ups para este site para poder imprimir.'); }
        }
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

        /* --- INÍCIO DA CORREÇÃO --- */
        .error-banner {
            background: #ffebee; 
            color: #c62828; 
            padding: 15px; 
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #ffcdd2;
        }
        .access-denied-container {
            background: white;
            border-radius: 12px;
            padding: 50px 30px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #f0f0f0;
        }
        .access-denied-container .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        .access-denied-container h1 {
            font-size: 24px;
            color: #c62828;
            margin-bottom: 10px;
        }
        .access-denied-container p {
            color: #333;
            font-size: 16px;
            max-width: 500px;
            margin: 0 auto 30px auto;
        }
        .btn-back {
            display: inline-block;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: 600;
            text-decoration: none;
            background: #667eea;
            color: white;
            transition: all 0.2s;
        }
        .btn-back:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        /* --- FIM DA CORREÇÃO --- */
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
                <!-- --- INÍCIO DA CORREÇÃO --- -->
                {% if not is_permission_error %}
                <p>Pacientes agendados para hoje: {{ data.data }}</p>
                {% endif %}
                <!-- --- FIM DA CORREÇÃO --- -->
            </div>
            <button onclick="location.reload()" class="btn-refresh">Atualizar</button>
        </div>

        <!-- --- INÍCIO DA CORREÇÃO --- -->
        {% if is_permission_error %}
            <div class="access-denied-container">
                <div class="icon">🚫</div>
                <h1>Acesso Negado</h1>
                <p>{{ error_message }}</p>
                <a href="{% url 'dashboard' %}" class="btn-back">Voltar para o Dashboard</a>
            </div>
        {% elif error_message %}
            <div class="error-banner">{{ error_message }}</div>
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
                        </div>
                    </div>
                {% empty %}
                    <div class="empty-list">
                        <h3>Nenhum paciente na fila para hoje.</h3>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
        <!-- --- FIM DA CORREÇÃO --- -->
    </div>
</body>
</html>
"""

# NO ARQUIVO: frontend.py

# ▼▼▼ SUBSTITUA A VARIÁVEL 'WORKSPACE_CONSULTA_TEMPLATE' INTEIRA PELA VERSÃO ABAIXO ▼▼▼
WORKSPACE_CONSULTA_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Consulta em Andamento - intelliMed</title>
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
        .menu-item { display: flex; align-items: center; padding: 14px 25px; color: white; text-decoration: none; font-size: 15px; border-left: 3px solid transparent; transition: all 0.3s; }
        .menu-item:hover { background: rgba(255,255,255,0.1); }
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
        
        .mic-selector { margin-bottom: 15px; }
        .mic-selector label { display: block; font-weight: 600; margin-bottom: 8px; color: #666; }
        .mic-selector select { width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        
        .volume-meter { margin-bottom: 15px; }
        .volume-meter-label { font-weight: 600; color: #666; margin-bottom: 8px; }
        .volume-bar-container { height: 30px; background: #f0f0f0; border-radius: 15px; overflow: hidden; position: relative; }
        .volume-bar { height: 100%; background: linear-gradient(90deg, #4caf50, #8bc34a, #ffc107, #ff5722); width: 0%; transition: width 0.1s; }
        .volume-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: 600; color: #333; font-size: 12px; }
        
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
        .document-list { display: flex; flex-direction: column; gap: 10px; }
        .document-item { background: #f9f9f9; border: 1px solid #eee; border-radius: 8px; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
        .document-item-name { font-weight: 600; color: #333; }
        .document-item-actions { display: flex; gap: 8px; }
        .btn-doc-action { padding: 8px 15px; font-size: 13px; font-weight: 500; border-radius: 20px; border: none; cursor: pointer; transition: all 0.2s; }
        .btn-doc-action:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .btn-view-doc { background: #e0e0e0; color: #555; }
        .btn-print-doc { background: #e3f2fd; color: #1976d2; }
        .text-blue { color: #007bff; }
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
            
            <div class="mic-selector">
                <label for="mic-select">🎙️ Selecione o Microfone:</label>
                <select id="mic-select">
                    <option value="">Carregando microfones...</option>
                </select>
            </div>
            
            <div class="volume-meter">
                <div class="volume-meter-label">📊 Nível de Áudio (teste se está captando):</div>
                <div class="volume-bar-container">
                    <div id="volume-bar" class="volume-bar"></div>
                    <div id="volume-text" class="volume-text">0%</div>
                </div>
            </div>
            
            <div style="display: flex; align-items: center; gap: 20px;">
                <button id="btn-rec" class="btn-rec" title="Iniciar Gravação">🎤</button>
                <div id="recording-status">Selecione um microfone e clique no botão para gravar</div>
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
        <div class="card">
            <h2 class="card-title">4. Documentos Salvos</h2>
            <div id="document-list" class="document-list">
                {% if documentos_salvos %}
                    {% for doc in documentos_salvos %}
                        <div class="document-item" id="doc-item-{{ doc.tipo }}">
                            <span class="document-item-name">
                                <span class="text-blue">{{ doc.data_geracao }}</span> - {{ consulta.paciente_nome }} - <span class="text-blue">{{ doc.tipo|capfirst }}</span>
                            </span>
                            <div class="document-item-actions">
                                <button class="btn-doc-action btn-view-doc" onclick="showModal('{{ doc.tipo }}', document.getElementById('doc-content-{{ doc.tipo }}').textContent)">
                                    Visualizar / Editar
                                </button>
                                <button class="btn-doc-action btn-print-doc" onclick="printDocument('{{ doc.tipo }}')">
                                    Imprimir
                                </button>
                            </div>
                            <div id="doc-content-{{ doc.tipo }}" style="display: none;">{{ doc.conteudo }}</div>
                        </div>
                    {% endfor %}
                {% else %}
                    <p id="no-docs-message" style="color: #999; text-align: center;">Nenhum documento salvo para esta consulta ainda.</p>
                {% endif %}
            </div>
        </div>
        <!-- --- INÍCIO DA CORREÇÃO --- -->
        <div class="final-actions">
            <button id="btn-finalizar" class="btn btn-secondary" onclick="finalizarConsulta()">Finalizar Consulta</button>
        </div>
        <!-- --- FIM DA CORREÇÃO --- -->
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
        // --- INÍCIO DA CORREÇÃO ---
        async function finalizarConsulta() {
            if (!confirm("Tem certeza que deseja finalizar esta consulta?")) {
                return;
            }

            const btnFinalizar = document.getElementById('btn-finalizar');
            btnFinalizar.textContent = 'Finalizando...';
            btnFinalizar.disabled = true;

            const backendUrl = '{{ BACKEND_URL }}';
            const consultaId = '{{ consulta.id }}';
            const token = '{{ token }}';

            try {
                const response = await fetch(`${backendUrl}/api/consultas/${consultaId}/finalizar/`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}` 
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.erro || 'Falha ao finalizar a consulta.');
                }
                
                alert("Consulta finalizada com sucesso!");
                window.location.href = "{% url 'consultas' %}";

            } catch (err) {
                console.error('❌ Erro ao finalizar consulta:', err);
                alert(`Erro: ${err.message}`);
                btnFinalizar.textContent = 'Finalizar Consulta';
                btnFinalizar.disabled = false;
            }
        }
        // --- FIM DA CORREÇÃO ---

        document.addEventListener('DOMContentLoaded', async () => {
            const btnRec = document.getElementById('btn-rec');
            const btnTranscrever = document.getElementById('btn-transcrever');
            const recStatus = document.getElementById('recording-status');
            const transcriptionOutput = document.getElementById('transcription-output');
            const timerDisplay = document.getElementById('timer');
            const documentCard = document.getElementById('document-generation-card');
            const micSelect = document.getElementById('mic-select');
            const volumeBar = document.getElementById('volume-bar');
            const volumeText = document.getElementById('volume-text');
            
            let isRecording = false;
            let mediaRecorder;
            let audioChunks = [];
            let timerInterval;
            let seconds = 0;
            let recordedMimeType = '';
            let audioContext;
            let analyser;
            let microphone;
            let animationId;
            let selectedDeviceId = null;

            await loadMicrophones();

            async function loadMicrophones() {
                try {
                    await navigator.mediaDevices.getUserMedia({ audio: true });
                    const devices = await navigator.mediaDevices.enumerateDevices();
                    const audioInputs = devices.filter(device => device.kind === 'audioinput');
                    micSelect.innerHTML = '';
                    if (audioInputs.length === 0) {
                        micSelect.innerHTML = '<option>Nenhum microfone detectado</option>';
                        recStatus.textContent = '❌ Nenhum microfone encontrado!';
                        recStatus.style.color = '#dc3545';
                        return;
                    }
                    audioInputs.forEach((device, index) => {
                        const option = document.createElement('option');
                        option.value = device.deviceId;
                        option.text = device.label || `Microfone ${index + 1}`;
                        micSelect.appendChild(option);
                    });
                    selectedDeviceId = audioInputs[0].deviceId;
                    startVolumeMonitoring();
                } catch (error) {
                    recStatus.textContent = 'Erro ao acessar microfones: ' + error.message;
                    recStatus.style.color = '#dc3545';
                }
            }

            micSelect.addEventListener('change', () => {
                selectedDeviceId = micSelect.value;
                stopVolumeMonitoring();
                startVolumeMonitoring();
            });

            async function startVolumeMonitoring() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: { deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined } 
                    });
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    analyser = audioContext.createAnalyser();
                    microphone = audioContext.createMediaStreamSource(stream);
                    analyser.fftSize = 256;
                    microphone.connect(analyser);
                    const bufferLength = analyser.frequencyBinCount;
                    const dataArray = new Uint8Array(bufferLength);
                    function updateVolume() {
                        analyser.getByteFrequencyData(dataArray);
                        let sum = 0;
                        for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
                        const average = sum / bufferLength;
                        const volume = Math.min(100, Math.floor((average / 128) * 100));
                        volumeBar.style.width = volume + '%';
                        volumeText.textContent = volume + '%';
                        if (!isRecording) animationId = requestAnimationFrame(updateVolume);
                    }
                    updateVolume();
                } catch (error) {
                    console.error('❌ Erro ao monitorar volume:', error);
                }
            }

            function stopVolumeMonitoring() {
                if (animationId) cancelAnimationFrame(animationId);
                if (audioContext) audioContext.close();
                if (microphone && microphone.mediaStream) {
                    microphone.mediaStream.getTracks().forEach(track => track.stop());
                }
            }

            btnRec.addEventListener('click', () => {
                if (isRecording) stopRecordingRec(); else startRecording();
            });

            async function startRecording() {
                try {
                    stopVolumeMonitoring();
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: { 
                            deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined,
                            echoCancellation: true, noiseSuppression: true, autoGainControl: true
                        } 
                    });
                    isRecording = true;
                    audioChunks = [];
                    let options = { mimeType: 'audio/webm;codecs=opus' };
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) options = { mimeType: 'audio/mp4' };
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) options = { mimeType: 'audio/webm' };
                    mediaRecorder = new MediaRecorder(stream, options);
                    recordedMimeType = mediaRecorder.mimeType || 'audio/webm;codecs=opus';
                    mediaRecorder.ondataavailable = event => {
                        if (event.data.size > 0) audioChunks.push(event.data);
                    };
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: recordedMimeType });
                        if (audioBlob.size === 0) {
                            alert('❌ Áudio vazio! Verifique o microfone.');
                            btnRec.disabled = false;
                            btnRec.innerHTML = '🎤';
                            recStatus.textContent = 'Erro: áudio vazio';
                            return;
                        }
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64String = reader.result.split(',')[1];
                            let formato = 'webm';
                            if (recordedMimeType.includes('mp4')) formato = 'mp4';
                            sendAudioToBackend(base64String, formato);
                        };
                        reader.readAsDataURL(audioBlob);
                    };
                    mediaRecorder.start(1000);
                    startTimer();
                    updateUIRecording(true);
                } catch (err) {
                    recStatus.textContent = "Erro ao acessar microfone: " + err.message;
                }
            }

            function stopRecordingRec() {
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                    mediaRecorder.stop();
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());
                }
                isRecording = false;
                stopTimer();
                updateUIRecording(false);
                setTimeout(() => startVolumeMonitoring(), 2000);
            }
            
            function updateUIRecording(isRec) {
                if (isRec) {
                    btnRec.classList.add('recording');
                    btnRec.innerHTML = '⏹️';
                    recStatus.textContent = "🔴 Gravando... Clique para parar.";
                    recStatus.style.color = '#dc3545';
                } else {
                    btnRec.classList.remove('recording');
                    btnRec.innerHTML = '...';
                    recStatus.textContent = "Processando áudio...";
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

            async function sendAudioToBackend(base64String, formato) {
                const backendUrl = '{{ BACKEND_URL }}', consultaId = '{{ consulta.id }}', token = '{{ token }}';
                try {
                    const response = await fetch(`${backendUrl}/api/consultas/${consultaId}/salvar-audio/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                        body: JSON.stringify({ audio_base64: base64String, audio_formato: formato })
                    });
                    if (!response.ok) throw new Error((await response.json()).erro || 'Falha ao salvar áudio.');
                    recStatus.textContent = "✅ Áudio salvo! Clique em 'Transcrever'.";
                    recStatus.style.color = '#28a745';
                    btnTranscrever.style.display = 'block';
                } catch (err) {
                    recStatus.textContent = `Erro: ${err.message}`;
                    recStatus.style.color = '#dc3545';
                } finally {
                    btnRec.disabled = false;
                    btnRec.innerHTML = '🎤';
                }
            }

            btnTranscrever.addEventListener('click', async () => {
                btnTranscrever.disabled = true;
                btnTranscrever.textContent = 'Transcrevendo...';
                transcriptionOutput.textContent = 'Processando com iA Gemini...';
                recStatus.textContent = "Aguarde, a iA está trabalhando...";
                const backendUrl = '{{ BACKEND_URL }}', consultaId = '{{ consulta.id }}', token = '{{ token }}';
                try {
                    const response = await fetch(`${backendUrl}/api/consultas/${consultaId}/transcrever-audio/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }
                    });
                    if (!response.ok) throw new Error((await response.json()).erro || `Erro ${response.status}`);
                    const data = await response.json();
                    const transcricao = data.transcricao_ia || data.transcricao_completa || "";
                    if (transcricao && transcricao.length > 10) {
                        transcriptionOutput.textContent = transcricao;
                        recStatus.textContent = "✅ Transcrição Concluída!";
                        recStatus.style.color = '#28a745';
                        documentCard.style.display = 'block';
                        btnTranscrever.style.display = 'none';
                    } else {
                        transcriptionOutput.textContent = "⚠️ Transcrição vazia.";
                        recStatus.textContent = "⚠️ Áudio sem fala detectável";
                        btnTranscrever.textContent = '🔄 Tentar Novamente';
                    }
                } catch (err) {
                    transcriptionOutput.textContent = `❌ Erro: ${err.message}`;
                    recStatus.textContent = `Erro: ${err.message}`;
                } finally {
                    if (btnTranscrever) btnTranscrever.disabled = false;
                }
            });

            window.generateDocument = async function(tipo) {
                // (O restante do código JavaScript permanece inalterado)
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
                    await refreshDocumentList();
                } catch(error) { alert(error.message); } 
                finally { saveBtn.textContent = 'Salvar Documento'; saveBtn.disabled = false; }
            }
            async function refreshDocumentList() {
                const backendUrl = '{{ BACKEND_URL }}', consultaId = '{{ consulta.id }}', token = '{{ token }}';
                const docListContainer = document.getElementById('document-list');
                try {
                    const response = await fetch(`${backendUrl}/api/consultas/${consultaId}/documentos/`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (!response.ok) return;
                    const data = await response.json();
                    const documents = data.documentos || [];
                    docListContainer.innerHTML = '';
                    if (documents.length > 0) {
                        documents.forEach(doc => {
                            const docTypeCapitalized = doc.tipo.charAt(0).toUpperCase() + doc.tipo.slice(1);
                            const docItemHTML = `
                                <div class="document-item" id="doc-item-${doc.tipo}">
                                    <span class="document-item-name">
                                        <span class="text-blue">${doc.data_geracao}</span> - {{ consulta.paciente_nome }} - <span class="text-blue">${docTypeCapitalized}</span>
                                    </span>
                                    <div class="document-item-actions">
                                        <button class="btn-doc-action btn-view-doc" onclick="showModal('${doc.tipo}', document.getElementById('doc-content-${doc.tipo}').textContent)">Visualizar / Editar</button>
                                        <button class="btn-doc-action btn-print-doc" onclick="printDocument('${doc.tipo}')">Imprimir</button>
                                    </div>
                                    <div id="doc-content-${doc.tipo}" style="display: none;">${doc.conteudo}</div>
                                </div>
                            `;
                            docListContainer.insertAdjacentHTML('beforeend', docItemHTML);
                        });
                    } else {
                        docListContainer.innerHTML = '<p id="no-docs-message" style="color: #999; text-align: center;">Nenhum documento salvo para esta consulta ainda.</p>';
                    }
                } catch(error) { console.error("Erro ao atualizar lista:", error); }
            }
            window.printDocument = function(tipo) {
                const contentToPrint = document.getElementById(`doc-content-${tipo}`).textContent;
                const printWindow = window.open('', '_blank');
                if (printWindow) {
                    printWindow.document.write('<html><head><title>Imprimir</title><style>body{font-family:"Courier New",monospace;white-space:pre-wrap;margin:20px;}</style></head><body>' + contentToPrint + '</body></html>');
                    printWindow.document.close();
                    printWindow.focus();
                    printWindow.print();
                    printWindow.onafterprint = () => printWindow.close();
                } else { alert('Habilite pop-ups para imprimir.'); }
            }
        });
    </script>
</body>
</html>
"""

EXAMES_ACCESS_DENIED_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Acesso Negado - intelliMed</title>
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
        .page-header h1 { font-size: 32px; color: #333; }
        .access-denied-container { background: white; border-radius: 12px; padding: 50px 30px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #f0f0f0; margin-top: 30px; }
        .access-denied-container .icon { font-size: 64px; margin-bottom: 20px; }
        .access-denied-container h1 { font-size: 24px; color: #c62828; margin-bottom: 10px; }
        .access-denied-container p { color: #333; font-size: 16px; max-width: 500px; margin: 0 auto 30px auto; }
        .btn-back { display: inline-block; padding: 12px 30px; border-radius: 25px; font-weight: 600; text-decoration: none; background: #667eea; color: white; transition: all 0.2s; }
        .btn-back:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
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
        <div class="page-header">
            <h1>Exames com Análise iA</h1>
        </div>
        <div class="access-denied-container">
            <div class="icon">🚫</div>
            <h1>Acesso Negado</h1>
            <p>{{ error_message }}</p>
            <a href="{% url 'dashboard' %}" class="btn-back">Voltar para o Dashboard</a>
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
        'token': token,
        'backend_url': Config.BACKEND_URL,
        'lista_espera_json': '[]',
        'csrf_token': get_token(request) # Adiciona o token CSRF ao contexto
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
        
        context['lista_espera_json'] = json.dumps(agendamentos_do_dia)

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

    # ▼▼▼ INÍCIO DA ALTERAÇÃO ▼▼▼
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
    # ▲▲▲ FIM DA ALTERAÇÃO ▲▲▲

    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/completo/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('paciente') and data['paciente'].get('data_nascimento'):
            data_nasc_str = data['paciente']['data_nascimento']
            try:
                data_nasc_obj = datetime.strptime(data_nasc_str, '%Y-%m-%d')
                data['paciente']['data_nascimento'] = data_nasc_obj.strftime('%d/%m/%Y')
            except ValueError:
                pass 
        
        # ▼▼▼ INÍCIO DA ALTERAÇÃO ▼▼▼
        # Adiciona o usuário ao contexto principal
        data['user'] = user
        # ▲▲▲ FIM DA ALTERAÇÃO ▲▲▲

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
    """Página para exibir o histórico completo de um paciente."""
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
        'historico': [],
        'error_message': None
    }

    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/historico_completo/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        context['paciente'] = data.get('paciente')
        context['historico'] = data.get('historico')

    except requests.exceptions.RequestException as e:
        context['error_message'] = f"Erro de comunicação ao buscar o histórico: {e}"
    except Exception as e:
        context['error_message'] = f"Ocorreu um erro inesperado: {e}"

    from django.template import Template, RequestContext
    template = Template(HISTORICO_PACIENTE_TEMPLATE)
    ctx = RequestContext(request, context)
    return HttpResponse(template.render(ctx))

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
        'token': token,
        'BACKEND_URL': Config.BACKEND_URL
    }

    # Se for médico ou admin e o método for POST, processa o formulário de novo exame
    if user.get('funcao') in ['medico', 'admin'] and request.method == 'POST':
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
        paciente_response = requests.get(f'{Config.BACKEND_URL}/api/pacientes/{paciente_id}/', headers={'Authorization': f'Bearer {token}'})
        paciente_response.raise_for_status()
        context['paciente'] = paciente_response.json()

        # Aumentar o page_size para garantir que todos os exames sejam carregados
        exames_response = requests.get(f'{Config.BACKEND_URL}/api/exames/?paciente_id={paciente_id}&page_size=100', headers={'Authorization': f'Bearer {token}'})
        exames_response.raise_for_status()
        todos_exames = exames_response.json().get('results', [])

        for exame in todos_exames:
            try:
                data_obj = datetime.strptime(exame['data_exame'], '%Y-%m-%d')
                exame['data_exame_formatada'] = data_obj.strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                exame['data_exame_formatada'] = exame['data_exame']

            # ▼▼▼ LÓGICA DE SEPARAÇÃO CORRIGIDA PARA USAR O STATUS ▼▼▼
            # Se o status do exame está em um estado de IA (interpretado, revisado, processando),
            # ou se o campo de interpretação_ia tem conteúdo, classificamos como Exame iA.
            ia_status = ['interpretado_ia', 'revisado_medico', 'processando_ia', 'enviado_ia']
            
            if exame.get('status') in ia_status or exame.get('interpretacao_ia'):
                context['exames_ia'].append(exame)
            else:
                context['exames_gerais'].append(exame)
            # ▲▲▲ FIM DA CORREÇÃO ▲▲▲

    except Exception as e:
        context['error_message'] = f"Erro ao carregar dados do paciente ou exames: {e}"

    from django.template import Template, RequestContext
    context['messages'] = messages.get_messages(request)
    
    if user.get('funcao') == 'secretaria':
        template = Template(PACIENTE_EXAMES_SECRETARIA_TEMPLATE)
    else:
        template = Template(PACIENTE_EXAMES_TEMPLATE)
        
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

            # ▼▼▼ ÍCONE SVG CORRIGIDO ADICIONADO AQUI ▼▼▼
            icon_svg = """
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
            </svg>
            """

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
                            {icon_svg}
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
        
    # ▼▼▼ INÍCIO DA ALTERAÇÃO ▼▼▼
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
    # ▲▲▲ FIM DA ALTERAÇÃO ▲▲▲

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
        'user': user # Adiciona o usuário ao contexto
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

# NO ARQUIVO: frontend.py

# ▼▼▼ SUBSTITUA A FUNÇÃO 'faturamento_view' INTEIRA PELA VERSÃO COMPLETA ABAIXO ▼▼▼
def faturamento_view(request):
    """Página de Gestão Financeira com dashboard e listas."""
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
    data_inicial_str = params.get('data_inicial')
    data_final_str = params.get('data_final')

    if not data_inicial_str and not data_final_str:
        # Se nenhum filtro de data for aplicado, padrão para o mês atual
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        # Calcula o último dia do mês
        proximo_mes = primeiro_dia_mes.replace(month=primeiro_dia_mes.month % 12 + 1, day=1)
        if primeiro_dia_mes.month == 12:
            proximo_mes = primeiro_dia_mes.replace(year=primeiro_dia_mes.year + 1, month=1)
        ultimo_dia_mes = proximo_mes - timedelta(days=1)
        
        params['data_inicial'] = primeiro_dia_mes.isoformat()
        params['data_final'] = ultimo_dia_mes.isoformat()
        filtro_ativo = 'mes'

    elif data_inicial_str and data_final_str:
        try:
            hoje = date.today()
            d_ini = datetime.strptime(data_inicial_str, '%Y-%m-%d').date()
            d_fim = datetime.strptime(data_final_str, '%Y-%m-%d').date()

            if d_ini == hoje and d_fim == hoje:
                filtro_ativo = 'hoje'
            elif d_ini.weekday() == 0 and (d_fim - d_ini).days == 6:
                filtro_ativo = 'semana'
            elif d_ini.day == 1 and (d_fim + timedelta(days=1)).day == 1 and d_ini.month == d_fim.month:
                filtro_ativo = 'mes'
            elif d_ini.day == 1 and d_ini.month == 1 and d_fim.day == 31 and d_fim.month == 12:
                filtro_ativo = 'ano'
        except (ValueError, TypeError):
            pass

    try:
        dash_response = requests.get(f'{Config.BACKEND_URL}/api/faturamento/dashboard/', headers={'Authorization': f'Bearer {token}'}, params=params)
        if dash_response.status_code == 200:
            dashboard_data_raw = dash_response.json()
            dashboard_data = {
                'receitas': {
                    'recebidas': format_currency_brl(dashboard_data_raw.get('receitas', {}).get('recebidas')),
                    'a_receber': format_currency_brl(dashboard_data_raw.get('receitas', {}).get('a_receber')),
                    'vencidas': format_currency_brl(dashboard_data_raw.get('receitas', {}).get('vencidas')),
                },
                'despesas': {
                    'pagas': format_currency_brl(dashboard_data_raw.get('despesas', {}).get('pagas')),
                    'a_pagar': format_currency_brl(dashboard_data_raw.get('despesas', {}).get('a_pagar')),
                    'vencidas': format_currency_brl(dashboard_data_raw.get('despesas', {}).get('vencidas')),
                },
                'lucro_liquido': dashboard_data_raw.get('lucro_liquido', 0),
                'previsao_mensal': dashboard_data_raw.get('previsao_mensal', 0),
                'lucro_liquido_formatado': format_currency_brl(dashboard_data_raw.get('lucro_liquido', 0)),
                'previsao_mensal_formatado': format_currency_brl(dashboard_data_raw.get('previsao_mensal', 0)),
                'fechamento_caixa': [
                    {**item, 
                     'receitas_formatado': format_currency_brl(item.get('receitas')),
                     'despesas_formatado': format_currency_brl(item.get('despesas')),
                     'saldo_formatado': format_currency_brl(item.get('saldo'))
                    } for item in dashboard_data_raw.get('fechamento_caixa', [])
                ],
                'total_saldo_caixa': dashboard_data_raw.get('total_saldo_caixa', 0),
                'total_saldo_caixa_formatado': format_currency_brl(dashboard_data_raw.get('total_saldo_caixa', 0))
            }

        rec_response = requests.get(f'{Config.BACKEND_URL}/api/faturamento/receitas/', headers={'Authorization': f'Bearer {token}'}, params=params)
        if rec_response.status_code == 200: receitas = rec_response.json().get('results', rec_response.json())

        desp_response = requests.get(f'{Config.BACKEND_URL}/api/faturamento/despesas/', headers={'Authorization': f'Bearer {token}'}, params=params)
        if desp_response.status_code == 200: despesas = desp_response.json().get('results', desp_response.json())
        
        pendentes_response = requests.get(f'{Config.BACKEND_URL}/api/faturamento/receitas/agendamentos_pendentes/', headers={'Authorization': f'Bearer {token}'})
        if pendentes_response.status_code == 200:
            agendamentos_pendentes = pendentes_response.json().get('agendamentos', [])

    except requests.RequestException as e:
        messages.error(request, f"Erro de comunicação: {e}")

    icon_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
    </svg>
    """

    receitas_html = []
    for r in receitas:
        try: data_vencimento = datetime.strptime(r['data_vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except: data_vencimento = r['data_vencimento']
        
        status_options = f"""
            <option value="a_receber" {'selected' if r['status'] == 'a_receber' else ''}>A Receber</option>
            <option value="recebida" {'selected' if r['status'] == 'recebida' else ''}>Recebida</option>
            <option value="vencida" {'selected' if r['status'] == 'vencida' else ''}>Vencida</option>
        """
        status_html = f'<select class="status-select status-{r["status"]}" onchange="updateLancamentoStatus(\'receita\', {r["id"]}, this)">{status_options}</select>'
        forma_pagamento = r.get('forma_pagamento') or '---'

        receitas_html.append(f"""
        <tr>
            <td class="truncate-text">{r['descricao']}</td>
            <td class="text-success">R$ {format_currency_brl(r['valor'])}</td>
            <td class="truncate-text">{r.get('categoria_nome', 'N/A')}</td>
            <td class="truncate-text">{data_vencimento}</td>
            <td class="truncate-text">{forma_pagamento}</td>
            <td>{status_html}</td>
            <td>
                <div class="actions-dropdown">
                    <button class="actions-btn" data-dropdown-id="dropdown-receita-{r['id']}">
                        {icon_svg}
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
        
        status_options = f"""
            <option value="a_pagar" {'selected' if d['status'] == 'a_pagar' else ''}>A Pagar</option>
            <option value="paga" {'selected' if d['status'] == 'paga' else ''}>Paga</option>
            <option value="vencida" {'selected' if d['status'] == 'vencida' else ''}>Vencida</option>
        """
        status_html = f'<select class="status-select status-{d["status"]}" onchange="updateLancamentoStatus(\'despesa\', {d["id"]}, this)">{status_options}</select>'
        forma_pagamento = d.get('forma_pagamento') or '---'

        despesas_html.append(f"""
        <tr>
            <td class="truncate-text">{d['descricao']}</td>
            <td class="text-danger">R$ {format_currency_brl(d['valor'])}</td>
            <td class="truncate-text">{d.get('categoria_nome', 'N/A')}</td>
            <td class="truncate-text">{data_vencimento}</td>
            <td class="truncate-text">{forma_pagamento}</td>
            <td>{status_html}</td>
            <td>
                <div class="actions-dropdown">
                    <button class="actions-btn" data-dropdown-id="dropdown-despesa-{d['id']}">
                        {icon_svg}
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
        'token': token,
        'backend_url': Config.BACKEND_URL
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
    
    if user.get('funcao') == 'medico':
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    # --- Lógica de Filtro para Auditoria Financeira ---
    from datetime import datetime
    current_year = datetime.now().year
    try:
        selected_mes = int(request.GET.get('mes', datetime.now().month))
        selected_ano = int(request.GET.get('ano', current_year))
    except (ValueError, TypeError):
        selected_mes = datetime.now().month
        selected_ano = current_year

    context = {
        'user': user,
        'data': {},
        'total_inativos': 0,
        'error_message': None,
        'log_exames': [],
        'log_documentos': [],
        'log_financeiro': [], # Novo contexto para o log financeiro
        'anos_disponiveis': range(current_year, current_year - 5, -1),
        'meses_disponiveis': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'selected_mes': selected_mes,
        'selected_ano': selected_ano,
    }

    try:
        # Requisição principal para dados consolidados
        response_dados = requests.get(f'{Config.BACKEND_URL}/api/dados-clinica/', headers={'Authorization': f'Bearer {token}'}, timeout=15)
        response_dados.raise_for_status()
        context['data'] = response_dados.json()

        # Requisição para total de inativos
        response_inativos = requests.get(f'{Config.BACKEND_URL}/api/pacientes/inativos/', headers={'Authorization': f'Bearer {token}'}, timeout=10)
        if response_inativos.status_code == 200:
            context['total_inativos'] = len(response_inativos.json())

        # Requisição para o histórico de auditoria de exames/documentos
        response_auditoria = requests.get(f'{Config.BACKEND_URL}/api/auditoria/recente/', headers={'Authorization': f'Bearer {token}'}, timeout=15)
        if response_auditoria.status_code == 200:
            todos_eventos = response_auditoria.json()
            context['log_exames'] = [e for e in todos_eventos if 'Exame' in e['tipo_evento']]
            context['log_documentos'] = [e for e in todos_eventos if 'Documento' in e['tipo_evento']]
        
        # --- NOVA REQUISIÇÃO PARA AUDITORIA FINANCEIRA ---
        params_financeiro = {'mes': selected_mes, 'ano': selected_ano}
        response_financeiro = requests.get(
            f'{Config.BACKEND_URL}/api/auditoria/financeira/',
            headers={'Authorization': f'Bearer {token}'},
            params=params_financeiro,
            timeout=15
        )
        if response_financeiro.status_code == 200:
            context['log_financeiro'] = response_financeiro.json()

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

    # VERIFICA A PERMISSÃO ANTES DE RENDERIZAR QUALQUER PÁGINA
    if user.get('funcao') == 'secretaria':
        from django.template import Template, RequestContext
        template = Template(EXAMES_ACCESS_DENIED_TEMPLATE)
        context = RequestContext(request, {
            'user': user,
            'error_message': f"Seu perfil de '{user.get('funcao_display')}' não tem permissão para acessar o módulo de Análise de Exames por iA."
        })
        return HttpResponse(template.render(context))

    # Se a permissão for válida, continua com o fluxo normal
    from django.template import Template, RequestContext
    template = Template(EXAMES_IA_TERMOS_TEMPLATE)
    context = RequestContext(request, {'user': user})
    return HttpResponse(template.render(context))

def exame_visualizar_view(request, exame_id):
    """Página para visualizar e editar o laudo de um exame específico."""
    token = request.session.get('token')
    if not token:
        return redirect('login')

    user = request.session.get('user', {})
    funcoes_pt = {'super_admin': 'Super Administrador', 'admin': 'Administrador', 'medico': 'Médico', 'secretaria': 'Secretária'}
    user['funcao_display'] = funcoes_pt.get(user.get('funcao', ''), user.get('funcao', ''))
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"

    # Captura o paciente_id da URL para saber para onde voltar
    paciente_id_origem = request.GET.get('paciente_id')

    context = {
        'user': user, 
        'error_message': None, 
        'exame': {},
        'paciente_id_origem': paciente_id_origem  # Passa o ID para o template
    }
    api_url = f'{Config.BACKEND_URL}/api/exames/{exame_id}/'

    if request.method == 'POST':
        # Esta lógica é inacessível para secretária, pois o formulário não é renderizado
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
            # Mantém o paciente_id na URL ao redirecionar
            redirect_url = f'/exames/{exame_id}/visualizar/'
            if paciente_id_origem:
                redirect_url += f'?paciente_id={paciente_id_origem}'
            return redirect(redirect_url)
        except Exception as e:
            messages.error(request, f"Erro ao salvar o laudo: {e}")
            return redirect('exame_visualizar', exame_id=exame_id)

    # Lógica GET
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
    from datetime import date

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
    if user.get('funcao') == 'medico' and not user.get('nome_completo', '').startswith('Dr.'):
        user['nome_completo'] = f"Dr. {user.get('nome_completo', '')}"
    
    if tipo_lancamento == 'receita':
        form_title = "Nova Receita"
        api_base_url = f'{Config.BACKEND_URL}/api/faturamento/receitas/'
        api_categorias_url = f'{Config.BACKEND_URL}/api/faturamento/categorias/receitas/'
    else:
        form_title = "Nova Despesa"
        api_base_url = f'{Config.BACKEND_URL}/api/faturamento/despesas/'
        api_categorias_url = f'{Config.BACKEND_URL}/api/faturamento/categorias/despesas/'

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
            'status': request.POST.get('status'),
            'clinica_id': user.get('clinica_id'),
            # --- INÍCIO DA CORREÇÃO ---
            'forma_pagamento': request.POST.get('forma_pagamento') or None
            # --- FIM DA CORREÇÃO ---
        }
        
        if payload['status'] == 'recebida':
            payload['data_recebimento'] = request.POST.get('data_recebimento') or date.today().isoformat()
        elif payload['status'] == 'paga':
            payload['data_pagamento'] = request.POST.get('data_pagamento') or date.today().isoformat()
        # --- INÍCIO DA CORREÇÃO ---
        else:
            # Se o status não for 'paga' ou 'recebida', garante que a forma de pagamento seja nula
            payload['forma_pagamento'] = None
        # --- FIM DA CORREÇÃO ---

        try:
            response = http_method(api_url, headers={'Authorization': f'Bearer {token}'}, json=payload)
            response.raise_for_status()
            messages.success(request, f"{tipo_lancamento.capitalize()} salva com sucesso!")
            return redirect('faturamento')
        except requests.exceptions.HTTPError as e:
            try:
                error_details = e.response.json()
                error_message = "; ".join([f"{k}: {v[0] if isinstance(v, list) else v}" for k, v in error_details.items()])
                messages.error(request, f"Erro de validação: {error_message}")
            except:
                 messages.error(request, f"Erro ao salvar: {e.response.text}")
        except Exception as e:
            messages.error(request, f"Erro ao salvar: {e}")

    from django.template import Template, RequestContext
    template = Template(LANCAMENTO_FORM_TEMPLATE)
    context = RequestContext(request, {
        'form_title': form_title,
        'tipo_lancamento': tipo_lancamento,
        'lancamento': lancamento_data,
        'categorias': categorias,
        'user': user,
        'messages': messages.get_messages(request)
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

    # --- INÍCIO DA CORREÇÃO ---
    # Verifica a permissão ANTES de fazer a chamada à API
    if user.get('funcao') == 'secretaria':
        context = {
            'user': user,
            'is_permission_error': True,
            'error_message': f"Seu perfil de '{user.get('funcao_display')}' não tem permissão para acessar o módulo de Consultas."
        }
        from django.template import Template, RequestContext
        template = Template(CONSULTAS_TEMPLATE)
        ctx = RequestContext(request, context)
        return HttpResponse(template.render(ctx))
    # --- FIM DA CORREÇÃO ---

    context = { 'user': user, 'data': {}, 'error_message': None, 'is_permission_error': False }

    try:
        response = requests.get(
            f'{Config.BACKEND_URL}/api/consultas/fila-hoje/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        response.raise_for_status()
        context['data'] = response.json()
        
        if context['data'].get('data'):
            try:
                data_obj = datetime.strptime(context['data']['data'], '%Y-%m-%d')
                context['data']['data'] = data_obj.strftime('%d/%m/%Y')
            except ValueError:
                pass

    except requests.exceptions.RequestException as e:
        # A verificação de permissão agora acontece antes, então este erro será majoritariamente para problemas de conexão.
        context['error_message'] = f"Erro de conexão ao carregar a fila de atendimento: {e}"

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
        'documentos_salvos': [], # Novo contexto para os documentos
        'error_message': None,
        'token': token,
        'BACKEND_URL': Config.BACKEND_URL
    }

    try:
        # 1. Busca os dados principais da consulta
        response_consulta = requests.get(
            f'{Config.BACKEND_URL}/api/consultas/{consulta_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        response_consulta.raise_for_status()
        context['consulta'] = response_consulta.json()

        # 2. Busca a lista de documentos já salvos
        response_docs = requests.get(
            f'{Config.BACKEND_URL}/api/consultas/{consulta_id}/documentos/',
            headers={'Authorization': f'Bearer {token}'}
        )
        response_docs.raise_for_status()
        context['documentos_salvos'] = response_docs.json().get('documentos', [])
        
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