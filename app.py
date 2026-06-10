from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import json
import os

from ml_detector import prever

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
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nome         TEXT NOT NULL,
            email        TEXT NOT NULL,
            telefone     TEXT NOT NULL,
            ong          TEXT NOT NULL,
            mensagem     TEXT,
            score_ml     REAL DEFAULT NULL,
            alertas_ml   TEXT DEFAULT NULL,
            motivo_ml    TEXT DEFAULT NULL
)
        ''')
        # Migração segura: adiciona colunas novas se o banco já existia
        for col, tipo in [("alertas_ml", "TEXT"), ("motivo_ml", "TEXT")]:
            try:
                conn.execute(f"ALTER TABLE voluntarios ADD COLUMN {col} {tipo} DEFAULT NULL")
            except Exception:
                pass  # coluna já existe
        conn.commit()


init_db()


def _campos_obrigatorios(dados: dict) -> bool:
    return all(dados.get(c) for c in ("nome", "email", "telefone", "ong"))


# ── Rotas da API ──────────────────────────────────────────────────────────────

@app.route('/api/voluntarios', methods=['GET'])
def listar_voluntarios():
    conn  = get_db()
    rows  = conn.execute('SELECT * FROM voluntarios ORDER BY id').fetchall()
    conn.close()

    resultado = []
    for r in rows:
        v = dict(r)

        # Renomeia campos ML
        v.pop('predicao_ml', None)
        v['motivo'] = v.pop('motivo_ml', None)
        alertas_raw   = v.pop('alertas_ml', '[]')
        v['alertas']  = json.loads(alertas_raw) if alertas_raw else []

        # Remove colunas antigas do banco que não são mais usadas
        for campo_antigo in ('modelo_usado', 'nivel_suspeita', 'alertas_detector',
                             'score_suspeita', 'rotulo_manual', 'confianca'):
            v.pop(campo_antigo, None)

        resultado.append(v)

    return jsonify(resultado)
@app.route('/api/voluntarios', methods=['POST'])
def cadastrar_voluntario():
    dados = request.get_json()

    if not _campos_obrigatorios(dados):
        return jsonify({'erro': 'Campos obrigatórios faltando.'}), 400

    resultado = prever(dados)

    conn = get_db()
    conn.execute('''
        INSERT INTO voluntarios
            (nome, email, telefone, ong, mensagem,
             score_ml, alertas_ml, motivo_ml)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados['nome'],
        dados['email'],
        dados['telefone'],
        dados['ong'],
        dados.get('mensagem', ''),
        resultado['score_ml'],
        json.dumps(resultado.get('alertas', []), ensure_ascii=False),
        resultado.get('motivo', ''),
    ))
    conn.commit()
    conn.close()

    return jsonify({'mensagem': 'Cadastro realizado com sucesso!', 'ml': resultado}), 201

@app.route('/api/voluntarios/<int:id>', methods=['PUT'])
def editar_voluntario(id):
    dados = request.get_json()
    conn  = get_db()

    if not conn.execute('SELECT id FROM voluntarios WHERE id = ?', (id,)).fetchone():
        conn.close()
        return jsonify({'erro': 'Voluntário não encontrado.'}), 404

    resultado = prever(dados)

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


# ── Estatísticas (opcional, caso o admin use) ─────────────────────────────────

@app.route('/api/voluntarios/estatisticas', methods=['GET'])
def estatisticas():
    conn = get_db()
    total  = conn.execute("SELECT COUNT(*) FROM voluntarios").fetchone()[0]
    reais  = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE predicao_ml='real'").fetchone()[0]
    falsos = conn.execute("SELECT COUNT(*) FROM voluntarios WHERE predicao_ml='falso'").fetchone()[0]
    conn.close()
    return jsonify({'total': total, 'reais': reais, 'falsos': falsos})


# ── Front-end ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    caminho = os.path.join(BASE_DIR, 'public', 'html')

    if not os.path.exists(os.path.join(caminho, 'index.html')):
        return "API funcionando!", 200

    return send_from_directory(caminho, 'index.html')

@app.route('/<path:filename>.html')
def serve_html(filename):
    return send_from_directory('public/html', f'{filename}.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)