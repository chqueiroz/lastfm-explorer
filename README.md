# LastFM Explorer

Aplicação em Python para coleta, análise e exploração de histórico musical do Last.fm, com dashboard interativo e um sistema de recomendação de artistas baseado em histórico de escuta, recência, similaridade entre artistas e tags musicais.

O projeto foi desenvolvido como um projeto independente de estudo e portfólio, com foco em **Python, APIs, SQL, análise de dados e sistemas de recomendação**.

---

## Funcionalidades

### Análise do histórico

O dashboard permite explorar:

- total de scrobbles e artistas;
- artistas mais ouvidos;
- faixas e álbuns mais ouvidos;
- principais características musicais a partir das tags dos artistas;
- evolução das tags ao longo do tempo;
- evolução temporal dos scrobbles;
- novos artistas descobertos;
- dias da semana com maior atividade;
- horários de maior atividade;
- distribuição das escutas por período do dia;
- evolução anual do histórico.

As análises podem ser filtradas por:

- últimos 30 dias;
- últimos 90 dias;
- último ano;
- histórico completo.

---

## Sistema de recomendação

O projeto também possui um sistema próprio de recomendação de artistas.

O pipeline atual funciona da seguinte forma:

```text
Histórico de scrobbles
        ↓
Perfil musical do usuário
        ↓
Seleção de artistas-semente
        ↓
Artistas similares do Last.fm
        ↓
Remoção de artistas já conhecidos
        ↓
Análise das tags dos candidatos
        ↓
Cálculo de compatibilidade
        ↓
Ranking final
```

O perfil musical considera:

- quantidade de scrobbles;
- tags associadas aos artistas;
- importância relativa das tags;
- recência das escutas.

A influência temporal utiliza um decaimento exponencial com **half-life de 180 dias**, fazendo com que escutas recentes tenham maior influência sem eliminar o histórico antigo.

Os candidatos são encontrados a partir das relações de artistas similares fornecidas pelo Last.fm.

O score final combina:

- **30% — sinal de similaridade do Last.fm**
- **70% — compatibilidade entre as tags do candidato e o perfil do usuário**

O score é utilizado para **ranking** e não representa uma probabilidade.

Artistas que já aparecem no histórico do usuário são removidos das recomendações.

---

## Dashboard

O projeto possui duas versões do dashboard.

### Demo pública

```bash
streamlit run app.py
```

A versão pública utiliza um **snapshot estático** armazenado em `data/demo.db`.

Ela:

- não utiliza API key;
- não realiza chamadas à API do Last.fm;
- utiliza dados previamente armazenados;
- apresenta um exemplo completo das funcionalidades analíticas;
- apresenta um snapshot das recomendações geradas pelo modelo.

Essa separação permite disponibilizar uma demonstração do projeto sem expor credenciais de API.

### Versão local

```bash
streamlit run app_local.py
```

A versão local permite informar um username do Last.fm.

O sistema então:

1. valida o usuário;
2. cria o banco local, caso necessário;
3. sincroniza o histórico de scrobbles;
4. coleta as tags dos artistas;
5. normaliza os dados;
6. atualiza as análises;
7. gera novas recomendações;
8. exibe o dashboard completo.

No primeiro uso, a sincronização pode demorar alguns minutos dependendo do tamanho do histórico da conta.

Nas execuções seguintes, o sistema identifica o histórico já armazenado e busca apenas novos dados.

---

## Interface via terminal

O projeto também mantém uma interface CLI:

```bash
python main.py
```

Ela permite executar o pipeline fora do Streamlit e é útil para testes e utilização direta pelo terminal.

---

## Arquitetura

```text
lastfm-explorer/
│
├── data/
│   ├── demo.db
│   └── lastfm.db
│
├── analytics.py
├── api.py
├── app.py
├── app_local.py
├── cli.py
├── config.py
├── dashboard_ui.py
├── database.py
├── demo_data.py
├── main.py
├── preprocessing.py
├── recommender.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Responsabilidade dos módulos

| Arquivo | Responsabilidade |
|---|---|
| `api.py` | Comunicação com a API do Last.fm |
| `database.py` | Criação e sincronização do banco SQLite |
| `preprocessing.py` | Limpeza e normalização das tags |
| `recommender.py` | Construção do perfil e sistema de recomendação |
| `analytics.py` | Consultas analíticas utilizadas pelos dashboards |
| `dashboard_ui.py` | Componentes visuais e gráficos compartilhados |
| `demo_data.py` | Leitura das recomendações estáticas da demo |
| `app.py` | Dashboard demonstrativo público |
| `app_local.py` | Dashboard interativo conectado à API |
| `cli.py` | Interface de linha de comando |
| `config.py` | Configurações e parâmetros globais |

---

## Tecnologias

Principais tecnologias utilizadas:

- Python
- Pandas
- NumPy
- SQLite / SQL
- Requests
- Last.fm API
- Streamlit
- Altair
- python-dotenv
- Git / GitHub

---

## Instalação

### 1. Clone o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd lastfm-explorer
```

### 2. Crie um ambiente virtual

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

---

## Configuração da API

A demo pública (`app.py`) não precisa de credenciais.

Para utilizar `app_local.py` ou a interface CLI, é necessário configurar uma API key do Last.fm.

Crie um arquivo `.env` na raiz do projeto a partir do `.env.example`:

```env
LASTFM_API_KEY=sua_api_key
LASTFM_USER_AGENT=LastFM Explorer/0.1
```

O arquivo `.env` está incluído no `.gitignore` e não deve ser enviado ao repositório.

---

## Bancos de dados

O projeto utiliza SQLite.

### `data/lastfm.db`

Banco local criado automaticamente durante o uso.

Pode armazenar dados de diferentes usuários e não é versionado pelo Git.

### `data/demo.db`

Banco utilizado exclusivamente pela demonstração pública.

Ele contém um snapshot dos dados utilizados pelo dashboard e das recomendações exibidas na demo.

Esse arquivo é versionado propositalmente para permitir que a demonstração funcione sem acesso à API.

---

## Atualização dos dados

O sistema utiliza sincronização incremental.

Quando já existe histórico local, o timestamp do scrobble mais recente é utilizado como referência para buscar somente reproduções posteriores.

Dessa forma, não é necessário baixar novamente todo o histórico a cada execução.

---

## Tratamento das tags

As tags retornadas pelo Last.fm passam por uma etapa de pré-processamento antes de serem utilizadas nas análises e recomendações.

Entre as etapas estão:

- normalização de texto;
- padronização de caixa;
- remoção de espaços desnecessários;
- filtragem de tags pouco úteis para representar características musicais;
- consolidação das tags associadas aos artistas.

As tags são utilizadas tanto na construção do perfil musical quanto na explicação das recomendações.

---

## Limitações atuais

Algumas limitações da versão atual:

- qualidade das recomendações depende das informações disponíveis no Last.fm;
- tags são dados colaborativos e podem apresentar inconsistências;
- relações de artistas similares são fornecidas pelo próprio Last.fm;
- o modelo trabalha principalmente no nível de artistas, e não de faixas;
- a primeira sincronização de contas com históricos grandes pode demorar;
- o sistema de recomendação atual utiliza pesos definidos manualmente e ainda não possui aprendizado supervisionado.

---

## Próximos passos

Possíveis evoluções futuras incluem:

- aprimorar a avaliação das recomendações;
- explorar diferentes estratégias de recomendação;
- adicionar análises estatísticas;
- criar novos indicadores de evolução do gosto musical;
- experimentar técnicas de Machine Learning;
- explorar arquitetura em cloud;
- permitir consultas sobre o histórico em linguagem natural.

---

## Sobre o projeto

O LastFM Explorer começou como um estudo de consumo de APIs e análise de dados musicais e evoluiu para uma aplicação que integra:

```text
API
 ↓
Coleta de dados
 ↓
SQLite
 ↓
Pré-processamento
 ↓
Analytics
 ↓
Sistema de recomendação
 ↓
Dashboard
```

O objetivo principal é utilizar um domínio de interesse pessoal como ambiente prático para estudar e aplicar conceitos de **Data Science e desenvolvimento em Python**.

---

## Last.fm

Projeto acadêmico e independente, não oficial e não afiliado ao Last.fm.

Os dados musicais utilizados pelo projeto são provenientes do Last.fm.

A versão pública do dashboard utiliza um snapshot estático e não realiza chamadas à API.

---

## Autor

Desenvolvido por **Christian Queiroz**.