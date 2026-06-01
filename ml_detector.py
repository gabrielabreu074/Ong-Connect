"""
Detector de voluntários falsos usando Random Forest.
Integrado ao sistema de cadastro de ONGs.
"""

import re
import os
import joblib
import numpy as np
import unicodedata
import random

from difflib import SequenceMatcher
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

# ─── Caminho do modelo ────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "modelo_voluntarios.pkl")

# ─── Listas de referência ─────────────────────────────────────────────────────
DOMINIOS_DESCARTAVEIS = {
    "mailinator.com", "guerrillamail.com", "trashmail.com", "yopmail.com",
    "tempmail.com", "throwam.com", "sharklasers.com", "grr.la", "spam4.me",
    "dispostable.com", "maildrop.cc", "mintemail.com", "fakeinbox.com",
    "10minutemail.com", "tempinbox.com", "mailnull.com", "spamcorpse.com",
    "binkmail.com", "spambog.com", "trashmail.at", "trashmail.io",
    "trashmail.me", "trashmail.net", "discard.email", "getnada.com",
    "tempr.email", "anonaddy.com", "inboxbear.com",
}

NOMES_SUSPEITOS = {
    "teste", "test", "fulano", "ciclano", "beltrano", "asdf", "qwerty",
    "joao silva", "maria silva", "jose silva", "admin", "user", "usuario",
    "anonimo", "anonymous", "fake", "falso", "ninguem", "none", "null",
}

# ONGs com nomes claramente falsos/teste
ONGS_SUSPEITAS = {
    "teste", "test", "ong teste", "nenhuma", "none", "null", "fake",
    "qualquer", "asdf", "qwerty", "ong fake", "admin", "n/a", "na",
}

# DDDs válidos no Brasil (ANATEL)
DDDS_VALIDOS = {
    11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28,
    31, 32, 33, 34, 35, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48, 49,
    51, 53, 54, 55, 61, 62, 63, 64, 65, 66, 67, 68, 69,
    71, 73, 74, 75, 77, 79, 81, 82, 83, 84, 85, 86, 87, 88, 89,
    91, 92, 93, 94, 95, 96, 97, 98, 99,
}

SPAM_PALAVRAS = re.compile(
    r"\b(comprar|vender|venda|produto|promoção|clique aqui|acesse|"
    r"ganhar dinheiro|renda extra|investimento|bitcoin|cripto)\b",
    re.IGNORECASE,
)


# ─── Utilitários ──────────────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    """Minúsculas, sem acento, sem espaços nas bordas."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def _similaridade_max(texto: str, lista: set) -> float:
    return max(
        (SequenceMatcher(None, texto, s).ratio() for s in lista),
        default=0.0,
    )


# ─── Extração de features ─────────────────────────────────────────────────────

def extrair_features(dados: dict) -> list[float]:
    """
    Transforma os campos do formulário em 21 features numéricas para o modelo.
    Campos esperados: nome, email, telefone, ong, mensagem
    """
    nome     = _normalizar(dados.get("nome", ""))
    email    = dados.get("email", "").lower().strip()
    telefone = _so_digitos(dados.get("telefone", ""))
    ong      = _normalizar(dados.get("ong", ""))
    msg      = dados.get("mensagem", "").lower()

    # Remove DDI do Brasil se vier junto (+55 ou 55)
    if telefone.startswith("55") and len(telefone) in (12, 13):
        telefone = telefone[2:]

    dominio      = email.split("@")[1] if "@" in email else ""
    local        = email.split("@")[0] if "@" in email else email
    ddd          = int(telefone[:2]) if len(telefone) >= 2 else 0
    numero       = telefone[2:] if len(telefone) >= 4 else ""
    palavras_msg = msg.split()

    features = [
        # ── Nome ──────────────────────────────────────────────────────────────
        float(len(nome)),                                                        # 0  comprimento do nome
        1.0 if bool(re.search(r"\d", nome)) else 0.0,                           # 1  tem número no nome?
        1.0 if " " in nome else 0.0,                                             # 2  tem sobrenome?
        _similaridade_max(nome, NOMES_SUSPEITOS),                                # 3  parecido com nome suspeito?

        # ── E-mail ────────────────────────────────────────────────────────────
        1.0 if bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)) else 0.0, # 4  formato válido?
        1.0 if dominio in DOMINIOS_DESCARTAVEIS else 0.0,                        # 5  domínio descartável?
        float(len(local)),                                                       # 6  tamanho da parte local
        1.0 if bool(re.fullmatch(r"[a-z]{1,2}\d{4,}", local)) else 0.0,         # 7  parece gerado por bot?

        # ── Telefone ──────────────────────────────────────────────────────────
        1.0 if len(telefone) in (10, 11) else 0.0,                              # 8  tamanho correto?
        1.0 if ddd in DDDS_VALIDOS else 0.0,                                    # 9  DDD existe no Brasil?
        1.0 if (numero and len(set(numero)) == 1) else 0.0,                     # 10 todos dígitos iguais?
        1.0 if numero in ("12345678", "123456789", "987654321") else 0.0,        # 11 sequência óbvia?

        # ── Mensagem ──────────────────────────────────────────────────────────
        1.0 if bool(re.search(r"https?://", msg)) else 0.0,                     # 12 tem link?
        1.0 if bool(SPAM_PALAVRAS.search(msg)) else 0.0,                        # 13 tem palavras de spam?
        (len(set(palavras_msg)) / len(palavras_msg))
            if len(palavras_msg) > 3 else 1.0,                                  # 14 variedade de palavras

        # ── Nome (complementar) ───────────────────────────────────────────────
        float(len(nome.replace(" ", ""))),                                      # 15 letras no nome (sem espaços)
        1.0 if bool(re.fullmatch(r"(.)\1+", nome.replace(" ", ""))) else 0.0,   # 16 nome todo repetido?

        # ── ONG ───────────────────────────────────────────────────────────────
        float(len(ong)),                                                         # 17 comprimento do nome da ONG
        1.0 if " " in ong else 0.0,                                              # 18 ONG tem mais de uma palavra?
        _similaridade_max(ong, ONGS_SUSPEITAS),                                  # 19 ONG parecida com nome suspeito?
        1.0 if bool(re.search(r"\d{3,}", ong)) else 0.0,                        # 20 ONG com sequência de números?
    ]

    return features


# ─── Treinamento ──────────────────────────────────────────────────────────────

def treinar_modelo(registros: list[dict], rotulos: list[int]) -> dict:
    if len(registros) < 10:
        return {
            "erro": "São necessários pelo menos 10 exemplos para treinar.",
            "total": len(registros),
        }

    if len(set(rotulos)) < 2:
        return {"erro": "É necessário ter exemplos de classe 0 e 1."}

    X = np.array([extrair_features(r) for r in registros])
    y = np.array(rotulos)

    modelo = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )

    acuracia_cv = None
    if len(registros) >= 50:
        k      = min(5, len(registros) // 10)
        scores = cross_val_score(modelo, X, y, cv=k, scoring="f1_weighted")
        acuracia_cv = float(round(scores.mean(), 4))

    modelo.fit(X, y)
    joblib.dump(modelo, MODEL_PATH)

    return {
        "mensagem"       : "Modelo treinado com sucesso!",
        "total_exemplos" : len(registros),
        "acuracia_cv"    : acuracia_cv,
        "modelo_salvo"   : MODEL_PATH,
    }


# ─── Predição ─────────────────────────────────────────────────────────────────

def carregar_modelo():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


THRESHOLD = 0.5  # Score acima disso = bloqueado como falso


def _diagnostico(dados: dict, features: list) -> list[str]:
    """Retorna lista de motivos legíveis pelo qual o cadastro foi suspeito."""
    motivos = []

    if features[3] > 0.70:
        motivos.append("Nome muito parecido com nomes suspeitos (ex: 'teste', 'fulano')")
    if features[1] == 1.0:
        motivos.append("Nome contém números")
    if features[16] == 1.0:
        motivos.append("Nome formado por letras repetidas (ex: 'aaaa')")
    if features[2] == 0.0:
        motivos.append("Nome sem sobrenome")
    if features[4] == 0.0:
        motivos.append("E-mail com formato inválido")
    if features[5] == 1.0:
        motivos.append("E-mail usa domínio descartável (ex: mailinator, yopmail)")
    if features[7] == 1.0:
        motivos.append("E-mail parece gerado automaticamente por bot")
    if features[8] == 0.0:
        motivos.append(f"Telefone com tamanho incorreto (esperado 10 ou 11 dígitos, recebido: '{_so_digitos(dados.get('telefone',''))}')")
    if features[9] == 0.0:
        tel = _so_digitos(dados.get("telefone", ""))
        ddd = tel[:2] if len(tel) >= 2 else "??"
        motivos.append(f"DDD '{ddd}' não existe no Brasil")
    if features[10] == 1.0:
        motivos.append("Telefone com todos os dígitos iguais (ex: 99999-9999)")
    if features[11] == 1.0:
        motivos.append("Telefone com sequência óbvia (ex: 12345-6789)")
    if features[12] == 1.0:
        motivos.append("Mensagem contém link (URL)")
    if features[13] == 1.0:
        motivos.append("Mensagem contém palavras de spam (bitcoin, venda, renda extra...)")
    if features[19] > 0.70:
        motivos.append("Nome da ONG parece falso ou genérico")

    return motivos


def prever(dados: dict) -> dict:
    """
    Recebe um dict com nome, email, telefone, ong, mensagem.
    Retorna score_ml, predicao, confianca, aprovado, modelo_usado, motivos.
    """
    modelo   = carregar_modelo()
    features = extrair_features(dados)
    features_arr = np.array([features])

    if modelo is None:
        score  = _score_heuristico_fallback(dados)
        falso  = score >= THRESHOLD
        return {
            "score_ml"    : round(score, 4),
            "predicao"    : "falso" if falso else "real",
            "confianca"   : round(abs(score - THRESHOLD) * 2, 4),
            "aprovado"    : not falso,
            "modelo_usado": False,
            "motivos"     : _diagnostico(dados, features) if falso else [],
            "aviso"       : "Usando fallback heurístico (modelo ainda não treinado)",
        }

    proba      = modelo.predict_proba(features_arr)[0]
    idx_falso  = list(modelo.classes_).index(1)
    prob_falso = float(proba[idx_falso])
    falso      = prob_falso >= THRESHOLD

    return {
        "score_ml"    : round(prob_falso, 4),
        "predicao"    : "falso" if falso else "real",
        "confianca"   : round(abs(prob_falso - THRESHOLD) * 2, 4),
        "aprovado"    : not falso,
        "modelo_usado": True,
        "motivos"     : _diagnostico(dados, features) if falso else [],
    }


# ─── Importância das features ─────────────────────────────────────────────────

def importancia_features() -> dict:
    modelo = carregar_modelo()
    if modelo is None:
        return {"erro": "Modelo não treinado ainda."}

    nomes = [
        "nome_len", "nome_numero", "nome_sobrenome", "nome_similaridade",
        "email_valido", "email_descartavel", "email_local_len", "email_bot",
        "tel_ok", "tel_ddd", "tel_repetido", "tel_sequencial",
        "msg_url", "msg_spam", "msg_diversidade",
        "nome_letras", "nome_repetido",
        "ong_len", "ong_palavras", "ong_similaridade", "ong_numeros",
    ]

    ranking = sorted(
        zip(nomes, modelo.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "ranking": [
            {"feature": n, "importancia": float(round(i, 4))}
            for n, i in ranking
        ]
    }


# ─── Fallback heurístico ──────────────────────────────────────────────────────

def _score_heuristico_fallback(dados: dict) -> float:
    f = extrair_features(dados)

    penalidades = 0.0
    if f[8]  == 0.0: penalidades += 1.00  # telefone com tamanho errado
    if f[9]  == 0.0: penalidades += 1.00  # DDD inválido
    if f[10] == 1.0: penalidades += 0.50  # dígitos todos iguais
    if f[5]  == 1.0: penalidades += 1.00  # domínio descartável
    if f[4]  == 0.0: penalidades += 0.60  # email com formato inválido
    if f[2]  == 0.0: penalidades += 0.40  # sem sobrenome
    if f[3]  > 0.70: penalidades += 0.70  # nome muito parecido com lista suspeita
    if f[19] > 0.70: penalidades += 0.50  # ONG suspeita
    if f[17] < 3.0 : penalidades += 0.30  # nome de ONG muito curto

    return min(penalidades / 4.0, 1.0)





# ─── Dados sintéticos para pré-treino ─────────────────────────────────────────

def gerar_dados_sinteticos() -> tuple[list[dict], list[int]]:
    """
    Gera exemplos balanceados de cadastros reais e falsos
    para pré-treinar o modelo sem precisar de dados reais.
    """

    nomes_reais = [
        "Ana Paula Ferreira", "Carlos Eduardo Souza", "Mariana Lima Costa",
        "Roberto Alves Pereira", "Fernanda Oliveira Santos", "Lucas Mendes Rodrigues",
        "Juliana Nascimento Silva", "Paulo Henrique Carvalho", "Beatriz Rocha Martins",
        "Gabriel Araujo Ribeiro", "Camila Dias Goncalves", "Diego Vieira Barbosa",
        "Larissa Cunha Monteiro", "Rafael Teixeira Cardoso", "Priscila Moura Freitas",
        "Thiago Lopes Cavalcanti", "Amanda Pinto Correia", "Bruno Azevedo Moreira",
        "Vanessa Campos Nunes", "Rodrigo Farias Melo",
    ]

    nomes_falsos = [
        "teste", "Teste Teste", "asdf qwer", "fulano de tal", "aaaaaa bbbbbb",
        "user123", "admin admin", "fake user", "joao silva", "maria silva",
        "Jose Silva", "nome sobrenome", "aaaa bbbb", "xpto xpto", "null null",
        "zzzzzz", "123456 789", "anon anonimo", "ninguem nenhum", "tt tt", "djfsdf dffsdfs",
        "sdfsdj ueeom", "qwerty asdfgh", "abc abc", "test test", "fake fake", "saaasaaa fwefv", 
        "efjsndfksdfsdf sdfsd", "asdf asdf", "qwer qwer", "zxcv zxcv", "aaaaaa aaaaaa", "bbbbbb bbbbbb",
    ]

    emails_reais = [
        "ana.ferreira@gmail.com", "carlos.souza@hotmail.com", "mariana.costa@yahoo.com",
        "roberto.pereira@outlook.com", "fernanda.santos@gmail.com",
        "lucas.rodrigues@hotmail.com", "juliana.silva@yahoo.com",
        "paulo.carvalho@gmail.com", "beatriz.martins@outlook.com",
        "gabriel.ribeiro@gmail.com", "camila.goncalves@hotmail.com",
        "diego.barbosa@gmail.com", "larissa.monteiro@yahoo.com",
        "rafael.cardoso@outlook.com", "priscila.freitas@gmail.com",
        "thiago.cavalcanti@hotmail.com", "amanda.correia@gmail.com",
        "bruno.moreira@yahoo.com", "vanessa.nunes@outlook.com",
        "rodrigo.melo@gmail.com",
    ]

    emails_falsos = [
        "test@mailinator.com", "fake@guerrillamail.com", "spam@yopmail.com",
        "a1234@trashmail.com", "b9876@tempmail.com", "x123@throwam.com",
        "asdf@fakeinbox.com", "zz@10minutemail.com", "aa@spambog.com",
        "temp@getnada.com", "bot@discard.email", "trash@maildrop.cc",
        "x@x.com", "a@b.c", "123@456.com", "noreply@fake.net",
        "void@null.com", "noone@nowhere.org", "q1w2e3@trashmail.io",
        "abc123@sharklasers.com", "dgagfaugfia172@gmail.com",
        "naoexisto29783@gmai.com", "xkqwzmn88@gmail.com",
        "bvrtplxk91@hotmail.com", "wqzxmnbv44@outlook.com",
        "1234567890@gmail.com", "9988776655@hotmail.com",
        "abcdefghijklmnopqrstu@gmail.com", "randomrandomrandomrr1@gmail.com",
        "spamspamspam129875@hotmail.com",
    ]

    telefones_reais = [
        "11987654321", "21976543210", "31965432109", "41954321098",
        "51943210987", "61932109876", "71921098765", "81910987654",
        "91909876543", "11876543210", "21865432109", "31854321098",
        "41843210987", "51832109876", "61821098765", "71810987654",
        "81809876543", "91898765432", "11987123456", "21976234567",
    ]

    telefones_falsos = [
        "11900000000", "11911111111", "11922222222", "21901234567",
        "31912121212", "41900011122", "51911111112", "61900000001",
        "71900000000", "81912345678", "85912340000", "92900000000",
        "98912345678", "62911111111", "67900000000", "1133334444",
        "2122223333", "3133334444", "4133334444", "5133334444",
    ]

    ongs_reais = [
        "Lar dos Anjos", "Instituto Esperança", "Fundação Vida Nova",
        "Associação Mãos Solidárias", "ONG Recomeço", "Projeto Semente",
        "Casa da Criança Feliz", "Centro Comunitário Luz", "Abrigo São Francisco",
        "Instituto Novo Horizonte", "Associação Bem Querer", "Fundação Caminhos",
        "ONG Raízes", "Projeto Florescer", "Centro de Apoio Familiar",
        "Instituto Cidadania Ativa", "Lar Esperança Viva", "ONG Mãe Terra",
        "Fundação Passos de Luz", "Associação Renascer",
    ]

    ongs_falsas = [
        "teste", "ong teste", "nenhuma", "fake", "asdf", "qwerty",
        "n/a", "na", "admin", "null", "ong fake", "qualquer",
        "123", "ong 123", "xpto", "abc", "tt", "zz", "aa bb", "ff gg",
    ]

    mensagens_reais = [
        "Quero ajudar crianças carentes da minha cidade.",
        "Tenho experiência com trabalho voluntário em abrigos.",
        "Gostaria de contribuir com meu tempo livre aos fins de semana.",
        "Sou estudante de pedagogia e quero ajudar em projetos educacionais.",
        "Tenho disponibilidade nas tardes e quero fazer a diferença.",
        "Já fui voluntário em outras ONGs e quero continuar.",
        "Me interesso por causas ambientais e gostaria de participar.",
        "Quero ajudar idosos e tenho experiência como cuidador.",
        "Sou formada em nutrição e posso colaborar com projetos alimentares.",
        "Tenho carro e posso ajudar com transporte de doações.",
        "", "", "", "", "",
    ]

    mensagens_falsas = [
        "Compre agora! Acesse http://spam.com e ganhe dinheiro!",
        "Renda extra garantida! Bitcoin e cripto investimento seguro.",
        "Clique aqui para ganhar dinheiro fácil! http://fraude.net",
        "Venda produtos e ganhe comissão. Acesse já!",
        "Promoção imperdível! Invista em cripto agora.",
        "http://malware.com clique aqui urgente!!!",
        "ganhar dinheiro facil sem sair de casa investimento bitcoin",
        "venda venda venda produto promoção acesse já",
        "https://phishing.com/login confirme seus dados agora",
        "renda extra todos os dias bitcoin cripto investimento",
    ]

    registros, rotulos = [], []

    for _ in range(60):
        registros.append({
            "nome"     : random.choice(nomes_reais),
            "email"    : random.choice(emails_reais),
            "telefone" : random.choice(telefones_reais),
            "ong"      : random.choice(ongs_reais),
            "mensagem" : random.choice(mensagens_reais),
        })
        rotulos.append(0)  # real

    for _ in range(60):
        registros.append({
            "nome"     : random.choice(nomes_falsos),
            "email"    : random.choice(emails_falsos),
            "telefone" : random.choice(telefones_falsos),
            "ong"      : random.choice(ongs_falsas),
            "mensagem" : random.choice(mensagens_falsas),
        })
        rotulos.append(1)  # falso

    return registros, rotulos


# ─── Inicialização ────────────────────────────────────────────────────────────

def inicializar_modelo():
    """Treina com dados sintéticos se o modelo ainda não existir."""
    if not os.path.exists(MODEL_PATH):
        print("[ML] Modelo não encontrado. Treinando com dados sintéticos...")
        registros, rotulos = gerar_dados_sinteticos()
        resultado = treinar_modelo(registros, rotulos)
        print(f"[ML] {resultado.get('mensagem', resultado.get('erro'))}")
    else:
        print("[ML] Modelo carregado com sucesso.")


inicializar_modelo()