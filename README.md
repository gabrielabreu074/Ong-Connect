# ONG Connect

Sistema web desenvolvido para conectar voluntários a ONGs, permitindo o cadastro de interessados e a análise automática das mensagens utilizando Machine Learning e Processamento de Linguagem Natural (NLP).

## Acesso ao Projeto

O projeto pode ser executado localmente ou acessado através da plataforma de hospedagem utilizada pela equipe.

**Repositório:**

```
https://github.com/gabrielabreu074/Ong-Connect
```

**Aplicação Online:**

```
https://huggingface.co/spaces/Marcus017/OngConnect
```



---

## Objetivo

O ONG Connect tem como objetivo facilitar o processo de recrutamento de voluntários por organizações não governamentais (ONGs).

A plataforma permite o cadastro de interessados e utiliza técnicas de Machine Learning para analisar automaticamente a qualidade das mensagens enviadas pelos candidatos, auxiliando as ONGs na avaliação dos cadastros recebidos.

---

## Tecnologias Utilizadas

### Backend

* Python
* Flask
* SQLite

### Frontend

* HTML
* CSS
* JavaScript

### Machine Learning

* Sentence Transformers
* Transformers (Hugging Face)
* PyTorch
* NumPy
* Scikit-Learn

---

## Funcionalidades

* Cadastro de voluntários
* Armazenamento das informações em banco de dados
* Painel administrativo para visualização dos cadastros
* Análise semântica automática das mensagens
* Geração de score de qualidade por meio de IA
* Exibição de alertas para auxiliar a análise dos administradores

---

## Como o ML Funciona

O sistema utiliza Processamento de Linguagem Natural (NLP) para analisar as mensagens enviadas pelos voluntários.

Por meio do modelo Sentence Transformer, o texto é convertido em embeddings (representações numéricas vetoriais). Esses vetores são comparados semanticamente com exemplos previamente definidos de mensagens consideradas relevantes.

A partir dessa comparação, o sistema gera um score de qualidade que auxilia a ONG na avaliação dos cadastros.

---

## Requisitos

Para executar o projeto localmente é necessário possuir:

* Python 3.10 ou superior
* Git
* Pip

---

## Como Executar o Projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/ong-connect.git
cd ong-connect
```

### 2. Criar ambiente virtual

```bash
python -m venv .venv
```

### 3. Ativar ambiente virtual

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

### 5. Executar a aplicação

```bash
python app.py
```

A aplicação ficará disponível em:

```txt
http://localhost:7860
```

---

## Estrutura do Projeto

```
## Estrutura do Projeto

ONG-CONNECT/
│
├── app.py                 # Backend principal (Flask e rotas da API)
├── ml_detector.py         # Sistema de Machine Learning e NLP
├── database.db            # Banco de dados SQLite
├── requirements.txt       # Dependências do projeto
├── Dockerfile             # Configuração para deploy com Docker
├── README.md              # Documentação do projeto
├── .gitignore             # Arquivos ignorados pelo Git
│
├── public/
│   │
│   ├── assets/            # Imagens, ícones e recursos visuais
│   │
│   ├── css/
│   │   ├── admin.css      
│   │   ├── ajude.css      
│   │   ├── apa.css        
│   │   ├── casa.css      
│   │   ├── glpv.css      
│   │   ├── ongs.css      
│   │   ├── pontes.css     
│   │   ├── sal.css        
│   │   ├── style.css      
│   │   └── voluntario.css 
│   │
│   ├── html/
│   │   ├── admin.html       
│   │   ├── ajude.html       
│   │   ├── apa.html       
│   │   ├── casa.html       
│   │   ├── glpv.html       
│   │   ├── index.html  
│   │   ├── ongs.html        
│   │   ├── pontes.html      
│   │   ├── sal.html       
│   │   └── voluntario.html  
│   │
│   └── js/
│       ├── admin.js       
│       ├── ongs.js        
│       ├── script.js
│       └── volun.js      
│
├── .venv/                # Ambiente virtual Python
└── __pycache__/          # Arquivos temporários do Python
```



---

## Diferenciais

* Aplicação prática de Machine Learning em um cenário real
* Utilização de NLP para análise textual
* Integração entre frontend, backend e banco de dados
* Interface simples e intuitiva
* Auxílio à tomada de decisão das ONGs

---

## Resultados

* Sistema web funcional
* Integração completa entre frontend e backend
* Persistência de dados utilizando SQLite
* Implementação de NLP para análise de mensagens
* Geração automática de score para auxiliar a avaliação de voluntários

---

## Autores

**Marcus Vinicius e Gabriel Alan**

Projeto acadêmico desenvolvido para aplicação prática de conceitos de Desenvolvimento Web, Banco de Dados e Machine Learning, com apoio de ferramentas de Inteligência Artificial durante o processo de desenvolvimento.
