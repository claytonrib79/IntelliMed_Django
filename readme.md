# IntelliMed - Sistema de Gestão de Clínicas Médicas

Sistema completo de gestão para clínicas e consultórios médicos com inteligência artificial integrada para transcrição de consultas e interpretação de exames.

## 📋 Funcionalidades

### Backend Principal (main.py - porta 8000)
- **Autenticação JWT** com controle de permissões por função
- **Multi-tenant** - Isolamento total entre clínicas
- **Gestão de Pacientes** - CRUD completo com histórico
- **Agendamentos** - Sistema completo com fila de atendimento
- **Consultas com IA**
  - Gravação de áudio da consulta
  - Transcrição automática com Google Gemini
  - Identificação de falas (médico/paciente)
  - Geração automática de documentos médicos (atestados, anamnese, prescrições, relatórios)
- **Exames com IA**
  - Upload de imagens e PDFs
  - Interpretação automática por IA
  - Laudo completo com fontes médicas
  - Revisão médica obrigatória
- **Faturamento Completo** - Receitas, despesas e dashboard financeiro
- **Dashboards** - Estatísticas e métricas em tempo real

### Admin Panel (admin_panel_django.py - porta 9000)
- Interface web exclusiva para super_admin
- Gestão de clínicas (CRUD completo)
- Gestão de usuários (CRUD completo)
- Dashboard com estatísticas

## 🚀 Tecnologias

- Python 3.11+
- Django 5.2.7
- Django REST Framework
- JWT Authentication
- Google Gemini AI (1.5 Flash)
- Channels (WebSocket)
- SQLite

## 📦 Instalação

### 1. Clonar o repositório
```bash
git clone https://github.com/claytonrib79/intellimed_Django_2025.git
cd intellimed_Django_2025