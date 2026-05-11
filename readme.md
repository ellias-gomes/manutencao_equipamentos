# ⚙️ Portal de Gestão de Manutenção

Um sistema web completo e responsivo para o controle, acompanhamento e execução de manutenções de maquinário industrial. Este sistema foi desenhado para atender equipes de chão de fábrica, dividindo o acesso entre Técnicos e Gestores.

## 🚀 Funcionalidades

O sistema possui fluxos de trabalho dinâmicos baseados no nível de acesso do usuário:

*   **🔒 Autenticação e Perfis:** Login seguro por matrícula. Níveis de acesso que definem a visão do usuário (Técnico ou Coordenador/Admin).
*   **📊 Dashboard de Desempenho:** Gráficos interativos gerados via Pandas mostrando o ritmo de conclusão de manutenções no mês.
*   **📋 Controle de Ordens de Serviço (OS):** Criação de novas OSs com níveis de prioridade, listagem de pendências e atualização de status em tempo real.
*   **🔍 Histórico de Máquinas:** Consulta rápida da máquina via Número de Patrimônio (`num_pat`), exibindo todas as intervenções passadas.
*   **👑 Painel de Gestão (Exclusivo para Líderes):**
    *   Visão geral da produtividade e pendências de cada técnico sob sua supervisão.
    *   Ferramenta de transferência e reatribuição de Ordens de Serviço entre técnicos.
    *   Cadastro instantâneo de novos colaboradores para a equipe.
    *   Exportação de relatórios gerenciais em formato `.csv`.

## 🛠️ Arquitetura e Tecnologias

O projeto utiliza uma arquitetura separada entre front-end (painel interativo) e back-end (API RESTful), garantindo escalabilidade.

*   **Front-end:** Python, [Streamlit](https://streamlit.io/) (para construção da interface web), Pandas (para tratamento de dados e gráficos) e Requests (consumo de API).
*   **Back-end:** Node.js, Express.
*   **Banco de Dados:** PostgreSQL. *Nota arquitetural: As chaves primárias do banco utilizam o prefixo `cod_` (ex: `cod_manutencao`, `cod_colaborador`) como padrão de nomenclatura.*

## ⚙️ Como executar o projeto localmente

### 1. Configurando a API (Node.js)
1. Navegue até a pasta do back-end.
2. Instale as dependências com `npm install`.
3. Configure suas variáveis de ambiente (conexão com o banco PostgreSQL) no arquivo `.env`.
4. Inicie o servidor:
   ```bash
   node index.js
   ```
### 2. Configurando o Front-end (Python/Streamlit)
Navegue até a pasta do front-end.

Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
source venv/bin/activate  # No Windows use: venv\Scripts\activate
```

Instale as bibliotecas necessárias:

```bash
pip install streamlit requests pandas
```

Execute a aplicação:

```bash
streamlit run app.py
```


## 👨‍💻 Autoria
Desenvolvido como parte do Projeto Integrador do curso de Engenharia da Computação por Ellias Gomes.