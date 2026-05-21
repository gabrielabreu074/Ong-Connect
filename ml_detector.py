"""
Detector de voluntários falsos usando Random Forest.
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
    11, 12, 13, 14, 15, 16, 17, 18, 19,21, 22, 24, 27, 28,31, 32, 33, 34, 35, 37, 38,41, 42, 43, 44, 45, 46,
    47, 48, 49,51, 53, 54, 55, 61, 62, 64, 63, 65, 66, 67, 68, 69, 79, 71, 73, 74, 75, 77,81, 87, 82, 83, 84,
    85, 88, 86, 89, 91, 93, 94, 92, 97, 96, 95, 98, 99,
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
        # Nome
        len(nome),                                                          # comprimento do nome
        1.0 if bool(re.search(r"\d", nome)) else 0.0,                      # tem número no nome?
        1.0 if " " in nome else 0.0,                                       # tem sobrenome?
        _similaridade_max(nome, NOMES_SUSPEITOS),                          # parecido com nome suspeito?

        # Emails 
        1.0 if bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)) else 0.0,  # formato válido?
        1.0 if dominio in DOMINIOS_DESCARTAVEIS else 0.0,                  # domínio descartável?
        len(local),                                                         # tamanho da parte local
        1.0 if bool(re.fullmatch(r"[a-z]{1,2}\d{4,}", local)) else 0.0,  # parece gerado por bot?

        # Tel
        1.0 if len(telefone) in (10, 11) else 0.0,                        # tamanho correto?
        1.0 if ddd in DDDS_VALIDOS else 0.0,                              # DDD existe no Brasil?
        1.0 if (numero and len(set(numero)) == 1) else 0.0,               # todos dígitos iguais? (ex: 99999999)
        1.0 if numero in ("12345678", "123456789", "987654321") else 0.0,  # sequência óbvia?

        # Mensagem da text area
        1.0 if bool(re.search(r"https?://", msg)) else 0.0,               # tem link?
        1.0 if bool(SPAM_PALAVRAS.search(msg)) else 0.0,                  # tem palavras de spam?
        (len(set(palavras_msg)) / len(palavras_msg)) if len(palavras_msg) > 3 else 1.0,  # variedade de palavras

        # Avalia o nome denovo
        float(len(nome.replace(" ", ""))),                                 # letras no nome (sem espaços)
        1.0 if bool(re.fullmatch(r"(.)\1+", nome.replace(" ", ""))) else 0.0,  # nome todo repetido? (ex: "aaaa")
    ]

    return features


"""
Modelo do ML(Random Forest )
"""

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
            "predicao": "falso" if score >= 0.3 else "real",
            "confianca": round(abs(score - 0.3) * 2, 4),
            "aprovado": score < 0.3,
            "modelo_usado": False,
            "aviso":       "Usando fallback (modelo ainda não treinado)",
        }

    proba     = modelo.predict_proba(features)[0]
    idx_falso = list(modelo.classes_).index(1)
    prob_falso = float(proba[idx_falso])

    return {
        "score_ml":    round(prob_falso, 4),
        "predicao":    "falso" if prob_falso >= 0.3 else "real",
        "confianca":   round(abs(prob_falso - 0.3) * 2, 4),
        "aprovado":    prob_falso < 0.3,
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



def _score_heuristico_fallback(dados: dict) -> float:
    f = extrair_features(dados)

    penalidades = 0.0

    if f[8]  == 0.0: penalidades += 1.0   # telefone com tamanho errado
    if f[9]  == 0.0: penalidades += 1.0   # DDD inválido
    if f[10] == 1.0: penalidades += 0.50   # dígitos todos iguais
    if f[5]  == 1.0: penalidades += 1.00   # domínio descartável
    if f[4]  == 0.0: penalidades += 0.60   # email com formato inválido
    if f[2]  == 0.0: penalidades += 0.40   # sem sobrenome
    if f[3]  > 0.70: penalidades += 0.70   # nome muito parecido com lista suspeita

    return min(penalidades, 1.0)


def gerar_dados_sinteticos() -> tuple[list[dict], list[int]]:
    """
        Gera exemplos de dados reais e falsos para pré-treinar o 
        modelo de ML sem precisar de dados reais.
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
        "zzzzzz", "123456 789", "anon anonimo", "ninguem nenhum", "tt tt",
    ]

    emails_reais = [
        "ana.ferreira@gmail.com", "carlos.souza@hotmail.com", "mariana.costa@yahoo.com",
        "roberto.pereira@outlook.com", "fernanda.santos@gmail.com", "lucas.rodrigues@hotmail.com",
        "juliana.silva@yahoo.com", "paulo.carvalho@gmail.com", "beatriz.martins@outlook.com",
        "gabriel.ribeiro@gmail.com", "camila.goncalves@hotmail.com", "diego.barbosa@gmail.com",
        "larissa.monteiro@yahoo.com", "rafael.cardoso@outlook.com", "priscila.freitas@gmail.com",
        "thiago.cavalcanti@hotmail.com", "amanda.correia@gmail.com", "bruno.moreira@yahoo.com",
        "vanessa.nunes@outlook.com", "rodrigo.melo@gmail.com",
    ]

    emails_falsos = [
        "test@mailinator.com", "fake@guerrillamail.com", "spam@yopmail.com",
        "a1234@trashmail.com", "b9876@tempmail.com", "x123@throwam.com",
        "asdf@fakeinbox.com", "zz@10minutemail.com", "aa@spambog.com",
        "temp@getnada.com", "bot@discard.email", "trash@maildrop.cc",
        "x@x.com", "a@b.c", "123@456.com",
        "noreply@fake.net", "void@null.com", "noone@nowhere.org",
        "q1w2e3@trashmail.io", "abc123@sharklasers.com", "dgagfaugfia172@gmail.com", "naoexisto29783@gmai.com",
        "falsotest@outlook.com", "spamspamspam129875@hotmail.com", "aposteaqui@gmail.com", "xkqwzmn88@gmail.com",
        "bvrtplxk91@hotmail.com", "wqzxmnbv44@outlook.com", "kplxqwrtz77@yahoo.com", "zxcvbnmqw33@gmail.com", 
        "dghjklmnpq@gmail.com", "bcdfghjklm@hotmail.com", "qwrtpsdfgh@outlook.com", "zxcvbnmpqr@yahoo.com", "mnbvcxzlkj@gmail.com",
        "1234567890@gmail.com", "9988776655@hotmail.com","1122334455@outlook.com", "0987654321@yahoo.com", "1111222233@gmail.com",
        "brunosantos19283@gmail.com", "fernandaoliveira28374@hotmail.com", "thiagoribeiro91827@outlook.com", "camilaferreira37261@yahoo.com", 
        "rodrigomartins46372@gmail.com", "maria29837461@gmail.com", "joao88712634@hotmail.com", "pedro11029374@outlook.com",
        "ana99182736@yahoo.com", "lucas77261534@gmail.com", "abcdefghijklmnopqrstu@gmail.com","aaabbbcccdddeeefffggg@hotmail.com",
        "xyzxyzxyzxyzxyzxyz99@outlook.com", "testetetestetestetest@yahoo.com", "randomrandomrandomrr1@gmail.com",

    ]

    telefones_reais = [
        "11987654321", "21976543210", "31965432109", "41954321098", "51943210987",
        "61932109876", "71921098765", "81910987654", "91909876543", "11876543210",
        "21865432109", "31854321098", "41843210987", "51832109876", "61821098765",
        "71810987654", "81809876543", "91898765432", "11987123456", "21976234567",
    ]

    telefones_falsos = [

    "11900000000", "11911111111", "11922222222", "11933333333", "11944444444", "21901234567", "21912345678", "21923456789",
    "21934567890", "21987654321", "31912121212", "31923232323", "31934343434", "31945454545", "31956565656", "41900011122",
    "41911122233", "41922233344", "41933344455", "41910203040", "51911111112", "51922222223", "51933333334", "51944444445",
    "51901010101", "61900000001", "61910000000", "61900000100", "61900010001", "61911001100", "71900000000", "71911111111",
    "71999999990", "71988888881", "71977777772", "81912345678", "81998765432", "81911223344", "81900102030", "81955443322",
    "85912340000", "85900001234", "85911110000", "85900000123", "85912121212", "92900000000", "92911111110", "92922222221", 
    "92933333332", "92999999998",

    "98912345678", "62911111111", "67900000000", "68912121212", "96901234567", "95911223344", "94912345678", "93900000001", 
    "69901010101", "63911111112", "1133334444", "2122223333", "3133334444", "4133334444", "5133334444", "98912345678", 
    "62911111111", "67900000000", "68912121212", "96901234567", "95911223344", "94912345678", "93900000001", "69901010101",
    "63911111112", "1133334444", "2122223333", "3133334444", "4133334444", "5133334444",
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
            "nome":      random.choice(nomes_reais),
            "email":     random.choice(emails_reais),
            "telefone":  random.choice(telefones_reais),
            "mensagem":  random.choice(mensagens_reais),
        })
        rotulos.append(0)  # real

    for _ in range(60):
        registros.append({
            "nome":      random.choice(nomes_falsos),
            "email":     random.choice(emails_falsos),
            "telefone":  random.choice(telefones_falsos),
            "mensagem":  random.choice(mensagens_falsas),
        })
        rotulos.append(1)  # falso

    return registros, rotulos


def inicializar_modelo():
    """
    Se o modelo do ML ainda não existir, será treinado com os dados mencionados acima.
    """
    if not os.path.exists(MODEL_PATH):
        print("[ML] Modelo não encontrado. Treinando com dados sintéticos...")
        registros, rotulos = gerar_dados_sinteticos()
        resultado = treinar_modelo(registros, rotulos)
        print(f"[ML] {resultado.get('mensagem', resultado.get('erro'))}")
    else:
        print("[ML] Modelo carregado com sucesso.")

# Vai chamar a função quando o arquivo for importado.
inicializar_modelo()

print(importancia_features())