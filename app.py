import os
import sqlite3
import uuid
from pathlib import Path

from flask import (Flask, flash, g, redirect, render_template, request,
                   url_for)
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "lista.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
EXTENSOES = {"png", "jpg", "jpeg", "gif", "webp"}

PRIORIDADES = {1: "Alta", 2: "Média", 3: "Baixa"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "lista-de-desejos-local"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB por envio
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- banco ----
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL DEFAULT 0,
            prioridade INTEGER NOT NULL DEFAULT 2,
            loja TEXT,
            link TEXT,
            observacoes TEXT,
            foto TEXT,
            comprado INTEGER NOT NULL DEFAULT 0,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT OR IGNORE INTO config (chave, valor) VALUES ('banca', '0');
        """
    )
    db.commit()
    db.close()


def get_banca():
    row = get_db().execute(
        "SELECT valor FROM config WHERE chave = 'banca'"
    ).fetchone()
    return float(row["valor"]) if row else 0.0


def set_banca(valor):
    db = get_db()
    db.execute("UPDATE config SET valor = ? WHERE chave = 'banca'", (str(valor),))
    db.commit()


# -------------------------------------------------------------- helpers ----
def parse_dinheiro(texto):
    """Aceita '1.299,90', '1299,90', '1299.90' e 'R$ 50'."""
    texto = (texto or "").replace("R$", "").strip().replace(" ", "")
    if not texto:
        return 0.0
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") > 1:
        texto = texto.replace(".", "")
    return float(texto)


def fmt_brl(valor):
    s = f"{valor:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


app.jinja_env.filters["brl"] = fmt_brl


def salvar_foto(arquivo):
    if not arquivo or not arquivo.filename:
        return None
    ext = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
    if ext not in EXTENSOES:
        raise ValueError("Formato de imagem não suportado (use png, jpg, gif ou webp).")
    nome = f"{uuid.uuid4().hex}.{ext}"
    arquivo.save(UPLOAD_DIR / secure_filename(nome))
    return nome


def apagar_foto(nome):
    if nome:
        try:
            (UPLOAD_DIR / nome).unlink()
        except FileNotFoundError:
            pass


def preparar_item(row, banca):
    item = dict(row)
    preco = item["preco"] or 0
    if preco > 0:
        item["progresso"] = max(0.0, min(banca / preco, 1.0)) * 100
    else:
        item["progresso"] = 100.0
    item["falta"] = max(preco - banca, 0)
    item["pode_comprar"] = banca >= preco
    item["prioridade_nome"] = PRIORIDADES.get(item["prioridade"], "Média")
    return item


# ----------------------------------------------------------------- rotas ----
@app.route("/")
def index():
    db = get_db()
    banca = get_banca()
    ordem = request.args.get("ordem", "prioridade")
    order_sql = {
        "prioridade": "prioridade ASC, id DESC",
        "preco_asc": "preco ASC",
        "preco_desc": "preco DESC",
        "recentes": "id DESC",
    }.get(ordem, "prioridade ASC, id DESC")

    pendentes = [
        preparar_item(r, banca)
        for r in db.execute(f"SELECT * FROM itens WHERE comprado = 0 ORDER BY {order_sql}")
    ]
    comprados = [
        preparar_item(r, banca)
        for r in db.execute("SELECT * FROM itens WHERE comprado = 1 ORDER BY id DESC")
    ]

    total = sum(i["preco"] for i in pendentes)
    geral = {
        "total": total,
        "falta": max(total - banca, 0),
        "progresso": (min(banca / total, 1.0) * 100) if total > 0 else 0,
    }
    return render_template(
        "index.html", banca=banca, pendentes=pendentes, comprados=comprados,
        geral=geral, ordem=ordem,
    )


@app.route("/banca", methods=["POST"])
def atualizar_banca():
    try:
        valor = parse_dinheiro(request.form.get("banca"))
        if valor < 0:
            raise ValueError
        set_banca(valor)
        flash("Banca atualizada.", "ok")
    except ValueError:
        flash("Valor de banca inválido.", "erro")
    return redirect(url_for("index"))


def ler_formulario():
    nome = (request.form.get("nome") or "").strip()
    if not nome:
        raise ValueError("Dê um nome ao item.")
    try:
        preco = parse_dinheiro(request.form.get("preco"))
    except ValueError:
        raise ValueError("Preço inválido.")
    if preco < 0:
        raise ValueError("Preço não pode ser negativo.")
    try:
        prioridade = int(request.form.get("prioridade", 2))
    except ValueError:
        prioridade = 2
    if prioridade not in PRIORIDADES:
        prioridade = 2
    return {
        "nome": nome,
        "preco": preco,
        "prioridade": prioridade,
        "loja": (request.form.get("loja") or "").strip(),
        "link": (request.form.get("link") or "").strip(),
        "observacoes": (request.form.get("observacoes") or "").strip(),
    }


@app.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        try:
            dados = ler_formulario()
            dados["foto"] = salvar_foto(request.files.get("foto"))
            db = get_db()
            db.execute(
                """INSERT INTO itens (nome, preco, prioridade, loja, link, observacoes, foto)
                   VALUES (:nome, :preco, :prioridade, :loja, :link, :observacoes, :foto)""",
                dados,
            )
            db.commit()
            flash("Item adicionado à lista.", "ok")
            return redirect(url_for("index"))
        except ValueError as e:
            flash(str(e), "erro")
    return render_template("form.html", item=None, prioridades=PRIORIDADES)


@app.route("/editar/<int:item_id>", methods=["GET", "POST"])
def editar(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM itens WHERE id = ?", (item_id,)).fetchone()
    if item is None:
        flash("Item não encontrado.", "erro")
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            dados = ler_formulario()
            dados["id"] = item_id
            foto = item["foto"]
            nova = salvar_foto(request.files.get("foto"))
            if nova:
                apagar_foto(foto)
                foto = nova
            elif request.form.get("remover_foto"):
                apagar_foto(foto)
                foto = None
            dados["foto"] = foto
            db.execute(
                """UPDATE itens SET nome=:nome, preco=:preco, prioridade=:prioridade,
                   loja=:loja, link=:link, observacoes=:observacoes, foto=:foto
                   WHERE id=:id""",
                dados,
            )
            db.commit()
            flash("Item atualizado.", "ok")
            return redirect(url_for("index"))
        except ValueError as e:
            flash(str(e), "erro")
    return render_template("form.html", item=item, prioridades=PRIORIDADES)


@app.route("/comprar/<int:item_id>", methods=["POST"])
def comprar(item_id):
    """Marca como comprado e desconta o valor da banca."""
    db = get_db()
    item = db.execute(
        "SELECT * FROM itens WHERE id = ? AND comprado = 0", (item_id,)
    ).fetchone()
    if item is None:
        return redirect(url_for("index"))
    banca = get_banca()
    if banca < item["preco"]:
        flash("Sua banca ainda não cobre esse item.", "erro")
        return redirect(url_for("index"))
    set_banca(round(banca - item["preco"], 2))
    db.execute("UPDATE itens SET comprado = 1 WHERE id = ?", (item_id,))
    db.commit()
    flash(f"'{item['nome']}' comprado! {fmt_brl(item['preco'])} descontados da banca.", "ok")
    return redirect(url_for("index"))


@app.route("/desfazer/<int:item_id>", methods=["POST"])
def desfazer(item_id):
    """Volta o item para a lista e devolve o valor à banca."""
    db = get_db()
    item = db.execute(
        "SELECT * FROM itens WHERE id = ? AND comprado = 1", (item_id,)
    ).fetchone()
    if item is None:
        return redirect(url_for("index"))
    set_banca(round(get_banca() + item["preco"], 2))
    db.execute("UPDATE itens SET comprado = 0 WHERE id = ?", (item_id,))
    db.commit()
    flash(f"'{item['nome']}' voltou para a lista e o valor foi devolvido à banca.", "ok")
    return redirect(url_for("index"))


@app.route("/excluir/<int:item_id>", methods=["POST"])
def excluir(item_id):
    db = get_db()
    item = db.execute("SELECT foto FROM itens WHERE id = ?", (item_id,)).fetchone()
    if item:
        apagar_foto(item["foto"])
        db.execute("DELETE FROM itens WHERE id = ?", (item_id,))
        db.commit()
        flash("Item removido.", "ok")
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    import sys

    # Porta: `py app.py 5050`, ou variável de ambiente PORT, ou 5000 por padrão
    porta = 5010
    try:
        if len(sys.argv) > 1:
            porta = int(sys.argv[1])
        elif os.environ.get("PORT"):
            porta = int(os.environ["PORT"])
    except ValueError:
        sys.exit("Porta inválida. Exemplo: py app.py 5050")

    print(f"\n  Lista de Desejos rodando em http://127.0.0.1:{porta}\n")
    try:
        app.run(host="127.0.0.1", port=porta, debug=False)
    except OSError:
        sys.exit(f"A porta {porta} já está em uso. Tente outra: py app.py {porta + 1}")
