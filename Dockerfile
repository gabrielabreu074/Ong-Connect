# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── Variáveis de ambiente ──────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false \
    PORT=7860

# ── Dependências do sistema ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Diretório de trabalho ──────────────────────────────────────────────────────
WORKDIR /app

# ── Instala torch CPU-only primeiro (muito mais leve que a versão com CUDA) ────
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

# ── Copia e instala o restante das dependências ────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copia o projeto ────────────────────────────────────────────────────────────
COPY . .

# ── Porta exposta (HF Spaces exige 7860) ──────────────────────────────────────
EXPOSE 7860

# ── Inicia o Flask ─────────────────────────────────────────────────────────────
CMD ["python", "app.py"]