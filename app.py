import streamlit as st
import requests
import pandas as pd
from datetime import date

# Configuração da página
st.set_page_config(page_title='Sistema de Manutenção', page_icon='⚙️', layout="wide")

# URL base da API (Node.js)
API_URL = 'http://localhost:3000/api'

# Inicializa as variáveis de controle na sessão do navegador
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.dados_usuario = None

def fazer_login(matricula, senha):
    '''Função que conecta no Node.js para validar as credenciais'''
    try:
        resposta = requests.post(
            f'{API_URL}/login', 
            json={'matricula': matricula, 'senha': senha}
        )
        
        if resposta.status_code == 200:
            dados = resposta.json()
            st.session_state.logado = True
            st.session_state.dados_usuario = dados 
            st.success('Login realizado com sucesso!')
            st.rerun() 
        else:
            st.error('Matrícula ou senha incorretos.')
            
    except requests.exceptions.ConnectionError:
        st.error('Erro de conexão: Não foi possível encontrar a API Node.js.')

def fazer_logout():
    '''Função para limpar os dados da sessão'''
    st.session_state.logado = False
    st.session_state.dados_usuario = None
    st.rerun()

# Interface do sistema
if not st.session_state.logado:
    # Tela de Login
    _, col_centro, _ = st.columns([1, 7, 1])
    
    with col_centro:
        st.write('') 
        st.write('')
        st.markdown('<h1 align="center">⚙️ Portal de Manutenção</h1>', unsafe_allow_html=True)
        st.markdown('<h2 align="center">Acesso ao Sistema</h2>', unsafe_allow_html=True)
    
        with st.form('form_login'):
            matricula_input = st.text_input('Matrícula (ex: MAT-1234)')
            senha_input = st.text_input('Senha', type='password')
            btn_entrar = st.form_submit_button('Entrar', use_container_width=True)

            if btn_entrar:
                if matricula_input and senha_input:
                    fazer_login(matricula_input, senha_input)
                else:
                    st.warning('Preencha a matrícula e a senha.')

else:
    # Dashboard inicial
    usuario = st.session_state.dados_usuario
    cod_colab = usuario.get('cod_colaborador')

    # Se for gestor ou admin, ganha a 5ª aba
    nivel_usuario = usuario.get('nivel_acesso', 'TÉCNICO')
    is_gestor = nivel_usuario in ['COORDENADOR', 'GERENTE', 'ADMIN']
    
    # Barra lateral
    st.sidebar.title('⚙️ Menu Principal')
    st.sidebar.write(f'👤 Olá, **{usuario.get('nome', 'Usuário')}**!')
    st.sidebar.write(f'🔑 Matrícula: {usuario.get('matricula', '-')}')
    st.sidebar.write(f'🧰 Cargo: {usuario.get('cargo', '-')}')
    if is_gestor:
        st.sidebar.write(f'😎 Nível de Acesso: {usuario.get('nivel_acesso', '-')}')
    st.sidebar.divider()
    
    if st.sidebar.button('Desconectar', type='primary' , use_container_width=True):
        fazer_logout()
        
    # Área central - Topo Fixo
    st.title('📋 Painel de Controle')
    st.write('Visão geral das suas atividades e pendências.')

    # Buscando os dados da API para os Cards
    dados_dash = {'qtd_pendente': 0, 'qtd_concluidas_na_semana': 0, 'qtd_alertas': 0}
    try:
        resp_dash = requests.get(f'{API_URL}/dashboard/{cod_colab}')
        if resp_dash.status_code == 200:
            dados_dash = resp_dash.json()
    except requests.exceptions.ConnectionError:
        st.error('Erro de conexão com a API Node.js')

    # Cards de Resumo
    col1, col2, col3 = st.columns(3)
    with col1:
        pendentes = int(dados_dash.get('qtd_pendente', 0))
        st.metric(label='Minhas Ordens Abertas', value=pendentes, delta='Normal', delta_color='off')
    with col2:
        concluidas_na_semana = int(dados_dash.get('qtd_concluidas_na_semana', 0))
        st.metric(label='Concluídas na Semana', value=concluidas_na_semana, delta='Na semana')
    with col3:
        alertas = int(dados_dash.get('qtd_alertas', 0))
        delta_text = 'Atenção necessária' if alertas > 0 else 'Nenhum alerta'
        st.metric(label='Alertas de Máquinas', value=alertas, delta=delta_text, delta_color='inverse' if alertas > 0 else 'normal')

    st.divider()

    # Sistema de abas (organização do layout com controle de acesso)
    titulos_abas = ["📈 Desempenho", "📋 Minhas OS", "🔍 Consulta de Máquina", "➕ Nova Ordem"]
    
    if is_gestor:
        titulos_abas.append("👑 Gestão da Equipe")

    abas = st.tabs(titulos_abas)

    # Sistema de abas (organização do layout)
    # aba_dashboard, aba_os, aba_consulta, aba_nova_os = st.tabs([
    #     "📈 Desempenho", 
    #     "📋 Minhas OS", 
    #     "🔍 Consulta de Máquina",
    #     "➕ Nova Ordem"
    # ])

    # Gráfico de desempenho
    with abas[0]:
        st.subheader('📈 Meu Desempenho Mensal')
        try:
            resp_grafico = requests.get(f'{API_URL}/desempenho/{cod_colab}')
            if resp_grafico.status_code == 200:
                dados_grafico = resp_grafico.json()
                if len(dados_grafico) > 0:
                    df_grafico = pd.DataFrame(dados_grafico)
                    df_pivot = df_grafico.pivot_table(
                        index='mes', columns='status', values='qtd_concluida', 
                        aggfunc='sum', fill_value=0
                    )
                    
                    cores = []
                    if 'CONCLUÍDA' in df_pivot.columns: cores.append('#28c76f') 
                    if 'PENDENTE' in df_pivot.columns: cores.append('#ff9f43') 
                    
                    st.line_chart(df_pivot, color=cores if len(cores) == len(df_pivot.columns) else None)
                else:
                    st.info('✨ Nenhuma manutenção registrada para gerar o gráfico.')
        except requests.exceptions.ConnectionError:
            st.warning('Aviso: Não foi possível carregar o gráfico de desempenho.')

    # Listagem e conclusão de os
    with abas[1]:
        st.subheader('⚙️ Ordens de Manutenções')
        resp_manut = requests.get(f'{API_URL}/os/{cod_colab}')
        lista_manutencoes = []
        
        if resp_manut.status_code == 200:    
            lista_manutencoes = resp_manut.json()
            if len(lista_manutencoes) > 0:
                df = pd.DataFrame(lista_manutencoes)
                colunas_amigaveis = {
                    'os': 'OS', 'maquina': 'Máquina', 'setor': 'Setor',
                    'tipo_manutencao': 'Tipo', 'data_agendada': 'Agendada para',
                    'data_conclusao': 'Concluída em', 'status': 'Status'
                }
                df = df.rename(columns=colunas_amigaveis)
                
                def colorir_status(val):
                    if val == 'PENDENTE': return 'color: #ff9f43; font-weight: bold;' 
                    elif val == 'CONCLUÍDA': return 'color: #28c76f; font-weight: bold;'
                    return ''
                
                df_estilizado = df.style.map(colorir_status, subset=['Status'])
                st.dataframe(df_estilizado, use_container_width=True, hide_index=True)
            else:
                st.success('Você não tem nenhuma manutenção no sistema.')
        else:
            st.error('Erro ao buscar as ordens de manutenção.')    

        st.divider()

        st.subheader('✅ Concluir Ordem de Serviço')
        os_pendentes = [m for m in lista_manutencoes if m['status'] == 'PENDENTE']
        
        if len(os_pendentes) > 0:
            with st.form('form_concluir_os'):
                opcoes_os = {m['os']: f"OS {m['os']} - Máquina: {m['maquina']}" for m in os_pendentes}
                os_selecionada = st.selectbox(
                    'Selecione a Ordem de Serviço:', 
                    options=list(opcoes_os.keys()), 
                    format_func=lambda x: opcoes_os[x]
                )
                data_fim = st.date_input('Data de Conclusão:', value=date.today())
                btn_salvar = st.form_submit_button('Salvar Conclusão', type='primary', use_container_width=True)
                
                if btn_salvar:
                    dados_atualizacao = {'data_conclusao': data_fim.strftime('%Y-%m-%d')}
                    try:
                        resp_update = requests.put(f'{API_URL}/manutencoes/{os_selecionada}/concluir', json=dados_atualizacao)
                        if resp_update.status_code == 200:
                            st.success(f'OS {os_selecionada} concluída com sucesso!')
                            st.rerun() 
                        else:
                            st.error('Erro ao atualizar a OS no servidor.')
                    except requests.exceptions.ConnectionError:
                        st.error('Erro de conexão com a API.')
        else:
            st.info('✨ Não há manutenções pendentes aguardando conclusão.') 

    # Histórico e consulta de máquina
    with abas[2]:
        st.subheader('🔍 Histórico da Máquina')
        st.write('Pesquise pelo Número de Patrimônio para ver os detalhes.')
        num_pat_busca = st.text_input('Número de Patrimônio:', placeholder='Ex: PAT-2026')
            
        if st.button('Buscar Máquina', type='primary', use_container_width=True):
            if num_pat_busca:
                try:
                    resp_maq = requests.get(f'{API_URL}/maquinas/patrimonio/{num_pat_busca}')
                    if resp_maq.status_code == 200:
                        dados_maq = resp_maq.json()
                        st.success('✅ Máquina localizada!')
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f'**Máquina:** {dados_maq.get("nome")}')
                            st.write(f'**Setor:** {dados_maq.get("setor")}')
                        with c2:
                            st.write(f'**Patrimônio:** {dados_maq.get("num_pat")}')
                            ultima_manut = dados_maq.get('ultima_manutencao')
                            
                            if ultima_manut:
                                data_formatada = pd.to_datetime(ultima_manut).strftime('%d/%m/%Y')
                                st.write(f'**Última Manutenção:** {data_formatada}')
                            else:
                                st.write('**Última Manutenção:** ⚠️ Nenhuma registrada')
                    else:
                        st.warning('Máquina não encontrada. Verifique o número digitado.')
                except requests.exceptions.ConnectionError:
                    st.error('Erro de conexão com o servidor.')
            else:
                st.info('Digite o número do patrimônio antes de buscar.')

        st.divider()

        st.write("📋 **Histórico de Manutenções**")
                        
        # Busca o histórico completo
        resp_hist = requests.get(f'{API_URL}/maquinas/patrimonio/{num_pat_busca}/historico')
        if resp_hist.status_code == 200:
            hist_maq = resp_hist.json()
            if len(hist_maq) > 0:
                df_hist = pd.DataFrame(hist_maq)
                # Formata a data para ficar no padrão BR
                df_hist['data_conclusao'] = pd.to_datetime(df_hist['data_conclusao']).dt.strftime('%d/%m/%Y')
                df_hist = df_hist.rename(columns={'os': 'OS', 'tipo': 'Serviço Realizado', 'data_conclusao': 'Data', 'tecnico': 'Técnico'})
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma manutenção concluída registrada para esta máquina.")

    # Nova ordem de serviço
    with abas[3]:
        st.subheader('📝 Abertura de Nova OS')
        
        try:
            # Busca a lista de máquinas disponíveis no banco
            resp_maquinas = requests.get(f'{API_URL}/maquinas')
            
            if resp_maquinas.status_code == 200:
                lista_maquinas = resp_maquinas.json()
                
                if len(lista_maquinas) > 0:
                    # Constrói o formulário
                    with st.form('form_nova_os'):
                        # Prepara o seletor para mostrar Nome + Patrimônio, mas enviar o cod_maquina para o banco
                        opcoes_maq = {m['cod_maquina']: f"{m['nome']} (Pat.: {m['num_pat']})" for m in lista_maquinas}
                        
                        maq_selecionada = st.selectbox(
                            'Selecione a Máquina para manutenção:', 
                            options=list(opcoes_maq.keys()), 
                            format_func=lambda x: opcoes_maq[x]
                        )
                        
                        # Seletor de Tipo
                        tipo_manut = st.selectbox('Tipo de Manutenção:', ['Preventiva', 'Corretiva', 'Preditiva', 'Inspeção de Rotina'])

                        # Nova opção de prioridade
                        nivel_prioridade = st.selectbox('Prioridade da OS:', ['BAIXA', 'MÉDIA', 'ALTA'])
                        
                        data_agendamento = st.date_input('Agendar para a data:', value=date.today())
                        btn_criar = st.form_submit_button('Criar Ordem de Serviço', type='primary')
                        
                        if btn_criar:
                            nova_os = {
                                'cod_colaborador': cod_colab,
                                'cod_maquina': maq_selecionada,
                                'tipo_manutencao': tipo_manut,
                                'data_agendada': data_agendamento.strftime('%Y-%m-%d'),
                                'prioridade': nivel_prioridade
                            }
                            
                            resp_post = requests.post(f'{API_URL}/manutencoes', json=nova_os)
                            
                            if resp_post.status_code == 201:
                                st.success('✅ Ordem de Serviço criada com sucesso!')
                                st.info('Atualizando a página para incluir na sua listagem...')
                                st.rerun() # Recarrega a página para o número de "Ordens Abertas" subir nos Cards
                            else:
                                st.error('Erro ao registrar a OS no banco de dados.')
                else:
                    st.warning('Nenhuma máquina cadastrada no sistema. Fale com um administrador.')
        except requests.exceptions.ConnectionError:
            st.error('Erro de conexão com a API ao tentar carregar o formulário.')

    # Aba 5: Gestão exclusiva
    if is_gestor:
        with abas[4]:
            # Desempenho da Equipe
            st.subheader('👥 Desempenho da Equipe')
            st.write('Acompanhe a produtividade e pendências dos seus técnicos.')
            
            try:
                resp_desempenho = requests.get(f'{API_URL}/desempenho/equipe/{cod_colab}')
                
                if resp_desempenho.status_code == 200:
                    dados_equipe = resp_desempenho.json()
                    
                    if len(dados_equipe) > 0:
                        df_equipe = pd.DataFrame(dados_equipe)
                        
                        # Renomeando as colunas para o visual ficar bonito
                        df_equipe = df_equipe.rename(columns={
                            'nome': 'Técnico',
                            'qtd_pendente': 'Pendentes',
                            'concluidas_na_semana': 'Concluídas (Semana)',
                            'qtd_alertas': 'Alertas de Atraso',
                            'qtd_total': 'Total Histórico'
                        })
                        
                        # Destaca de vermelho na tabela caso o técnico tenha algum Alerta de Atraso
                        def cor_alerta(val):
                            if int(val) > 0:
                                return 'color: #ff4b4b; font-weight: bold;'
                            return ''
                            
                        df_equipe_estilizado = df_equipe.style.map(cor_alerta, subset=['Alertas de Atraso'])
                        
                        # Renderiza a tabela da equipe
                        st.dataframe(df_equipe_estilizado, use_container_width=True, hide_index=True)
                        
                        # --- NOVO: BOTÃO DE EXPORTAR ---
                        st.write('') # Espaço em branco
                        # Converte o DataFrame original (sem o estilo visual) para CSV
                        csv = df_equipe.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label='📥 Exportar Relatório (CSV)',
                            data=csv,
                            file_name=f'relatorio_equipe_{date.today().strftime('%Y%m%d')}.csv',
                            mime='text/csv'
                        )
                    else:
                        st.info('Sua equipe ainda não tem dados registrados.')
            except requests.exceptions.ConnectionError:
                st.warning('Não foi possível carregar as métricas da equipe (Verifique o Node.js).')

            st.divider()

            st.subheader('👑 Controle Administrativo')
            st.write('Transfira manutenções entre técnicos ou cancele ordens incorretas.')
            
            # Busca a lista de OS da equipe
            try:
                resp_os_equipe = requests.get(f'{API_URL}/os/equipe/{cod_colab}')
                
                if resp_os_equipe.status_code == 200:
                    lista_os_equipe = resp_os_equipe.json()
                    
                    if len(lista_os_equipe) > 0:
                        with st.form('form_gestao_os'):
                            c1, c2 = st.columns(2)
                            
                            with c1:
                                st.write('1. Selecione a Ordem de Serviço')
                                # Seleciona a OS (agora mostrando o nome do técnico junto)
                                opcoes_todas_os = {m['os']: f"OS {m['os']} ({m['status']}) - Téc: {m['tecnico']} - {m['maquina']}" for m in lista_os_equipe}
                                
                                os_alvo = st.selectbox(
                                    'Ordem de Serviço:', 
                                    options=list(opcoes_todas_os.keys()), 
                                    format_func=lambda x: opcoes_todas_os[x]
                                )
                                
                                acao_gestor = st.radio('2. O que deseja fazer?', ['Transferir para outro técnico', 'Cancelar/Excluir OS'])
                            
                            with c2:
                                st.write('3. Detalhes da Ação')
                                # Busca os técnicos disponíveis na equipe do gestor
                                resp_equipe = requests.get(f'{API_URL}/equipe/{cod_colab}')
                                lista_equipe = resp_equipe.json() if resp_equipe.status_code == 200 else []
                                
                                tecnico_alvo = None
                                if acao_gestor == 'Transferir para outro técnico':
                                    opcoes_equipe = {t['cod_colaborador']: t['nome'] for t in lista_equipe}
                                    tecnico_alvo = st.selectbox(
                                        'Selecione o novo responsável:',
                                        options=list(opcoes_equipe.keys()),
                                        format_func=lambda x: opcoes_equipe[x]
                                    )
                                else:
                                    st.warning('⚠️ Atenção: A exclusão da OS é permanente e não pode ser desfeita.')
                                    
                            st.divider()
                            btn_executar = st.form_submit_button('Executar Ação', type='primary', use_container_width=True)
                            
                            if btn_executar:
                                if acao_gestor == 'Transferir para outro técnico' and tecnico_alvo:
                                    resp_transf = requests.put(
                                        f'{API_URL}/manutencoes/{os_alvo}/transferir', 
                                        json={'novo_cod_colaborador': tecnico_alvo}
                                    )
                                    if resp_transf.status_code == 200:
                                        st.success('OS transferida com sucesso!')
                                        st.rerun()
                                    else:
                                        st.error('Erro ao transferir.')
                                        
                                elif acao_gestor == 'Cancelar/Excluir OS':
                                    resp_del = requests.delete(f'{API_URL}/manutencoes/{os_alvo}')
                                    if resp_del.status_code == 200:
                                        st.success('OS excluída do sistema.')
                                        st.rerun()
                                    else:
                                        st.error('Erro ao excluir.')
                    else:
                        st.info('Não há ordens de serviço registradas na sua equipe.')
            except requests.exceptions.ConnectionError:
                st.error("Erro de conexão com o servidor Node.js.")

            st.divider()

            st.subheader('➕ Adicionar Membro à Equipe')
            st.write('Cadastre um novo técnico para atuar sob sua supervisão.')

            with st.form('form_novo_colab'):
                c1, c2 = st.columns(2)
                
                with c1:
                    nome_novo = st.text_input('Nome Completo:')
                    matricula_nova = st.text_input('Matrícula de Acesso (ex: MAT-1001):')
                    senha_nova = st.text_input('Senha Inicial:', type='password')
                
                with c2:
                    cargo_novo = st.text_input('Cargo (ex: Mecânico, Eletricista):')

                    # Se for Admin, então pode adicionar todos os níveis de acesso
                    if nivel_usuario == 'ADMIN':
                        nivel_novo = st.selectbox('Nível de Acesso:', ['TÉCNICO', 'COORDENADOR', 'GERENTE', 'ADMIN'])
                    # Se for Gerente, pode adicionar técnicos e coordenadores
                    elif nivel_usuario == 'GERENTE':
                        nivel_novo = st.selectbox('Nível de Acesso:', ['TÉCNICO', 'COORDENADOR'])
                    # Se for Coordenador, pode adicionar técnicos
                    elif nivel_usuario == 'COORDENADOR':
                        nivel_novo = st.selectbox('Nível de Acesso:', ['TÉCNICO'])
                    else:
                        nivel_novo = st.selectbox('Nível de Acesso:', ['TÉCNICO'])
                
                btn_cadastrar_colab = st.form_submit_button('Salvar Cadastro', type='primary')

                if btn_cadastrar_colab:
                    if nome_novo and matricula_nova and senha_nova and cargo_novo:
                        
                        # Monta o pacote de dados amarrando o cod_gestor ao usuário que está logado!
                        dados_novo_colab = {
                            'nome': nome_novo,
                            'matricula': matricula_nova,
                            'senha': senha_nova, 
                            'cargo': cargo_novo,
                            'nivel_acesso': nivel_novo,
                            'cod_gestor': cod_colab  
                        }

                        try:
                            resp_cadastro = requests.post(f'{API_URL}/colaboradores', json=dados_novo_colab)
                            
                            if resp_cadastro.status_code == 201:
                                st.success(f'✅ Técnico {nome_novo} cadastrado e adicionado à sua equipe com sucesso!')
                                st.rerun() # Atualiza a tela e o cara já aparece na tabela de desempenho lá em cima!
                            elif resp_cadastro.status_code == 400:
                                st.warning(resp_cadastro.json().get('erro', 'Matrícula inválida.'))
                            else:
                                st.error('Erro ao cadastrar no banco de dados.')
                        except requests.exceptions.ConnectionError:
                            st.error('Erro de conexão com o servidor Node.js.')
                    else:
                        st.warning('Por favor, preencha todos os campos do formulário antes de salvar.')