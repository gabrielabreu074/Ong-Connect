"""
Analisador de qualidade de voluntários usando NLP (sentence-transformers).
- NÃO bloqueia cadastros (aprovado sempre True)
- Analisa o texto da textarea com NLP real (BERT multilingual)
- Score reflete qualidade genuína da mensagem
- Validações de email/telefone/nome reduzem score mas não bloqueiam
"""

import re
import os
import unicodedata
import numpy as np
from sentence_transformers import SentenceTransformer, util

# ── Modelo NLP ────────────────────────────────────────────────────────────────
_MODELO_NLP = None

def _carregar_modelo():
    global _MODELO_NLP
    if _MODELO_NLP is None:
        print("[ML] Carregando modelo NLP...")
        _MODELO_NLP = SentenceTransformer("paraphrase-MiniLM-L3-v2")
        print("[ML] Modelo NLP pronto.")
    return _MODELO_NLP



# ── Referências semânticas ────────────────────────────────────────────────────
MENSAGENS_GENUINAS = [
    "Quero ajudar crianças carentes da minha cidade e contribuir com a educação.",
    "Tenho experiência com trabalho voluntário e quero continuar fazendo a diferença.",
    "Me interesso por causas ambientais e tenho tempo disponível nos fins de semana.",
    "Sou estudante de pedagogia e quero aplicar meus conhecimentos em projetos sociais.",
    "Quero ajudar idosos e tenho experiência como cuidador na minha família.",
    "Já fui voluntário em abrigos e quero continuar contribuindo com a comunidade.",
    "Tenho disponibilidade e vontade de ajudar quem mais precisa.",
    "Acredito que posso contribuir com minhas habilidades para causas importantes.",
    "Quero devolver para a sociedade o que recebi e fazer parte de algo maior.",
    "Me identifico com a missão da ONG e quero colaborar ativamente.",
]

MENSAGENS_RUINS = [
    "quero ajudar",
    "sei lá",
    "porque sim",
    "não sei",
    "compre agora acesse o link e ganhe dinheiro",
    "bitcoin cripto renda extra investimento garantido",
    "clique aqui promoção imperdível acesse já",
    "aaaaaa",
    "teste teste teste",
    ".",
    "",
    "asdf qwer zxcv",
]

# Embeddings carregados sob demanda
_EMB_GENUINAS = None
_EMB_RUINS = None

def _carregar_embeddings():
    global _EMB_GENUINAS, _EMB_RUINS

    if _EMB_GENUINAS is None or _EMB_RUINS is None:
        modelo = _carregar_modelo()

        print("[ML] Gerando embeddings...")

        _EMB_GENUINAS = modelo.encode(
            MENSAGENS_GENUINAS,
            convert_to_tensor=True
        )

        _EMB_RUINS = modelo.encode(
            MENSAGENS_RUINS,
            convert_to_tensor=True
        )

        print("[ML] Embeddings prontos.")

# ── Listas de validação ───────────────────────────────────────────────────────
DOMINIOS_DESCARTAVEIS = {
    "mailinator.com", "guerrillamail.com", "trashmail.com", "yopmail.com",
    "tempmail.com", "throwam.com", "sharklasers.com", "grr.la", "spam4.me",
    "dispostable.com", "maildrop.cc", "mintemail.com", "fakeinbox.com",
    "10minutemail.com", "tempinbox.com", "getnada.com", "discard.email",
    "tempr.email", "inboxbear.com", "spambog.com", "trashmail.io",
}

NOMES_SUSPEITOS = {
    "teste", "test", "fulano", "ciclano", "beltrano", "asdf", "qwerty",
    "admin", "user", "usuario", "anonimo", "anonymous", "fake", "falso",
    "ninguem", "none", "null", "joao silva", "maria silva", "jose silva",
}

DDDS_VALIDOS = {
    11,12,13,14,15,16,17,18,19,21,22,24,27,28,
    31,32,33,34,35,37,38,41,42,43,44,45,46,47,48,49,
    51,53,54,55,61,62,63,64,65,66,67,68,69,
    71,73,74,75,77,79,81,82,83,84,85,86,87,88,89,
    91,92,93,94,95,96,97,98,99,
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

def _so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)

# ── Score da mensagem (NLP) ───────────────────────────────────────────────────
def _score_mensagem(mensagem: str) -> tuple[float, str]:
    texto = mensagem.strip() if mensagem else ""

    if len(texto) < 10:
        return 0.15, "mensagem ausente ou muito curta"

    _carregar_embeddings()   # ← ADICIONE ESTA LINHA

    modelo = _carregar_modelo()
    emb    = modelo.encode(texto, convert_to_tensor=True)

    sim_genuina = float(util.cos_sim(emb, _EMB_GENUINAS).max())
    sim_ruim    = float(util.cos_sim(emb, _EMB_RUINS).max())

    score = float(np.clip((sim_genuina * 0.7) - (sim_ruim * 0.3) + 0.3, 0.0, 1.0))

    if score >= 0.65:
        motivo = "mensagem genuína e bem elaborada"
    elif score >= 0.40:
        motivo = "mensagem mediana ou com pouca qualidade"
    else:
        motivo = "mensagem vaga, suspeita ou sem esforço"

    return round(score, 4), motivo

# ── Penalidades de validação ──────────────────────────────────────────────────
def _penalidades(dados: dict) -> tuple[float, list[str]]:
    alertas    = []
    penalidade = 0.0

    # E-mail
    email   = dados.get("email", "").lower().strip()
    dominio = email.split("@")[1] if "@" in email else ""
    local   = email.split("@")[0] if "@" in email else ""

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        alertas.append("e-mail com formato inválido")
        penalidade += 0.25

    if dominio in DOMINIOS_DESCARTAVEIS:
        alertas.append("e-mail descartável/temporário")
        penalidade += 0.30

    if re.fullmatch(r"[a-z]{6,}[0-9]{4,}@.+", local):
        alertas.append("e-mail com padrão suspeito")
        penalidade += 0.15

    # Telefone
    tel = _so_digitos(dados.get("telefone", ""))
    if tel.startswith("55") and len(tel) in (12, 13):
        tel = tel[2:]

    ddd    = int(tel[:2]) if len(tel) >= 2 else 0
    numero = tel[2:] if len(tel) >= 4 else ""

    if len(tel) not in (10, 11):
        alertas.append("telefone com tamanho inválido")
        penalidade += 0.20

    if ddd and ddd not in DDDS_VALIDOS:
        alertas.append("DDD inexistente no Brasil")
        penalidade += 0.20

    if numero and len(set(numero)) == 1:
        alertas.append("telefone com dígitos todos iguais")
        penalidade += 0.15

    if numero in ("12345678", "123456789", "987654321"):
        alertas.append("telefone sequencial óbvio")
        penalidade += 0.15

    # Nome
    nome = _normalizar(dados.get("nome", ""))

    if nome in NOMES_SUSPEITOS:
        alertas.append("nome suspeito ou genérico")
        penalidade += 0.25

    if not re.search(r"\s", nome):
        alertas.append("nome sem sobrenome")
        penalidade += 0.10

    if re.search(r"\d", nome):
        alertas.append("nome contém números")
        penalidade += 0.15

    return min(penalidade, 0.60), alertas

# ── Função principal ──────────────────────────────────────────────────────────
def prever(dados: dict) -> dict:
    score_msg, motivo = _score_mensagem(dados.get("mensagem", ""))
    penalidade, alertas = _penalidades(dados)

    score_final = round(max(0.0, score_msg - penalidade * 0.5), 4)

    if score_final >= 0.55:
        predicao  = "real"
        confianca = round((score_final - 0.55) / 0.45, 4)
    else:
        predicao  = "falso"
        confianca = round((0.55 - score_final) / 0.55, 4)

    return {
    "score_ml": score_final,
    "confianca": round(min(confianca, 1.0), 4),
    "aprovado": True,
    "motivo": motivo,
    "alertas": alertas,
}
# Pré-carrega o modelo e os embeddings
try:
    _carregar_embeddings()
except Exception as e:
    print(f"[ML] Erro ao inicializar NLP: {e}")