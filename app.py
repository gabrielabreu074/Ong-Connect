from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os

from ml_detector import prever, importancia_features

app = Flask(__name__, static_folder='public', static_url_path='')

# ── Banco de dados ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS voluntarios (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                nome            TEXT    NOT NULL,
                email           TEXT    NOT NULL,
                telefone        TEXT    NOT NULL,
                ong             TEXT    NOT NULL,
                mensagem        TEXT,
                score_ml        REAL    DEFAULT NULL,
                predicao_ml     TEXT    DEFAULT NULL,
                modelo_usado    INTEGER DEFAULT 0
            )
        ''')
        conn.commit()


init_db()


def _campos_obrigatorios(dados: dict) -> bool:
    return all(dados.get(c) for c in ("nome", "email", "telefone", "ong"))


# ── Rotas da API ──────────────────────────────────────────────────────────────

@app.route('/api/voluntarios', methods=['GET'])
def listar_voluntarios():
    conn     = get_db()
    predicao = request.args.get('predicao')
    so_sus   = request.args.get('apenas_suspeitos')

    if predicao:
        rows = conn.execute(
            'SELECT * FROM voluntarios WHERE predicao_ml = ? ORDER BY score_ml DESC',
            (predicao,)
        ).fetchall()
    elif so_sus:
        rows = conn.execute(
            "SELECT * FROM voluntarios WHERE predicao_ml = 'falso' ORDER BY score_ml DESC"
        ).fetchall()
    else:
        rows = conn.execute('SELECT * FROM voluntarios ORDER BY id').fetchall()

    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/voluntarios', methods=['POST'])
def cadastrar_voluntario():
    dados = request.get_json()

    if not _campos_obrigatorios(dados):
        return jsonify({'erro': 'Campos obrigatórios faltando.'}), 400

    resultado = prever(dados)

    if not resultado['aprovado']:
        return jsonify({
            'erro': 'Cadastro bloqueado pelo detector de voluntários falsos.',
            'ml'  : resultado,
        }), 422

    conn = get_db()
    conn.execute('''
        INSERT INTO voluntarios
            (nome, email, telefone, ong, mensagem,
             score_ml, predicao_ml, modelo_usado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados['nome'], dados['email'], dados['telefone'],
        dados['ong'],  dados.get('mensagem', ''),
        resultado['score_ml'],
        resultado['predicao'],
        1 if resultado['modelo_usado'] else 0,
    ))
    conn.commit()
    conn.close()
    return jsonify({'mensagem': 'Cadastro realizado!', 'ml': resultado}), 201


@app.route('/api/voluntarios/<int:id>', methods=['PUT'])
def editar_voluntario(id):
    dados = request.get_json()
    conn  = get_db()

    if not conn.execute('SELECT id FROM voluntarios WHERE id = ?', (id,)).fetchone():
        conn.close()
        return jsonify({'erro': 'Voluntário não encontrado.'}), 404

    resultado = prever(dados)

    if not resultado['aprovado']:
        conn.close()
        return jsonify({
            'erro': 'Atualização bloqueada pelo detector.',
            'ml'  : resultado,
        }), 422

    conn.execute('''
        UPDATE voluntarios
        SET nome=?, email=?, telefone=?, ong=?, mensagem=?,
            score_ml=?, predicao_ml=?, modelo_usado=?
        WHERE id=?
    ''', (
        dados.get('nome'), dados.get('email'),
        dados.get('telefone'), dados.get('ong'),
        dados.get('mensagem', ''),
        resultado['score_ml'], resultado['predicao'],
        1 if resultado['modelo_usado'] else 0,
        id,
    ))
    conn.commit()
    conn.close()
    return jsonify({'mensagem': 'Dados atualizados!', 'ml': resultado})


@app.route('/api/voluntarios/<int:id>', methods=['DELETE'])
def excluir_voluntario(id):
    conn = get_db()
    if not conn.execute('SELECT id FROM voluntarios WHERE id = ?', (id,)).fetchone():
        conn.close()
        return jsonify({'erro': 'Voluntário não encontrado.'}), 404
    conn.execute('DELETE FROM voluntarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'mensagem': 'Excluído com sucesso!'})


# ── Rotas de Machine Learning ─────────────────────────────────────────────────

@app.route('/api/ml/prever', methods=['POST'])
def prever_externo():
    """Testa o modelo com dados avulsos sem salvar no banco."""
    dados = request.get_json()
    if not _campos_obrigatorios(dados):
        return jsonify({'erro': 'Campos obrigatórios faltando.'}), 400
    return jsonify(prever(dados))


@app.route('/api/ml/importancia', methods=['GET'])
def importancia():
    """Mostra quais características mais influenciam o modelo."""
    return jsonify(importancia_features())


@app.route('/api/ml/status', methods=['GET'])
def status_ml():
    """Resumo do estado atual do modelo."""
    from ml_detector import MODEL_PATH

    conn        = get_db()
    total       = conn.execute("SELECT COUNT(*) FROM voluntarios").fetchone()[0]
    falsos_pred = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE predicao_ml='falso'").fetchone()[0]
    reais_pred  = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE predicao_ml='real'").fetchone()[0]
    conn.close()

    modelo_existe = os.path.exists(MODEL_PATH)
    modelo_kb     = round(os.path.getsize(MODEL_PATH) / 1024, 1) if modelo_existe else 0

    return jsonify({
        'modelo_treinado'  : modelo_existe,
        'modelo_tamanho_kb': modelo_kb,
        'total_voluntarios': total,
        'preditos_falsos'  : falsos_pred,
        'preditos_reais'   : reais_pred,
    })


@app.route('/api/voluntarios/estatisticas', methods=['GET'])
def estatisticas():
    conn = get_db()
    total        = conn.execute("SELECT COUNT(*) FROM voluntarios").fetchone()[0]
    reais        = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE predicao_ml='real'").fetchone()[0]
    falsos       = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE predicao_ml='falso'").fetchone()[0]
    sem_predicao = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE predicao_ml IS NULL").fetchone()[0]
    conn.close()
    return jsonify({'total': total, 'reais': reais, 'falsos': falsos, 'sem_predicao': sem_predicao})


# ── Front-end ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('public/html', 'index.html')

@app.route('/<path:filename>.html')
def serve_html(filename):
    return send_from_directory('public/html', f'{filename}.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)