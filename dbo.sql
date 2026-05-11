-- Tabela de Máquinas
CREATE TABLE maquinas (
    cod_maquina SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    num_pat INTEGER NOT NULL,
    num_serie VARCHAR(50) UNIQUE NOT NULL,
    fabricante VARCHAR(100),
    setor VARCHAR(100) NOT NULL,
    status VARCHAR(30) DEFAULT 'ATIVA'
);

-- Tabela de Colaboradores
CREATE TABLE colaboradores (
    cod_colaborador SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    matricula VARCHAR(20) UNIQUE NOT NULL,
    cargo VARCHAR(50) NOT NULL,
    status VARCHAR(30) DEFAULT 'ATIVO',
    senha VARCHAR(255), -- O Node.js deve salvar isso criptografado (ex: bcrypt)
    nivel_acesso VARCHAR(20) DEFAULT 'TECNICO', -- Ex: 'ADMIN', 'COORDENADOR', 'GERENTE', 'TECNICO'
    cod_gestor INTEGER, -- Informa quem é o chefe direto deste colaborador
    FOREIGN KEY (cod_gestor) REFERENCES colaboradores (cod_colaborador)
);

-- Tabela de Manutenções
CREATE TABLE manutencoes (
    cod_manutencao SERIAL PRIMARY KEY,
    cod_maquina INTEGER NOT NULL,
    cod_colaborador INTEGER NOT NULL,
    tipo_manutencao VARCHAR(50) NOT NULL,
    data_agendada DATE NOT NULL,
    data_conclusao DATE,
    descricao TEXT,
    status VARCHAR(30) DEFAULT 'PENDENTE',
    prioridade VARCHAR(20) DEFAULT 'BAIXA',
    FOREIGN KEY (cod_maquina) REFERENCES maquinas (cod_maquina),
    FOREIGN KEY (cod_colaborador) REFERENCES colaboradores (cod_colaborador)
);

CREATE
OR REPLACE VIEW vw_mostra_colab_geral AS
SELECT
    cod_colaborador,
    COUNT(*) FILTER (
        WHERE
            data_conclusao IS NULL
    ) AS qtd_pendente,
    COUNT(*) FILTER (
        WHERE
            data_conclusao >= CURRENT_DATE - INTERVAL '7 days'
    ) AS qtd_concluidas_na_semana,
    COUNT(*) FILTER (
        WHERE
            data_conclusao IS NULL
            AND data_agendada < CURRENT_DATE
    ) AS qtd_alertas,
    COUNT(cod_manutencao) AS qtd_total,
    MAX(data_conclusao) AS ultima_manutencao
FROM
    manutencoes
GROUP BY
    1;

CREATE
OR REPLACE VIEW vw_resumo_manutencao AS
SELECT
    man.cod_manutencao AS os,
    c.cod_colaborador,
    maq.nome AS maquina,
    maq.setor,
    man.tipo_manutencao,
    DATE(man.data_agendada) AS data_agendada,
    DATE(man.data_conclusao) AS data_conclusao,
    man.status
FROM
    manutencoes AS man
    LEFT JOIN colaboradores AS c ON man.cod_colaborador = c.cod_colaborador
    LEFT JOIN maquinas AS maq ON man.cod_maquina = maq.cod_maquina;

CREATE
OR REPLACE VIEW vw_grafico_anual AS
SELECT
    cod_colaborador,
    status,
    TO_CHAR (
        COALESCE(data_conclusao, data_agendada),
        'MM/YYYY'
    ) AS mes,
    DATE_TRUNC ('month', COALESCE(data_conclusao, data_agendada)) AS data_ref,
    CAST(COUNT(*) AS INTEGER) AS qtd_concluida
FROM
    manutencoes
GROUP BY
    1,
    2,
    3,
    4;

CREATE
OR REPLACE VIEW vw_ultima_manutencao AS
SELECT
    m.num_pat,
    m.nome,
    m.setor,
    MAX(mn.data_conclusao) AS ultima_manutencao
FROM
    maquinas m
    LEFT JOIN manutencoes mn ON m.cod_maquina = mn.cod_maquina
GROUP BY
    1,
    2,
    3;

CREATE
OR REPLACE VIEW vw_detalhes_manutencao AS
SELECT
    mn.cod_manutencao AS os,
    m.nome AS maquina,
    mn.status,
    c.nome AS tecnico,
    c.cod_gestor, -- Necessário para o Node.js filtrar a equipe
    mn.cod_colaborador -- Necessário para o Node.js filtrar a própria OS do gestor
FROM
    manutencoes mn
    JOIN maquinas m ON mn.cod_maquina = m.cod_maquina
    JOIN colaboradores c ON mn.cod_colaborador = c.cod_colaborador;

CREATE
OR REPLACE VIEW vw_desempenho_equipe AS
SELECT
    c.cod_colaborador,
    c.cod_gestor,
    c.nome,
    COALESCE(v.qtd_pendente, 0) AS qtd_pendente,
    COALESCE(v.qtd_concluidas_na_semana, 0) AS concluidas_na_semana,
    COALESCE(v.qtd_alertas, 0) AS qtd_alertas,
    COALESCE(v.qtd_total, 0) AS qtd_total
FROM
    colaboradores c
    LEFT JOIN vw_mostra_colab_geral v ON c.cod_colaborador = v.cod_colaborador;

-- Inserindo colaborador
INSERT INTO
    colaboradores (nome, matricula, cargo, senha, nivel_acesso)
VALUES
    (
        'Admin',
        'MAT-0001',
        'Administrador',
        'admin',
        'ADMIN'
    );

-- Inserindo Máquina
INSERT INTO
    maquinas (nome, num_pat, num_serie, fabricante, setor)
VALUES
    (
        'Bicicleta Movement RT 230',
        609,
        'S/N',
        'Movement',
        'Cond. Físico'
    );