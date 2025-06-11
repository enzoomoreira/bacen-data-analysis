# Code/DataUtils.py

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Dict, Union, Optional

# ==============================================================================
# FUNÇÕES DE UTILIDADE GLOBAL
# ==============================================================================

def standardize_cnpj_base8(cnpj_input: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Padroniza um CNPJ ou código para uma string de 8 dígitos."""
    def _process_single_cnpj(cnpj_element_val):
        if pd.isna(cnpj_element_val): return None
        cnpj_str_val = str(cnpj_element_val).split('.')[0]
        cleaned = re.sub(r'[^0-9]', '', cnpj_str_val)
        if not cleaned: return None
        return cleaned.ljust(8, '0')[:8]

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
        """(Método interno) 'Tradutor universal' de identificadores."""
        info = {'cnpj_interesse': cnpj_8, 'cnpj_reporte_cosif': cnpj_8, 'cod_congl_prud': None}
        if not cnpj_8: return info
        entry_cad = self.df_ifd_cad[self.df_ifd_cad['CNPJ_8'] == cnpj_8].sort_values('DATA', ascending=False)
        if entry_cad.empty: return info
        linha_interesse = entry_cad.iloc[0]
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

    def get_dados_cosif(self, identificador: str, contas: List[str], datas: Union[int, List[int]], tipo: str = 'prudencial', documentos: Optional[Union[int, List[int]]] = None) -> pd.DataFrame:
        """Busca dados de contas específicas no COSIF para um banco."""
        df_base = self.df_cosif_prud if tipo == 'prudencial' else self.df_cosif_ind
        if not isinstance(datas, list): datas = [datas]
        if documentos and not isinstance(documentos, list): documentos = [documentos]
        cnpj_8 = self._find_cnpj(identificador)
        if not cnpj_8: return pd.DataFrame()
        info_ent = self._get_entity_identifiers(cnpj_8)
        cnpj_busca = info_ent.get('cnpj_reporte_cosif', cnpj_8)
        if not cnpj_busca: return pd.DataFrame()
        filtro = (df_base['CNPJ_8'] == cnpj_busca) & (df_base['DATA'].isin(datas)) & (df_base['NOME_CONTA_COSIF'].isin(contas))
        if documentos:
            filtro &= df_base['DOCUMENTO_COSIF'].isin(documentos)
        temp_df = df_base[filtro].copy()
        if not temp_df.empty:
            temp_df['BANCO_CONSULTADO'] = identificador
        return temp_df.reset_index(drop=True)

    def get_dados_ifdata(
        self,
        identificador: str,
        contas: List[str],
        datas: Union[int, List[int]]
    ) -> pd.DataFrame:
        """
        Busca dados de contas específicas no IFDATA Valores para um banco.
        Implementa uma busca em cascata de 3 níveis:
        1. Código do Conglomerado Prudencial
        2. Código do Conglomerado Financeiro
        3. Código da Instituição Individual (CNPJ_8)
        """
        if not isinstance(datas, list):
            datas = [datas]
        
        # Passo 1: Encontrar todos os identificadores possíveis para a entidade
        cnpj_8 = self._find_cnpj(identificador)
        if not cnpj_8:
            return pd.DataFrame()

        # O _get_entity_identifiers já nos dá o cnpj_8 e o cod_congl_prud.
        # Agora, também precisamos do cod_congl_fin.
        info_ent = self._get_entity_identifiers(cnpj_8)
        
        # Busca a linha de cadastro para pegar o código financeiro
        entry_cad = self.df_ifd_cad[self.df_ifd_cad['CNPJ_8'] == cnpj_8].sort_values('DATA', ascending=False)
        cod_congl_fin_busca = None
        if not entry_cad.empty:
            cod_congl_fin_busca = entry_cad.iloc[0].get('COD_CONGL_FIN_IFD_CAD')

        # Cria a lista de IDs para a busca em cascata, na ordem de prioridade
        ids_para_buscar = [
            info_ent.get('cod_congl_prud'),
            cod_congl_fin_busca,
            cnpj_8
        ]
        # Remove Nones e duplicatas, mantendo a ordem
        ids_para_buscar = [str(i) for i in ids_para_buscar if pd.notna(i)]
        ids_para_buscar = list(dict.fromkeys(ids_para_buscar))

        # Passo 2: Iterar sobre os IDs e retornar o primeiro resultado encontrado
        for id_busca in ids_para_buscar:
            filtro = (
                (self.df_ifd_val['COD_INST_IFD_VAL'] == id_busca) &
                (self.df_ifd_val['DATA'].isin(datas)) &
                (self.df_ifd_val['NOME_CONTA_IFD_VAL'].isin(contas))
            )
            df_resultado = self.df_ifd_val[filtro].copy()
            
            # Se encontrou resultado, anexa informações e retorna.
            if not df_resultado.empty:
                df_resultado['BANCO_CONSULTADO'] = identificador
                df_resultado['ID_BUSCA_USADO'] = id_busca # Info de debug útil
                return df_resultado.reset_index(drop=True)

        # Se nenhuma das tentativas funcionou, retorna um DataFrame vazio.
        return pd.DataFrame()

    def get_atributos_cadastro(self, identificador: Union[str, List[str]], atributos: List[str]) -> pd.DataFrame:
        """Busca atributos (colunas) específicos do cadastro IFDATA."""
        if not isinstance(identificador, list): identificador = [identificador]
        resultados = []
        for ident in identificador:
            cnpj_8 = self._find_cnpj(ident)
            if not cnpj_8: continue
            entry = self.df_ifd_cad[self.df_ifd_cad['CNPJ_8'] == cnpj_8]
            if not entry.empty:
                linha = entry.sort_values('DATA', ascending=False).iloc[0].copy()
                linha['BANCO_CONSULTADO'] = ident
                for atr in atributos:
                    if atr not in linha.index: linha[atr] = None
                resultados.append(linha[atributos + ['BANCO_CONSULTADO']])
        return pd.DataFrame(resultados) if resultados else pd.DataFrame()

    def comparar_indicadores(
        self,
        identificadores: List[str],
        indicadores: Dict[str, Dict],
        data: int,
        documento_cosif: Optional[int] = 4060,
        fillna: Optional[Union[int, float, str]] = None
    ) -> pd.DataFrame:
        """
        Cria uma tabela comparativa de indicadores, exibindo sempre o Nome e o CNPJ da entidade.
        A apresentação é limpa, sem a coluna de input original.
        """
        lista_resultados = []

        for ident in identificadores:
            # Passo 1: Encontrar os identificadores padronizados
            cnpj_8 = self._find_cnpj(ident)
            
            if not cnpj_8:
                # Se não encontrar, cria uma linha de erro para clareza
                dados_banco = {'Nome_Entidade': f"'{ident}' não encontrado", 'CNPJ_8': 'N/A'}
                for nome_coluna in indicadores: dados_banco[nome_coluna] = None
                lista_resultados.append(dados_banco)
                continue

            # Busca o nome principal associado ao CNPJ encontrado
            nome_entidade_match = self._mapa_nomes_df[self._mapa_nomes_df['cnpj_8'] == cnpj_8]
            nome_entidade = nome_entidade_match['nome'].iloc[0] if not nome_entidade_match.empty else ident

            # Inicia o dicionário de resultados com os identificadores limpos
            dados_banco = {'Nome_Entidade': nome_entidade, 'CNPJ_8': cnpj_8}

            # Passo 2: Buscar o valor de cada indicador
            for nome_coluna, info_ind in indicadores.items():
                valor = None
                tipo = info_ind['tipo'].upper()
                
                # A lógica de busca interna permanece a mesma, pois já é robusta
                if tipo == 'COSIF':
                    df_res = self.get_dados_cosif(ident, contas=[info_ind['conta']], datas=[data], tipo='prudencial', documentos=[documento_cosif] if documento_cosif else None)
                    if not df_res.empty: valor = df_res.sort_values('DOCUMENTO_COSIF', ascending=False)['VALOR_CONTA_COSIF'].iloc[0]
                
                elif tipo == 'IFDATA':
                    df_res = self.get_dados_ifdata(ident, contas=[info_ind['conta']], datas=[data])
                    if not df_res.empty: valor = df_res['VALOR_CONTA_IFD_VAL'].iloc[0]

                elif tipo == 'ATRIBUTO':
                    df_res = self.get_atributos_cadastro(ident, atributos=[info_ind['atributo']])
                    if not df_res.empty: valor = df_res[info_ind['atributo']].iloc[0]
                        
                dados_banco[nome_coluna] = valor
            
            lista_resultados.append(dados_banco)

        if not lista_resultados:
            return pd.DataFrame()
            
        # Passo 3: Montar o DataFrame final
        df_final = pd.DataFrame(lista_resultados)
        
        cols_indicadores = list(indicadores.keys())

        # Seleciona apenas as colunas de indicadores numéricos para aplicar a lógica
        cols_numericas = [c for c in cols_indicadores if c in df_final.columns and pd.api.types.is_numeric_dtype(df_final[c])]

        if fillna is not None:
            if fillna == 0:
                # Cenário: Preencher ausentes com 0
                df_final[cols_numericas] = df_final[cols_numericas].fillna(0)
            elif pd.isna(fillna) or (isinstance(fillna, str) and fillna.lower() == 'nan'):
                # Cenário: Tratar 0 como ausente (NaN)
                df_final[cols_numericas] = df_final[cols_numericas].replace(0, np.nan)

        cols_id = ['Nome_Entidade', 'CNPJ_8']
        ordem_final = cols_id + [col for col in cols_indicadores if col in df_final.columns]
        return df_final[ordem_final]

    def get_serie_temporal_indicador(
        self,
        identificador: str,
        conta: str,
        data_inicio: int,
        data_fim: int,
        fonte: str = 'COSIF',
        documento_cosif: Optional[int] = 4060,
        fillna: Optional[Union[int, float, str]] = None
    ) -> pd.DataFrame:
        """
        Busca a série temporal de um indicador, com opção flexível de preenchimento.

        Args:
            ...
            fillna (opcional):
                - None (padrão): Retorna os dados como estão (0 é 0, ausente é NaN).
                - 0: Preenche todos os valores ausentes (NaN) com 0.
                - np.nan ou 'nan': Converte todos os 0s e ausentes para NaN.
        """
        try:
            start_date_str = f'{data_inicio // 100}-{data_inicio % 100:02d}-01'
            end_date_str = f'{data_fim // 100}-{data_fim % 100:02d}-01'
            datas_periodo = pd.date_range(start=start_date_str, end=end_date_str, freq='MS')
            datas_yyyymm = datas_periodo.strftime('%Y%m').astype(int).tolist()
        except ValueError:
            print("Erro: Formato de data inválido. Use YYYYMM.")
            return pd.DataFrame()

        df_pivot = pd.DataFrame()
        if fonte.upper() == 'COSIF':
            df = self.get_dados_cosif(identificador, contas=[conta], datas=datas_yyyymm, tipo='prudencial', documentos=[documento_cosif] if documento_cosif else None)
            if not df.empty:
                df_pivot = df.pivot_table(index='DATA', values='VALOR_CONTA_COSIF', aggfunc='first').rename(columns={'VALOR_CONTA_COSIF': conta})
        
        elif fonte.upper() == 'IFDATA':
            df = self.get_dados_ifdata(identificador, contas=[conta], datas=datas_yyyymm)
            if not df.empty:
                df_pivot = df.pivot_table(index='DATA', values='VALOR_CONTA_IFD_VAL', aggfunc='first').rename(columns={'VALOR_CONTA_IFD_VAL': conta})
        
        # Se não encontrou nenhum dado em nenhuma fonte, retorna um DataFrame vazio
        if df_pivot.empty:
            return pd.DataFrame()

        # Converte o índice para Datetime para o reindex
        df_pivot.index = pd.to_datetime(df_pivot.index, format='%Y%m')
        
        # Reindexa para garantir que todos os meses do período estejam presentes, preenchendo com NaN
        df_pivot = df_pivot.reindex(datas_periodo)
        
        # --- LÓGICA DE PREENCHIMENTO APLICADA AQUI ---
        if fillna is not None:
            if pd.isna(fillna) or (isinstance(fillna, str) and fillna.lower() == 'nan'):
                # Cenário: Tratar 0 como ausente (NaN)
                df_pivot[conta] = df_pivot[conta].replace(0, np.nan)
            elif fillna == 0:
                # Cenário: Preencher ausentes com 0
                df_pivot[conta] = df_pivot[conta].fillna(0)
            # Você poderia adicionar outras lógicas aqui, como .fillna('ffill') para preenchimento forward
        
        return df_pivot