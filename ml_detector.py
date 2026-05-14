"""
ml_detector.py
--------------
Detector de voluntários falsos usando Machine Learning (Random Forest).

Fluxo:
  1. Extrai features numéricas de cada cadastro
  2. Treina um RandomForestClassifier com os dados rotulados
  3. Prediz se um novo cadastro é falso ou real
  4. Persiste o modelo em disco (modelo.pkl)

Rótulos:
  0 = real/confiável
  1 = falso/suspeito
"""

import re
import os
import json
import unicodedata
import joblib
import numpy as np
from difflib import SequenceMatcher

# ─── Scikit-learn ────────────────────────────────────────────────────────────
from sklearn.ensemble         import RandomForestClassifier
from sklearn.model_selection  import cross_val_score
from sklearn.preprocessing    import StandardScaler
from sklearn.pipeline         import Pipeline

# ─── Caminho do modelo salvo ─────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "modelo_voluntarios.pkl")

# ─── Listas de referência (mesmas do rule-based) ─────────────────────────────
DOMINIOS_DESCARTAVEIS = {
    "mailinator.com","guerrillamail.com","trashmail.com","yopmail.com",
    "tempmail.com","throwam.com","sharklasers.com","grr.la","spam4.me",
    "dispostable.com","maildrop.cc","mintemail.com","fakeinbox.com",
    "10minutemail.com","tempinbox.com","mailnull.com","spamcorpse.com",
    "binkmail.com","spambog.com","trashmail.at","trashmail.io",
    "trashmail.me","trashmail.net","discard.email","getnada.com",
    "tempr.email","anonaddy.com","inboxbear.com",
}

NOMES_SUSPEITOS = {
    "teste","test","fulano","ciclano","beltrano","asdf","qwerty",
    "joao silva","maria silva","jose silva","admin","user","usuario",
    "anonimo","anonymous","fake","falso","ninguem","none","null",
}

ONGS_SUSPEITAS = {
    "teste","test","ong","nenhuma","qualquer","asdf","abc","xyz",
    "n/a","na","nao sei","não sei","qualquer uma",
}

DDDS_VALIDOS = {
    11,12,13,14,15,16,17,18,19,
    21,22,24,27,28,
    31,32,33,34,35,37,38,
    41,42,43,44,45,46,47,48,49,
    51,53,54,55,
    61,62,63,64,65,66,67,68,69,
    71,73,74,75,77,79,
    81,82,83,84,85,86,87,88,89,
    91,92,93,94,95,96,97,98,99,
}

SPAM_PALAVRAS = re.compile(
    r"\b(comprar|vender|venda|produto|promoção|clique aqui|acesse|"
    r"ganhar dinheiro|renda extra|investimento|bitcoin|cripto)\b",
    re.IGNORECASE
)

# ─────────────────────────────────────────────────────────────────────────────
# EXTRAÇÃO DE FEATURES
# Cada cadastro vira um vetor de 20 números que o modelo entende
# ─────────────────────────────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

def _so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)

def _similaridade_max(texto: str, lista: set) -> float:
    return max((SequenceMatcher(None, texto, s).ratio() for s in lista), default=0.0)


def extrair_features(dados: dict) -> list[float]:
    """
    Converte um cadastro em 20 features numéricas.
    Retorna uma lista de floats pronta para o modelo.
    """
    nome     = _normalizar(dados.get("nome", ""))
    email    = dados.get("email", "").lower().strip()
    telefone = _so_digitos(dados.get("telefone", ""))
    ong      = _normalizar(dados.get("ong", ""))
    msg      = dados.get("mensagem", "").lower()

    # Remove DDI se presente
    if telefone.startswith("55") and len(telefone) in (12, 13):
        telefone = telefone[2:]

    dominio   = email.split("@")[1] if "@" in email else ""
    local     = email.split("@")[0] if "@" in email else email
    ddd       = int(telefone[:2]) if len(telefone) >= 2 else 0
    numero    = telefone[2:] if len(telefone) >= 4 else ""
    palavras_msg = msg.split()

    features = [
        # ── NOME (5 features) ─────────────────────────────────────────
        len(nome),                                          # f01: comprimento
        1.0 if bool(re.search(r"\d", nome)) else 0.0,     # f02: tem número?
        1.0 if " " in nome else 0.0,                       # f03: tem espaço (sobrenome)?
        _similaridade_max(nome, NOMES_SUSPEITOS),           # f04: sim. com nomes falsos
        1.0 if bool(re.search(r"\se\s", nome)) else 0.0,  # f05: padrão "X e Y" (dupla)?

        # ── E-MAIL (4 features) ───────────────────────────────────────
        1.0 if bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)) else 0.0,  # f06: formato válido?
        1.0 if dominio in DOMINIOS_DESCARTAVEIS else 0.0,  # f07: domínio descartável?
        len(local),                                         # f08: comprimento do local
        1.0 if bool(re.fullmatch(r"[a-z]{1,2}\d{4,}", local)) else 0.0,  # f09: padrão bot?

        # ── TELEFONE (4 features) ─────────────────────────────────────
        1.0 if len(telefone) in (10, 11) else 0.0,         # f10: qtd dígitos ok?
        1.0 if ddd in DDDS_VALIDOS else 0.0,               # f11: DDD válido?
        1.0 if (numero and len(set(numero)) == 1) else 0.0,# f12: todos dígitos iguais?
        1.0 if numero in ("12345678","123456789","987654321") else 0.0,  # f13: sequencial?

        # ── ONG (2 features) ──────────────────────────────────────────
        len(ong),                                           # f14: comprimento
        1.0 if ong in ONGS_SUSPEITAS else 0.0,             # f15: ONG suspeita?

        # ── MENSAGEM (3 features) ─────────────────────────────────────
        1.0 if bool(re.search(r"https?://", msg)) else 0.0,        # f16: tem URL?
        1.0 if bool(SPAM_PALAVRAS.search(msg)) else 0.0,            # f17: tem spam?
        (len(set(palavras_msg)) / len(palavras_msg))
            if len(palavras_msg) > 3 else 1.0,              # f18: diversidade de palavras

        # ── GERAL (2 features) ────────────────────────────────────────
        float(len(nome.replace(" ", ""))),                  # f19: qtd letras do nome
        1.0 if bool(re.fullmatch(r"(.)\1+", nome.replace(" ",""))) else 0.0,  # f20: nome repetido?
    ]

    return features


# ─────────────────────────────────────────────────────────────────────────────
# MODELO
# ─────────────────────────────────────────────────────────────────────────────

def _criar_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("modelo", RandomForestClassifier(
            n_estimators=200,       # 200 árvores de decisão
            max_depth=10,           # profundidade máxima de cada árvore
            min_samples_leaf=2,     # evita overfitting com poucos dados
            class_weight="balanced",# compensa se tiver poucos exemplos falsos
            random_state=42,
        )),
    ])


def treinar_modelo(registros: list[dict], rotulos: list[int]) -> dict:
    """
    Treina (ou re-treina) o modelo com os dados fornecidos.

    Parâmetros
    ----------
    registros : list de dicts com campos do voluntário
    rotulos   : list de int  — 0 = real, 1 = falso

    Retorna métricas do treino.
    """
    if len(registros) < 4:
        return {
            "erro": "São necessários pelo menos 4 exemplos para treinar o modelo.",
            "total": len(registros),
        }

    X = np.array([extrair_features(r) for r in registros])
    y = np.array(rotulos)

    pipeline = _criar_pipeline()

    # Cross-validation com k=min(5, n_amostras//2) para não quebrar com poucos dados
    k = min(5, len(registros) // 2)
    if k >= 2:
        scores = cross_val_score(pipeline, X, y, cv=k, scoring="f1_weighted")
        acuracia_cv = round(float(scores.mean()), 4)
    else:
        acuracia_cv = None

    pipeline.fit(X, y)
    joblib.dump(pipeline, MODEL_PATH)

    reais   = int(sum(1 for r in rotulos if r == 0))
    falsos  = int(sum(1 for r in rotulos if r == 1))

    return {
        "mensagem"      : "Modelo treinado e salvo com sucesso!",
        "total_exemplos": len(registros),
        "reais"         : reais,
        "falsos"        : falsos,
        "acuracia_cv"   : acuracia_cv,   # None se poucos dados
        "modelo_salvo"  : MODEL_PATH,
    }


def carregar_modelo() -> Pipeline | None:
    """Carrega o modelo do disco. Retorna None se não existir ainda."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def prever(dados: dict) -> dict:
    """
    Faz a predição para um cadastro.

    Retorna
    -------
    {
        "score_ml"    : float 0.0-1.0  (probabilidade de ser falso),
        "predicao"    : "real" | "falso",
        "confianca"   : float 0.0-1.0,
        "aprovado"    : bool,
        "modelo_usado": bool  (False = sem modelo, usou fallback heurístico)
    }
    """
    modelo = carregar_modelo()

    features = np.array([extrair_features(dados)])

    if modelo is None:
        # ── Fallback: score heurístico simples enquanto não há modelo ──
        score_heuristico = _score_heuristico_fallback(dados)
        return {
            "score_ml"    : score_heuristico,
            "predicao"    : "falso" if score_heuristico >= 0.5 else "real",
            "confianca"   : abs(score_heuristico - 0.5) * 2,
            "aprovado"    : score_heuristico < 0.5,
            "modelo_usado": False,
            "aviso"       : "Modelo ML ainda não treinado. Usando heurística como fallback.",
        }

    proba     = modelo.predict_proba(features)[0]  # [prob_real, prob_falso]
    idx_falso = list(modelo.classes_).index(1) if 1 in modelo.classes_ else 1
    prob_falso = float(proba[idx_falso]) if idx_falso < len(proba) else 0.0

    return {
        "score_ml"    : round(prob_falso, 4),
        "predicao"    : "falso" if prob_falso >= 0.5 else "real",
        "confianca"   : round(abs(prob_falso - 0.5) * 2, 4),
        "aprovado"    : prob_falso < 0.5,
        "modelo_usado": True,
    }


def importancia_features() -> dict:
    """Retorna quais features mais influenciam o modelo (interpretabilidade)."""
    modelo = carregar_modelo()
    if modelo is None:
        return {"erro": "Modelo ainda não treinado."}

    nomes = [
        "nome_comprimento","nome_tem_numero","nome_tem_sobrenome",
        "nome_sim_falsos","nome_padrao_dupla",
        "email_formato_valido","email_dominio_descartavel",
        "email_local_comprimento","email_padrao_bot",
        "tel_digitos_ok","tel_ddd_valido","tel_digitos_iguais","tel_sequencial",
        "ong_comprimento","ong_suspeita",
        "msg_tem_url","msg_tem_spam","msg_diversidade_palavras",
        "nome_qtd_letras","nome_caracteres_repetidos",
    ]

    rf = modelo.named_steps["modelo"]
    importancias = rf.feature_importances_

    ranking = sorted(
        zip(nomes, importancias),
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "ranking": [
            {"feature": n, "importancia": round(float(i), 4)}
            for n, i in ranking
        ]
    }


# ─── Fallback heurístico (usado antes do primeiro treino) ────────────────────

def _score_heuristico_fallback(dados: dict) -> float:
    """Score simples 0-1 baseado nas features extraídas, sem modelo treinado."""
    f = extrair_features(dados)
    # Features mais importantes: DDD válido(f10), email válido(f05), dígitos iguais(f11)
    penalidades = 0.0
    if f[10] == 0.0: penalidades += 0.50   # DDD inválido
    if f[11] == 1.0: penalidades += 0.45   # todos dígitos iguais
    if f[6]  == 1.0: penalidades += 0.45   # e-mail descartável
    if f[5]  == 0.0: penalidades += 0.10   # e-mail formato inválido
    if f[2]  == 0.0: penalidades += 0.20   # sem sobrenome
    if f[4]  == 1.0: penalidades += 0.30   # padrão dupla artística
    if f[14] == 1.0: penalidades += 0.40   # ONG suspeita
    if f[3] > 0.70: penalidades += 0.50   # nome similar a falso
    return min(penalidades, 1.0)