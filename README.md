# Sistema de Tarefas

Mini sistema para estudar as três partes de um site com banco de dados:

- **Frontend** (`templates/index.html` + `static/`): a tela que o usuário vê.
- **Backend** (`app.py`): API em Flask que recebe os pedidos e aplica as regras.
- **Banco** (PostgreSQL no Supabase): onde usuários e tarefas ficam salvos.

Tem cadastro e login: cada usuário só vê e mexe nas próprias tarefas.

O caminho de um clique: o JavaScript faz um `fetch("/api/tarefas")` → o Flask recebe → roda um SQL no banco → devolve JSON → o JavaScript desenha a lista.

## Estrutura

```
sistema-tarefas/
├── app.py              # backend + rotas da API
├── requirements.txt    # bibliotecas Python
├── .python-version     # versão do Python que o Render vai usar
├── .env.example        # modelo da variável de conexão com o banco
├── .gitignore          # impede que o .env (com senha) vá pro GitHub
├── templates/
│   ├── index.html      # lista de tarefas (só logado)
│   └── login.html      # telas de entrar e criar conta
└── static/
    ├── style.css
    ├── script.js
    └── favicon.svg
```

## Como o login funciona

1. No cadastro, a senha passa por `generate_password_hash` (algoritmo scrypt). O banco guarda só o hash, nunca a senha.
2. No login, `check_password_hash` compara a senha digitada com o hash salvo.
3. Se bater, o Flask grava o `usuario_id` na **sessão**: um cookie assinado com a `SECRET_KEY`. Sem a chave, ninguém consegue forjar esse cookie.
4. O decorator `@login_obrigatorio` barra quem não tem sessão: páginas mandam para `/login`, a API responde `401`.
5. Toda consulta de tarefas tem `WHERE usuario_id = ...`, então um usuário não alcança as tarefas de outro, nem chutando o id.

## Rotas

- `GET/POST /login` entrar
- `GET/POST /cadastro` criar conta
- `POST /sair` sair

## Rotas da API (exigem login)

- `GET /api/tarefas` lista todas
- `POST /api/tarefas` cria uma (`{"titulo": "..."}`)
- `PATCH /api/tarefas/<id>` marca ou desmarca como concluída
- `DELETE /api/tarefas/<id>` exclui

## 1. Criar o banco no Supabase

1. Crie uma conta em supabase.com e clique em **New project**.
2. Escolha uma senha para o banco **sem caracteres especiais** (só letras e números), para não quebrar a URL de conexão. Guarde essa senha.
3. Região: **South America (São Paulo)**.
4. Com o projeto criado, clique em **Connect** no topo, escolha **Session pooler** e copie a URI.
5. Troque `[YOUR-PASSWORD]` pela senha que você criou.

Use o **Session pooler**, não a "Direct connection": a conexão direta do Supabase é só IPv6, e o Render não consegue acessar.

A tabela é criada sozinha na primeira vez que o sistema roda.

## 2. Rodar no seu PC (opcional, mas recomendado)

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # depois preencha DATABASE_URL e SECRET_KEY no .env
python app.py
```

Abra http://127.0.0.1:5000

Para gerar a `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 3. Subir para o GitHub

Crie um repositório vazio no GitHub e, dentro da pasta:

```bash
git init
git add .
git commit -m "Sistema de tarefas"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/sistema-tarefas.git
git push -u origin main
```

Confira no GitHub que o arquivo `.env` **não** apareceu lá.

## 4. Publicar no Render

1. Crie conta em render.com entrando com o GitHub.
2. **New → Web Service** → escolha o repositório `sistema-tarefas`.
3. Preencha:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Instance Type: **Free**
4. Em **Environment Variables**, adicione:
   - `DATABASE_URL` com a URL do Supabase
   - `SECRET_KEY` com uma chave gerada pelo comando acima (use uma diferente da do seu PC). Sem ela o sistema se recusa a subir no Render, de propósito.
5. Clique em **Deploy**. Em alguns minutos aparece o link `sistema-tarefas-xxxx.onrender.com`.

Toda vez que você der `git push`, o Render publica a nova versão sozinho.

## Limites do plano grátis

- O Render "dorme" depois de um tempo sem acesso; a primeira visita depois disso demora para carregar.
- O Supabase pausa projetos grátis que ficam muito tempo sem uso; é só reativar no painel.

Para estudo isso não é problema. Para um sistema que a empresa usa todo dia, vale um plano pago ou um servidor próprio.

## Próximos passos para estudar

- Limitar tentativas de login (biblioteca Flask-Limiter), contra quem tenta adivinhar senhas.
- Tela para trocar a senha.
- Editar o título de uma tarefa (nova rota `PUT`).
- Adicionar um campo de prazo (`ALTER TABLE tarefas ADD COLUMN prazo DATE`).
