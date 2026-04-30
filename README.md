# ZapSign API — Automação de Documentos Encadeados

Aplicação Django que integra com a [API da ZapSign](https://docs.zapsign.com.br) para automatizar o envio de **dois documentos em sequência**: o Documento 2 é criado e enviado para assinatura automaticamente assim que o Documento 1 for totalmente assinado, via **webhook**.

---

## Funcionalidades

- Criação de um **fluxo** com 2 documentos encadeados via formulário web
- Envio imediato do **Documento 1** para assinatura na ZapSign
- Geração automática do **Documento 2** ao receber o webhook `doc_signed` com `status: "signed"`
- Suporte a múltiplos signatários por documento
- Envio automático de e-mail ao signatário (quando e-mail informado)
- Acompanhamento do status de cada documento e signatário em tempo real
- Download do documento assinado (link gerado via webhook)
- Autenticação de usuários (login/logout) com redirecionamento protegido por `@login_required`
- Interface moderna com sidebar animada (efeito gooey pill), página de login com anéis animados e favicon SVG personalizado

---

## Pré-requisitos

- Python 3.10+
- Conta na [ZapSign](https://app.zapsign.com.br) com token de API (Sandbox ou Produção)
- Para testes locais: [ngrok](https://ngrok.com) (para expor o webhook ao exterior)

---

## Instalação

```bash
# 1. Clone o repositório / acesse a pasta do projeto
cd Zapgsing_API

# 2. Crie e ative o ambiente virtual
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com seu token ZapSign e uma SECRET_KEY segura

# 5. Aplique as migrations
python manage.py makemigrations
python manage.py migrate

# 6. Crie um superusuário para o admin
python manage.py createsuperuser

# 7. Inicie o servidor
python manage.py runserver
```

Acesse: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Variáveis de ambiente (`.env`)

| Variável            | Descrição                                               | Exemplo                          |
|---------------------|--------------------------------------------------------|----------------------------------|
| `SECRET_KEY`        | Chave secreta do Django                                | `django-insecure-...`            |
| `DEBUG`             | Modo debug (`True` em desenvolvimento)                 | `True`                           |
| `ALLOWED_HOSTS`          | Hosts permitidos, separados por vírgula                     | `127.0.0.1,localhost`                     |
| `CSRF_TRUSTED_ORIGINS`   | Origens confiáveis para POST (incluir URL do ngrok em dev)  | `http://127.0.0.1:8000,https://seu.ngrok` |
| `ZAPSIGN_API_TOKEN`      | Token de API da ZapSign (funciona para sandbox e produção)  | `xxxxxxxx-xxxx-xxxx-xxxx-xxxx`            |

---

## Estrutura do projeto

```
Zapgsing_API/
├── .env                        ← variáveis de ambiente (não versionar)
├── .env.example                ← modelo do .env
├── requirements.txt
├── manage.py
│
├── static/                     ← arquivos estáticos globais
│   └── favicon.svg             ← favicon SVG do sistema
│
├── zapgsing_api/               ← configurações do projeto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── documents/                  ← app principal
│   ├── models.py               ← DocumentFlow, ZapSignDocument, Signer
│   ├── services.py             ← chamadas à API ZapSign (criar documento)
│   ├── views.py                ← listagem, criação e detalhe de fluxos
│   ├── urls.py
│   └── admin.py
│
├── webhooks/                   ← app de recepção de eventos
│   ├── views.py                ← lógica de automação (receive_webhook)
│   └── urls.py
│
└── templates/
    ├── base.html               ← layout com sidebar animada (Bootstrap 5)
    ├── registration/
    │   └── login.html          ← página de login com anéis animados
    └── documents/
        ├── index.html          ← lista de fluxos com filtros
        ├── create_flow.html    ← formulário de criação com validação inline
        └── flow_detail.html    ← detalhe com links de assinatura e download
```

---

## Fluxo de automação

```
┌──────────────────────────────────────────────────────────┐
│  Usuário preenche o formulário com 2 documentos          │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
              Documento 1 enviado à ZapSign
              (links de assinatura gerados)
                             │
                    Signatário(s) assina(m)
                             │
              ZapSign dispara webhook POST
              /webhooks/receive/
              { event_type: "doc_signed",
                status: "signed" }
                             │
                             ▼
         Django cria Documento 2 automaticamente
         na ZapSign e atualiza o status do fluxo
                             │
                    Signatário(s) assina(m)
                             │
              ZapSign dispara webhook novamente
                             │
                             ▼
                  Fluxo marcado como "Concluído"
```

---

## Configurando o Webhook na ZapSign

1. Acesse **Configurações → Integrações → API ZapSign → Webhooks**
2. Adicione a URL do endpoint:
   ```
   https://seu-dominio.com/webhooks/receive/
   ```
3. Selecione o evento **Documento Assinado (`doc_signed`)**
4. Salve

> **Testes locais com ngrok:**
> ```bash
> ngrok http 8000
> # Use a URL gerada (ex: https://abc123.ngrok.io/webhooks/receive/)
> ```

---

## Rotas disponíveis

| Método | URL                       | Descrição                                          |
|--------|---------------------------|----------------------------------------------------|
| GET    | `/`                       | Lista todos os fluxos (requer login)               |
| GET    | `/fluxo/novo/`            | Formulário para criar um novo fluxo (requer login) |
| POST   | `/fluxo/novo/`            | Processa a criação do fluxo                        |
| GET    | `/fluxo/<id>/`            | Detalhe do fluxo com links e download              |
| POST   | `/webhooks/receive/`      | Endpoint que recebe eventos da ZapSign             |
| GET    | `/login/`                 | Página de login                                    |
| POST   | `/logout/`                | Encerra a sessão do usuário                        |
| \*     | `/admin/`                 | Painel administrativo Django                       |

---

## Admin Django

O painel em `/admin/` permite visualizar e gerenciar:

- **Fluxos** (`DocumentFlow`) com os documentos inline
- **Documentos** (`ZapSignDocument`) com os signatários inline
- **Signatários** (`Signer`) com tokens e links de assinatura

---

## Segurança em produção

- Defina `DEBUG=False` no `.env`
- Use uma `SECRET_KEY` longa e aleatória
- Configure `ALLOWED_HOSTS` com seu domínio real
- Sirva a aplicação com **gunicorn** + **nginx**
- Use HTTPS — a ZapSign exige que o endpoint do webhook seja HTTPS

---

## Referências

- [Documentação ZapSign — Criar Documento](https://docs.zapsign.com.br/documentos/criar-documento)
- [Documentação ZapSign — Webhooks](https://docs.zapsign.com.br/webhooks)
- [Documentação ZapSign — Evento doc_signed](https://docs.zapsign.com.br/webhooks/eventos/document/documento-assinado)
