"""
Mini sistema de tarefas com login
Frontend (HTML/CSS/JS) + Backend (Flask) + Banco (PostgreSQL no Supabase)
"""
import os
import re
from contextlib import contextmanager
from datetime import timedelta
from functools import wraps

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

# Lê o arquivo .env quando você roda no seu PC.
# No Render, as variáveis são configuradas no painel.
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY")
EM_PRODUCAO = bool(os.environ.get("RENDER"))  # o Render define RENDER=true sozinho

if EM_PRODUCAO and not SECRET_KEY:
    raise RuntimeError("Configure a variável SECRET_KEY no Render (veja o README).")

app = Flask(__name__)
app.config.update(
    # A SECRET_KEY assina o cookie de sessão. Sem ela, qualquer um forjaria um login.
    SECRET_KEY=SECRET_KEY or "chave-so-para-testar-no-pc",
    SESSION_COOKIE_HTTPONLY=True,      # JavaScript não consegue ler o cookie
    SESSION_COOKIE_SAMESITE="Lax",     # outros sites não conseguem usar seu login
    SESSION_COOKIE_SECURE=EM_PRODUCAO,  # em produção, cookie só trafega por HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

USUARIO_VALIDO = re.compile(r"^[a-zA-Z0-9._-]{3,30}$")
# Hash "falso" usado quando o usuário não existe, para o tempo de resposta
# ser parecido e ninguém descobrir quais usuários existem medindo a demora.
HASH_FALSO = generate_password_hash("senha-que-ninguem-usa")


# ---------- BANCO DE DADOS ----------

@contextmanager
def banco():
    """Abre uma conexão, entrega um cursor, salva (commit) e fecha no final."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        with conn:  # commit automático se der certo, rollback se der erro
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()


def criar_tabelas():
    """Cria/atualiza as tabelas. Pode rodar várias vezes sem problema."""
    with banco() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id          SERIAL PRIMARY KEY,
                usuario     TEXT NOT NULL UNIQUE,
                senha_hash  TEXT NOT NULL,
                criado_em   TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tarefas (
                id         SERIAL PRIMARY KEY,
                titulo     TEXT NOT NULL,
                concluida  BOOLEAN NOT NULL DEFAULT FALSE,
                criada_em  TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        # Liga cada tarefa a um usuário. Se o usuário for apagado, as tarefas dele também.
        cur.execute("""
            ALTER TABLE tarefas
            ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE
        """)


# ---------- PROTEÇÃO DAS ROTAS ----------

def login_obrigatorio(rota):
    """Decorator: só deixa passar quem está logado."""
    @wraps(rota)
    def protegida(*args, **kwargs):
        if "usuario_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"erro": "Faça login."}), 401
            return redirect(url_for("login"))
        return rota(*args, **kwargs)
    return protegida


def entrar_como(usuario):
    session.clear()  # descarta qualquer sessão antiga antes de logar
    session.permanent = True
    session["usuario_id"] = usuario["id"]
    session["usuario"] = usuario["usuario"]


# ---------- LOGIN / CADASTRO / SAIR ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return redirect(url_for("inicio"))

    if request.method == "GET":
        return render_template("login.html", modo="login")

    nome = request.form.get("usuario", "").strip().lower()
    senha = request.form.get("senha", "")

    with banco() as cur:
        cur.execute("SELECT id, usuario, senha_hash FROM usuarios WHERE usuario = %s", (nome,))
        usuario = cur.fetchone()

    hash_salvo = usuario["senha_hash"] if usuario else HASH_FALSO
    if not check_password_hash(hash_salvo, senha) or not usuario:
        # Mesma mensagem para "usuário não existe" e "senha errada", de propósito.
        return render_template("login.html", modo="login", erro="Usuário ou senha incorretos.", usuario=nome), 401

    entrar_como(usuario)
    return redirect(url_for("inicio"))


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if "usuario_id" in session:
        return redirect(url_for("inicio"))

    if request.method == "GET":
        return render_template("login.html", modo="cadastro")

    nome = request.form.get("usuario", "").strip().lower()
    senha = request.form.get("senha", "")
    confirmar = request.form.get("confirmar", "")

    erro = None
    if not USUARIO_VALIDO.match(nome):
        erro = "Usuário deve ter de 3 a 30 caracteres: letras, números, ponto, hífen ou _."
    elif len(senha) < 8:
        erro = "A senha precisa ter pelo menos 8 caracteres."
    elif senha != confirmar:
        erro = "As senhas não conferem."

    if erro:
        return render_template("login.html", modo="cadastro", erro=erro, usuario=nome), 400

    try:
        with banco() as cur:
            # Nunca salvamos a senha em si, só o hash (uma "impressão digital" irreversível).
            cur.execute(
                "INSERT INTO usuarios (usuario, senha_hash) VALUES (%s, %s) RETURNING id, usuario",
                (nome, generate_password_hash(senha)),
            )
            usuario = cur.fetchone()
    except psycopg2.errors.UniqueViolation:
        return render_template("login.html", modo="cadastro", erro="Esse usuário já existe.", usuario=nome), 400

    entrar_como(usuario)
    return redirect(url_for("inicio"))


@app.post("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


# ---------- PÁGINA ----------

@app.route("/")
@login_obrigatorio
def inicio():
    return render_template("index.html", usuario=session["usuario"])


# ---------- API (o JavaScript do site conversa com essas rotas) ----------
# Toda consulta filtra por usuario_id: cada um só vê e mexe nas próprias tarefas.

@app.get("/api/tarefas")
@login_obrigatorio
def listar():
    with banco() as cur:
        cur.execute(
            "SELECT id, titulo, concluida FROM tarefas WHERE usuario_id = %s ORDER BY concluida, criada_em DESC",
            (session["usuario_id"],),
        )
        return jsonify(cur.fetchall())


@app.post("/api/tarefas")
@login_obrigatorio
def criar():
    dados = request.get_json(silent=True) or {}
    titulo = str(dados.get("titulo", "")).strip()

    if not titulo:
        return jsonify({"erro": "O título não pode ficar vazio."}), 400
    if len(titulo) > 200:
        return jsonify({"erro": "Máximo de 200 caracteres."}), 400

    with banco() as cur:
        # %s evita SQL injection: o psycopg2 trata o texto com segurança
        cur.execute(
            "INSERT INTO tarefas (titulo, usuario_id) VALUES (%s, %s) RETURNING id, titulo, concluida",
            (titulo, session["usuario_id"]),
        )
        return jsonify(cur.fetchone()), 201


@app.patch("/api/tarefas/<int:tarefa_id>")
@login_obrigatorio
def alternar(tarefa_id):
    """Marca como concluída / não concluída."""
    with banco() as cur:
        cur.execute(
            """UPDATE tarefas SET concluida = NOT concluida
               WHERE id = %s AND usuario_id = %s
               RETURNING id, titulo, concluida""",
            (tarefa_id, session["usuario_id"]),
        )
        tarefa = cur.fetchone()
    if not tarefa:
        return jsonify({"erro": "Tarefa não encontrada."}), 404
    return jsonify(tarefa)


@app.delete("/api/tarefas/<int:tarefa_id>")
@login_obrigatorio
def excluir(tarefa_id):
    with banco() as cur:
        cur.execute(
            "DELETE FROM tarefas WHERE id = %s AND usuario_id = %s",
            (tarefa_id, session["usuario_id"]),
        )
        if cur.rowcount == 0:
            return jsonify({"erro": "Tarefa não encontrada."}), 404
    return "", 204


# Cria/atualiza as tabelas assim que o sistema sobe
if DATABASE_URL:
    criar_tabelas()
else:
    print("ATENÇÃO: DATABASE_URL não configurada. Veja o README.")


if __name__ == "__main__":
    app.run(debug=True)
