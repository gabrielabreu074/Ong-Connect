"""
Detector de voluntários falsos usando Random Forest.
"""
import re
import os
import joblib
import numpy as np
import unicodedata

from difflib import SequenceMatcher
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

# ─── Caminho do modelo ───────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "modelo_voluntarios.pkl")

# Lista de emails 
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

# DDDs reais do Brasil segundo a ANATEL.
DDDS_VALIDOS = {
    # SP
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    # RJ
    21, 22, 24,
    # ES
    27, 28,
    # MG
    31, 32, 33, 34, 35, 37, 38,
    # PR
    41, 42, 43, 44, 45, 46,
    # SC
    47, 48, 49,
    # RS
    51, 53, 54, 55,
    # DF
    61,
    # GO
    62, 64,
    # TO
    63,
    # MT
    65, 66,
    # MS
    67,
    # AC
    68,
    # RO
    69,
    # SE
    79,
    # BA
    71, 73, 74, 75, 77,
    # PE
    81, 87,
    # AL
    82,
    # PB
    83,
    # RN
    84,
    # CE
    85, 88,
    # PI
    86, 89,
    # PA
    91, 93, 94,
    # AM
    92, 97,
    # AP
    96,
    # RR
    95,
    # MA
    98, 99,
}

SPAM_PALAVRAS = re.compile(
    r"\b(comprar|vender|venda|produto|promoção|clique aqui|acesse|"
    r"ganhar dinheiro|renda extra|investimento|bitcoin|cripto)\b",
    re.IGNORECASE,
)


"""
Converte todos os caracteres Maiúsculos em Minúsculos, tira os acentos e remove espaços na borda

"""

def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def _similaridade_max(texto: str, lista: set) -> float:
    return max((SequenceMatcher(None, texto, s).ratio() for s in lista), default=0.0)


"""
Transforma todos os caracteres em números, já que o ML só entende números.
"""

def extrair_features(dados: dict) -> list[float]:
    nome     = _normalizar(dados.get("nome", ""))
    email    = dados.get("email", "").lower().strip()
    telefone = _so_digitos(dados.get("telefone", ""))
    msg      = dados.get("mensagem", "").lower()

    # Remove DDI do Brasil se vier junto
    if telefone.startswith("55") and len(telefone) in (12, 13):
        telefone = telefone[2:]

    dominio = email.split("@")[1] if "@" in email else ""
    local   = email.split("@")[0] if "@" in email else email

    ddd    = int(telefone[:2]) if len(telefone) >= 2 else 0
    numero = telefone[2:] if len(telefone) >= 4 else ""
    palavras_msg = msg.split()

    features = [
        # NOME (4) — removida feature "nome_dupla" (\se\s) por ser inútil na prática
        len(nome),                                                          # comprimento do nome
        1.0 if bool(re.search(r"\d", nome)) else 0.0,                      # tem número no nome?
        1.0 if " " in nome else 0.0,                                       # tem sobrenome?
        _similaridade_max(nome, NOMES_SUSPEITOS),                          # parecido com nome suspeito?

        # EMAIL (4)
        1.0 if bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)) else 0.0,  # formato válido?
        1.0 if dominio in DOMINIOS_DESCARTAVEIS else 0.0,                  # domínio descartável?
        len(local),                                                         # tamanho da parte local
        1.0 if bool(re.fullmatch(r"[a-z]{1,2}\d{4,}", local)) else 0.0,  # parece gerado por bot?

        # TELEFONE (4)
        1.0 if len(telefone) in (10, 11) else 0.0,                        # tamanho correto?
        1.0 if ddd in DDDS_VALIDOS else 0.0,                              # DDD existe no Brasil?
        1.0 if (numero and len(set(numero)) == 1) else 0.0,               # todos dígitos iguais? (ex: 99999999)
        1.0 if numero in ("12345678", "123456789", "987654321") else 0.0,  # sequência óbvia?

        # MENSAGEM (3)
        1.0 if bool(re.search(r"https?://", msg)) else 0.0,               # tem link?
        1.0 if bool(SPAM_PALAVRAS.search(msg)) else 0.0,                  # tem palavras de spam?
        (len(set(palavras_msg)) / len(palavras_msg)) if len(palavras_msg) > 3 else 1.0,  # variedade de palavras

        # GERAL (2)
        float(len(nome.replace(" ", ""))),                                 # letras no nome (sem espaços)
        1.0 if bool(re.fullmatch(r"(.)\1+", nome.replace(" ", ""))) else 0.0,  # nome todo repetido? (ex: "aaaa")
    ]

    return features


# ─────────────────────────────────────────────────────────────
# MODELO
# ─────────────────────────────────────────────────────────────

def treinar_modelo(registros: list[dict], rotulos: list[int]) -> dict:
    if len(registros) < 10:
        return {
            "erro": "São necessários pelo menos 10 exemplos para treinar o modelo.",
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
    # Cross-validation só vale a pena com dados suficientes
    if len(registros) >= 50:
        k = min(5, len(registros) // 10)
        scores = cross_val_score(modelo, X, y, cv=k, scoring="f1_weighted")
        acuracia_cv = float(round(scores.mean(), 4))

    modelo.fit(X, y)
    joblib.dump(modelo, MODEL_PATH)

    return {
        "mensagem": "Modelo treinado com sucesso!",
        "total_exemplos": len(registros),
        "acuracia_cv": acuracia_cv,
        "modelo_salvo": MODEL_PATH,
    }


def carregar_modelo():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def prever(dados: dict) -> dict:
    modelo   = carregar_modelo()
    features = np.array([extrair_features(dados)])

    if modelo is None:
        score = _score_heuristico_fallback(dados)
        return {
            "score_ml":    round(score, 4),
            "predicao":    "falso" if score >= 0.5 else "real",
            "confianca":   round(abs(score - 0.5) * 2, 4),
            "aprovado":    score < 0.5,
            "modelo_usado": False,
            "aviso":       "Usando fallback (modelo ainda não treinado)",
        }

    proba     = modelo.predict_proba(features)[0]
    idx_falso = list(modelo.classes_).index(1)
    prob_falso = float(proba[idx_falso])

    return {
        "score_ml":    round(prob_falso, 4),
        "predicao":    "falso" if prob_falso >= 0.5 else "real",
        "confianca":   round(abs(prob_falso - 0.5) * 2, 4),
        "aprovado":    prob_falso < 0.5,
        "modelo_usado": True,
    }


def importancia_features() -> dict:
    modelo = carregar_modelo()
    if modelo is None:
        return {"erro": "Modelo não treinado"}

    nomes = [
        "nome_len", "nome_numero", "nome_sobrenome", "nome_similaridade",
        "email_valido", "email_descartavel", "email_local_len", "email_bot",
        "tel_ok", "tel_ddd", "tel_repetido", "tel_sequencial",
        "msg_url", "msg_spam", "msg_diversidade",
        "nome_letras", "nome_repetido",
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


"""
Fallback Heurístico, vai ser usado quando o modelo de ML ainda não foi treinado, como por exemplo acabamos de instalar o sistema e não temos 
exemplos rotulados suficientes para treinar o Random Forest.
""" 

def _score_heuristico_fallback(dados: dict) -> float:
    f = extrair_features(dados)

    penalidades = 0.0

    if f[8]  == 0.0: penalidades += 0.30   # telefone com tamanho errado
    if f[9]  == 0.0: penalidades += 0.50   # DDD inválido
    if f[10] == 1.0: penalidades += 0.45   # dígitos todos iguais
    if f[5]  == 1.0: penalidades += 0.45   # domínio descartável
    if f[4]  == 0.0: penalidades += 0.20   # email com formato inválido
    if f[2]  == 0.0: penalidades += 0.20   # sem sobrenome
    if f[3]  > 0.70: penalidades += 0.50   # nome muito parecido com lista suspeita

    return min(penalidades, 1.0)