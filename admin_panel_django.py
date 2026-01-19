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
        # ▼▼▼ NOVA CONDIÇÃO ADICIONADA AQUI ▼▼▼
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        # ▲▲▲ FIM DA NOVA CONDIÇÃO ▲▲▲
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        return response
    except Exception as e:
        print(f"[API REQUEST ERROR] {method} {endpoint} - Erro: {str(e)}")
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

# NO ARQUIVO: admin_panel_django.py
# ANTES DE: def logout_view(request):
# DEPOIS DE: # ============================================ # VIEWS - AUTENTICAÇÃO # ============================================

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
                
                # --- ALTERAÇÃO APLICADA AQUI ---
                # Verifica se 'super_admin' está na LISTA de funcoes
                if 'super_admin' in user_info.get('funcoes', []):
                # --- FIM DA ALTERAÇÃO ---
                    # Salvar token e info na sessão
                    request.session['token'] = data['access_token']
                    request.session['user_info'] = user_info
                    return redirect('dashboard')
                else:
                    error = "Acesso negado. Apenas Super Admin pode acessar."
            else:
                error = "Email ou senha incorretos"
        except KeyError as e:
            # Captura o erro específico se a chave 'funcoes' não existir na resposta
            error = f"Erro de comunicação com o servidor: chave esperada não encontrada '{e}'"
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
    
    # <<< NOVA IMPORTAÇÃO ADICIONADA AQUI >>>
    import json
    
    clinicas = []
    usuarios = []
    
    # --- BLOCO DE DEBUG ADICIONADO ---
    print("\n--- DEBUG PAINEL ADMIN: DASHBOARD_VIEW ---")
    try:
        # Buscar clínicas
        clinicas_response = api_request('GET', '/api/clinicas/', token)
        print(f"Status da Resposta de Clínicas: {clinicas_response.status_code if clinicas_response else 'N/A'}")
        if clinicas_response and clinicas_response.status_code == 200:
            clinicas = clinicas_response.json()
            print(f"Clínicas recebidas da API: {len(clinicas)} item(ns)")
        elif clinicas_response:
            print(f"Erro ao buscar clínicas: {clinicas_response.text}")

        # Buscar usuários
        usuarios_response = api_request('GET', '/api/usuarios/', token)
        print(f"Status da Resposta de Usuários: {usuarios_response.status_code if usuarios_response else 'N/A'}")
        if usuarios_response and usuarios_response.status_code == 200:
            usuarios = usuarios_response.json()
            print(f"Usuários recebidos da API: {len(usuarios)} item(ns)")
        elif usuarios_response:
            print(f"Erro ao buscar usuários: {usuarios_response.text}")
            
    except Exception as e:
        print(f"ERRO CRÍTICO na requisição da API: {e}")
    print("-------------------------------------------\n")
    # --- FIM DO BLOCO DE DEBUG ---
    
    clinicas_map = {c['id']: c for c in clinicas}
    for clinica in clinicas:
        clinica['usuarios_da_clinica'] = []

    for usuario in usuarios:
        clinica_id = usuario.get('clinica')
        if clinica_id and clinica_id in clinicas_map:
            clinicas_map[clinica_id]['usuarios_da_clinica'].append(usuario)
    
    context = {
        'clinicas': clinicas,
        'usuarios': usuarios,
        'total_clinicas': len(clinicas),
        'clinicas_ativas': len([c for c in clinicas if c.get('status') == 'ativo']),
        'total_usuarios': len(usuarios),
        'usuarios_ativos': len([u for u in usuarios if u.get('status') == 'ativo']),
        # <<< NOVA LINHA ADICIONADA AO CONTEXTO >>>
        'clinicas_json': json.dumps(clinicas),
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

def clinica_toggle_whatsapp_view(request, clinica_id):
    """
    View para ativar ou desativar o plano de WhatsApp IA de uma clínica.
    """
    token = request.session.get('token')
    if not token or request.method != 'POST':
        return redirect('dashboard')
    
    try:
        # Busca a clínica para garantir que ela existe
        response_get = api_request('GET', f'/api/clinicas/{clinica_id}/', token)
        if not response_get or response_get.status_code != 200:
            # Lidar com erro se a clínica não for encontrada
            return redirect('dashboard')

        clinica_data = response_get.json()
        
        # Inverte o status atual do plano_whatsapp_ia_ativo
        novo_status = not clinica_data.get('plano_whatsapp_ia_ativo', False)
        
        # Envia a requisição PATCH para atualizar apenas este campo
        payload = {'plano_whatsapp_ia_ativo': novo_status}
        api_request('PATCH', f'/api/clinicas/{clinica_id}/', token, data=payload)

    except Exception as e:
        print(f"Erro ao alternar status do WhatsApp: {e}")
        # Idealmente, aqui você adicionaria uma mensagem de erro para o usuário
    
    return redirect('dashboard')

def clinica_whatsapp_setup_view(request, clinica_id):
    """
    View para exibir o QR Code de conexão do WhatsApp
    """
    token = request.session.get('token')
    if not token: return redirect('login')
    
    clinica_response = api_request('GET', f'/api/clinicas/{clinica_id}/', token)
    if not clinica_response or clinica_response.status_code != 200:
        return redirect('dashboard')
    clinica_nome = clinica_response.json().get('nome')

    response = api_request('POST', f'/api/clinicas/{clinica_id}/whatsapp-setup/', token)
    
    # ADICIONADO clinica_id AQUI
    context = {'clinica_nome': clinica_nome, 'clinica_id': clinica_id, 'status': 'loading'}
    
    if response and response.status_code == 200:
        data = response.json()
        context['status'] = data.get('status')
        context['qrcode'] = data.get('qrcode')
    elif response and response.status_code == 403:
        return HttpResponse("Erro: Plano inativo.", status=403)
    
    return render_template(request, 'whatsapp_setup.html', context)

def clinica_whatsapp_reset_view(request, clinica_id):
    """View para resetar a instância do WhatsApp"""
    token = request.session.get('token')
    if not token: return redirect('login')
    
    api_request('POST', f'/api/clinicas/{clinica_id}/whatsapp-reset/', token)
    # Redireciona de volta para o setup para gerar novo QR
    return redirect('clinica_whatsapp_setup', clinica_id=clinica_id)

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
        # --- ALTERAÇÃO APLICADA AQUI ---
        # Coleta todas as funções selecionadas dos checkboxes
        funcoes_selecionadas = request.POST.getlist('funcoes')

        data = {
            'clinica': int(request.POST.get('clinica')),
            'nome_completo': request.POST.get('nome_completo'),
            'email': request.POST.get('email'),
            'cpf': request.POST.get('cpf'),
            'password': request.POST.get('password'),
            'data_nascimento': request.POST.get('data_nascimento'),
            'telefone_celular': request.POST.get('telefone_celular'),
            'funcoes': funcoes_selecionadas,  # Envia a lista de funções
        }
    
        # Campos específicos para médicos
        if 'medico' in data['funcoes']:
            data['crm'] = request.POST.get('crm')
            data['especialidade'] = request.POST.get('especialidade')
        # --- FIM DA ALTERAÇÃO ---
    
        response = api_request('POST', '/register', token, data)  

        if response and response.status_code == 201:
            return redirect('dashboard')
        else:
            error = "Erro ao cadastrar usuário. Verifique os dados."
            # Adiciona a resposta da API ao erro, se disponível, para mais detalhes
            try:
                api_error = response.json()
                error = f"Erro da API: {api_error.get('mensagem', 'Conteúdo inválido')}"
            except:
                pass
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
        # --- ALTERAÇÃO APLICADA AQUI ---
        funcoes_selecionadas = request.POST.getlist('funcoes')

        data = {
            'clinica': int(request.POST.get('clinica')),
            'nome_completo': request.POST.get('nome_completo'),
            'email': request.POST.get('email'),
            'cpf': usuario['cpf'],
            'data_nascimento': request.POST.get('data_nascimento'),
            'telefone_celular': request.POST.get('telefone_celular'),
            'funcoes': funcoes_selecionadas,
            'status': usuario['status'],
        }
        
        # Senha é opcional na edição
        password = request.POST.get('password')
        if password:
            data['password'] = password
        
        # Campos específicos para médicos
        if 'medico' in data['funcoes']:
            data['crm'] = request.POST.get('crm')
            data['especialidade'] = request.POST.get('especialidade')
        # --- FIM DA ALTERAÇÃO ---
        
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
            
            # Re-popula o usuário com os dados enviados em caso de erro para não perder as alterações
            usuario.update(data)

            return render_template(request, 'usuario_edit_form.html', {
                'clinicas': clinicas,
                'usuario': usuario,
                'error': error_msg
            })
    
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

def clinica_assinatura_view(request, clinica_id):
    """
    View para gerenciar o plano de assinatura de uma clínica.
    """
    token = request.session.get('token')
    if not token:
        return redirect('login')

    # Busca dados da clínica
    clinica_response = api_request('GET', f'/api/clinicas/{clinica_id}/', token)
    if not clinica_response or clinica_response.status_code != 200:
        return redirect('dashboard')
    clinica = clinica_response.json()

    # Busca lista de planos disponíveis
    planos_response = api_request('GET', '/api/planos/', token)
    planos = planos_response.json() if planos_response and planos_response.status_code == 200 else []

    if request.method == 'POST':
        plano_id = request.POST.get('plano_id')
        data_inicio = request.POST.get('data_inicio')
        
        payload = {
            'clinica': clinica_id,
            'plano': int(plano_id),
            'data_inicio': data_inicio,
        }
        
        # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
        # Verifica de forma segura se a assinatura já existe antes de tentar acessar o ID.
        assinatura_info = clinica.get('assinatura_info')
        assinatura_id = assinatura_info.get('id') if assinatura_info else None
        # ▲▲▲ FIM DA CORREÇÃO ▲▲▲

        if assinatura_id:
            response = api_request('PUT', f'/api/assinaturas/{assinatura_id}/', token, data=payload)
        else:
            response = api_request('POST', '/api/assinaturas/', token, data=payload)
        
        if response and response.status_code in [200, 201]:
            return redirect('dashboard')
        else:
            error = "Erro ao salvar assinatura. Verifique os dados."
            if response:
                try: error += f" Detalhe: {response.json()}"
                except: pass
            
            context = {
                'clinica': clinica,
                'planos': planos,
                'error': error,
            }
            return render_template(request, 'assinatura_form.html', context)

    context = {
        'clinica': clinica,
        'planos': planos,
    }
    return render_template(request, 'assinatura_form.html', context)

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
                <input type="email" name="email" value="" placeholder="Digite o e-mail" required>
            </div>
            <div class="form-group">
                <label>Senha:</label>
                <input type="password" name="password" value="" placeholder="Digite a senha" required>
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
    <title>IntelliMed - Dashboard Admin</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
        .header { background: #667eea; color: white; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; }
        .header a { color: white; text-decoration: none; padding: 10px 20px; background: rgba(255,255,255,0.2); border-radius: 5px; margin-left: 10px; }
        .header a:hover { background: rgba(255,255,255,0.3); }
        .container { max-width: 1600px; margin: 20px auto; padding: 20px; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-card .number { font-size: 36px; font-weight: bold; color: #667eea; }
        .section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .section h2 { color: #333; }
        .btn { padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; display: inline-block; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; }
        .btn-info { background: #17a2b8; color: white; padding: 5px 10px; font-size: 12px; }
        .btn-danger { background: #dc3545; color: white; padding: 5px 10px; font-size: 12px; }
        .btn-success { background: #28a745; color: white; padding: 5px 10px; font-size: 12px; }
        .btn-warning { background: #ffc107; color: black; padding: 5px 10px; font-size: 12px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f9f9f9; font-weight: bold; color: #666; }
        .badge { padding: 5px 10px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-info { background: #d1ecf1; color: #0c5460; }
        .actions { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
        .whatsapp-toggle { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: bold; }
        .whatsapp-toggle input { width: 18px; height: 18px; cursor: pointer; }
        .plan-badge-button { cursor: pointer; text-decoration: underline; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: #fefefe; margin: 5% auto; padding: 20px; border: 1px solid #888; width: 90%; max-width: 900px; border-radius: 8px; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 20px; }
        .modal-header h2 { margin: 0; }
        .close-btn { color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer; }
        .consumo-table { width: 100%; margin-top: 15px; }
        .consumo-table th, .consumo-table td { padding: 8px; text-align: center; }
        .consumo-table th { background-color: #f2f2f2; }
        .consumo-table .label-col { text-align: left; font-weight: bold; }
        .medicos-info { margin-top: 20px; font-size: 16px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>IntelliMed - Dashboard Admin</h1>
        <div><a href="/logout/">Sair</a></div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card"><h3>TOTAL DE CLINICAS</h3><div class="number">{{ total_clinicas }}</div></div>
            <div class="stat-card"><h3>CLINICAS ATIVAS</h3><div class="number">{{ clinicas_ativas }}</div></div>
            <div class="stat-card"><h3>TOTAL DE USUARIOS</h3><div class="number">{{ total_usuarios }}</div></div>
            <div class="stat-card"><h3>USUARIOS ATIVOS</h3><div class="number">{{ usuarios_ativos }}</div></div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>Clinicas Cadastradas</h2>
                <a href="/clinicas/criar/" class="btn btn-primary">Nova Clinica</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th><th>Nome</th><th>Plano</th><th>Consumo (Mês)</th><th>Vencimento</th><th>Status</th><th>Acoes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for clinica in clinicas %}
                    <tr>
                        <td>{{ clinica.id }}</td>
                        <td>{{ clinica.nome }}</td>
                        <td>
                            {% if clinica.assinatura_info %}
                                <a href="#" class="plan-badge-button badge badge-info" onclick="showConsumoModal({{ clinica.id }})">
                                    {{ clinica.assinatura_info.plano_nome }}
                                </a>
                            {% else %}
                                <span class="badge badge-warning">Sem Plano</span>
                            {% endif %}
                        </td>
                        <td>{{ clinica.consumo_formatado }}</td>
                        <td>{{ clinica.assinatura_info.data_fim|default:"N/A" }}</td>
                        <td>
                            {% if clinica.status == 'ativo' %}<span class="badge badge-success">ATIVO</span>
                            {% elif clinica.status == 'inativo' %}<span class="badge badge-danger">INATIVO</span>
                            {% else %}<span class="badge badge-warning">SUSPENSO</span>{% endif %}
                        </td>
                        <td>
                            <div class="actions">
                                <a href="/clinicas/{{ clinica.id }}/assinatura/" class="btn btn-info">Gerenciar Plano</a>
                                <a href="/clinicas/{{ clinica.id }}/" class="btn btn-success">Ver</a>
                                <a href="/clinicas/{{ clinica.id }}/editar/" class="btn btn-warning">Editar</a>
                                <a href="/clinicas/{{ clinica.id }}/delete/" class="btn btn-danger" onclick="return confirm('Confirma exclusao?')">Excluir</a>
                                
                                <form method="POST" action="/clinicas/{{ clinica.id }}/toggle-whatsapp/" style="margin-left: 10px; display: inline-block;">
                                    {% csrf_token %}
                                    <div class="whatsapp-toggle">
                                        <label for="whatsapp-{{ clinica.id }}">Plano WhatsApp</label>
                                        <input type="checkbox" id="whatsapp-{{ clinica.id }}" onchange="this.form.submit()" 
                                            {% if clinica.plano_whatsapp_ia_ativo %}checked{% endif %}>
                                    </div>
                                </form>
                                
                                {% if clinica.plano_whatsapp_ia_ativo %}
                                    <a href="/clinicas/{{ clinica.id }}/whatsapp-setup/" class="btn" style="background: #25D366; color: white; margin-left: 5px; padding: 5px 10px; font-size: 12px;">
                                        📱 Conectar
                                    </a>
                                {% endif %}
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>Usuarios Cadastrados</h2>
                <a href="/usuarios/criar/" class="btn btn-primary">Novo Usuario</a>
            </div>
        </div>

        {% for clinica in clinicas %}
        <div class="section" style="margin-top: -10px;">
            <div class="section-header"><h3>Clínica: {{ clinica.nome }}</h3></div>
            <table>
                <thead>
                    <tr><th>ID</th><th>Nome</th><th>Email</th><th>Funções</th><th>Status</th><th>Acoes</th></tr>
                </thead>
                <tbody>
                    {% for usuario in clinica.usuarios_da_clinica %}
                    <tr>
                        <td>{{ usuario.id }}</td>
                        <td>{{ usuario.nome_completo }}</td>
                        <td>{{ usuario.email }}</td>
                        <td>{{ usuario.funcoes|join:", " }}</td>
                        <td>
                            {% if usuario.status == 'ativo' %}<span class="badge badge-success">ATIVO</span>
                            {% else %}<span class="badge badge-danger">INATIVO</span>{% endif %}
                        </td>
                        <td>
                            <div class="actions">
                                <a href="/usuarios/{{ usuario.id }}/" class="btn btn-success">Ver</a>
                                <a href="/usuarios/{{ usuario.id }}/editar/" class="btn btn-warning">Editar</a>
                                <a href="/usuarios/{{ usuario.id }}/delete/" class="btn btn-danger" onclick="return confirm('Confirma exclusao?')">Excluir</a>
                            </div>
                        </td>
                    </tr>
                    {% empty %}
                    <tr><td colspan="6" style="text-align: center;">Nenhum usuário cadastrado nesta clínica.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    </div>

    <div id="consumoModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Uso e Limites do Plano</h2>
                <span class="close-btn">&times;</span>
            </div>
            <div class="medicos-info">
                <strong>Médicos:</strong> 
                <span id="medicosUsados"></span> / <span id="medicosLimite"></span> contratados
                (<span id="medicosRestantes"></span> disponíveis)
            </div>
            <table class="consumo-table">
                <thead>
                    <tr>
                        <th class="label-col">Recurso de IA</th>
                        <th>Uso Diário</th>
                        <th>Uso Semanal</th>
                        <th>Uso Mensal</th>
                        <th>Restante (Mês)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="label-col">Transcrição de Consultas</td>
                        <td id="tc_dia"></td>
                        <td id="tc_semana"></td>
                        <td id="tc_mes"></td>
                        <td id="tc_restante"></td>
                    </tr>
                    <tr>
                        <td class="label-col">Transcrição de Exames Gerais</td>
                        <td id="teg_dia"></td>
                        <td id="teg_semana"></td>
                        <td id="teg_mes"></td>
                        <td id="teg_restante"></td>
                    </tr>
                    <tr>
                        <td class="label-col">Laudos de Exames com IA</td>
                        <td id="le_dia"></td>
                        <td id="le_semana"></td>
                        <td id="le_mes"></td>
                        <td id="le_restante"></td>
                    </tr>
                    <tr>
                        <td class="label-col">Documentos Médicos com IA</td>
                        <td id="dm_dia"></td>
                        <td id="dm_semana"></td>
                        <td id="dm_mes"></td>
                        <td id="dm_restante"></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const clinicasData = JSON.parse('{{ clinicas_json|safe }}');
        const modal = document.getElementById('consumoModal');
        const closeBtn = document.querySelector('.close-btn');

        function findClinicaById(id) {
            return clinicasData.find(c => c.id === id);
        }

        function showConsumoModal(clinicaId) {
            const clinica = findClinicaById(clinicaId);
            if (!clinica) return;

            document.getElementById('modalTitle').textContent = `Uso e Limites - ${clinica.nome}`;

            const limitesMedicos = clinica.limites_medicos || { usados: 0, limite: 0, restantes: 0 };
            document.getElementById('medicosUsados').textContent = limitesMedicos.usados;
            document.getElementById('medicosLimite').textContent = limitesMedicos.limite;
            document.getElementById('medicosRestantes').textContent = limitesMedicos.restantes;

            const consumo = clinica.consumo_ia;
            if (consumo) {
                const tc = consumo.transcricao_consulta || {};
                document.getElementById('tc_dia').textContent = tc.usado_dia || 0;
                document.getElementById('tc_semana').textContent = tc.usado_semana || 0;
                document.getElementById('tc_mes').textContent = `${tc.usado_mes || 0} / ${tc.limite_mes || 0}`;
                document.getElementById('tc_restante').textContent = tc.restante_mes || 0;
                
                const teg = consumo.transcricao_exame_geral || {};
                document.getElementById('teg_dia').textContent = teg.usado_dia || 0;
                document.getElementById('teg_semana').textContent = teg.usado_semana || 0;
                document.getElementById('teg_mes').textContent = `${teg.usado_mes || 0} / ${teg.limite_mes || 0}`;
                document.getElementById('teg_restante').textContent = teg.restante_mes || 0;

                const le = consumo.laudo_exame_ia || {};
                document.getElementById('le_dia').textContent = le.usado_dia || 0;
                document.getElementById('le_semana').textContent = le.usado_semana || 0;
                document.getElementById('le_mes').textContent = `${le.usado_mes || 0} / ${le.limite_mes || 0}`;
                document.getElementById('le_restante').textContent = le.restante_mes || 0;

                const dm = consumo.documento_medico_ia || {};
                document.getElementById('dm_dia').textContent = dm.usado_dia || 0;
                document.getElementById('dm_semana').textContent = dm.usado_semana || 0;
                document.getElementById('dm_mes').textContent = `${dm.usado_mes || 0} / ${dm.limite_mes || 0}`;
                document.getElementById('dm_restante').textContent = dm.restante_mes || 0;
            }

            modal.style.display = 'block';
        }

        closeBtn.onclick = function() {
            modal.style.display = 'none';
        }

        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
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
        .header { background: #667eea; color: white; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .container { max-width: 800px; margin: 20px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h2 { margin-bottom: 20px; color: #333; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #666; font-weight: bold; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .btn { padding: 12px 24px; border-radius: 5px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .actions { margin-top: 20px; display: flex; gap: 10px; }
        .error { background: #fee; color: #c00; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        #medico-fields { display: none; }
        /* --- NOVO CSS PARA CHECKBOXES --- */
        .funcoes-group { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
        .funcoes-group label { display: inline-block; margin-right: 15px; font-weight: normal; }
        .funcoes-group input[type="checkbox"] { width: auto; margin-right: 5px; }
        /* --- FIM DO NOVO CSS --- */
    </style>
    <script>
        function toggleMedicoFields() {
            // --- LÓGICA DO SCRIPT ATUALIZADA ---
            var medicoCheckbox = document.getElementById('funcao_medico');
            var medicoFields = document.getElementById('medico-fields');
            if (medicoCheckbox && medicoCheckbox.checked) {
                medicoFields.style.display = 'block';
            } else {
                medicoFields.style.display = 'none';
            }
        }
        // Garante que a função seja chamada ao carregar a página
        window.onload = toggleMedicoFields;
        // --- FIM DA LÓGICA DO SCRIPT ---
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
                    <input type="password" name="password" required placeholder="Será gerada uma senha temporária">
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
                <!-- --- CAMPO DE FUNÇÕES ALTERADO PARA CHECKBOXES --- -->
                <div class="form-group">
                    <label>Funções:</label>
                    <div class="funcoes-group">
                        <label>
                            <input type="checkbox" name="funcoes" value="admin" onchange="toggleMedicoFields()"> Administrador
                        </label>
                        <label>
                            <input type="checkbox" name="funcoes" value="medico" id="funcao_medico" onchange="toggleMedicoFields()"> Médico
                        </label>
                        <label>
                            <input type="checkbox" name="funcoes" value="secretaria" onchange="toggleMedicoFields()"> Secretária
                        </label>
                    </div>
                </div>
                <!-- --- FIM DA ALTERAÇÃO --- -->
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

TEMPLATES['assinatura_form.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>Gerenciar Plano - IntelliMed</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }
        .header { background: #667eea; color: white; padding: 20px; }
        .container { max-width: 800px; margin: 20px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        p { color: #666; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .btn { padding: 12px 24px; border-radius: 5px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .actions { margin-top: 20px; display: flex; gap: 10px; }
        .error { background: #fee; color: #c00; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        .current-plan { background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin-bottom: 20px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header"><h1>Gerenciar Plano de Assinatura</h1></div>
    <div class="container">
        <h1>Clínica: {{ clinica.nome }}</h1>
        <p>Selecione um novo plano para a clínica e a data de início do ciclo de faturamento.</p>

        {% if clinica.assinatura_info %}
            <div class="current-plan">
                <strong>Plano Atual:</strong> {{ clinica.assinatura_info.plano_nome }} <br>
                <strong>Válido de:</strong> {{ clinica.assinatura_info.data_inicio }} <strong>até</strong> {{ clinica.assinatura_info.data_fim }}
            </div>
        {% else %}
            <div class="current-plan" style="border-color: #ffc107;">
                <strong>A clínica não possui um plano ativo no momento.</strong>
            </div>
        {% endif %}

        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        
        <form method="post">
            <div class="form-group">
                <label for="plano_id">Plano de Assinatura</label>
                <select name="plano_id" id="plano_id" required>
                    <option value="">Selecione um plano...</option>
                    {% for plano in planos %}
                        <option value="{{ plano.id }}" {% if plano.id == clinica.assinatura_info.plano_id %}selected{% endif %}>
                            {{ plano.nome }} ({{ plano.limite_medicos }} médico(s), {{ plano.limite_transcricao_consulta_mes }} req. IA/mês)
                        </option>
                    {% endfor %}
                </select>
            </div>
            <div class="form-group">
                <label for="data_inicio">Data de Início do Plano</label>
                <input type="date" name="data_inicio" id="data_inicio" value="{{ clinica.assinatura_info.data_inicio }}" required>
            </div>
            <div class="actions">
                <button type="submit" class="btn btn-primary">Salvar Assinatura</button>
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
        .header { background: #667eea; color: white; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .container { max-width: 800px; margin: 20px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h2 { margin-bottom: 20px; color: #333; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #666; font-weight: bold; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .btn { padding: 12px 24px; border-radius: 5px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .actions { margin-top: 20px; display: flex; gap: 10px; }
        .error { background: #fee; color: #c00; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        #medico-fields { display: none; }
        .info-box { background: #e7f3ff; border-left: 4px solid #2196F3; padding: 10px; margin-bottom: 20px; border-radius: 4px; }
        /* --- NOVO CSS PARA CHECKBOXES --- */
        .funcoes-group { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
        .funcoes-group label { display: inline-block; margin-right: 15px; font-weight: normal; }
        .funcoes-group input[type="checkbox"] { width: auto; margin-right: 5px; }
        /* --- FIM DO NOVO CSS --- */
    </style>
    <script>
        function toggleMedicoFields() {
            var medicoCheckbox = document.getElementById('funcao_medico');
            var medicoFields = document.getElementById('medico-fields');
            if (medicoCheckbox && medicoCheckbox.checked) {
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
                <!-- --- CAMPO DE FUNÇÕES ALTERADO PARA CHECKBOXES --- -->
                <div class="form-group">
                    <label>Funções:</label>
                    <div class="funcoes-group">
                        <label>
                            <input type="checkbox" name="funcoes" value="admin" onchange="toggleMedicoFields()" {% if 'admin' in usuario.funcoes %}checked{% endif %}> Administrador
                        </label>
                        <label>
                            <input type="checkbox" name="funcoes" value="medico" id="funcao_medico" onchange="toggleMedicoFields()" {% if 'medico' in usuario.funcoes %}checked{% endif %}> Médico
                        </label>
                        <label>
                            <input type="checkbox" name="funcoes" value="secretaria" onchange="toggleMedicoFields()" {% if 'secretaria' in usuario.funcoes %}checked{% endif %}> Secretária
                        </label>
                    </div>
                </div>
                <!-- --- FIM DA ALTERAÇÃO --- -->
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

TEMPLATES['whatsapp_setup.html'] = """
<!DOCTYPE html>
<html>
<head>
    <title>Conectar WhatsApp - IntelliMed</title>
    <meta charset="utf-8">
    <!-- Recarrega apenas se estiver esperando QR Code ou loading -->
    {% if status == 'qrcode' or status == 'loading' %}
    <meta http-equiv="refresh" content="30">
    {% endif %}
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); text-align: center; max-width: 500px; width: 90%; }
        h1 { color: #333; margin-bottom: 10px; }
        p { color: #666; margin-bottom: 30px; }
        .qr-container { margin: 20px 0; border: 2px dashed #ddd; padding: 10px; display: inline-block; }
        img { max-width: 100%; height: auto; }
        .btn { padding: 12px 24px; border-radius: 5px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; display: inline-block; margin-top: 20px; margin-right: 10px; }
        .btn-primary { background: #667eea; color: white; }
        .btn-danger { background: #e53935; color: white; }
        .btn-secondary { background: #ccc; color: #333; }
        .status-badge { display: inline-block; padding: 8px 15px; border-radius: 20px; font-weight: bold; margin-bottom: 20px; }
        .status-connected { background: #d4edda; color: #155724; }
        .status-disconnected { background: #f8d7da; color: #721c24; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Conectar WhatsApp</h1>
        <p>Clínica: <strong>{{ clinica_nome }}</strong></p>
        
        {% if status == 'connected' %}
            <div class="status-badge status-connected">✅ WhatsApp Conectado com Sucesso!</div>
            <p>A secretária virtual já está ativa para esta clínica.</p>
            
            <div>
                <a href="/dashboard/" class="btn btn-primary">Voltar ao Dashboard</a>
                <!-- Botão de Reset -->
                <form action="/clinicas/{{ clinica_id }}/whatsapp-reset/" method="POST" style="display:inline;">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger" onclick="return confirm('Tem certeza? Isso irá desconectar o WhatsApp atual.')">Resetar Conexão</button>
                </form>
            </div>
        
        {% elif status == 'qrcode' %}
            <div class="status-badge status-disconnected">Aguardando Leitura...</div>
            <p>Abra o WhatsApp no celular da clínica e escaneie o código abaixo:</p>
            
            <div class="qr-container">
                <img src="data:image/png;base64,{{ qrcode }}" alt="QR Code WhatsApp">
            </div>
            
            <div>
                <p><small>A página recarrega automaticamente a cada 30 segundos.</small></p>
                <a href="" class="btn btn-primary">Atualizar Agora</a>
            </div>

        {% else %}
            <!-- Estado Loading ou Incerto -->
            <div class="loader"></div>
            <p>Verificando status...</p>
            
             <!-- Botão de Reset de Emergência caso trave -->
            <form action="/clinicas/{{ clinica_id }}/whatsapp-reset/" method="POST" style="margin-top: 20px;">
                {% csrf_token %}
                <button type="submit" class="btn btn-danger" style="font-size: 12px;">Forçar Reset</button>
            </form>
        {% endif %}
        
        <br>
        <a href="/dashboard/" class="btn btn-secondary" style="font-size: 12px;">Voltar</a>
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
    path('clinicas/<int:clinica_id>/', clinica_view, name='clinica_view'),
    path('clinicas/<int:clinica_id>/editar/', clinica_edit_view, name='clinica_edit'),
    path('clinicas/<int:clinica_id>/delete/', clinica_delete_view, name='clinica_delete'),
    path('clinicas/<int:clinica_id>/status/<str:status>/', clinica_toggle_status_view, name='clinica_toggle_status'),
    path('clinicas/<int:clinica_id>/toggle-whatsapp/', clinica_toggle_whatsapp_view, name='clinica_toggle_whatsapp'),
    # NOVA ROTA ADICIONADA:
    path('clinicas/<int:clinica_id>/whatsapp-setup/', clinica_whatsapp_setup_view, name='clinica_whatsapp_setup'),
    path('clinicas/<int:clinica_id>/whatsapp-reset/', clinica_whatsapp_reset_view, name='clinica_whatsapp_reset'),
    path('clinicas/<int:clinica_id>/assinatura/', clinica_assinatura_view, name='clinica_assinatura'),
    
    # Usuários
    path('usuarios/criar/', usuario_create_view, name='usuario_create'),
    path('usuarios/<int:usuario_id>/', usuario_view, name='usuario_view'),
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
