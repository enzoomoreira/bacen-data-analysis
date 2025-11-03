"""
Analisador Bancário - Facade principal para análise de dados do BCB
"""

import pandas as pd
from typing import List, Dict, Union, Optional, Any
from bacen_analysis.data.loader import DataLoader
from bacen_analysis.data.repository import DataRepository
from bacen_analysis.core.entity_resolver import EntityIdentifierResolver
from bacen_analysis.providers.cosif import COSIFDataProvider
from bacen_analysis.providers.ifdata import IFDATADataProvider
from bacen_analysis.providers.cadastro import CadastroProvider
from bacen_analysis.analysis.comparator import IndicadorComparator
from bacen_analysis.analysis.time_series import TimeSeriesProvider
from bacen_analysis.utils.logger import get_logger


class AnalisadorBancario:
    """
    Uma classe para carregar, conectar e analisar dados financeiros de bancos
    provenientes das fontes COSIF e IFDATA do Banco Central.
    
    Esta classe atua como um Facade, agregando todos os componentes especializados
    e fornecendo uma interface unificada e simples para análise de dados.
    """
    
    def __init__(self, diretorio_output: str):
        """
        Inicializa o Analisador Bancário.
        
        Args:
            diretorio_output: Caminho para o diretório contendo os arquivos .parquet
            
        Raises:
            FileNotFoundError: Se algum arquivo necessário não for encontrado
        """
        self._logger = get_logger(__name__)
        self._logger.info("Iniciando o Analisador Bancário...")
        
        # Camada de dados
        loader = DataLoader(diretorio_output)
        self._repository = DataRepository(loader)
        
        # Carrega dados na inicialização
        self._repository.load()
        
        # Core services
        self._entity_resolver = EntityIdentifierResolver(self._repository)
        
        # Providers
        self._cosif_provider = COSIFDataProvider(self._repository, self._entity_resolver)
        self._ifdata_provider = IFDATADataProvider(self._repository, self._entity_resolver)
        self._cadastro_provider = CadastroProvider(self._repository, self._entity_resolver)
        
        # Analysis modules
        self._comparator = IndicadorComparator(
            self._cosif_provider,
            self._ifdata_provider,
            self._cadastro_provider,
            self._entity_resolver
        )
        self._time_series_provider = TimeSeriesProvider(
            self._cosif_provider,
            self._ifdata_provider,
            self._entity_resolver
        )
        
        # Exposição de dados para compatibilidade (se necessário)
        self.df_cosif_ind = self._repository.df_cosif_ind
        self.df_cosif_prud = self._repository.df_cosif_prud
        self.df_ifd_val = self._repository.df_ifd_val
        self.df_ifd_cad = self._repository.df_ifd_cad
        
        stats = self._repository.get_stats()
        self._logger.info("Analisador Bancário iniciado com sucesso!")
        self._logger.info(f"  - {stats['cosif_ind']:,} linhas em COSIF Individual")
        self._logger.info(f"  - {stats['cosif_prud']:,} linhas em COSIF Prudencial")
        self._logger.info(f"  - {stats['ifd_val']:,} linhas em IFDATA Valores")
        self._logger.info(f"  - {stats['ifd_cad']:,} linhas em IFDATA Cadastro")
    
    # Métodos públicos - delegam para os providers
    
    def get_dados_cosif(
        self,
        identificador: str,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        tipo: str,
        documentos: Optional[Union[int, List[int]]] = None
    ) -> pd.DataFrame:
        """
        Busca dados COSIF com tipo obrigatório.
        
        Args:
            identificador: Nome ou CNPJ da instituição
            contas: Lista de nomes ou códigos de contas COSIF
            datas: Data única ou lista de datas no formato YYYYMM
            tipo: Tipo de dados OBRIGATÓRIO ('prudencial' ou 'individual')
            documentos: Documento único ou lista de documentos COSIF
            
        Returns:
            DataFrame com os dados solicitados
            
        Raises:
            InvalidScopeError: Se o tipo não for válido
            EntityNotFoundError: Se a entidade não for encontrada
            DataUnavailableError: Se os dados não estiverem disponíveis
        """
        return self._cosif_provider.get_dados(
            identificador=identificador,
            contas=contas,
            datas=datas,
            tipo=tipo,
            documentos=documentos
        )
    
    def get_dados_ifdata(
        self,
        identificador: str,
        contas: Union[List[str], List[int], List[Union[str, int]]],
        datas: Union[int, List[int]],
        escopo: str
    ) -> pd.DataFrame:
        """
        Busca dados IFDATA com escopo obrigatório.
        
        Args:
            identificador: Nome ou CNPJ da instituição
            contas: Lista de nomes ou códigos de contas IFDATA
            datas: Data única ou lista de datas no formato YYYYMM
            escopo: Escopo OBRIGATÓRIO da busca ('individual', 'prudencial', 'financeiro')
            
        Returns:
            DataFrame com os dados solicitados
            
        Raises:
            InvalidScopeError: Se o escopo não for válido
            EntityNotFoundError: Se a entidade não for encontrada
            DataUnavailableError: Se os dados não estiverem disponíveis
        """
        return self._ifdata_provider.get_dados(
            identificador=identificador,
            contas=contas,
            datas=datas,
            escopo=escopo
        )
    
    def get_atributos_cadastro(
        self,
        identificador: Union[str, List[str]],
        atributos: List[str]
    ) -> pd.DataFrame:
        """
        Busca atributos (colunas) específicos do cadastro IFDATA,
        com colunas de identificação padronizadas.
        
        Args:
            identificador: Nome, CNPJ ou lista de identificadores de instituições
            atributos: Lista de nomes de atributos (colunas) do cadastro
            
        Returns:
            DataFrame com os atributos solicitados
        """
        return self._cadastro_provider.get_atributos(
            identificador=identificador,
            atributos=atributos
        )
    
    def comparar_indicadores(
        self,
        identificadores: List[str],
        indicadores: Dict[str, Dict],
        data: int,
        fillna: Optional[Union[int, float, str]] = None
    ) -> pd.DataFrame:
        """
        Cria uma tabela comparativa de indicadores, usando a lógica centralizada
        para obter Nome e CNPJ da entidade.
        
        Args:
            identificadores: Lista de identificadores (nomes ou CNPJs) de instituições
            indicadores: Dicionário de configuração de indicadores. Cada indicador deve ter:
                - 'tipo' ('COSIF', 'IFDATA', ou 'ATRIBUTO')
                - 'conta' (para COSIF/IFDATA) ou 'atributo' (para ATRIBUTO)
                - Para indicadores COSIF: 'tipo_cosif' ('prudencial' ou 'individual') e 
                  'documento_cosif' (OBRIGATÓRIO - especificar na configuração do indicador)
                - Para indicadores IFDATA: 'escopo_ifdata' ('individual', 'prudencial' ou 'financeiro')
            data: Data no formato YYYYMM para comparação
            fillna: Valor para preencher NaNs
            
        Returns:
            DataFrame pivotado com identificadores nas linhas e indicadores nas colunas
            
        Raises:
            InvalidScopeError: Se documento_cosif não for especificado em indicador COSIF
            KeyError: Se configuração de indicador estiver incompleta
        """
        return self._comparator.comparar(
            identificadores=identificadores,
            indicadores=indicadores,
            data=data,
            fillna=fillna
        )
    
    def get_serie_temporal_indicador(
        self,
        identificador: str,
        conta: Union[str, int],
        fonte: str = 'COSIF',
        documento_cosif: Optional[int] = None,
        tipo_cosif: Optional[str] = None,
        escopo_ifdata: Optional[str] = None,
        fill_value: Optional[Union[int, float]] = None,
        replace_zeros_with_nan: bool = False,
        drop_na: bool = True,
        data_inicio: Optional[int] = None,
        data_fim: Optional[int] = None,
        datas: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Busca a série temporal de um indicador, com controle de escopo obrigatório.

        Args:
            identificador: Nome ou CNPJ da instituição
            conta: Nome ou código da conta/indicador
            fonte: Fonte dos dados ('COSIF' ou 'IFDATA')
            documento_cosif: Documento COSIF a usar (OBRIGATÓRIO se fonte='COSIF')
            tipo_cosif: Tipo OBRIGATÓRIO para COSIF ('prudencial' ou 'individual')
            escopo_ifdata: Escopo OBRIGATÓRIO para IFDATA ('individual', 'prudencial', 'financeiro')
            fill_value: Valor para preencher NaNs
            replace_zeros_with_nan: Se True, converte zeros em NaN
            drop_na: Se True, remove linhas com NaN
            data_inicio: Data inicial no formato YYYYMM
            data_fim: Data final no formato YYYYMM
            datas: Lista de datas específicas

        Returns:
            DataFrame com série temporal
            
        Raises:
            ValueError: Se escopo/tipo não for especificado quando necessário
            InvalidScopeError: Se escopo/tipo inválido
            EntityNotFoundError: Se identificador não encontrado
        """
        return self._time_series_provider.get_serie_temporal(
            identificador=identificador,
            conta=conta,
            fonte=fonte,
            documento_cosif=documento_cosif,
            tipo_cosif=tipo_cosif,
            escopo_ifdata=escopo_ifdata,
            fill_value=fill_value,
            replace_zeros_with_nan=replace_zeros_with_nan,
            drop_na=drop_na,
            data_inicio=data_inicio,
            data_fim=data_fim,
            datas=datas
        )

    def get_series_temporais_lote(
        self,
        requisicoes: List[Dict[str, Any]],
        fill_value: Optional[Union[int, float]] = None,
        replace_zeros_with_nan: bool = False,
        drop_na: bool = True
    ) -> pd.DataFrame:
        """
        Busca múltiplas séries temporais em um único lote otimizado.

        Esta função é significativamente mais rápida que chamar get_serie_temporal_indicador()
        múltiplas vezes, pois resolve todos os identificadores de uma só vez e
        usa métodos otimizados internos.

        Args:
            requisicoes: Lista de dicionários com:
                - identificador: str (nome ou CNPJ da instituição)
                - conta: str | int (nome ou código da conta/indicador)
                - fonte: 'COSIF' | 'IFDATA'
                - datas: List[int] (datas no formato YYYYMM)
                - documento_cosif: Optional[int] (para COSIF, default: 4060)
                - escopo_ifdata: str (OBRIGATÓRIO para IFDATA: 'individual', 'prudencial' ou 'financeiro')
                - nome_indicador: str (para identificação na coluna 'Conta')
            fill_value: Valor para preencher NaNs (aplicado a todos)
            replace_zeros_with_nan: Se True, converte zeros em NaN (aplicado a todos)
            drop_na: Se True, remove linhas com NaN (aplicado a todos)

        Returns:
            DataFrame consolidado com colunas:
            ['DATA', 'Nome_Entidade', 'CNPJ_8', 'Conta', 'Valor']

        Example:
            >>> requisicoes = [
            ...     {
            ...         'identificador': '00000000',
            ...         'conta': 'Ativo Total',
            ...         'fonte': 'IFDATA',
            ...         'datas': [202501, 202502, 202503],
            ...         'escopo_ifdata': 'prudencial',
            ...         'nome_indicador': 'Ativo Total'
            ...     }
            ... ]
            >>> df = analisador.get_series_temporais_lote(requisicoes, fill_value=0)
        """
        return self._time_series_provider.get_series_temporais_lote(
            requisicoes=requisicoes,
            fill_value=fill_value,
            replace_zeros_with_nan=replace_zeros_with_nan,
            drop_na=drop_na
        )
    
    # Métodos auxiliares
    
    def clear_cache(self) -> None:
        """Limpa o cache LRU dos métodos internos."""
        self._entity_resolver.clear_cache()
    
    def reload_data(self) -> None:
        """Recarrega todos os arquivos Parquet e recria os mapeamentos internos."""
        self._logger.info("Recarregando dados...")
        self._repository.reload()
        self._entity_resolver.reload_mapping()
        self.clear_cache()
        
        # Atualiza referências diretas (se ainda forem usadas)
        self.df_cosif_ind = self._repository.df_cosif_ind
        self.df_cosif_prud = self._repository.df_cosif_prud
        self.df_ifd_val = self._repository.df_ifd_val
        self.df_ifd_cad = self._repository.df_ifd_cad
        
        stats = self._repository.get_stats()
        self._logger.info("Dados recarregados com sucesso!")
        self._logger.info(f"  - {stats['cosif_ind']:,} linhas em COSIF Individual")
        self._logger.info(f"  - {stats['cosif_prud']:,} linhas em COSIF Prudencial")
        self._logger.info(f"  - {stats['ifd_val']:,} linhas em IFDATA Valores")
        self._logger.info(f"  - {stats['ifd_cad']:,} linhas em IFDATA Cadastro")

