require('dotenv').config();
const { Pool } = require('pg');

// Configurando a conexão com a URL do Neon
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: {
        rejectUnauthorized: false
    }
});

// Testando conexão
pool.connect((err, client, release) => {
    if (err) {
        return console.error('Erro ao conectar ao banco de dados: ', err.stack);
    }

    console.log('Conexão com o banco estabelecida com sucesso!');
    release(); // Libera a conexão para que possa ser usada por outras requisições
})

module.exports = pool;