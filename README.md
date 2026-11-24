# Dashboard de Enchentes em Porto Alegre — INCT SiMAI

Este é um projeto extensionista desenvolvido para a disciplina de Coleta, Preparação e Análise de Dados da PUCRS (turma 310/110), em parceria com o INCT SiMAI.

O objetivo deste projeto é propor uma solução interativa, em dashboard com duas telas, para visualizar dados de simulação de enchentes no Rio Guaíba, em Porto Alegre - RS. Além de responder à pergunta “se o rio chegar a X metros, quais bairros e quantas pessoas são afetados?”, já respondida pela simulação Flood do INCT SiMAI, neste trabalho procura-se também responder "A partir de qual nível de alagamento simulado as casas de bomba da cidade ficam em áreas alagadas?".

## Equipe
* Amanda Flores Domeneghini
* Milena Fontana Bregalda
* Mariana Nunes dos Santos
* Karen Cristiane Nascimento

## Link do dashboard
Acesse: [Dashboard de Enchentes em Porto Alegre - Impactos da Elevação do Guaíba e Casas de Bomba e Inundação](https://projeto-enchentes-tf-5p9zgebetvruspngnhm2ev.streamlit.app/)

## Como executar o projeto

### 1. Pré-requisitos que devem estar instalados no seu computador

- Python 3
- Git

### 2. Clonar o repositório

```bash
git clone https://github.com/Amanda-Domeneghini/projeto-enchentes-TF.git
```

Entrar na pasta do projeto:

```bash
cd projeto-enchentes-TF
```

### 3. Criar um ambiente virtual (venv)

**Windows:**

```bash
python -m venv .venv
```

**Linux/macOS:**

```bash
python3 -m venv .venv
```

### 4. Ativar o ambiente virtual

**Windows:**

```bash
.venv\Scripts\activate.bat
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 5. Instalar as dependências

Com o ambiente virtual ativado, execute:

```bash
pip install -r requirements.txt
```

### 6. Executar o dashboard

```bash
streamlit run app/app.py
```

Após a execução deste comando, o Streamlit disponibilizará um endereço local para acessar o dashboard, e uma página se abrirá no navegador.

## Estrutura do Repositório
```text
projeto-enchentes-TF/
├── .streamlit/           # Arquivos de configuração do Streamlit
├── app/                  # Código-fonte do dashboard
├── dados/
│   ├── originais/        # Dados disponibilizados pelo INCT e coletados de fontes externas
│   └── processados/      # Dados limpos e processados que são utilizados pelo dashboard
├── notebooks/            # Notebook de Análise Exploratória de Dados (EDA)
├── relatorios/           # Relatórios de base de dados, limpeza de dados e dashboard
├── scripts/              # Scripts de coleta e de limpeza dos dados
├── .gitignore
├── README.md             # Equipe, link do dashboard, como executar o projeto, estrutura do repositório
└── requirements.txt      # Dependências necessárias para o projeto ser executado
```

 
