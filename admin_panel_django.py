"""
Admin Panel Django - IntelliMed
Interface Web para Administração de Clínicas e Usuários
Consome API do main.py (porta 8000)
"""

import os
import sys
import requests
from pathlib import Path

# Django imports
import django
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import path
from django.template import Template, Context

# ============================================
# CONFIGURAÇÃO DO DJANGO
# ============================================

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='admin-panel-secret-key',
        ALLOWED_HOSTS=['*'],
        ROOT_URLCONF=__name__,
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
        ],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': False,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.request',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'admin_panel.db',
            }
        },
        SESSION_ENGINE='django.contrib.sessions.backends.db',
        STATIC_URL='/static/',
        USE_TZ=True,
        TIME_ZONE='America/Sao_Paulo',
    )
    
    django.setup()

# ============================================
# CONFIGURAÇÃO DA API
# ============================================

API_BASE_URL = "http://127.0.0.1:8000"

# ============================================
# HELPER FUNCTIONS
# ============================================

def api_request(method, endpoint, token, data=None):
    """
    Fazer requisição para a API do backend Django
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        return response
    except Exception as e:
        print(f"[API REQUEST ERROR] {method} {endpoint} - Erro: {str(e)}")  # ← ADICIONE
        return None
    
def render_template(request, template_name, context=None):
    """
    Renderizar template HTML
    
    Args:
        request: objeto request do Django
        template_name: nome do template (ex: 'login.html')
        context: dicionário com variáveis do template
    
    Returns:
        HttpResponse com HTML renderizado
    """
    template = Template(TEMPLATES[template_name])
    ctx = Context(context or {})
    return HttpResponse(template.render(ctx))

# ============================================
# VIEWS - AUTENTICAÇÃO
# ============================================

def login_view(request):
    """
    View de login - GET exibe formulário, POST processa login
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/login",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_info = data['user_info']
                
                # Verificar se é super admin
                if user_info['funcao'] == 'super_admin':
                    # Salvar token e info na sessão
                    request.session['token'] = data['access_token']
                    request.session['user_info'] = user_info
                    return redirect('dashboard')
                else:
                    error = "Acesso negado. Apenas Super Admin pode acessar."
            else:
                error = "Email ou senha incorretos"
        except Exception as e:
            error = f"Erro de conexão com o servidor: {str(e)}"
        
        return render_template(request, 'login.html', {'error': error})
    
    # GET - exibir formulário
    return render_template(request, 'login.html')


def logout_view(request):
    """
    View de logout - limpa sessão e redireciona para login
    """
    request.session.flush()
    return redirect('login')

# ============================================
# VIEWS - DASHBOARD
# ============================================

def dashboard_view(request):
    """
    Dashboard principal com listagem de clínicas e usuários agrupados por clínica.
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    # Buscar clínicas
    clinicas_response = api_request('GET', '/api/clinicas/', token)
    clinicas = clinicas_response.json() if clinicas_response and clinicas_response.status_code == 200 else []
    
    # Buscar usuários
    usuarios_response = api_request('GET', '/api/usuarios/', token)
    usuarios = usuarios_response.json() if usuarios_response and usuarios_response.status_code == 200 else []

    # ▼▼▼ INÍCIO DA LÓGICA DE AGRUPAMENTO ▼▼▼
    # Cria um dicionário para acesso rápido às clínicas por ID
    clinicas_map = {c['id']: c for c in clinicas}

    # Inicializa uma lista vazia de usuários para cada clínica
    for clinica in clinicas:
        clinica['usuarios_da_clinica'] = []

    # Agrupa os usuários dentro de suas respectivas clínicas
    for usuario in usuarios:
        clinica_id = usuario.get('clinica')
        if clinica_id and clinica_id in clinicas_map:
            clinicas_map[clinica_id]['usuarios_da_clinica'].append(usuario)
    # ▲▲▲ FIM DA LÓGICA DE AGRUPAMENTO ▲▲▲
    
    # Calcular estatísticas
    context = {
        'clinicas': clinicas,
        'usuarios': usuarios, # Mantém a lista original para contagem total
        'total_clinicas': len(clinicas),
        'clinicas_ativas': len([c for c in clinicas if c.get('status') == 'ativo']),
        'total_usuarios': len(usuarios),
        'usuarios_ativos': len([u for u in usuarios if u.get('status') == 'ativo']),
    }
    
    return render_template(request, 'dashboard.html', context)

# ============================================
# VIEWS - CLÍNICAS
# ============================================

def clinica_create_view(request):
    """
    View para criar nova clínica - GET exibe formulário, POST cria
    """
    token = request.session.get('token') 
    if not token:
        return redirect('login')
    
    if request.method == 'POST':
        data = {
            'nome': request.POST.get('nome'),
            'cnpj': request.POST.get('cnpj'),
            'telefone': request.POST.get('telefone'),
            'email': request.POST.get('email'),
            'logradouro': request.POST.get('logradouro'),
            'numero': request.POST.get('numero'),
            'bairro': request.POST.get('bairro'),
            'cidade': request.POST.get('cidade'),
            'estado': request.POST.get('estado'),
            'cep': request.POST.get('cep'),
            'responsavel_nome': request.POST.get('responsavel_nome'),
            'responsavel_cpf': request.POST.get('responsavel_cpf'),
            'responsavel_telefone': request.POST.get('responsavel_telefone'),
            'responsavel_email': request.POST.get('responsavel_email'),
        }
        
        response = api_request('POST', '/api/clinicas/', token, data)
        
        if response and response.status_code == 201:
            return redirect('dashboard')
        else:
            error = "Erro ao cadastrar clínica. Verifique os dados."
            return render_template(request, 'clinica_form.html', {'error': error})
    
    # GET - exibir formulário
    return render_template(request, 'clinica_form.html')


def clinica_delete_view(request, clinica_id):
    """
    View para excluir clínica
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    api_request('DELETE', f'/api/clinicas/{clinica_id}/', token)
    return redirect('dashboard')


def clinica_toggle_status_view(request, clinica_id, status):
    """
    View para alterar status da clínica (ativo/inativo/suspensa)
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    # Buscar clínica atual
    response = api_request('GET', f'/api/clinicas/{clinica_id}/', token)
    
    if response and response.status_code == 200:
        clinica = response.json()
        clinica['status'] = status
        
        # Atualizar
        api_request('PUT', f'/api/clinicas/{clinica_id}/', token, clinica)
    
    return redirect('dashboard')

# ============================================
# VIEWS - USUÁRIOS
# ============================================

def usuario_create_view(request):
    """
    View para criar novo usuário - GET exibe formulário, POST cria
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    # Buscar clínicas para o dropdown
    clinicas_response = api_request('GET', '/api/clinicas/', token)
    clinicas = clinicas_response.json() if clinicas_response and clinicas_response.status_code == 200 else []
    
    if request.method == 'POST':
        data = {
            'clinica': int(request.POST.get('clinica')),
            'nome_completo': request.POST.get('nome_completo'),
            'email': request.POST.get('email'),
            'cpf': request.POST.get('cpf'),
            'password': request.POST.get('password'),
            'data_nascimento': request.POST.get('data_nascimento'),
            'telefone_celular': request.POST.get('telefone_celular'),
            'funcao': request.POST.get('funcao'),
        }
    
        # Campos específicos para médicos
        if data['funcao'] == 'medico':
            data['crm'] = request.POST.get('crm')
            data['especialidade'] = request.POST.get('especialidade')
    
    
        response = api_request('POST', '/register', token, data)  

        if response and response.status_code == 201:
            return redirect('dashboard')
        else:
            error = "Erro ao cadastrar usuário. Verifique os dados."
            return render_template(request, 'usuario_form.html', {'clinicas': clinicas, 'error': error})
    
    # GET - exibir formulário
    return render_template(request, 'usuario_form.html', {'clinicas': clinicas})


def usuario_delete_view(request, usuario_id):
    """
    View para excluir usuário
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    api_request('DELETE', f'/api/usuarios/{usuario_id}/', token)
    return redirect('dashboard')


def usuario_toggle_status_view(request, usuario_id, status):
    """
    View para alterar status do usuário (ativo/inativo/alerta)
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    # Usar o endpoint correto: /api/usuarios/{id}/alterar-status/
    data = {'status': status}
    api_request('POST', f'/api/usuarios/{usuario_id}/alterar-status/', token, data)
    
    return redirect('dashboard')

# ============================================
# VIEWS - EDIÇÃO DE CLÍNICAS
# ============================================

def clinica_edit_view(request, clinica_id):
    """
    View para editar clínica existente
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    # Buscar clínica atual
    response = api_request('GET', f'/api/clinicas/{clinica_id}/', token)
    
    if not response or response.status_code != 200:
        return redirect('dashboard')
    
    clinica = response.json()
    
    if request.method == 'POST':
        data = {
            'nome': request.POST.get('nome'),
            'cnpj': request.POST.get('cnpj'),
            'telefone': request.POST.get('telefone'),
            'email': request.POST.get('email'),
            'logradouro': request.POST.get('logradouro'),
            'numero': request.POST.get('numero'),
            'bairro': request.POST.get('bairro'),
            'cidade': request.POST.get('cidade'),
            'estado': request.POST.get('estado'),
            'cep': request.POST.get('cep'),
            'responsavel_nome': request.POST.get('responsavel_nome'),
            'responsavel_cpf': request.POST.get('responsavel_cpf'),
            'responsavel_telefone': request.POST.get('responsavel_telefone'),
            'responsavel_email': request.POST.get('responsavel_email'),
            'status': clinica['status'],  # Manter status atual
        }
        
        response = api_request('PUT', f'/api/clinicas/{clinica_id}/', token, data)
        
        if response and response.status_code == 200:
            return redirect('dashboard')
        else:
            error = "Erro ao atualizar clínica. Verifique os dados."
            return render_template(request, 'clinica_edit_form.html', {'clinica': clinica, 'error': error})
    
    return render_template(request, 'clinica_edit_form.html', {'clinica': clinica})


# ============================================
# VIEWS - EDIÇÃO DE USUÁRIOS
# ============================================

def usuario_edit_view(request, usuario_id):
    """
    View para editar usuário existente
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    # Buscar clínicas para o dropdown
    clinicas_response = api_request('GET', '/api/clinicas/', token)
    clinicas = clinicas_response.json() if clinicas_response and clinicas_response.status_code == 200 else []
    
    # Buscar usuário atual
    response = api_request('GET', f'/api/usuarios/{usuario_id}/', token)
    
    if not response or response.status_code != 200:
        return redirect('dashboard')
    
    usuario = response.json()
    
    if request.method == 'POST':
        data = {
            'clinica': int(request.POST.get('clinica')),
            'nome_completo': request.POST.get('nome_completo'),
            'email': request.POST.get('email'),
            'cpf': usuario['cpf'],
            'data_nascimento': request.POST.get('data_nascimento'),
            'telefone_celular': request.POST.get('telefone_celular'),
            'funcao': request.POST.get('funcao'),
            'status': usuario['status'],
        }
        
        # Senha é opcional na edição
        password = request.POST.get('password')
        if password:
            data['password'] = password
        
        # Campos específicos para médicos
        if data['funcao'] == 'medico':
            data['crm'] = request.POST.get('crm')
            data['especialidade'] = request.POST.get('especialidade')
        
        response = api_request('PUT', f'/api/usuarios/{usuario_id}/', token, data)
        
        if response and response.status_code == 200:
            return redirect('dashboard')
        else:
            error_msg = "Erro ao atualizar usuário."
            if response:
                try:
                    error_data = response.json()
                    error_msg = f"Erro: {error_data}"
                except:
                    pass
            
            return render_template(request, 'usuario_edit_form.html', {
                'clinicas': clinicas,
                'usuario': usuario,
                'error': error_msg
            })
    
    # GET - exibir formulário (ESTA LINHA ESTAVA FALTANDO)
    return render_template(request, 'usuario_edit_form.html', {
        'clinicas': clinicas,
        'usuario': usuario
    })

# ============================================
# VIEWS - VISUALIZAÇÃO DE CLÍNICAS
# ============================================

def clinica_view(request, clinica_id):
    """
    View para visualizar detalhes da clínica
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    response = api_request('GET', f'/api/clinicas/{clinica_id}/', token)
    
    if not response or response.status_code != 200:
        return redirect('dashboard')
    
    clinica = response.json()
    
    # Buscar usuários da clínica
    usuarios_response = api_request('GET', '/api/usuarios/', token)
    todos_usuarios = usuarios_response.json() if usuarios_response and usuarios_response.status_code == 200 else []
    usuarios_clinica = [u for u in todos_usuarios if u.get('clinica') == clinica_id]
    
    return render_template(request, 'clinica_view.html', {
        'clinica': clinica,
        'usuarios': usuarios_clinica
    })


# ============================================
# VIEWS - VISUALIZAÇÃO DE USUÁRIOS
# ============================================

def usuario_view(request, usuario_id):
    """
    View para visualizar detalhes do usuário
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')
    
    response = api_request('GET', f'/api/usuarios/{usuario_id}/', token)
    
    if not response or response.status_code != 200:
        return redirect('dashboard')
    
    usuario = response.json()
    
    return render_template(request, 'usuario_view.html', {'usuario': usuario})

# ============================================
# TEMPLATES HTML
# ============================================

TEMPLATES = {}

TEMPLATES['login.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>IntelliMed - Login Admin</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 400px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #666;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background: #5568d3;
        }
        .error {
            background: #fee;
            color: #c00;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            border: 1px solid #fcc;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>IntelliMed Admin</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <div class="form-group">
                <label>Email:</label>
                <input type="email" name="email" value="superadmin@intellimed.com" required>
            </div>
            <div class="form-group">
                <label>Senha:</label>
                <input type="password" name="password" value="superadmin123" required>
            </div>
            <button type="submit">Entrar</button>
        </form>
    </div>
</body>
</html>
"""

TEMPLATES['dashboard.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>IntelliMed - Dashboard</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
        }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            font-size: 24px;
        }
        .header a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            border-radius: 5px;
            margin-left: 10px;
        }
        .header a:hover {
            background: rgba(255,255,255,0.3);
        }
        .container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .stat-card .number {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .section h2 {
            color: #333;
        }
        .btn {
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            display: inline-block;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
            padding: 5px 10px;
            font-size: 12px;
        }
        .btn-success {
            background: #28a745;
            color: white;
            padding: 5px 10px;
            font-size: 12px;
        }
        .btn-warning {
            background: #ffc107;
            color: black;
            padding: 5px 10px;
            font-size: 12px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f9f9f9;
            font-weight: bold;
            color: #666;
        }
        .badge {
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .actions {
            display: flex;
            gap: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>IntelliMed - Dashboard Admin</h1>
        <div>
            <a href="/logout/">Sair</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h3>TOTAL DE CLINICAS</h3>
                <div class="number">{{ total_clinicas }}</div>
            </div>
            <div class="stat-card">
                <h3>CLINICAS ATIVAS</h3>
                <div class="number">{{ clinicas_ativas }}</div>
            </div>
            <div class="stat-card">
                <h3>TOTAL DE USUARIOS</h3>
                <div class="number">{{ total_usuarios }}</div>
            </div>
            <div class="stat-card">
                <h3>USUARIOS ATIVOS</h3>
                <div class="number">{{ usuarios_ativos }}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>Clinicas Cadastradas</h2>
                <a href="/clinicas/criar/" class="btn btn-primary">Nova Clinica</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nome</th>
                        <th>CNPJ</th>
                        <th>Cidade/UF</th>
                        <th>Status</th>
                        <th>Usuarios</th>
                        <th>Acoes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for clinica in clinicas %}
                    <tr>
                        <td>{{ clinica.id }}</td>
                        <td>{{ clinica.nome }}</td>
                        <td>{{ clinica.cnpj }}</td>
                        <td>{{ clinica.cidade }}/{{ clinica.estado }}</td>
                        <td>
                            {% if clinica.status == 'ativo' %}
                                <span class="badge badge-success">ATIVO</span>
                            {% elif clinica.status == 'inativo' %}
                                <span class="badge badge-danger">INATIVO</span>
                            {% else %}
                                <span class="badge badge-warning">SUSPENSO</span>
                            {% endif %}
                        </td>
                        <td>{{ clinica.total_usuarios|default:0 }}</td>
                        <td>
                            <div class="actions">
                                <a href="/clinicas/{{ clinica.id }}/" class="btn btn-success">Ver</a>
                                <a href="/clinicas/{{ clinica.id }}/editar/" class="btn btn-success">Editar</a>
                                <a href="/clinicas/{{ clinica.id }}/status/ativo/" class="btn btn-success">Ativar</a>
                                <a href="/clinicas/{{ clinica.id }}/status/inativo/" class="btn btn-warning">Inativar</a>
                                <a href="/clinicas/{{ clinica.id }}/delete/" class="btn btn-danger" onclick="return confirm('Confirma exclusao?')">Excluir</a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- ▼▼▼ INÍCIO DA SEÇÃO DE USUÁRIOS MODIFICADA ▼▼▼ -->
        <div class="section">
            <div class="section-header">
                <h2>Usuarios Cadastrados</h2>
                <a href="/usuarios/criar/" class="btn btn-primary">Novo Usuario</a>
            </div>
        </div>

        {% for clinica in clinicas %}
        <div class="section" style="margin-top: -10px;"> <!-- Margin-top ajustado para melhor espaçamento -->
            <div class="section-header">
                <h3>Clínica: {{ clinica.nome }}</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Funcao</th>
                        <th>Status</th>
                        <th>Acoes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for usuario in clinica.usuarios_da_clinica %}
                    <tr>
                        <td>{{ usuario.id }}</td>
                        <td>{{ usuario.nome_completo }}</td>
                        <td>{{ usuario.email }}</td>
                        <td>{{ usuario.funcao }}</td>
                        <td>
                            {% if usuario.status == 'ativo' %}
                                <span class="badge badge-success">ATIVO</span>
                            {% else %}
                                <span class="badge badge-danger">INATIVO</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="actions">
                                <a href="/usuarios/{{ usuario.id }}/" class="btn btn-success">Ver</a>
                                <a href="/usuarios/{{ usuario.id }}/editar/" class="btn btn-success">Editar</a>
                                <a href="/usuarios/{{ usuario.id }}/status/ativo/" class="btn btn-success">Ativar</a>
                                <a href="/usuarios/{{ usuario.id }}/status/inativo/" class="btn btn-warning">Inativar</a>
                                <a href="/usuarios/{{ usuario.id }}/delete/" class="btn btn-danger" onclick="return confirm('Confirma exclusao?')">Excluir</a>
                            </div>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="6" style="text-align: center;">Nenhum usuário cadastrado nesta clínica.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
        <!-- ▲▲▲ FIM DA SEÇÃO DE USUÁRIOS MODIFICADA ▲▲▲ -->

    </div>
</body>
</html>
"""

TEMPLATES['clinica_form.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>Nova Clinica</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 800px;
            margin: 20px auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h2 { margin-bottom: 20px; color: #333; }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #666;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .btn {
            padding: 12px 24px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            border: none;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .actions {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .error {
            background: #fee;
            color: #c00;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Nova Clinica</h1>
    </div>
    <div class="container">
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <h2>Dados da Clinica</h2>
            <div class="row">
                <div class="form-group">
                    <label>Nome:</label>
                    <input type="text" name="nome" required>
                </div>
                <div class="form-group">
                    <label>CNPJ:</label>
                    <input type="text" name="cnpj" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" name="telefone" required>
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="email" required>
                </div>
            </div>
            
            <h2 style="margin-top: 30px;">Endereco</h2>
            <div class="form-group">
                <label>Logradouro:</label>
                <input type="text" name="logradouro" required>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Numero:</label>
                    <input type="text" name="numero" required>
                </div>
                <div class="form-group">
                    <label>Bairro:</label>
                    <input type="text" name="bairro" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Cidade:</label>
                    <input type="text" name="cidade" required>
                </div>
                <div class="form-group">
                    <label>UF:</label>
                    <input type="text" name="estado" maxlength="2" required>
                </div>
            </div>
            <div class="form-group">
                <label>CEP:</label>
                <input type="text" name="cep" required>
            </div>
            
            <h2 style="margin-top: 30px;">Responsavel</h2>
            <div class="row">
                <div class="form-group">
                    <label>Nome:</label>
                    <input type="text" name="responsavel_nome" required>
                </div>
                <div class="form-group">
                    <label>CPF:</label>
                    <input type="text" name="responsavel_cpf" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" name="responsavel_telefone" required>
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="responsavel_email" required>
                </div>
            </div>
            
            <div class="actions">
                <button type="submit" class="btn btn-primary">Cadastrar</button>
                <a href="/dashboard/" class="btn btn-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

TEMPLATES['usuario_form.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>Novo Usuario</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 800px;
            margin: 20px auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h2 { margin-bottom: 20px; color: #333; }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #666;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .btn {
            padding: 12px 24px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            border: none;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .actions {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .error {
            background: #fee;
            color: #c00;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        #medico-fields {
            display: none;
        }
    </style>
    <script>
        function toggleMedicoFields() {
            var funcao = document.getElementById('funcao').value;
            var medicoFields = document.getElementById('medico-fields');
            if (funcao === 'medico') {
                medicoFields.style.display = 'block';
            } else {
                medicoFields.style.display = 'none';
            }
        }
    </script>
</head>
<body>
    <div class="header">
        <h1>Novo Usuario</h1>
    </div>
    <div class="container">
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <div class="form-group">
                <label>Clinica:</label>
                <select name="clinica" required>
                    <option value="">Selecione...</option>
                    {% for clinica in clinicas %}
                    <option value="{{ clinica.id }}">{{ clinica.nome }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <h2>Dados Pessoais</h2>
            <div class="form-group">
                <label>Nome Completo:</label>
                <input type="text" name="nome_completo" required>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="email" required>
                </div>
                <div class="form-group">
                    <label>CPF:</label>
                    <input type="text" name="cpf" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Senha:</label>
                    <input type="password" name="password" required>
                </div>
                <div class="form-group">
                    <label>Data Nascimento:</label>
                    <input type="date" name="data_nascimento" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" name="telefone_celular" required>
                </div>
                <div class="form-group">
                    <label>Funcao:</label>
                    <select name="funcao" id="funcao" onchange="toggleMedicoFields()" required>
                        <option value="">Selecione...</option>
                        <option value="admin">Administrador</option>
                        <option value="medico">Medico</option>
                        <option value="secretaria">Secretaria</option>
                    </select>
                </div>
            </div>
            
            <div id="medico-fields">
                <h2>Dados do Medico</h2>
                <div class="row">
                    <div class="form-group">
                        <label>CRM:</label>
                        <input type="text" name="crm">
                    </div>
                    <div class="form-group">
                        <label>Especialidade:</label>
                        <input type="text" name="especialidade">
                    </div>
                </div>
            </div>
            
            <div class="actions">
                <button type="submit" class="btn btn-primary">Cadastrar</button>
                <a href="/dashboard/" class="btn btn-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

TEMPLATES['clinica_edit_form.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>Editar Clinica</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 800px;
            margin: 20px auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h2 { margin-bottom: 20px; color: #333; }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #666;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .btn {
            padding: 12px 24px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            border: none;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .actions {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .error {
            background: #fee;
            color: #c00;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Editar Clinica</h1>
    </div>
    <div class="container">
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <h2>Dados da Clinica</h2>
            <div class="row">
                <div class="form-group">
                    <label>Nome:</label>
                    <input type="text" name="nome" value="{{ clinica.nome }}" required>
                </div>
                <div class="form-group">
                    <label>CNPJ:</label>
                    <input type="text" name="cnpj" value="{{ clinica.cnpj }}" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" name="telefone" value="{{ clinica.telefone }}" required>
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="email" value="{{ clinica.email }}" required>
                </div>
            </div>
            
            <h2 style="margin-top: 30px;">Endereco</h2>
            <div class="form-group">
                <label>Logradouro:</label>
                <input type="text" name="logradouro" value="{{ clinica.logradouro }}" required>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Numero:</label>
                    <input type="text" name="numero" value="{{ clinica.numero }}" required>
                </div>
                <div class="form-group">
                    <label>Bairro:</label>
                    <input type="text" name="bairro" value="{{ clinica.bairro }}" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Cidade:</label>
                    <input type="text" name="cidade" value="{{ clinica.cidade }}" required>
                </div>
                <div class="form-group">
                    <label>UF:</label>
                    <input type="text" name="estado" value="{{ clinica.estado }}" maxlength="2" required>
                </div>
            </div>
            <div class="form-group">
                <label>CEP:</label>
                <input type="text" name="cep" value="{{ clinica.cep }}" required>
            </div>
            
            <h2 style="margin-top: 30px;">Responsavel</h2>
            <div class="row">
                <div class="form-group">
                    <label>Nome:</label>
                    <input type="text" name="responsavel_nome" value="{{ clinica.responsavel_nome }}" required>
                </div>
                <div class="form-group">
                    <label>CPF:</label>
                    <input type="text" name="responsavel_cpf" value="{{ clinica.responsavel_cpf }}" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" name="responsavel_telefone" value="{{ clinica.responsavel_telefone }}" required>
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="responsavel_email" value="{{ clinica.responsavel_email }}" required>
                </div>
            </div>
            
            <div class="actions">
                <button type="submit" class="btn btn-primary">Salvar Alteracoes</button>
                <a href="/dashboard/" class="btn btn-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

TEMPLATES['usuario_edit_form.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>Editar Usuario</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 800px;
            margin: 20px auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h2 { margin-bottom: 20px; color: #333; }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #666;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .btn {
            padding: 12px 24px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            border: none;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .actions {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .error {
            background: #fee;
            color: #c00;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        #medico-fields {
            display: none;
        }
        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
    </style>
    <script>
        function toggleMedicoFields() {
            var funcao = document.getElementById('funcao').value;
            var medicoFields = document.getElementById('medico-fields');
            if (funcao === 'medico') {
                medicoFields.style.display = 'block';
            } else {
                medicoFields.style.display = 'none';
            }
        }
        
        window.onload = function() {
            toggleMedicoFields();
        }
    </script>
</head>
<body>
    <div class="header">
        <h1>Editar Usuario</h1>
    </div>
    <div class="container">
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <div class="info-box">
            <strong>Nota:</strong> O CPF não pode ser alterado. Deixe o campo senha em branco para manter a senha atual.
        </div>
        
        <form method="post">
            <div class="form-group">
                <label>Clinica:</label>
                <select name="clinica" required>
                    {% for clinica in clinicas %}
                    <option value="{{ clinica.id }}" {% if clinica.id == usuario.clinica %}selected{% endif %}>
                        {{ clinica.nome }}
                    </option>
                    {% endfor %}
                </select>
            </div>
            
            <h2>Dados Pessoais</h2>
            <div class="form-group">
                <label>Nome Completo:</label>
                <input type="text" name="nome_completo" value="{{ usuario.nome_completo }}" required>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="email" value="{{ usuario.email }}" required>
                </div>
                <div class="form-group">
                    <label>CPF (não editável):</label>
                    <input type="text" value="{{ usuario.cpf }}" disabled>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Nova Senha (deixe em branco para manter):</label>
                    <input type="password" name="password" placeholder="Deixe em branco para não alterar">
                </div>
                <div class="form-group">
                    <label>Data Nascimento:</label>
                    <input type="date" name="data_nascimento" value="{{ usuario.data_nascimento }}" required>
                </div>
            </div>
            <div class="row">
                <div class="form-group">
                    <label>Telefone:</label>
                    <input type="text" name="telefone_celular" value="{{ usuario.telefone_celular }}" required>
                </div>
                <div class="form-group">
                    <label>Funcao:</label>
                    <select name="funcao" id="funcao" onchange="toggleMedicoFields()" required>
                        <option value="admin" {% if usuario.funcao == 'admin' %}selected{% endif %}>Administrador</option>
                        <option value="medico" {% if usuario.funcao == 'medico' %}selected{% endif %}>Medico</option>
                        <option value="secretaria" {% if usuario.funcao == 'secretaria' %}selected{% endif %}>Secretaria</option>
                    </select>
                </div>
            </div>
            
            <div id="medico-fields">
                <h2>Dados do Medico</h2>
                <div class="row">
                    <div class="form-group">
                        <label>CRM:</label>
                        <input type="text" name="crm" value="{{ usuario.crm }}">
                    </div>
                    <div class="form-group">
                        <label>Especialidade:</label>
                        <input type="text" name="especialidade" value="{{ usuario.especialidade }}">
                    </div>
                </div>
            </div>
            
            <div class="actions">
                <button type="submit" class="btn btn-primary">Salvar Alteracoes</button>
                <a href="/dashboard/" class="btn btn-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

TEMPLATES['clinica_view.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>Detalhes da Clinica</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 1000px;
            margin: 20px auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h2 {
            color: #333;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            margin-bottom: 10px;
        }
        .label {
            font-weight: bold;
            color: #666;
        }
        .value {
            color: #333;
        }
        .badge {
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .btn {
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            display: inline-block;
            margin-top: 20px;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f9f9f9;
            font-weight: bold;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Detalhes da Clinica</h1>
    </div>
    <div class="container">
        <h2>Informacoes Gerais</h2>
        <div class="info-grid">
            <div class="label">Nome:</div>
            <div class="value">{{ clinica.nome }}</div>
            
            <div class="label">CNPJ:</div>
            <div class="value">{{ clinica.cnpj }}</div>
            
            <div class="label">Telefone:</div>
            <div class="value">{{ clinica.telefone }}</div>
            
            <div class="label">Email:</div>
            <div class="value">{{ clinica.email }}</div>
            
            <div class="label">Status:</div>
            <div class="value">
                {% if clinica.status == 'ativo' %}
                    <span class="badge badge-success">ATIVO</span>
                {% elif clinica.status == 'inativo' %}
                    <span class="badge badge-danger">INATIVO</span>
                {% else %}
                    <span class="badge badge-warning">SUSPENSO</span>
                {% endif %}
            </div>
        </div>
        
        <h2>Endereco</h2>
        <div class="info-grid">
            <div class="label">Logradouro:</div>
            <div class="value">{{ clinica.logradouro }}, {{ clinica.numero }}</div>
            
            <div class="label">Bairro:</div>
            <div class="value">{{ clinica.bairro }}</div>
            
            <div class="label">Cidade/UF:</div>
            <div class="value">{{ clinica.cidade }}/{{ clinica.estado }}</div>
            
            <div class="label">CEP:</div>
            <div class="value">{{ clinica.cep }}</div>
        </div>
        
        <h2>Responsavel</h2>
        <div class="info-grid">
            <div class="label">Nome:</div>
            <div class="value">{{ clinica.responsavel_nome }}</div>
            
            <div class="label">CPF:</div>
            <div class="value">{{ clinica.responsavel_cpf }}</div>
            
            <div class="label">Telefone:</div>
            <div class="value">{{ clinica.responsavel_telefone }}</div>
            
            <div class="label">Email:</div>
            <div class="value">{{ clinica.responsavel_email }}</div>
        </div>
        
        <h2>Usuarios da Clinica ({{ usuarios|length }})</h2>
        {% if usuarios %}
        <table>
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>Email</th>
                    <th>Funcao</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for usuario in usuarios %}
                <tr>
                    <td>{{ usuario.nome_completo }}</td>
                    <td>{{ usuario.email }}</td>
                    <td>{{ usuario.funcao }}</td>
                    <td>
                        {% if usuario.status == 'ativo' %}
                            <span class="badge badge-success">ATIVO</span>
                        {% else %}
                            <span class="badge badge-danger">INATIVO</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>Nenhum usuario cadastrado nesta clinica.</p>
        {% endif %}
        
        <a href="/dashboard/" class="btn btn-secondary">Voltar</a>
    </div>
</body>
</html>
"""

TEMPLATES['usuario_view.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>Detalhes do Usuario</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 800px;
            margin: 20px auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h2 {
            color: #333;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            margin-bottom: 10px;
        }
        .label {
            font-weight: bold;
            color: #666;
        }
        .value {
            color: #333;
        }
        .badge {
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .btn {
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            display: inline-block;
            margin-top: 20px;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Detalhes do Usuario</h1>
    </div>
    <div class="container">
        <h2>Informacoes Pessoais</h2>
        <div class="info-grid">
            <div class="label">Nome Completo:</div>
            <div class="value">{{ usuario.nome_completo }}</div>
            
            <div class="label">Email:</div>
            <div class="value">{{ usuario.email }}</div>
            
            <div class="label">CPF:</div>
            <div class="value">{{ usuario.cpf }}</div>
            
            <div class="label">Data Nascimento:</div>
            <div class="value">{{ usuario.data_nascimento }}</div>
            
            <div class="label">Telefone:</div>
            <div class="value">{{ usuario.telefone_celular }}</div>
            
            <div class="label">Status:</div>
            <div class="value">
                {% if usuario.status == 'ativo' %}
                    <span class="badge badge-success">ATIVO</span>
                {% else %}
                    <span class="badge badge-danger">INATIVO</span>
                {% endif %}
            </div>
        </div>
        
        <h2>Dados Profissionais</h2>
        <div class="info-grid">
            <div class="label">Funcao:</div>
            <div class="value">{{ usuario.funcao }}</div>
            
            <div class="label">Clinica:</div>
            <div class="value">{{ usuario.clinica_nome|default:"N/A" }}</div>
            
            {% if usuario.funcao == 'medico' %}
            <div class="label">CRM:</div>
            <div class="value">{{ usuario.crm|default:"N/A" }}</div>
            
            <div class="label">Especialidade:</div>
            <div class="value">{{ usuario.especialidade|default:"N/A" }}</div>
            {% endif %}
        </div>
        
        <h2>Auditoria</h2>
        <div class="info-grid">
            <div class="label">Ultimo Login:</div>
            <div class="value">{{ usuario.last_login|default:"Nunca" }}</div>
            
            <div class="label">Data Cadastro:</div>
            <div class="value">{{ usuario.data_cadastro }}</div>
            
            <div class="label">Ultima Atualizacao:</div>
            <div class="value">{{ usuario.data_atualizacao }}</div>
        </div>
        
        <a href="/dashboard/" class="btn btn-secondary">Voltar</a>
    </div>
</body>
</html>
"""

# ============================================
# URLs
# ============================================

urlpatterns = [
    path('', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    
    # Clínicas
    path('clinicas/criar/', clinica_create_view, name='clinica_create'),
    path('clinicas/<int:clinica_id>/', clinica_view, name='clinica_view'),  # ← NOVO
    path('clinicas/<int:clinica_id>/editar/', clinica_edit_view, name='clinica_edit'),
    path('clinicas/<int:clinica_id>/delete/', clinica_delete_view, name='clinica_delete'),
    path('clinicas/<int:clinica_id>/status/<str:status>/', clinica_toggle_status_view, name='clinica_toggle_status'),
    
    # Usuários
    path('usuarios/criar/', usuario_create_view, name='usuario_create'),
    path('usuarios/<int:usuario_id>/', usuario_view, name='usuario_view'),  # ← NOVO
    path('usuarios/<int:usuario_id>/editar/', usuario_edit_view, name='usuario_edit'),
    path('usuarios/<int:usuario_id>/delete/', usuario_delete_view, name='usuario_delete'),
    path('usuarios/<int:usuario_id>/status/<str:status>/', usuario_toggle_status_view, name='usuario_toggle_status'),
]

# ============================================
# SERVIDOR
# ============================================

if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    
    print("="*70)
    print("INTELLIMED - ADMIN PANEL WEB")
    print("Interface de Administracao de Clinicas e Usuarios")
    print("="*70)
    print(f"\nAcesse: http://127.0.0.1:9000")
    print("\nCredenciais:")
    print("  Email: superadmin@intellimed.com")
    print("  Senha: superadmin123")
    print("\nCertifique-se que o main.py esta rodando na porta 8000!")
    print("\nPressione CTRL+C para parar\n")
    
    sys.argv = ['manage.py', 'runserver', '127.0.0.1:9000', '--noreload']
    execute_from_command_line(sys.argv)