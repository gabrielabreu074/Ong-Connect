# ONG Connect

Sistema web desenvolvido para conectar voluntários a ONGs, permitindo o cadastro de interessados e a análise automática das mensagens utilizando Machine Learning.

## Objetivo

Facilitar o processo de recrutamento de voluntários, permitindo o cadastro de interessados e a análise automática da qualidade das mensagens enviadas.

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

## Requisitos

Para executar o projeto localmente é necessário ter instalado:

- Python 3.10 ou superior
- Git
- Pip (gerenciador de pacotes do Python)

As dependências do projeto podem ser instaladas através do arquivo `requirements.txt`.

## Funcionalidades

* Cadastro de voluntários
* Armazenamento das informações em banco de dados
* Painel administrativo para visualização dos cadastros
* Análise semântica automática das mensagens enviadas
* Geração de score de qualidade por meio de IA

## Como o ML Funciona

O sistema utiliza Processamento de Linguagem Natural (NLP) para analisar as mensagens enviadas pelos voluntários.

Por meio do modelo Sentence Transformer, o texto é convertido em embeddings (representações numéricas vetoriais). Esses vetores são comparados semanticamente com exemplos previamente definidos de mensagens consideradas relevantes.

A partir dessa comparação, o sistema gera um score de qualidade que auxilia a ONG na avaliação dos cadastros.

## Diferenciais

* Utilização de Machine Learning aplicado a um problema real
* Análise inteligente de mensagens de voluntários
* Interface simples e intuitiva
* Auxílio às ONGs na organização e avaliação de inscrições

## Resultados

* Sistema web totalmente funcional
* Integração entre frontend, backend e banco de dados
* Implementação de NLP para análise textual
* Geração automática de avaliações para os cadastros realizados

## Autores

**Marcus Vinicius, Gabriel Alan e cocriação com a Inteligência Artificial**

Projeto acadêmico desenvolvido para aplicação prática de conceitos de Desenvolvimento Web, Banco de Dados e Machine Learning.
