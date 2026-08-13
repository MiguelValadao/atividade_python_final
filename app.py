import os
import sqlite3

import requests
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "tarefas.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "troque-esta-chave-em-producao"
)
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

ADVICE_API = "https://api.adviceslip.com/advice"

STATUS_EM_ANDAMENTO = "andamento"
STATUS_LABELS = {
    "pendente": "Pendente",
    "andamento": "Em andamento",
    "concluida": "Concluída",
}


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            status TEXT NOT NULL DEFAULT 'pendente',
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        );
        """
    )
    conn.commit()
    conn.close()


def usuario_logado():
    return session.get("usuario_id")


@app.context_processor
def inject_usuario():
    usuario_id = usuario_logado()
    nome = None
    if usuario_id:
        conn = get_db()
        usuario = conn.execute(
            "SELECT nome FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        conn.close()
        if usuario:
            nome = usuario["nome"]
    return {"usuario_nome": nome}


def login_necessario():
    if not usuario_logado():
        flash("Faça login para acessar esta página.", "warning")
        return redirect(url_for("login"))
    return None


@app.route("/")
def index():
    return render_template("index.html", status_labels=STATUS_LABELS)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if usuario_logado():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")

        if not nome or not email or not senha:
            flash("Preencha todos os campos obrigatórios.", "danger")
        elif senha != confirmacao:
            flash("As senhas não coincidem.", "danger")
        elif "@" not in email or "." not in email:
            flash("Informe um e-mail válido.", "danger")
        elif len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
        else:
            conn = get_db()
            existe = conn.execute(
                "SELECT id FROM usuarios WHERE email = ?", (email,)
            ).fetchone()
            if existe:
                conn.close()
                flash("Já existe uma conta com este e-mail.", "danger")
            else:
                hash_senha = generate_password_hash(senha)
                cursor = conn.execute(
                    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                    (nome, email, hash_senha),
                )
                conn.commit()
                conn.close()
                session["usuario_id"] = cursor.lastrowid
                flash("Conta criada com sucesso. Bem-vindo(a)!", "success")
                return redirect(url_for("dashboard"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if usuario_logado():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        conn = get_db()
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario["senha"], senha):
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("dashboard"))
        flash("E-mail ou senha incorretos.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    bloqueio = login_necessario()
    if bloqueio:
        return bloqueio

    conn = get_db()
    tarefas = conn.execute(
        """
        SELECT * FROM tarefas
        WHERE usuario_id = ?
        ORDER BY CASE status
            WHEN 'pendente' THEN 1
            WHEN 'andamento' THEN 2
            ELSE 3
        END, id DESC
        """,
        (usuario_logado(),),
    ).fetchall()
    conn.close()

    frase = obter_frase_motivacional()

    return render_template(
        "dashboard.html", tarefas=tarefas, frase=frase, status_labels=STATUS_LABELS
    )


def obter_frase_motivacional():
    try:
        resposta = requests.get(ADVICE_API, timeout=5)
        resposta.raise_for_status()
        dado = resposta.json()
        return dado.get("slip", {}).get("advice", "")
    except (requests.RequestException, ValueError):
        return "Aproveite o dia e conquiste seus objetivos, um passo de cada vez."


@app.route("/nova_tarefa", methods=["GET", "POST"])
def nova_tarefa():
    bloqueio = login_necessario()
    if bloqueio:
        return bloqueio

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        status = request.form.get("status", "pendente")

        if status not in STATUS_LABELS:
            status = "pendente"
        if not titulo:
            flash("O título da tarefa é obrigatório.", "danger")
        else:
            conn = get_db()
            conn.execute(
                """
                INSERT INTO tarefas (titulo, descricao, status, usuario_id)
                VALUES (?, ?, ?, ?)
                """,
                (titulo, descricao, status, usuario_logado()),
            )
            conn.commit()
            conn.close()
            flash("Tarefa criada com sucesso!", "success")
            return redirect(url_for("dashboard"))

    return render_template("nova_tarefa.html", status_labels=STATUS_LABELS)


@app.route("/editar/<int:tarefa_id>", methods=["GET", "POST"])
def editar_tarefa(tarefa_id):
    bloqueio = login_necessario()
    if bloqueio:
        return bloqueio

    conn = get_db()
    tarefa = conn.execute(
        "SELECT * FROM tarefas WHERE id = ? AND usuario_id = ?",
        (tarefa_id, usuario_logado()),
    ).fetchone()

    if not tarefa:
        conn.close()
        flash("Tarefa não encontrada.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        status = request.form.get("status", "pendente")

        if status not in STATUS_LABELS:
            status = "pendente"
        if not titulo:
            flash("O título da tarefa é obrigatório.", "danger")
        else:
            conn.execute(
                "UPDATE tarefas SET titulo = ?, descricao = ?, status = ? WHERE id = ?",
                (titulo, descricao, status, tarefa_id),
            )
            conn.commit()
            conn.close()
            flash("Tarefa atualizada com sucesso!", "success")
            return redirect(url_for("dashboard"))

    conn.close()
    return render_template(
        "editar_tarefa.html", tarefa=tarefa, status_labels=STATUS_LABELS
    )


@app.route("/excluir/<int:tarefa_id>", methods=["POST"])
def excluir_tarefa(tarefa_id):
    bloqueio = login_necessario()
    if bloqueio:
        return bloqueio

    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM tarefas WHERE id = ? AND usuario_id = ?",
        (tarefa_id, usuario_logado()),
    )
    conn.commit()
    conn.close()
    if cursor.rowcount:
        flash("Tarefa excluída.", "info")
    else:
        flash("Tarefa não encontrada.", "danger")
    return redirect(url_for("dashboard"))


@app.route("/concluir/<int:tarefa_id>", methods=["POST"])
def concluir_tarefa(tarefa_id):
    bloqueio = login_necessario()
    if bloqueio:
        return bloqueio

    conn = get_db()
    cursor = conn.execute(
        """
        UPDATE tarefas SET status = 'concluida'
        WHERE id = ? AND usuario_id = ?
        """,
        (tarefa_id, usuario_logado()),
    )
    conn.commit()
    conn.close()
    if cursor.rowcount:
        flash("Tarefa marcada como concluída!", "success")
    else:
        flash("Tarefa não encontrada.", "danger")
    return redirect(url_for("dashboard"))


@app.route("/api/tarefas")
def api_tarefas():
    bloqueio = login_necessario()
    if bloqueio:
        return jsonify({"erro": "Não autenticado"}), 401

    status = request.args.get("status", "").strip()
    conn = get_db()
    if status in STATUS_LABELS:
        tarefas = conn.execute(
            """
            SELECT * FROM tarefas
            WHERE usuario_id = ? AND status = ?
            ORDER BY id DESC
            """,
            (usuario_logado(), status),
        ).fetchall()
    else:
        tarefas = conn.execute(
            """
            SELECT * FROM tarefas
            WHERE usuario_id = ?
            ORDER BY CASE status
                WHEN 'pendente' THEN 1
                WHEN 'andamento' THEN 2
                ELSE 3
            END, id DESC
            """,
            (usuario_logado(),),
        ).fetchall()
    conn.close()

    dados = [
        {
            "id": t["id"],
            "titulo": t["titulo"],
            "descricao": t["descricao"] or "",
            "status": t["status"],
            "status_label": STATUS_LABELS.get(t["status"], t["status"]),
        }
        for t in tarefas
    ]
    return jsonify(dados)


@app.route("/api/progresso")
def api_progresso():
    bloqueio = login_necessario()
    if bloqueio:
        return jsonify({"erro": "Não autenticado"}), 401

    conn = get_db()
    linhas = conn.execute(
        "SELECT status, COUNT(*) AS total FROM tarefas WHERE usuario_id = ? GROUP BY status",
        (usuario_logado(),),
    ).fetchall()
    conn.close()

    contagem = {status: 0 for status in STATUS_LABELS}
    for linha in linhas:
        if linha["status"] in contagem:
            contagem[linha["status"]] = linha["total"]

    return jsonify(
        {
            "labels": [STATUS_LABELS[s] for s in STATUS_LABELS],
            "valores": [contagem[s] for s in STATUS_LABELS],
            "cores": ["#fdcb6e", "#5b8def", "#27ae60"],
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=app.config["DEBUG"])