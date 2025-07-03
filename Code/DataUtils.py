# Code/DataUtils.py

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Dict, Union, Optional
from pandas.tseries.offsets import MonthEnd

# ==============================================================================
# FUNÇÕES DE UTILIDADE GLOBAL
# ==============================================================================

def standardize_cnpj_base8(cnpj_input: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """
    Padroniza um CNPJ ou código para uma string de 8 dígitos, lidando com
    diferentes formatos de entrada.
    """
    def _process_single_cnpj(cnpj_element_val):
        if pd.isna(cnpj_element_val):
            return None
        
        # 1. Converte para string e remove caracteres não numéricos.
        cleaned = re.sub(r'[^0-9]', '', str(cnpj_element_val).strip())
        
        if not cleaned:
            return None
            
        # 2. Usa zfill() para preencher com zeros à ESQUERDA e pega os 8 primeiros dígitos.
        return cleaned.zfill(8)[:8]

    if isinstance(cnpj_input, pd.Series):
        return cnpj_input.apply(_process_single_cnpj)
    
    return _process_single_cnpj(cnpj_input)

# ==============================================================================
# CLASSE DE ANÁLISE BANCÁRIA
# ==============================================================================

class AnalisadorBancario:
    """
    Uma classe para carregar, conectar e analisar dados financeiros de bancos
    provenientes das fontes COSIF e IFDATA do Banco Central.
    """
    
    def __init__(self, diretorio_output: str):
        """
        Inicializa o analisador carregando todos os DataFrames necessários.
        """
        print("Iniciando o Analisador Bancário...")
        base_path = Path(diretorio_output)
        
        try:
            self.df_cosif_ind = pd.read_parquet(base_path / 'df_cosif_individual.parquet')
            self.df_cosif_prud = pd.read_parquet(base_path / 'df_cosif_prudencial.parquet')
            self.df_ifd_val = pd.read_parquet(base_path / 'df_ifdata_valores.parquet')
            self.df_ifd_cad = pd.read_parquet(base_path / 'df_ifdata_cadastro.parquet')
            self._criar_mapa_identificadores()

            self.doc_to_tipo_map = {
                4060: 'prudencial', 4066: 'prudencial',
                4010: 'individual', 4016: 'individual',
                4020: 'individual', 4026: 'individual'
            }
            
            print("Analisador Bancário iniciado com sucesso!")
            print(f"  - {self.df_cosif_ind.shape[0]:,} linhas em COSIF Individual")
            print(f"  - {self.df_cosif_prud.shape[0]:,} linhas em COSIF Prudencial")
            print(f"  - {self.df_ifd_val.shape[0]:,} linhas em IFDATA Valores")
            print(f"  - {self.df_ifd_cad.shape[0]:,} linhas em IFDATA Cadastro")
            print(f"  - Mapeamento interno criado para {len(self._mapa_nomes_df):,} nomes únicos.")
            
        except FileNotFoundError as e:
            print(f"Erro Crítico: Arquivo não encontrado! Verifique o caminho do diretório de output.")
            print(f"Detalhe: {e}")
            raise

    def _criar_mapa_identificadores(self):
        """(Método interno) Cria um DataFrame para traduzir nomes de bancos para CNPJ_8."""
        mapa1 = self.df_ifd_cad[['NOME_INSTITUICAO_IFD_CAD', 'CNPJ_8']].dropna().drop_duplicates()
        mapa2 = self.df_cosif_prud[['NOME_INSTITUICAO_COSIF', 'CNPJ_8']].dropna().drop_duplicates()
        mapa3 = self.df_cosif_ind[['NOME_INSTITUICAO_COSIF', 'CNPJ_8']].dropna().drop_duplicates()
        mapa1.columns = ['nome', 'cnpj_8']
        mapa2.columns = ['nome', 'cnpj_8']
        mapa3.columns = ['nome', 'cnpj_8']
        self._mapa_nomes_df = pd.concat([mapa1, mapa2, mapa3]).drop_duplicates(subset='nome', keep='first').reset_index(drop=True)
        self._mapa_nomes_df['nome_upper'] = self._mapa_nomes_df['nome'].str.strip().str.upper()

    def _find_cnpj(self, identificador: str) -> Optional[str]:
        """(Método interno) Encontra o CNPJ_8 a partir de um nome ou de um CNPJ."""
        identificador_upper = identificador.strip().upper()
        if re.fullmatch(r'\d{8}', identificador): return identificador
        match_exato = self._mapa_nomes_df[self._mapa_nomes_df['nome_upper'] == identificador_upper]
        if not match_exato.empty: return match_exato['cnpj_8'].iloc[0]
        match_contains = self._mapa_nomes_df[self._mapa_nomes_df['nome_upper'].str.contains(identificador_upper)]
        if not match_contains.empty:
            if len(match_contains) == 1: return match_contains['cnpj_8'].iloc[0]
            # print(f"AVISO: Múltiplos nomes para '{identificador}'. Usando: '{match_contains['nome'].iloc[0]}'")
            return match_contains['cnpj_8'].iloc[0]
        print(f"AVISO: Identificador '{identificador}' não encontrado no mapa.")
        return None

    def _get_entity_identifiers(self, cnpj_8: str) -> Dict[str, Optional[str]]:
        """
        (Método interno) 'Tradutor universal' de identificadores.
        Busca CNPJ de reporte e nome canônico da entidade.
        """
        # Dicionário de retorno agora inclui 'nome_entidade'
        info = {
            'cnpj_interesse': cnpj_8,
            'cnpj_reporte_cosif': cnpj_8,
            'cod_congl_prud': None,
            'nome_entidade': None  # Inicializa como None
        }
        if not cnpj_8:
            return info

        # Busca o registro mais recente da entidade no cadastro
        entry_cad = self.df_ifd_cad[self.df_ifd_cad['CNPJ_8'] == cnpj_8].sort_values('DATA', ascending=False)
        if entry_cad.empty:
            # Se não achar no cadastro, não conseguimos o nome canônico
            return info

        linha_interesse = entry_cad.iloc[0]

        # --- Captura e adiciona o nome canônico ---
        info['nome_entidade'] = linha_interesse.get('NOME_INSTITUICAO_IFD_CAD')

        # Lógica para encontrar o CNPJ de reporte do conglomerado
        cod_congl = linha_interesse.get('COD_CONGL_PRUD_IFD_CAD')
        if pd.notna(cod_congl):
            info['cod_congl_prud'] = cod_congl
            df_conglomerado = self.df_ifd_cad[self.df_ifd_cad['COD_CONGL_PRUD_IFD_CAD'] == cod_congl]
            df_lideres_potenciais = df_conglomerado.dropna(subset=['CNPJ_LIDER_8_IFD_CAD'])
            if not df_lideres_potenciais.empty:
                lider_info = df_lideres_potenciais.sort_values('DATA', ascending=False).iloc[0]
                cnpj_lider = lider_info.get('CNPJ_LIDER_8_IFD_CAD')
                if pd.notna(cnpj_lider):
                    info['cnpj_reporte_cosif'] = cnpj_lider
                
        return info

    def get_dados_cosif(
        self,
        identificador: str,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        tipo: str = 'prudencial',
        documentos: Optional[Union[int, List[int]]] = None
    ) -> pd.DataFrame:
        """
        Busca dados COSIF. Determina automaticamente o 'tipo' (prudencial/individual)
        se um 'documento' for fornecido, tornando o parâmetro 'tipo' um fallback.
        """
        # --- LÓGICA INTELIGENTE DE SELEÇÃO DE TIPO ---
        tipo_busca = tipo
        if documentos and not isinstance(documentos, list):
            documentos = [documentos]
        if documentos:
            primeiro_doc = documentos[0]
            if primeiro_doc in self.doc_to_tipo_map:
                tipo_definido_pelo_doc = self.doc_to_tipo_map[primeiro_doc]
                if tipo_busca != tipo_definido_pelo_doc:
                    tipo_busca = tipo_definido_pelo_doc
        df_base = self.df_cosif_prud if tipo_busca == 'prudencial' else self.df_cosif_ind
        
        # --- Passo 1: Encontrar identificadores canônicos ---
        cnpj_8 = self._find_cnpj(identificador)
        if not cnpj_8:
            # Retornar DF vazio com colunas padronizadas
            # As novas colunas são Nome_Entidade e CNPJ_8, não mais BANCO_CONSULTADO
            return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8'] + [c for c in df_base.columns if c not in ['NOME_INSTITUICAO_COSIF', 'CNPJ_8']])

        info_ent = self._get_entity_identifiers(cnpj_8)
        nome_entidade_canonico = info_ent.get('nome_entidade', identificador) # Fallback para o input
        cnpj_busca = info_ent.get('cnpj_reporte_cosif', cnpj_8)
        if not cnpj_busca:
            return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8'] + [c for c in df_base.columns if c not in ['NOME_INSTITUICAO_COSIF', 'CNPJ_8']])

        # --- LÓGICA DE FILTRO ---
        if not isinstance(datas, list):
            datas = [datas]
        filtro_base = (df_base['CNPJ_8'] == cnpj_busca) & (df_base['DATA'].isin(datas))
        nomes_busca = [c for c in contas if isinstance(c, str)]
        codigos_busca = [c for c in contas if isinstance(c, int)]
        filtro_nomes = df_base['NOME_CONTA_COSIF'].isin(nomes_busca)
        filtro_codigos = df_base['CONTA_COSIF'].isin(codigos_busca)
        filtro_conta = filtro_nomes | filtro_codigos
        filtro_final = filtro_base & filtro_conta
        if documentos:
            filtro_final &= df_base['DOCUMENTO_COSIF'].isin(documentos)

        temp_df = df_base[filtro_final].copy()

        # Padronizar e reordenar as colunas de saída ###
        if not temp_df.empty:
            # Renomeia a coluna de nome para o padrão 'Nome_Entidade'
            temp_df.rename(columns={'NOME_INSTITUICAO_COSIF': 'Nome_Entidade'}, inplace=True)
            # Garante que o nome seja o canônico, para consistência
            temp_df['Nome_Entidade'] = nome_entidade_canonico
            
            # Define a ordem final das colunas, colocando as de identificação na frente
            cols_base = list(temp_df.columns)
            cols_prioritarias = ['Nome_Entidade', 'CNPJ_8']
            # Remove as prioritárias da lista base para evitar duplicatas
            cols_restantes = [c for c in cols_base if c not in cols_prioritarias]
            
            ordem_final = cols_prioritarias + cols_restantes
            return temp_df.reset_index(drop=True)[ordem_final]
        else:
            # Retorna DF vazio, mas com a estrutura correta
            return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8'] + [c for c in df_base.columns if c not in ['NOME_INSTITUICAO_COSIF', 'CNPJ_8']])


    def get_dados_ifdata(
        self,
        identificador: str,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]]
    ) -> pd.DataFrame:
        """Busca dados IFDATA, consolidando resultados de todas as chaves de identificação relevantes."""
        # --- Passo 1: Encontrar identificadores canônicos ---
        cnpj_8 = self._find_cnpj(identificador)
        if not cnpj_8:
            return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8'] + list(self.df_ifd_val.columns))

        info_ent = self._get_entity_identifiers(cnpj_8)
        nome_entidade_canonico = info_ent.get('nome_entidade', identificador)

        if not isinstance(datas, list):
            datas = [datas]
        entry_cad = (self.df_ifd_cad[self.df_ifd_cad['CNPJ_8'] == cnpj_8]).sort_values('DATA', ascending=False)
        cod_congl_fin_busca = entry_cad.iloc[0].get('COD_CONGL_FIN_IFD_CAD') if not entry_cad.empty else None
        
        ids_para_buscar = [cnpj_8, info_ent.get('cod_congl_prud'), cod_congl_fin_busca]
        ids_para_buscar = [str(i) for i in ids_para_buscar if pd.notna(i)]
        ids_para_buscar = list(dict.fromkeys(ids_para_buscar))

        # 1. Criar uma lista para armazenar os DataFrames encontrados em cada iteração
        resultados_coletados = []

        # --- Passo 2: Iterar e COLETAR todos os resultados ---
        for id_busca in ids_para_buscar:
            filtro_base = (self.df_ifd_val['COD_INST_IFD_VAL'] == id_busca) & (self.df_ifd_val['DATA'].isin(datas))
            nomes_busca = [c for c in contas if isinstance(c, str)]
            codigos_busca = [c for c in contas if isinstance(c, int)]
            filtro_nomes = self.df_ifd_val['NOME_CONTA_IFD_VAL'].isin(nomes_busca)
            filtro_codigos = self.df_ifd_val['CONTA_IFD_VAL'].isin(codigos_busca)
            filtro_conta = filtro_nomes | filtro_codigos
            
            df_resultado_parcial = self.df_ifd_val[filtro_base & filtro_conta].copy()

            # 2. Se um resultado parcial for encontrado, adicione-o à lista de coleta
            if not df_resultado_parcial.empty:
                df_resultado_parcial['ID_BUSCA_USADO'] = id_busca
                resultados_coletados.append(df_resultado_parcial)

        # 3. Após o loop, verificar se algum dado foi coletado
        if not resultados_coletados:
            # Retorna DF vazio com a estrutura correta se nada for encontrado
            return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8', 'ID_BUSCA_USADO'] + list(self.df_ifd_val.columns))

        # 4. Consolidar todos os resultados em um único DataFrame
        df_final = pd.concat(resultados_coletados, ignore_index=True)
        
        # Remove duplicatas que podem surgir se a mesma info exata estiver em duas fontes
        df_final.drop_duplicates(inplace=True)

        # 5. Adicionar colunas padronizadas e reordenar (agora no DataFrame final)
        df_final['Nome_Entidade'] = nome_entidade_canonico
        df_final['CNPJ_8'] = cnpj_8
        
        # Define a ordem final das colunas
        cols_base = list(df_final.columns)
        cols_prioritarias = ['Nome_Entidade', 'CNPJ_8', 'ID_BUSCA_USADO']
        cols_restantes = [c for c in cols_base if c not in cols_prioritarias]
        
        ordem_final = cols_prioritarias + cols_restantes
        return df_final.reset_index(drop=True)[ordem_final]


    def get_atributos_cadastro(self, identificador: Union[str, List[str]], atributos: List[str]) -> pd.DataFrame:
        """
        Busca atributos (colunas) específicos do cadastro IFDATA,
        com colunas de identificação padronizadas.
        """
        if not isinstance(identificador, list):
            identificador = [identificador]
        
        resultados = []
        for ident in identificador:
            cnpj_8 = self._find_cnpj(ident)
            if not cnpj_8:
                continue

            # --- Usa a fonte única da verdade para obter o nome ---
            info_ent = self._get_entity_identifiers(cnpj_8)
            nome_entidade = info_ent.get('nome_entidade') or ident # Fallback para o input

            entry = self.df_ifd_cad[self.df_ifd_cad['CNPJ_8'] == cnpj_8]
            if not entry.empty:
                linha = entry.sort_values('DATA', ascending=False).iloc[0]
                
                # --- Constrói um dicionário com a saída padronizada ---
                dados_linha = {
                    'Nome_Entidade': nome_entidade,
                    'CNPJ_8': cnpj_8
                }
                for atr in atributos:
                    # Usa .get() para evitar erro se o atributo não existir na linha
                    dados_linha[atr] = linha.get(atr, None)
                
                resultados.append(dados_linha)

        if not resultados:
            # Retorna DF vazio com a estrutura de colunas correta
            return pd.DataFrame(columns=['Nome_Entidade', 'CNPJ_8'] + atributos)
        
        df_final = pd.DataFrame(resultados)
        
        # Garante a ordem das colunas
        ordem_final = ['Nome_Entidade', 'CNPJ_8'] + [atr for atr in atributos if atr in df_final.columns]
        return df_final[ordem_final]

    def comparar_indicadores(
        self,
        identificadores: List[str],
        indicadores: Dict[str, Dict],
        data: int,
        documento_cosif: Optional[int] = 4060,
        fillna: Optional[Union[int, float, str]] = None
    ) -> pd.DataFrame:
        """
        Cria uma tabela comparativa de indicadores, usando a lógica centralizada
        para obter Nome e CNPJ da entidade.
        """
        lista_resultados = []

        for ident in identificadores:
            cnpj_8 = self._find_cnpj(ident)
            
            if not cnpj_8:
                dados_banco = {'Nome_Entidade': f"'{ident}' não encontrado", 'CNPJ_8': 'N/A'}
                for nome_coluna in indicadores: dados_banco[nome_coluna] = None
                lista_resultados.append(dados_banco)
                continue

            # --- ALTERAÇÃO PRINCIPAL: Usa a fonte única da verdade ---
            # Remove a lógica antiga com `_mapa_nomes_df`
            info_ent = self._get_entity_identifiers(cnpj_8)
            nome_entidade = info_ent.get('nome_entidade') or ident # Fallback para o input
            
            dados_banco = {'Nome_Entidade': nome_entidade, 'CNPJ_8': cnpj_8}

            # O restante da lógica para buscar indicadores permanece o mesmo...
            for nome_coluna, info_ind in indicadores.items():
                valor = None
                tipo = info_ind.get('tipo', '').upper()

                if tipo == 'COSIF':
                    try: conta = info_ind['conta']
                    except KeyError: raise KeyError(f"Indicador '{nome_coluna}' de tipo COSIF precisa da chave 'conta'.")
                    df_res = self.get_dados_cosif(ident, contas=[conta], datas=[data], documentos=[documento_cosif] if documento_cosif else None)
                    if not df_res.empty: valor = df_res.sort_values('DOCUMENTO_COSIF', ascending=False)['VALOR_CONTA_COSIF'].iloc[0]

                elif tipo == 'IFDATA':
                    try: conta = info_ind['conta']
                    except KeyError: raise KeyError(f"Indicador '{nome_coluna}' de tipo IFDATA precisa da chave 'conta'.")
                    df_res = self.get_dados_ifdata(ident, contas=[conta], datas=[data])
                    if not df_res.empty: valor = df_res['VALOR_CONTA_IFD_VAL'].iloc[0]

                elif tipo == 'ATRIBUTO':
                    try: atributo = info_ind['atributo']
                    except KeyError: raise KeyError(f"Indicador '{nome_coluna}' de tipo ATRIBUTO precisa da chave 'atributo'.")
                    df_res = self.get_atributos_cadastro(ident, atributos=[atributo])
                    if not df_res.empty: valor = df_res[atributo].iloc[0]

                else:
                    raise ValueError(f"Tipo de indicador '{info_ind.get('tipo')}' não reconhecido em '{nome_coluna}'.")

                dados_banco[nome_coluna] = valor
            
            lista_resultados.append(dados_banco)

        if not lista_resultados:
            return pd.DataFrame()
            
        df_final = pd.DataFrame(lista_resultados)
        
        cols_indicadores = list(indicadores.keys())
        cols_numericas = [c for c in cols_indicadores if c in df_final.columns and pd.api.types.is_numeric_dtype(df_final[c])]

        if fillna is not None:
            if fillna == 0:
                df_final[cols_numericas] = df_final[cols_numericas].fillna(0)
            elif pd.isna(fillna) or (isinstance(fillna, str) and fillna.lower() == 'nan'):
                df_final[cols_numericas] = df_final[cols_numericas].replace(0, np.nan)

        cols_id = ['Nome_Entidade', 'CNPJ_8']
        ordem_final = cols_id + [col for col in cols_indicadores if col in df_final.columns]
        return df_final[ordem_final]

    def get_serie_temporal_indicador(
        self,
        identificador: str,
        conta: Union[str, int],
        data_inicio: int,
        data_fim: int,
        fonte: str = 'COSIF',
        documento_cosif: Optional[int] = 4060,
        fillna: Optional[Union[int, float, str]] = None
    ) -> pd.DataFrame:
        """
        Busca a série temporal de um indicador, retornando sempre em formato 'long'.

        Esta função é robusta a dados duplicados na fonte e prioriza valores
        numéricos sobre valores nulos (NaN) ao agregar dados de múltiplas fontes.
        """
        # --- Passo 1: Lógica de Identificação e Datas ---
        cnpj_8 = self._find_cnpj(identificador)
        if not cnpj_8:
            print(f"AVISO: Identificador '{identificador}' não encontrado.")
            return pd.DataFrame(columns=['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor'])

        info_ent = self._get_entity_identifiers(cnpj_8)
        nome_entidade = info_ent.get('nome_entidade', identificador)

        try:
            start_date_str = f'{data_inicio // 100}-{data_inicio % 100:02d}-01'
            end_date_ts = pd.to_datetime(f'{data_fim}', format='%Y%m') + MonthEnd(0)
            datas_periodo = pd.date_range(start=start_date_str, end=end_date_ts, freq='ME')
            datas_yyyymm  = datas_periodo.strftime('%Y%m').astype(int).tolist()
        except ValueError:
            print("Erro: Formato de data inválido. Use YYYYMM.")
            return pd.DataFrame()

        # --- Passo 2: Busca dos Dados Brutos ---
        df_bruto = pd.DataFrame()
        valor_col = ''
        if fonte.upper() == 'COSIF':
            df_bruto = self.get_dados_cosif(identificador, contas=[conta], datas=datas_yyyymm, documentos=[documento_cosif] if documento_cosif else None)
            valor_col = 'VALOR_CONTA_COSIF'
        elif fonte.upper() == 'IFDATA':
            df_bruto = self.get_dados_ifdata(identificador, contas=[conta], datas=datas_yyyymm)
            valor_col = 'VALOR_CONTA_IFD_VAL'
        
        if df_bruto.empty:
            return pd.DataFrame(columns=['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor'])

        # Passo 3.1: Criar uma coluna temporária para a ordenação.
        # Esta coluna será True (1) para NaNs e False (0) para números.
        coluna_temp_isna = '_valor_is_na'
        df_bruto[coluna_temp_isna] = df_bruto[valor_col].isna()
        
        # Passo 3.2: Ordenar usando os NOMES das colunas.
        # Isso garante que as linhas com números (False/0) venham ANTES das com NaN (True/1).
        df_bruto.sort_values(by=['DATA', coluna_temp_isna], inplace=True)
        
        # Passo 3.3: Remover a coluna temporária.
        df_bruto.drop(columns=[coluna_temp_isna], inplace=True)

        # Passo 3.4: Pivotar para Limpar e Agregar Duplicatas.
        # `aggfunc='first'` agora pegará de forma confiável o valor numérico.
        df_pivot = df_bruto.pivot_table(
            index='DATA', 
            values=valor_col, 
            aggfunc='first'
        )

        # --- Passo 4: Reindexar e Formatar para o Padrão 'Long' ---
        df_pivot.index = pd.to_datetime(df_pivot.index, format='%Y%m') + MonthEnd(0)
        df_pivot = df_pivot.reindex(datas_periodo)

        df_long = df_pivot.reset_index().rename(columns={'index': 'DATA', valor_col: 'Valor'})

        df_long['Nome_Entidade'] = nome_entidade
        df_long['CNPJ_8'] = cnpj_8
        df_long['Conta'] = conta if isinstance(conta, str) else str(conta)

        # --- Passo 5: Finalizar e Limpar (fillna e dropna) ---
        if fillna is not None:
            if pd.isna(fillna) or (isinstance(fillna, str) and fillna.lower() == 'nan'):
                df_long['Valor'] = df_long['Valor'].replace(0, np.nan)
            elif fillna == 0:
                df_long['Valor'] = df_long['Valor'].fillna(0)

        df_long.dropna(subset=['Valor'], inplace=True)
        
        return df_long[['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor']].reset_index(drop=True)