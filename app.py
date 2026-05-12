from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder='public', static_url_path='')

# ===== CAMINHO CORRETO DO BANCO =====
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                telefone TEXT NOT NULL,
                ong TEXT NOT NULL,
                mensagem TEXT
            )
        ''')
        conn.commit()

init_db()

# ---------- ROTAS DA API ----------
@app.route('/api/voluntarios', methods=['GET'])
def listar_voluntarios():
    conn = get_db()
    voluntarios = conn.execute('SELECT * FROM voluntarios ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(v) for v in voluntarios])

@app.route('/api/voluntarios', methods=['POST'])
def cadastrar_voluntario():
    dados = request.get_json()

    nome = dados.get('nome')
    email = dados.get('email')
    telefone = dados.get('telefone')
    ong = dados.get('ong')
    mensagem = dados.get('mensagem', '')

    if not all([nome, email, telefone, ong]):
        return jsonify({'erro': 'Campos obrigatórios faltando.'}), 400

    conn = get_db()
    cursor = conn.execute('''
        INSERT INTO voluntarios (nome, email, telefone, ong, mensagem)
        VALUES (?, ?, ?, ?, ?)
    ''', (nome, email, telefone, ong, mensagem))

    conn.commit()
    conn.close()

    return jsonify({'mensagem': 'Cadastro realizado!'}), 201

@app.route('/api/voluntarios/<int:id>', methods=['PUT'])
def editar_voluntario(id):
    dados = request.get_json()

    conn = get_db()
    voluntario = conn.execute('SELECT * FROM voluntarios WHERE id = ?', (id,)).fetchone()

    if not voluntario:
        conn.close()
        return jsonify({'erro': 'Voluntário não encontrado.'}), 404

    conn.execute('''
        UPDATE voluntarios
        SET nome = ?, email = ?, telefone = ?, ong = ?, mensagem = ?
        WHERE id = ?
    ''', (
        dados.get('nome'),
        dados.get('email'),
        dados.get('telefone'),
        dados.get('ong'),
        dados.get('mensagem', ''),
        id
    ))

    conn.commit()
    conn.close()

    return jsonify({'mensagem': 'Dados atualizados!'})

@app.route('/api/voluntarios/<int:id>', methods=['DELETE'])
def excluir_voluntario(id):
    conn = get_db()

    voluntario = conn.execute('SELECT * FROM voluntarios WHERE id = ?', (id,)).fetchone()
    if not voluntario:
        conn.close()
        return jsonify({'erro': 'Voluntário não encontrado.'}), 404

    conn.execute('DELETE FROM voluntarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return jsonify({'mensagem': 'Excluído com sucesso!'})

# ---------- FRONT ----------
@app.route('/')
def index():
    return send_from_directory('public/html', 'index.html')

@app.route('/<path:filename>.html')
def serve_html(filename):
    return send_from_directory('public/html', f'{filename}.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)