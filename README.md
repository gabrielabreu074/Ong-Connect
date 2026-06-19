# ONG Connect

Sistema web desenvolvido para conectar voluntários a ONGs, permitindo o cadastro de interessados e a análise automática das mensagens utilizando Machine Learning.

## Objetivo

Facilitar o processo de recrutamento de voluntários, organizando os cadastros e auxiliando as ONGs na identificação de candidatos mais engajados.

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
* Avaliação automática das mensagens enviadas
* Geração de score de qualidade por meio de IA

## Como o ML Funciona

O sistema utiliza Processamento de Linguagem Natural (NLP) para analisar a mensagem enviada pelo voluntário.

A mensagem é convertida em representações numéricas (embeddings) por um modelo de IA e comparada semanticamente com exemplos de mensagens genuínas. Com base nessa análise, é gerado um score que representa a qualidade e relevância da mensagem.

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

**Marcus Vinicius e Gabriel Alan**

Projeto acadêmico desenvolvido para aplicação prática de conceitos de Desenvolvimento Web, Banco de Dados e Machine Learning.
