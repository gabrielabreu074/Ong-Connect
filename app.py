from flask import Flask, request, jsonify, send_from_directory
from contextlib import contextmanager
import sqlite3, json, os

from ml_detector import prever

app = Flask(__name__, static_folder='public', static_url_path='')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')

# ── Banco ─────────────────────────────────────────────────────────────────────
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS voluntarios (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                nome       TEXT NOT NULL,
                email      TEXT NOT NULL,
                telefone   TEXT NOT NULL,
                ong        TEXT NOT NULL,
                mensagem   TEXT,
                score_ml   REAL DEFAULT NULL,
                alertas_ml TEXT DEFAULT NULL,
                motivo_ml  TEXT DEFAULT NULL
            )
        ''')
        for col, tipo in [("alertas_ml", "TEXT"), ("motivo_ml", "TEXT")]:
            try:
                conn.execute(f"ALTER TABLE voluntarios ADD COLUMN {col} {tipo} DEFAULT NULL")
            except Exception:
                pass
        conn.commit()

init_db()

def _campos_obrigatorios(dados):
    return all(dados.get(c) for c in ("nome", "email", "telefone", "ong"))

# ── Rotas ─────────────────────────────────────────────────────────────────────
@app.route('/api/voluntarios', methods=['GET'])
def listar_voluntarios():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM voluntarios ORDER BY id').fetchall()

    resultado = []
    for r in rows:
        v = dict(r)
        v['motivo']  = v.pop('motivo_ml', None)
        alertas_raw  = v.pop('alertas_ml', '[]')
        v['alertas'] = json.loads(alertas_raw) if alertas_raw else []
        for campo in ('predicao_ml', 'modelo_usado', 'nivel_suspeita',
                      'alertas_detector', 'score_suspeita', 'rotulo_manual', 'confianca'):
            v.pop(campo, None)
        resultado.append(v)

    return jsonify(resultado)

@app.route('/api/voluntarios', methods=['POST'])
def cadastrar_voluntario():
    dados = request.get_json()
    if not _campos_obrigatorios(dados):
        return jsonify({'erro': 'Campos obrigatórios faltando.'}), 400

    resultado = prever(dados)

    with get_db() as conn:
        conn.execute('''
            INSERT INTO voluntarios
                (nome, email, telefone, ong, mensagem, score_ml, alertas_ml, motivo_ml)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            dados['nome'], dados['email'], dados['telefone'], dados['ong'],
            dados.get('mensagem', ''),
            resultado['score_ml'],
            json.dumps(resultado.get('alertas', []), ensure_ascii=False),
            resultado.get('motivo', ''),
        ))
        conn.commit()

    return jsonify({'mensagem': 'Cadastro realizado com sucesso!', 'ml': resultado}), 201

@app.route('/api/voluntarios/<int:id>', methods=['PUT'])
def editar_voluntario(id):
    dados = request.get_json()
    resultado = prever(dados)

    with get_db() as conn:
        row = conn.execute('SELECT id FROM voluntarios WHERE id = ?', (id,)).fetchone()
        if not row:
            return jsonify({'erro': 'Voluntário não encontrado.'}), 404

        conn.execute('''
            UPDATE voluntarios
            SET nome=?, email=?, telefone=?, ong=?, mensagem=?,
                score_ml=?, alertas_ml=?, motivo_ml=?
            WHERE id=?
        ''', (
            dados.get('nome'), dados.get('email'),
            dados.get('telefone'), dados.get('ong'),
            dados.get('mensagem', ''),
            resultado['score_ml'],
            json.dumps(resultado.get('alertas', []), ensure_ascii=False),
            resultado.get('motivo', ''),
            id,
        ))
        conn.commit()

    return jsonify({'mensagem': 'Dados atualizados!', 'ml': resultado})

@app.route('/api/voluntarios/<int:id>', methods=['DELETE'])
def excluir_voluntario(id):
    with get_db() as conn:
        if not conn.execute('SELECT id FROM voluntarios WHERE id = ?', (id,)).fetchone():
            return jsonify({'erro': 'Voluntário não encontrado.'}), 404
        conn.execute('DELETE FROM voluntarios WHERE id = ?', (id,))
        conn.commit()
    return jsonify({'mensagem': 'Excluído com sucesso!'})

@app.route('/api/voluntarios/estatisticas', methods=['GET'])
def estatisticas():
    with get_db() as conn:
        total  = conn.execute("SELECT COUNT(*) FROM voluntarios").fetchone()[0]
        # score_ml >= 0.55 equivale à predição "real" (conforme ml_detector.py)
        reais  = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE score_ml >= 0.55").fetchone()[0]
        falsos = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE score_ml < 0.55").fetchone()[0]
    return jsonify({'total': total, 'reais': reais, 'falsos': falsos})

# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/')
def index():
    return send_from_directory('public/html', 'index.html')

@app.route('/<path:filename>.html')
def serve_html(filename):
    return send_from_directory('public/html', f'{filename}.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)