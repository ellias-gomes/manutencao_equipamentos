const express = require('express');
const pool = require('./database'); // Import arquivo de conexão com o banco Neon
const app = express();

// Permite que o Node entenda os dados JSON que o Python vai enviar
app.use(express.json());

// Login e validação de usuários
app.post('/api/login', async (req, res) => {
    const { matricula, senha } = req.body;
    try {
        // Busca o colaborador no banco Neon
        const query = 'SELECT cod_colaborador, nome, matricula,nivel_acesso, cargo FROM colaboradores WHERE matricula = $1 AND senha = $2';
        const result = await pool.query(query, [matricula, senha]);

        if (result.rows.length > 0) {
            // Retorna os dados do usuário para o Python guardar na sessão
            res.status(200).json(result.rows[0]);
        } else {
            res.status(401).json({ erro: 'Matrícula ou senha incorretos' });
        }
    } catch (erro) {
        console.error(erro);
        res.status(500).json({ erro: 'Erro interno no servidor' });
    }
});

// Buscar manutenções por perfil com hierarquia
app.get('/api/manutencoes/usuario/:cod_colaborador', async (req, res) => {
    const codColaborador = req.params.cod_colaborador;

    try {
        // Descobre o nível de acesso de quem está pedindo os dados
        const userResult = await pool.query(
            'SELECT nivel_acesso FROM colaboradores WHERE cod_colaborador = $1',
            [codColaborador]
        );

        if (userResult.rows.length === 0) {
            return res.status(404).json({ erro: 'Colaborador não encontrado' });
        }

        const nivelAcesso = userResult.rows[0].nivel_acesso;
        let queryManutencoes = '';
        let parametros = [];

        // Monta a consulta na View de acordo com o poder do usuário
        if (nivelAcesso === 'ADMIN') {
            // ADMIN: Vê absolutamente tudo
            queryManutencoes = 'SELECT * FROM vw_resumo_manutencao';
        } else if (nivelAcesso === 'COORDENADOR' || nivelAcesso === 'GERENTE') {
            // GESTOR: Vê as próprias manutenções E as da sua equipe
            queryManutencoes = `
                SELECT * FROM vw_resumo_manutencao 
                WHERE
                    cod_colaborador = $1 
                    OR cod_colaborador IN (
                        SELECT cod_colaborador FROM colaboradores WHERE cod_gestor = $1
                    )
            `;
            parametros = [codColaborador];

        } else {
            // TÉCNICO: Vê apenas as manutenções atribuídas ao seu próprio cod_colaborador
            queryManutencoes = 'SELECT * FROM vw_resumo_manutencao WHERE cod_colaborador = $1';
            parametros = [codColaborador];
        }

        // Executa a query final e devolve pro Python
        const manutencoes = await pool.query(queryManutencoes, parametros);
        res.status(200).json(manutencoes.rows);

    } catch (erro) {
        console.error(erro);
        res.status(500).json({ erro: 'Erro ao buscar manutenções' });
    }
});

// Dados do Dashboard
app.get('/api/dashboard/:cod_colaborador', async (req, res) => {
    const codColaborador = req.params.cod_colaborador;

    // Query que coleta os valores da view geral
    try {
        const query = 'SELECT * FROM vw_mostra_colab_geral WHERE cod_colaborador = $1';
        const result = await pool.query(query, [codColaborador]);

        if (result.rows.length > 0) {
            res.status(200).json(result.rows[0]);
        } else {
            // Se o usuário não tiver nenhuma manutenção, retorna tudo zerado
            res.status(200).json({
                qtd_pendentes: 0,
                qtd_concluidas_na_semana: 0,
                qtd_alertas: 0
            });
        }
    } catch (erro) {
        console.error(erro);
        res.status(500).json({ erro: 'Erro ao buscar dados do dashboard' });
    }
});

// Ordens de serviço
app.get('/api/os/:cod_colaborador', async (req, res) => {
    const codColaborador = req.params.cod_colaborador;
    try {
        const result = await pool.query('SELECT os, maquina, setor, tipo_manutencao, data_agendada, data_conclusao, status FROM vw_resumo_manutencao WHERE cod_colaborador = $1', [codColaborador]);
        res.status(200).json(result.rows);
    } catch (erro) {
        console.error(erro);
        res.status(500).json({ erro: 'Erro ao buscar ordens de serviço' });
    }
});

app.put('/api/manutencoes/:cod_manutencao/concluir', async (req, res) => {
    const codManutencao = req.params.cod_manutencao;
    const { data_conclusao } = req.body;

    try {
        // Atualiza o banco mudando o status e preenchendo a data enviada pelo Streamlit
        const query = `
            UPDATE manutencoes 
            SET status = 'CONCLUÍDA', data_conclusao = $1 
            WHERE cod_manutencao = $2
            RETURNING *;
        `;
        const result = await pool.query(query, [data_conclusao, codManutencao]);

        if (result.rows.length > 0) {
            res.status(200).json({
                mensagem: 'Manutenção concluída com sucesso',
                dados: result.rows[0]
            });
        } else {
            res.status(404).json({ erro: 'Ordem de manutenção não encontrada' });
        }
    } catch (erro) {
        console.error('Erro no banco de dados:', erro);
        res.status(500).json({ erro: 'Erro interno ao atualizar a manutenção' });
    }
});

// Rota para Gráfico de Desempenho Mensal
app.get('/api/desempenho/:cod_colaborador', async (req, res) => {
    const codColaborador = req.params.cod_colaborador;
    try {
        // Agrupa as manutenções concluídas por mês, ordenando do mais antigo pro mais novo
        const query = `
            SELECT status, mes, qtd_concluida
            FROM vw_grafico_anual
            WHERE cod_colaborador = $1
            ORDER BY 1 ASC
            LIMIT 24;
        `;
        const result = await pool.query(query, [codColaborador]);
        res.status(200).json(result.rows);

    } catch (erro) {
        console.error('Erro ao buscar dados do gráfico:', erro);
        res.status(500).json({ erro: 'Erro interno ao gerar desempenho' });
    }
});

// Rota para buscar dados da máquina pelo número de patrimônio
app.get('/api/maquinas/patrimonio/:num_pat', async (req, res) => {
    const numPat = req.params.num_pat;

    try {
        const query = `
            SELECT *
            FROM vw_ultima_manutencao
            WHERE num_pat = $1
        `;
        const result = await pool.query(query, [numPat]);

        if (result.rows.length > 0) {
            res.status(200).json(result.rows[0]);
        } else {
            res.status(404).json({ erro: 'Máquina não encontrada no sistema' });
        }
    } catch (erro) {
        console.error('Erro na busca de máquina:', erro);
        res.status(500).json({ erro: 'Erro interno ao consultar máquina' });
    }
});

// Rota para buscar máquinas
app.get('/api/maquinas', async (req, res) => {
    try {
        const query = 'SELECT cod_maquina, nome, num_pat FROM maquinas ORDER BY 1';
        const result = await pool.query(query);
        res.status(200).json(result.rows);
    } catch (erro) {
        console.error('Erro ao buscar máquinas:', erro);
        res.status(500).json({ erro: 'Erro interno ao listar máquinas' });
    }
});

app.get('/api/maquinas/patrimonio/:num_pat/historico', async (req, res) => {
    const numPat = req.params.num_pat;
    try {
        const query = `
            SELECT mn.cod_manutencao AS os, mn.tipo_manutencao AS tipo, mn.data_conclusao, c.nome AS tecnico
            FROM manutencoes mn
            JOIN colaboradores c ON mn.cod_colaborador = c.cod_colaborador
            JOIN maquinas m ON mn.cod_maquina = m.cod_maquina
            WHERE m.num_pat = $1 AND mn.status = 'CONCLUÍDA'
            ORDER BY mn.data_conclusao DESC;
        `;
        const result = await pool.query(query, [numPat]);
        res.status(200).json(result.rows);
    } catch (erro) {
        res.status(500).json({ erro: 'Erro ao buscar histórico' });
    }
});

// Rota para criar nova ordem de serviço
app.post('/api/manutencoes', async (req, res) => {
    // Recebe os dados enviados pelo Streamlit
    const { cod_colaborador, cod_maquina, tipo_manutencao, data_agendada, prioridade } = req.body;

    try {
        // Insere a nova manutenção e já define o status como PENDENTE automaticamente
        const query = `
            INSERT INTO manutencoes (cod_colaborador, cod_maquina, tipo_manutencao, data_agendada, prioridade, status) 
            VALUES ($1, $2, $3, $4, $5, 'PENDENTE') 
            RETURNING cod_manutencao;
        `;

        const values = [cod_colaborador, cod_maquina, tipo_manutencao, data_agendada, prioridade];
        const result = await pool.query(query, values);

        // Retorna status 201 (Created) e o código da nova OS
        res.status(201).json({
            mensagem: 'OS criada com sucesso!',
            cod_manutencao: result.rows[0].cod_manutencao
        });
    } catch (erro) {
        console.error('Erro ao criar OS:', erro);
        res.status(500).json({ erro: 'Erro interno ao registrar manutenção' });
    }
});

app.get('/api/equipe/:cod_gestor', async (req, res) => {
    const codGestor = req.params.cod_gestor;
    try {
        // Descobre o nível do usuário
        const userResult = await pool.query('SELECT nivel_acesso FROM colaboradores WHERE cod_colaborador = $1', [codGestor]);
        const nivel = userResult.rows[0].nivel_acesso;

        let query = '';
        let params = [];

        if (nivel === 'ADMIN') {
            query = 'SELECT cod_colaborador, nome FROM colaboradores ORDER BY 2';
        } else {
            // Traz os liderados do gestor e ele mesmo
            query = 'SELECT cod_colaborador, nome FROM colaboradores WHERE cod_gestor = $1 OR cod_colaborador = $1 ORDER BY 2';
            params = [codGestor];
        }

        const result = await pool.query(query, params);
        res.status(200).json(result.rows);
    } catch (erro) {
        res.status(500).json({ erro: 'Erro ao buscar equipe' });
    }
});

// Lista ordens de serviço do gestor
app.get('/api/os/equipe/:cod_gestor', async (req, res) => {
    const codGestor = req.params.cod_gestor;

    try {
        const userResult = await pool.query('SELECT nivel_acesso FROM colaboradores WHERE cod_colaborador = $1', [codGestor]);
        const nivel = userResult.rows[0].nivel_acesso;

        let query = '';
        let params = [];

        // JOIN para trazer o nome do técnico e da máquina para facilitar no front-end
        if (nivel === 'ADMIN') {
            query = `
                SELECT os, maquina, status, tecnico 
                FROM vw_detalhes_manutencao 
                ORDER BY os DESC;
            `;
        } else {
            query = `
                SELECT os, maquina, status, tecnico 
                FROM vw_detalhes_manutencao 
                WHERE cod_gestor = $1 OR cod_colaborador = $1 
                ORDER BY os DESC;
            `;
            params = [codGestor];
        }

        const result = await pool.query(query, params);
        res.status(200).json(result.rows);
    } catch (erro) {
        res.status(500).json({ erro: 'Erro ao buscar OS da equipe' });
    }
});

// Rota para buscar o desempenho geral da equipe
app.get('/api/desempenho/equipe/:cod_gestor', async (req, res) => {
    const codGestor = req.params.cod_gestor;

    try {
        const userResult = await pool.query('SELECT nivel_acesso FROM colaboradores WHERE cod_colaborador = $1', [codGestor]);
        if (userResult.rows.length === 0) return res.status(404).json({ erro: 'Gestor não encontrado' });

        const nivel = userResult.rows[0].nivel_acesso;
        let query = '';
        let params = [];

        // Fazemos um JOIN da tabela de Colaboradores com a sua View de estatísticas
        if (nivel === 'ADMIN') {
            query = `
                SELECT nome, qtd_pendente, concluidas_na_semana, qtd_alertas, qtd_total 
                FROM vw_desempenho_equipe 
                ORDER BY concluidas_na_semana DESC;
            `;
        } else {
            query = `
                SELECT nome, qtd_pendente, concluidas_na_semana, qtd_alertas, qtd_total 
                FROM vw_desempenho_equipe 
                WHERE cod_gestor = $1 OR cod_colaborador = $1 
                ORDER BY concluidas_na_semana DESC;
            `;
            params = [codGestor];
        }

        const result = await pool.query(query, params);
        res.status(200).json(result.rows);
    } catch (erro) {
        console.error('Erro ao buscar desempenho da equipe:', erro);
        res.status(500).json({ erro: 'Erro interno ao consultar equipe' });
    }
});

// Transferir OS (reatribuir)
app.put('/api/manutencoes/:cod_manutencao/transferir', async (req, res) => {
    const codManutencao = req.params.cod_manutencao;
    const { novo_cod_colaborador } = req.body;

    try {
        const query = 'UPDATE manutencoes SET cod_colaborador = $1 WHERE cod_manutencao = $2';
        await pool.query(query, [novo_cod_colaborador, codManutencao]);
        res.status(200).json({ mensagem: 'Ordem transferida com sucesso!' });
    } catch (erro) {
        res.status(500).json({ erro: 'Erro ao transferir OS' });
    }
});

// Cancelar/excluir OS
app.delete('/api/manutencoes/:cod_manutencao', async (req, res) => {
    const codManutencao = req.params.cod_manutencao;
    try {
        await pool.query('DELETE FROM manutencoes WHERE cod_manutencao = $1', [codManutencao]);
        res.status(200).json({ mensagem: 'Ordem excluída!' });
    } catch (erro) {
        res.status(500).json({ erro: 'Erro ao excluir OS' });
    }
});

// Adicionar novos funcionários pela gestão
app.post('/api/colaboradores', async (req, res) => {
    const { nome, matricula, senha, cargo, nivel_acesso, cod_gestor } = req.body;

    try {
        // Verifica se a matrícula já existe no banco
        const check = await pool.query('SELECT matricula FROM colaboradores WHERE matricula = $1', [matricula]);
        if (check.rows.length > 0) {
            return res.status(400).json({ erro: 'Essa matrícula já está cadastrada no sistema.' });
        }

        // Insere o novo usuário
        const query = `
            INSERT INTO colaboradores (nome, matricula, senha, cargo, nivel_acesso, cod_gestor) 
            VALUES ($1, $2, $3, $4, $5, $6) 
            RETURNING cod_colaborador, nome;
        `;
        const values = [nome, matricula, senha, cargo, nivel_acesso, cod_gestor];
        const result = await pool.query(query, values);

        res.status(201).json({
            mensagem: 'Colaborador cadastrado com sucesso!',
            dados: result.rows[0]
        });
    } catch (erro) {
        console.error('Erro ao cadastrar colaborador:', erro);
        res.status(500).json({ erro: 'Erro interno ao salvar o cadastro.' });
    }
});

// Inicia o servidor na porta 3000
app.listen(3000, () => {
    console.log('API rodando na porta 3000 - Pronta para receber conexões do Python!');
});
