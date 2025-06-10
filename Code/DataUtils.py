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

        Args:
            diretorio_output (str): Caminho para o diretório onde os arquivos .parquet estão salvos.
        """
        print("Iniciando o Analisador Bancário...")
        
        base_path = Path(diretorio_output)
        
        try:
            # --- Carregar DataFrames Principais ---
            self.df_cosif_ind = pd.read_parquet(base_path / 'df_cosif_individual.parquet')
            self.df_cosif_prud = pd.read_parquet(base_path / 'df_cosif_prudencial.parquet')
            self.df_ifd_val = pd.read_parquet(base_path / 'df_ifdata_valores.parquet')
            self.df_ifd_cad = pd.read_parquet(base_path / 'df_ifdata_cadastro.parquet')
            
            # --- Carregar Dicionários de Contas ---
            self.dict_contas_cosif_ind = pd.read_excel(base_path / 'dicionario_contas_cosif_individual.xlsx')
            self.dict_contas_cosif_prud = pd.read_excel(base_path / 'dicionario_contas_cosif_prudencial.xlsx')
            self.dict_contas_ifd_val = pd.read_excel(base_path / 'dicionario_contas_ifdata_valores.xlsx')

            # --- Criar um mapeamento unificado de nomes e CNPJs para busca rápida ---
            self._criar_mapa_identificadores()
            
            print("Analisador Bancário iniciado com sucesso!")
            print(f"  - {self.df_cosif_ind.shape[0]:,} linhas em COSIF Individual")
            print(f"  - {self.df_cosif_prud.shape[0]:,} linhas em COSIF Prudencial")
            print(f"  - {self.df_ifd_val.shape[0]:,} linhas em IFDATA Valores")
            print(f"  - {self.df_ifd_cad.shape[0]:,} linhas em IFDATA Cadastro")
            print(f"  - Mapeamento interno criado para {len(self._mapa_nomes):,} nomes únicos.")
            
        except FileNotFoundError as e:
            print(f"Erro Crítico: Arquivo não encontrado! Verifique o caminho do diretório de output.")
            print(f"Detalhe: {e}")
            raise

    def _criar_mapa_identificadores(self):
        """
        (Método interno) Cria um dicionário para traduzir nomes de bancos para CNPJ_8.
        """
        # Prioriza nomes do cadastro IFDATA por serem mais completos
        mapa1 = self.df_ifd_cad[['NOME_INSTITUICAO_IFD_CAD', 'CNPJ_8']].dropna().drop_duplicates()
        mapa2 = self.df_cosif_prud[['NOME_INSTITUICAO_COSIF', 'CNPJ_8']].dropna().drop_duplicates()
        mapa3 = self.df_cosif_ind[['NOME_INSTITUICAO_COSIF', 'CNPJ_8']].dropna().drop_duplicates()

        # Renomeia colunas para unificar
        mapa1.columns = ['nome', 'cnpj_8']
        mapa2.columns = ['nome', 'cnpj_8']
        mapa3.columns = ['nome', 'cnpj_8']
        
        # Concatena e remove duplicatas, dando prioridade ao primeiro (IFDATA CAD)
        mapa_final = pd.concat([mapa1, mapa2, mapa3]).drop_duplicates(subset='nome', keep='first')
        
        # Transforma em um dicionário rápido {NOME_MAIUSCULO: CNPJ_8}
        self._mapa_nomes = pd.Series(mapa_final.cnpj_8.values, index=mapa_final.nome.str.upper()).to_dict()

    def _find_cnpj(self, identificador: str) -> Optional[str]:
        """
        (Método interno) Encontra o CNPJ_8 a partir de um nome ou de um CNPJ.
        """
        if re.fullmatch(r'\d{8}', identificador):
            return identificador # Já é um CNPJ_8
        
        # Busca no mapa de nomes
        cnpj_encontrado = self._mapa_nomes.get(identificador.upper())
        if not cnpj_encontrado:
            print(f"AVISO: Identificador '{identificador}' não encontrado.")
            return None
        return cnpj_encontrado

    def _get_entity_identifiers(self, cnpj_8: str) -> Dict[str, Optional[str]]:
        """
        (Método interno) O 'tradutor universal'. Pega um CNPJ_8 e encontra todos os 
        outros códigos e CNPJs relacionados a ele nas diferentes fontes.
        """
        if not cnpj_8:
            return {}

        info = {
            'cnpj_interesse': cnpj_8,
            'cnpj_reporte_cosif': None, # CNPJ que efetivamente reporta no COSIF (pode ser o do líder)
            'cod_congl_prud': None
        }

        # Busca no cadastro IFDATA, nossa fonte mais rica para mapeamentos
        entry_cad = self.df_ifd_cad[self.df_ifd_cad['CNPJ_8'] == cnpj_8]
        if not entry_cad.empty:
            linha = entry_cad.sort_values('DATA', ascending=False).iloc[0] # Pega a mais recente
            info['cod_congl_prud'] = linha.get('COD_CONGL_PRUD_IFD_CAD')
            info['cnpj_reporte_cosif'] = linha.get('CNPJ_LIDER_8_IFD_CAD')

        # Se não achou um CNPJ de reporte no cadastro, assume que a própria entidade reporta
        if not info['cnpj_reporte_cosif']:
            info['cnpj_reporte_cosif'] = cnpj_8
            
        return info

    def get_dados_cosif(
        self,
        identificador: Union[str, List[str]],
        contas: List[str],
        datas: Union[int, List[int]],
        tipo: str = 'prudencial',
        documentos: Optional[Union[int, List[int]]] = None
    ) -> pd.DataFrame:
        """
        Busca dados de contas específicas no COSIF para um ou mais bancos.

        Args:
            identificador (str ou list): Nome(s) do banco ou CNPJ_8.
            contas (list): Lista de nomes exatos das contas COSIF.
            datas (int ou list): AnoMes (ex: 202312) ou lista de AnoMes.
            tipo (str): 'prudencial' (padrão) ou 'individual'.
            documentos (int ou list, opcional): Código(s) do documento (ex: 4010, 4060).

        Returns:
            pd.DataFrame: Um DataFrame com os dados encontrados.
        """
        df_base = self.df_cosif_prud if tipo == 'prudencial' else self.df_cosif_ind
        
        # Padroniza inputs
        if not isinstance(identificador, list): identificador = [identificador]
        if not isinstance(datas, list): datas = [datas]
        if documentos and not isinstance(documentos, list): documentos = [documentos]
        
        resultados = []
        for ident in identificador:
            cnpj_8 = self._find_cnpj(ident)
            if not cnpj_8: continue

            info_ent = self._get_entity_identifiers(cnpj_8)
            cnpj_busca = info_ent.get('cnpj_reporte_cosif', cnpj_8)

            filtro = (
                (df_base['CNPJ_8'] == cnpj_busca) &
                (df_base['DATA'].isin(datas)) &
                (df_base['NOME_CONTA_COSIF'].isin(contas))
            )
            
            if documentos:
                filtro &= df_base['DOCUMENTO_COSIF'].isin(documentos)
            
            temp_df = df_base[filtro].copy()
            if not temp_df.empty:
                temp_df['BANCO_CONSULTADO'] = ident # Adiciona o nome original da consulta
                resultados.append(temp_df)

        if not resultados:
            return pd.DataFrame()
            
        return pd.concat(resultados).reset_index(drop=True)

    def get_atributos_cadastro(self, identificador: Union[str, List[str]], atributos: List[str]) -> pd.DataFrame:
        """
        Busca atributos (colunas) específicos do cadastro IFDATA.

        Args:
            identificador (str ou list): Nome(s) do banco ou CNPJ_8.
            atributos (list): Lista de nomes de colunas do cadastro a serem retornadas.

        Returns:
            pd.DataFrame: DataFrame com os atributos para cada banco consultado.
        """
        if not isinstance(identificador, list): identificador = [identificador]
        
        resultados = []
        for ident in identificador:
            cnpj_8 = self._find_cnpj(ident)
            if not cnpj_8: continue
            
            entry = self.df_ifd_cad[self.df_ifd_cad['CNPJ_8'] == cnpj_8]
            if not entry.empty:
                linha_recente = entry.sort_values('DATA', ascending=False).iloc[0].copy()
                linha_recente['BANCO_CONSULTADO'] = ident
                # Garante que todas as colunas pedidas existam, preenchendo com None se faltar
                for atr in atributos:
                    if atr not in linha_recente.index:
                        linha_recente[atr] = None
                resultados.append(linha_recente[atributos + ['BANCO_CONSULTADO']])

        if not resultados:
            return pd.DataFrame()
            
        return pd.DataFrame(resultados).reset_index(drop=True)

    def comparar_indicadores(
        self,
        identificadores: List[str],
        indicadores: Dict[str, Dict],
        data: int,
        documento_cosif: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Cria uma tabela comparativa de indicadores para uma lista de bancos em uma data específica.

        Args:
            identificadores (List[str]): Lista de nomes de bancos ou CNPJs.
            indicadores (Dict[str, Dict]): Dicionário descrevendo os indicadores.
                Ex: {'PL': {'tipo': 'COSIF', 'conta': 'PATRIMÔNIO LÍQUIDO'},
                     'Basileia': {'tipo': 'IFDATA', 'conta': 'Índice de Basileia'},
                     'Situação': {'tipo': 'Atributo', 'atributo': 'SITUACAO_IFD_CAD'}}
            data (int): A data (AnoMes) para a consulta.
            documento_cosif (Optional[int]): Filtra por um documento COSIF específico (ex: 4010).

        Returns:
            pd.DataFrame: Tabela com bancos nas linhas e indicadores nas colunas.
        """
        lista_resultados = []

        for ident in identificadores:
            cnpj_8 = self._find_cnpj(ident)
            if not cnpj_8: continue

            info_ent = self._get_entity_identifiers(cnpj_8)
            dados_banco = {'Banco': ident, 'CNPJ_8': cnpj_8}

            for nome_coluna, info_ind in indicadores.items():
                valor = None
                tipo = info_ind['tipo'].upper()
                
                if tipo == 'COSIF':
                    cnpj_busca = info_ent.get('cnpj_reporte_cosif', cnpj_8)
                    df_res = self.get_dados_cosif(
                        identificador=cnpj_busca,
                        contas=[info_ind['conta']],
                        datas=[data],
                        documentos=documento_cosif
                    )
                    if not df_res.empty:
                        valor = df_res['VALOR_CONTA_COSIF'].iloc[0]

                # ... (Lógica para IFDATA e Atributo a ser implementada de forma similar) ...

                elif tipo == 'ATRIBUTO':
                    df_res = self.get_atributos_cadastro(
                        identificador=cnpj_8,
                        atributos=[info_ind['atributo']]
                    )
                    if not df_res.empty:
                        valor = df_res[info_ind['atributo']].iloc[0]
                        
                dados_banco[nome_coluna] = valor
            lista_resultados.append(dados_banco)

        if not lista_resultados:
            return pd.DataFrame()
            
        return pd.DataFrame(lista_resultados).set_index('Banco')