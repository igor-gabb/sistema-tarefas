# Sistema de Tarefas

Mini sistema para estudar as três partes de um site com banco de dados:

- **Frontend** (`templates/index.html` + `static/`): a tela que o usuário vê.
- **Backend** (`app.py`): API em Flask que recebe os pedidos e aplica as regras.
- **Banco** (PostgreSQL no Supabase): onde as tarefas ficam salvas.

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
│   └── index.html
└── static/
    ├── style.css
    ├── script.js
    └── favicon.svg
```

## Rotas da API

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
copy .env.example .env         # depois cole sua URL do Supabase no .env
python app.py
```

Abra http://127.0.0.1:5000

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
4. Em **Environment Variables**, adicione `DATABASE_URL` com a URL do Supabase.
5. Clique em **Deploy**. Em alguns minutos aparece o link `sistema-tarefas-xxxx.onrender.com`.

Toda vez que você der `git push`, o Render publica a nova versão sozinho.

## Limites do plano grátis

- O Render "dorme" depois de um tempo sem acesso; a primeira visita depois disso demora para carregar.
- O Supabase pausa projetos grátis que ficam muito tempo sem uso; é só reativar no painel.

Para estudo isso não é problema. Para um sistema que a empresa usa todo dia, vale um plano pago ou um servidor próprio.

## Próximos passos para estudar

- Adicionar login (o Supabase tem autenticação pronta).
- Editar o título de uma tarefa (nova rota `PUT`).
- Adicionar um campo de prazo (`ALTER TABLE tarefas ADD COLUMN prazo DATE`).
