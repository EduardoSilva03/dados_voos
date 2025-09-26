# Link do Medium

> https://medium.com/@eduaardo.silva03/atrasos-de-voos-no-brasil-2022-2024-3a2b581c0487 

# ✈️ Dashboard de Atrasos de Voos no Brasil (2022-2024)

> Um dashboard interativo construído com Streamlit para análise e visualização de dados de mais de 2.8 milhões de voos da aviação civil brasileira.

Este projeto transforma dados públicos e brutos da ANAC em um painel de controle interativo, permitindo a exploração de padrões e tendências sobre os atrasos de voos no Brasil durante o período de 2022 a 2024.

---

## ✨ Funcionalidades

- **Visualização de KPIs:** Métricas principais como total de voos, total de atrasos e a taxa de atraso geral.
- **Filtros Dinâmicos:** Filtre os dados por ano, companhia aérea e aeroporto de origem.
- **Análises Detalhadas:** 6 gráficos diferentes que respondem às principais perguntas sobre a pontualidade dos voos.
- **Interface Web:** Uma aplicação web limpa e responsiva, acessível por qualquer navegador.

---

## 📊 Fonte dos Dados

Os dados utilizados neste projeto são públicos e foram obtidos através do portal de **Dados Abertos da Agência Nacional de Aviação Civil (ANAC)**. Especificamente, foram utilizados os arquivos de **Voos e Atrasos (VRA)**.

Você pode encontrar os dados originais aqui: https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/voo-regular-ativo-vra

---

## 🛠️ Tecnologias Utilizadas

Este projeto foi desenvolvido utilizando as seguintes tecnologias:

- **Python**
- **Streamlit:** Para a criação do dashboard interativo.
- **Pandas:** Para manipulação e tratamento dos dados.
- **Matplotlib & Seaborn:** Para a criação das visualizações gráficas.

---

## 🚀 Como Rodar o Projeto

Siga os passos abaixo para executar a aplicação na sua máquina local.

### Pré-requisitos

- **Python 3.8** ou superior.
- **pip** (gerenciador de pacotes do Python).

### Estrutura de Pastas

Para que a aplicação funcione corretamente, os arquivos de dados devem seguir a estrutura de pastas abaixo. O script foi projetado para ler os arquivos `.csv` de dentro das subpastas de ano.

```
DADOS_VOOS/
|
|-- Dataset/
|   |-- 2022/
|   |   |-- VRA_202201.csv
|   |   |-- VRA_202202.csv
|   |   |-- ... (etc.)
|   |-- 2023/
|   |   |-- VRA_202301.csv
|   |   |-- ... (etc.)
|   `-- 2024/
|       |-- VRA_202401.csv
|       |-- ... (etc.)
|
`-- app.py
```

### Instalação

1.  Clone o repositório (ou faça o download dos arquivos):
    ```bash
    git clone https://github.com/EduardoSilva03/dados_voos.git
    ```

2.  Navegue até a pasta do projeto:
    ```bash
    cd DADOS_VOOS
    ```

3.  Crie um arquivo chamado `requirements.txt` e cole o conteúdo abaixo nele:
    ```txt
    streamlit
    pandas
    matplotlib
    seaborn
    ```

4.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

### Execução

1.  Com o terminal aberto na pasta do projeto, execute o seguinte comando:
    ```bash
    python -m streamlit run app.py
    ```
2.  Após a execução, o terminal exibirá um endereço local (Local URL). Copie e cole no seu navegador para acessar o dashboard.
