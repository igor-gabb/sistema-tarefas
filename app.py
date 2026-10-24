"""
Mini sistema de tarefas
Frontend (HTML/CSS/JS) + Backend (Flask) + Banco (PostgreSQL no Supabase)
"""
import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

# Lê o arquivo .env quando você roda no seu PC.
# No Render, a variável é configurada no painel.
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)


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


def criar_tabela():
    """Cria a tabela na primeira vez que o sistema roda."""
    with banco() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tarefas (
                id         SERIAL PRIMARY KEY,
                titulo     TEXT NOT NULL,
                concluida  BOOLEAN NOT NULL DEFAULT FALSE,
                criada_em  TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)


# ---------- PÁGINA ----------

@app.route("/")
def inicio():
    return render_template("index.html")


# ---------- API (o JavaScript do site conversa com essas rotas) ----------

@app.get("/api/tarefas")
def listar():
    with banco() as cur:
        cur.execute("SELECT id, titulo, concluida FROM tarefas ORDER BY concluida, criada_em DESC")
        return jsonify(cur.fetchall())


@app.post("/api/tarefas")
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
            "INSERT INTO tarefas (titulo) VALUES (%s) RETURNING id, titulo, concluida",
            (titulo,),
        )
        return jsonify(cur.fetchone()), 201


@app.patch("/api/tarefas/<int:tarefa_id>")
def alternar(tarefa_id):
    """Marca como concluída / não concluída."""
    with banco() as cur:
        cur.execute(
            "UPDATE tarefas SET concluida = NOT concluida WHERE id = %s RETURNING id, titulo, concluida",
            (tarefa_id,),
        )
        tarefa = cur.fetchone()
    if not tarefa:
        return jsonify({"erro": "Tarefa não encontrada."}), 404
    return jsonify(tarefa)


@app.delete("/api/tarefas/<int:tarefa_id>")
def excluir(tarefa_id):
    with banco() as cur:
        cur.execute("DELETE FROM tarefas WHERE id = %s", (tarefa_id,))
        if cur.rowcount == 0:
            return jsonify({"erro": "Tarefa não encontrada."}), 404
    return "", 204


# Cria a tabela assim que o sistema sobe
if DATABASE_URL:
    criar_tabela()
else:
    print("ATENÇÃO: DATABASE_URL não configurada. Veja o README.")


if __name__ == "__main__":
    app.run(debug=True)
