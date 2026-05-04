# Manual de Deploy — Django no Render com PostgreSQL

Guia completo para hospedar projetos Django no Render com banco PostgreSQL, plano gratuito.

---

## Pré-requisitos

- Projeto Django funcionando localmente
- Repositório no GitHub ou GitLab
- Conta no [Render](https://render.com)

---

## 1. Pacotes necessários

Certifique-se de que os seguintes pacotes estão instalados no ambiente virtual:

```bash
pip install gunicorn psycopg2-binary dj-database-url whitenoise python-dotenv
pip freeze > requirements.txt
```

| Pacote | Função |
|---|---|
| `gunicorn` | Servidor WSGI para produção |
| `psycopg2-binary` | Driver do PostgreSQL |
| `dj-database-url` | Lê a URL do banco como string |
| `whitenoise` | Serve arquivos estáticos sem nginx |
| `python-dotenv` | Carrega variáveis do `.env` |

---

## 2. Configurar o `settings.py`

### 2.1 Imports

```python
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()
```

### 2.2 SECRET_KEY, DEBUG e ALLOWED_HOSTS

```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'valor-inseguro-somente-dev')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
```

### 2.3 WhiteNoise no MIDDLEWARE

Adicione **logo após** o `SecurityMiddleware`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← aqui
    ...
]
```

### 2.4 Banco de dados via dj-database-url

```python
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}
```

> Em desenvolvimento continua usando SQLite (sem precisar do `.env`).  
> Em produção o Render injeta a `DATABASE_URL` automaticamente.

### 2.5 Arquivos estáticos

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

> **Atenção:** o nome correto é `STATICFILES_DIRS` (não `STATICSFILES_DIRS`).

---

## 3. Criar o `build.sh`

Na raiz do projeto, crie o arquivo `build.sh`:

```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py createsuperuser --no-input || true
```

> O `|| true` evita que o build falhe nos deploys seguintes, quando o superusuário já existe.

---

## 4. Criar o `render.yaml`

Na raiz do projeto, crie o arquivo `render.yaml`:

```yaml
services:
  - type: web
    name: nome-do-projeto
    runtime: python
    plan: free
    buildCommand: "./build.sh"
    startCommand: "gunicorn nome_projeto.wsgi:application"
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: ".onrender.com"
      - key: DATABASE_URL
        fromDatabase:
          name: nome-do-projeto-db
          property: connectionString
      - key: PYTHON_VERSION
        value: "3.12.0"
      - key: DJANGO_SUPERUSER_USERNAME
        value: "admin"
      - key: DJANGO_SUPERUSER_EMAIL
        value: "admin@admin.com"
      - key: DJANGO_SUPERUSER_PASSWORD
        generateValue: true

databases:
  - name: nome-do-projeto-db
    databaseName: nome_do_projeto
    user: nome_do_projeto
    plan: free
```

> Substitua `nome-do-projeto` e `nome_projeto.wsgi` pelo nome real do seu projeto.

---

## 5. Verificar o `.gitignore`

Certifique-se de que estes itens estão no `.gitignore`:

```
.env
db.sqlite3
staticfiles/
media/
venv/
__pycache__/
*.pyc
```

---

## 6. Atualizar o `.env.example`

```env
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Produção (Render / PostgreSQL)
# DATABASE_URL=postgres://user:password@host:5432/dbname
DATABASE_URL=sqlite:///db.sqlite3
```

---

## 7. Fazer o deploy

### 7.1 Commit e push

```bash
git add .
git commit -m "chore: configurações para deploy no Render"
git push
```

### 7.2 Criar o projeto no Render

1. Acesse [render.com](https://render.com) → **+ New → Blueprint**
2. Conecte o repositório GitHub/GitLab
3. Confirme o branch (`main`) e o caminho do `render.yaml`
4. Clique em **Plano de Implantação** (Apply)
5. O Render criará automaticamente o banco e o serviço web

---

## 8. Após o deploy

### Acessar o Django Admin

```
https://seu-app.onrender.com/admin/
```

- Usuário: `admin` (ou o definido em `DJANGO_SUPERUSER_USERNAME`)
- Senha: gerada automaticamente — veja em **Render → serviço → Environment → `DJANGO_SUPERUSER_PASSWORD`**

### Visualizar o banco de dados

Acesse o banco remotamente com **TablePlus**, **DBeaver** ou **pgAdmin**:

1. Render → **nome-do-projeto-db** → aba **Info**
2. Copie a **External Database URL**
3. Cole na ferramenta como string de conexão

---

## 9. Planos disponíveis

### Web Service

| Plano | Preço | RAM | CPU | Observações |
|---|---|---|---|---|
| **Free** | $0/mês | 512 MB | 0.1 | Hiberna após 15 min de inatividade. Sem SSH, scaling ou disco persistente |
| **Starter** | $7/mês | 512 MB | 0.5 | Zero downtime, SSH, one-off jobs |
| **Standard** | $25/mês | 2 GB | 1 | Recomendado para produção |
| **Pro** | $85/mês | 4 GB | 2 | Alta disponibilidade |

### PostgreSQL

| Plano | Preço | RAM | CPU | Storage | Observações |
|---|---|---|---|---|---|
| **Free** | $0/mês | 256 MB | 0.1 | 1 GB | Expira e é **excluído após 90 dias** |
| **Basic** | a partir de $6/mês | — | — | 1 GB+ | Sem expiração, recomendado para hobby |
| **Pro** | a partir de $55/mês | — | — | escalável | Para produção em escala |

### Quando usar cada plano

- **Free** — testes, demos e projetos pessoais sem prazo crítico
- **Basic (banco) + Starter (web)** — projetos reais sem grande volume (~$13/mês), sem risco de perda de dados após 90 dias
- **Standard + Pro (banco)** — produção com tráfego real

> Para mudar os planos, altere no `render.yaml`:
> - Banco: `plan: basic` (a partir de $6/mês, sem expiração de 90 dias)
> - Web service: `plan: starter` (a partir de $7/mês, com zero downtime e SSH)
> 
> Os planos do banco e do web service são **independentes** — você pode combinar como quiser.

---

## 10. Checklist rápido

- [ ] `gunicorn`, `psycopg2-binary`, `dj-database-url`, `whitenoise` no `requirements.txt`
- [ ] `settings.py` com `DEBUG`, `ALLOWED_HOSTS` e `DATABASES` via variáveis de ambiente
- [ ] `WhiteNoiseMiddleware` no `MIDDLEWARE`
- [ ] `STATICFILES_STORAGE` configurado
- [ ] `build.sh` criado e com `createsuperuser --no-input || true`
- [ ] `render.yaml` com `plan: free` no serviço e no banco
- [ ] `.gitignore` incluindo `.env`, `db.sqlite3`, `venv/`, `staticfiles/`
- [ ] Commit e push feitos
- [ ] Blueprint aplicado no Render
