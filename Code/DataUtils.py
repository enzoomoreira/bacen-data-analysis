# Code/DataUtils.py

import pandas as pd
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
# CLASSE DE ANÁLISE BANCÁRIA (VERSÃO COM NOVAS FUNCIONALIDADES)
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

    def get_dados_ifdata(self, identificador: str, contas: List[str], datas: Union[int, List[int]]) -> pd.DataFrame:
        """Busca dados de contas específicas no IFDATA Valores para um banco."""
        if not isinstance(datas, list): datas = [datas]
        cnpj_8 = self._find_cnpj(identificador)
        if not cnpj_8: return pd.DataFrame()
        info_ent = self._get_entity_identifiers(cnpj_8)
        cod_congl_busca = info_ent.get('cod_congl_prud')
        if not cod_congl_busca: return pd.DataFrame()
        filtro = (
            (self.df_ifd_val['COD_INST_IFD_VAL'] == cod_congl_busca) &
            (self.df_ifd_val['DATA'].isin(datas)) &
            (self.df_ifd_val['NOME_CONTA_IFD_VAL'].isin(contas))
        )
        temp_df = self.df_ifd_val[filtro].copy()
        if not temp_df.empty:
            temp_df['BANCO_CONSULTADO'] = identificador
        return temp_df.reset_index(drop=True)

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
        documento_cosif: Optional[int] = 4060
    ) -> pd.DataFrame:
        """
        Cria uma tabela comparativa de indicadores para uma lista de bancos em uma data específica.
        """
        lista_resultados = []
        for ident in identificadores:
            dados_banco = {'Banco': ident}
            for nome_coluna, info_ind in indicadores.items():
                valor = None
                tipo = info_ind['tipo'].upper()
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
        return pd.DataFrame(lista_resultados).set_index('Banco') if lista_resultados else pd.DataFrame()

    def get_serie_temporal_indicador(
        self,
        identificador: str,
        conta: str,
        data_inicio: int,
        data_fim: int,
        fonte: str = 'COSIF',
        documento_cosif: Optional[int] = 4060
    ) -> pd.DataFrame:
        """
        Busca a série temporal de um indicador para um banco.

        Args:
            identificador (str): Nome do banco ou CNPJ_8.
            conta (str): Nome exato da conta.
            data_inicio (int): Data de início da série (AnoMes).
            data_fim (int): Data de fim da série (AnoMes).
            fonte (str): 'COSIF' ou 'IFDATA'.
            documento_cosif (Optional[int]): Documento específico para a fonte COSIF.

        Returns:
            pd.DataFrame: DataFrame com a série temporal (índice de data e coluna com valores).
        """
        try:
            start_date_str = f'{data_inicio // 100}-{data_inicio % 100:02d}-01'
            end_date_str = f'{data_fim // 100}-{data_fim % 100:02d}-01'
            datas = pd.date_range(start=start_date_str, end=end_date_str, freq='MS').strftime('%Y%m').astype(int).tolist()
        except ValueError:
            print("Erro: Formato de data inválido. Use YYYYMM.")
            return pd.DataFrame()

        if fonte.upper() == 'COSIF':
            df = self.get_dados_cosif(identificador, contas=[conta], datas=datas, tipo='prudencial', documentos=[documento_cosif] if documento_cosif else None)
            if not df.empty:
                df_pivot = df.pivot_table(index='DATA', values='VALOR_CONTA_COSIF', aggfunc='first').rename(columns={'VALOR_CONTA_COSIF': conta})
                df_pivot.index = pd.to_datetime(df_pivot.index, format='%Y%m')
                return df_pivot
        
        elif fonte.upper() == 'IFDATA':
            df = self.get_dados_ifdata(identificador, contas=[conta], datas=datas)
            if not df.empty:
                df_pivot = df.pivot_table(index='DATA', values='VALOR_CONTA_IFD_VAL', aggfunc='first').rename(columns={'VALOR_CONTA_IFD_VAL': conta})
                df_pivot.index = pd.to_datetime(df_pivot.index, format='%Y%m')
                return df_pivot
                
        return pd.DataFrame()