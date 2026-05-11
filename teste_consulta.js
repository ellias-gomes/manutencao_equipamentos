// Importa o arquivo de conexão com o banco de dados
const pool = require('./database');

async function testarConsulta() {
    try {

        console.log('Iniciando teste de conexão com o banco...');

        // Select direto da View criada no banco
        const resposta = await pool.query('SELECT * FROM vw_resumo_manutencao')

        // Mostra a resposta
        console.log('Teste concluído com sucesso!');
        console.table(resposta.rows);
    } catch (erro) {
        console.error('\n Ocorreu um erro: ', error.message);
    } finally {
        console.log('Finalizando teste de conexão com o banco...');
        await pool.end();
    }
}

testarConsulta();