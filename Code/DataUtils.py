# Code/DataUtils.py

import pandas as pd
import re

# --- Sua função standardize_cnpj_base8 ---
def standardize_cnpj_base8(cnpj_input: str | pd.Series) -> str | pd.Series:
    # ... (código completo da função como definido e testado anteriormente)
    def _process_single_cnpj(cnpj_element_val):
        if pd.isna(cnpj_element_val): return "00000000"
        cnpj_str_val = str(cnpj_element_val)
        cleaned = re.sub(r'[^0-9]', '', cnpj_str_val)
        if not cleaned or cleaned.lower() == 'nan': return "00000000"
        return cleaned.zfill(8)
    if isinstance(cnpj_input, pd.Series): return cnpj_input.apply(_process_single_cnpj)
    elif isinstance(cnpj_input, (str, int, float)): return _process_single_cnpj(cnpj_input)
    else: return _process_single_cnpj(str(cnpj_input))


# --- Sua função encontrar_info_entidade (assumindo que está aqui e correta, aceitando 5 DFs) ---
def encontrar_info_entidade(
    cnpj_interesse_base8: str,
    df_banks: pd.DataFrame,
    df_map_prud_geral: pd.DataFrame,
    df_ifdata_final_valores: pd.DataFrame, 
    df_if_cadastro_completo: pd.DataFrame 
) -> dict:
    # ... (código completo da função encontrar_info_entidade como definido anteriormente,
    #      com os prints de debug para o Nubank se você os manteve)
    info = {
        'cnpj_interesse': cnpj_interesse_base8, 'nome_interesse': None,
        'cod_congl': None, 'cnpj_reporte_cosif_prud': None,
        'nome_congl_prud': None, 'nome_instituicao_if': None,
        'cnpj_lider_if': None
    }
    is_debug_cnpj = (cnpj_interesse_base8 == '30680829') 

    if is_debug_cnpj: print(f"\n[DEBUG Utils NUBANK] ------ encontrar_info_entidade para {cnpj_interesse_base8} ------")

    if not df_banks.empty:
        banco_info_df_banks = df_banks[df_banks['CNPJ'] == cnpj_interesse_base8]
        if not banco_info_df_banks.empty: info['nome_interesse'] = banco_info_df_banks['NOME'].iloc[0]

    if not df_map_prud_geral.empty:
        map_entry_direta = df_map_prud_geral[df_map_prud_geral['CNPJ'] == cnpj_interesse_base8]
        if not map_entry_direta.empty:
            info['cod_congl'] = map_entry_direta['COD_CONGL'].iloc[0]
            info['cnpj_reporte_cosif_prud'] = cnpj_interesse_base8
            if 'NOME_CONGL' in map_entry_direta.columns: info['nome_congl_prud'] = map_entry_direta['NOME_CONGL'].iloc[0]
            if is_debug_cnpj: print(f"  [DEBUG Utils NUBANK] 1a: Encontrado em map_prud_geral. COD_CONGL='{info['cod_congl']}'")
    
    if not info['cod_congl'] and not df_if_cadastro_completo.empty and 'CNPJ_ENTIDADE_IF_BASE8' in df_if_cadastro_completo.columns:
        if is_debug_cnpj: print(f"  [DEBUG Utils NUBANK] 1b: Buscando {cnpj_interesse_base8} em df_if_cadastro_completo['CNPJ_ENTIDADE_IF_BASE8']...")
        entry_entidade_cad = df_if_cadastro_completo[df_if_cadastro_completo['CNPJ_ENTIDADE_IF_BASE8'] == cnpj_interesse_base8]
        if not entry_entidade_cad.empty:
            potential_cod_congls = entry_entidade_cad['COD_CONGL'].dropna().unique()
            if is_debug_cnpj: print(f"    [DEBUG Utils NUBANK] 1b: Encontrado no cadastro! Potential COD_CONGLs: {potential_cod_congls}")
            if len(potential_cod_congls) > 0:
                info['cod_congl'] = potential_cod_congls[0]
                if is_debug_cnpj: print(f"      [DEBUG Utils NUBANK] 1b: COD_CONGL definido como '{info['cod_congl']}'")
                linha_entidade = entry_entidade_cad[entry_entidade_cad['COD_CONGL'] == info['cod_congl']].iloc[0]
                if pd.notna(linha_entidade.get('NomeInstituicao')): info['nome_instituicao_if'] = linha_entidade['NomeInstituicao']
                if pd.notna(linha_entidade.get('CnpjInstituicaoLider')): info['cnpj_lider_if'] = standardize_cnpj_base8(str(linha_entidade['CnpjInstituicaoLider']))
        elif is_debug_cnpj: print(f"    [DEBUG Utils NUBANK] 1b: Não encontrado como entidade no cadastro completo.")
            
    if not info['cod_congl'] and not df_if_cadastro_completo.empty and 'CnpjInstituicaoLider' in df_if_cadastro_completo.columns:
        if is_debug_cnpj: print(f"  [DEBUG Utils NUBANK] 1c: Buscando {cnpj_interesse_base8} como líder em df_if_cadastro_completo['CnpjInstituicaoLider']...")
        df_if_cadastro_completo['TEMP_LIDER_BASE8'] = standardize_cnpj_base8(df_if_cadastro_completo['CnpjInstituicaoLider'])
        entry_lider_cad = df_if_cadastro_completo[df_if_cadastro_completo['TEMP_LIDER_BASE8'] == cnpj_interesse_base8]
        df_if_cadastro_completo.drop(columns=['TEMP_LIDER_BASE8'], inplace=True, errors='ignore')
        if not entry_lider_cad.empty:
            potential_cod_congls = entry_lider_cad['COD_CONGL'].dropna().unique()
            if is_debug_cnpj: print(f"    [DEBUG Utils NUBANK] 1c: Encontrado como líder! Potential COD_CONGLs: {potential_cod_congls}")
            if len(potential_cod_congls) > 0:
                info['cod_congl'] = potential_cod_congls[0]
                info['cnpj_lider_if'] = cnpj_interesse_base8
                linha_lider = entry_lider_cad[entry_lider_cad['COD_CONGL'] == info['cod_congl']].iloc[0]
                if pd.notna(linha_lider.get('NomeInstituicao')): info['nome_instituicao_if'] = linha_lider['NomeInstituicao']
        elif is_debug_cnpj: print(f"    [DEBUG Utils NUBANK] 1c: Não encontrado como líder no cadastro completo.")

    if info['cod_congl']:
        if (not info['cnpj_reporte_cosif_prud'] or not info['nome_congl_prud']) and not df_map_prud_geral.empty:
            map_entry_via_cod = df_map_prud_geral[df_map_prud_geral['COD_CONGL'] == info['cod_congl']]
            if not map_entry_via_cod.empty:
                if not info['cnpj_reporte_cosif_prud']: info['cnpj_reporte_cosif_prud'] = map_entry_via_cod['CNPJ'].iloc[0]
                if not info['nome_congl_prud']: info['nome_congl_prud'] = map_entry_via_cod['NOME_CONGL'].iloc[0]
        if not df_ifdata_final_valores.empty: # df_ifdata_final_valores é o seu df_ifdata (valores + cad. mais recente)
            ifdata_val_entry = df_ifdata_final_valores[df_ifdata_final_valores['COD_CONGL'] == info['cod_congl']]
            if not ifdata_val_entry.empty:
                primeira_if_val = ifdata_val_entry.iloc[0]
                if not info['nome_instituicao_if'] and pd.notna(primeira_if_val.get('NOME_INSTITUICAO_IF')):
                    info['nome_instituicao_if'] = primeira_if_val['NOME_INSTITUICAO_IF']
                if not info['cnpj_lider_if'] and pd.notna(primeira_if_val.get('CNPJ_LIDER_BASE8_IF')):
                    info['cnpj_lider_if'] = primeira_if_val['CNPJ_LIDER_BASE8_IF']
    if is_debug_cnpj: print(f"[DEBUG Utils NUBANK] ------ Info final para {cnpj_interesse_base8}: {info} ------")
    return info


# --- Sua função extrair_dado_cosif (assumindo que está correta e como antes) ---
def extrair_dado_cosif(
    df_cosif: pd.DataFrame, cnpj_reporte_cosif: str, data_alvo: int,
    nome_conta_cosif: str, col_retorno: str = 'SALDO_COSIF'
) -> float | str | None:
    # ... (código completo da função como definido e testado anteriormente)
    if df_cosif.empty or not cnpj_reporte_cosif or pd.isna(cnpj_reporte_cosif) or cnpj_reporte_cosif == "00000000": return None
    subset = df_cosif[
        (df_cosif['CNPJ'] == cnpj_reporte_cosif) &
        (df_cosif['DATA'] == data_alvo) &
        (df_cosif['NOME_CONTA_COSIF'] == nome_conta_cosif)]
    if not subset.empty:
        if col_retorno in subset.columns and pd.notna(subset[col_retorno].iloc[0]): return subset[col_retorno].iloc[0]
    return None

# --- Sua função extrair_dado_ifdata (assumindo que está correta e como antes) ---
def extrair_dado_ifdata(
    df_ifdata: pd.DataFrame, cod_congl_alvo: str, data_alvo: int,
    nome_conta_if: str, col_retorno: str = 'SALDO_IF'
) -> float | str | None:
    # ... (código completo da função como definido e testado anteriormente)
    if df_ifdata.empty or not cod_congl_alvo or pd.isna(cod_congl_alvo): return None
    subset = df_ifdata[
        (df_ifdata['COD_CONGL'] == cod_congl_alvo) &
        (df_ifdata['DATA'] == data_alvo) &
        (df_ifdata['NOME_CONTA_IF'] == nome_conta_if)]
    if not subset.empty:
        if col_retorno in subset.columns and pd.notna(subset[col_retorno].iloc[0]): return subset[col_retorno].iloc[0]
    return None


# ===== FUNÇÃO CONSULTAR_INDICADOR_BANCO ATUALIZADA =====
def consultar_indicador_banco(
    identificador_banco: str,
    data_alvo: int,
    indicador_nome_cosif: str = None,
    indicador_nome_ifdata: str = None,
    df_banks: pd.DataFrame = None,
    df_cosif: pd.DataFrame = None,
    df_ifdata: pd.DataFrame = None, # Este é df_ifdata_final (valores + cad. mais recente)
    df_map_prud_geral: pd.DataFrame = None,
    df_if_cadastro_completo: pd.DataFrame = None # <<<< NOVO PARÂMETRO ADICIONADO
):
    """
    Função de alto nível para consultar indicadores COSIF e/ou IFDATA para um banco.
    """
    # Verificação de DataFrames necessários
    if df_banks is None or \
       df_cosif is None or \
       df_ifdata is None or \
       df_map_prud_geral is None or \
       df_if_cadastro_completo is None: # <<<< CHECAR NOVO DF AQUI
        print("ERRO: Um ou mais DataFrames necessários não foram fornecidos para consultar_indicador_banco.")
        print(f"  df_banks: {'Fornecido' if df_banks is not None else 'Ausente'}")
        print(f"  df_cosif: {'Fornecido' if df_cosif is not None else 'Ausente'}")
        print(f"  df_ifdata: {'Fornecido' if df_ifdata is not None else 'Ausente'}")
        print(f"  df_map_prud_geral: {'Fornecido' if df_map_prud_geral is not None else 'Ausente'}")
        print(f"  df_if_cadastro_completo: {'Fornecido' if df_if_cadastro_completo is not None else 'Ausente'}")
        return None

    cnpj_interesse = None
    nome_banco_original = str(identificador_banco) # Garante que é string para prints

    # Determinar CNPJ de interesse (já deve estar padronizado em df_banks)
    if isinstance(identificador_banco, str) and re.fullmatch(r'\d{8}', identificador_banco):
        cnpj_interesse = identificador_banco 
    elif isinstance(identificador_banco, str): 
        identificador_banco_upper = identificador_banco.upper().strip()
        # Assegurar que a coluna NOME em df_banks também seja tratada como string para comparação
        banco_encontrado = df_banks[df_banks['NOME'].astype(str).str.upper().str.strip() == identificador_banco_upper]
        if not banco_encontrado.empty:
            cnpj_interesse = banco_encontrado['CNPJ'].iloc[0] 
        else:
            print(f"Banco com nome '{identificador_banco}' não encontrado em df_banks.")
            return None
    else: 
        print(f"Tipo de identificador_banco não suportado: {type(identificador_banco)}")
        return None
            
    if not cnpj_interesse or cnpj_interesse == "00000000":
        print(f"CNPJ de interesse inválido ('{cnpj_interesse}') ou não determinado para '{identificador_banco}'.")
        return None

    print(f"\n--- Consultando Dados para '{nome_banco_original}' (CNPJ de Interesse: {cnpj_interesse}) na Data: {data_alvo} ---")
    
    # Chamar encontrar_info_entidade passando todos os DFs necessários
    info_ent = encontrar_info_entidade(
        cnpj_interesse_base8=cnpj_interesse, # Passar o CNPJ já determinado
        df_banks=df_banks, 
        df_map_prud_geral=df_map_prud_geral, 
        df_ifdata_final_valores=df_ifdata, # df_ifdata é o df_ifdata_final.parquet
        df_if_cadastro_completo=df_if_cadastro_completo # Passando o cadastro completo
    )
    print(f"Informações da Entidade Encontradas: {info_ent}")

    resultados = {
        'identificador_original': nome_banco_original,
        'cnpj_interesse': cnpj_interesse, 
        'data_alvo': data_alvo, 
        'info_entidade': info_ent 
    }

    # Extrair dado COSIF
    if indicador_nome_cosif:
        cnpj_para_cosif = info_ent.get('cnpj_reporte_cosif_prud')
        if not cnpj_para_cosif or cnpj_para_cosif == "00000000":
            cnpj_para_cosif = info_ent.get('cnpj_interesse')

        if cnpj_para_cosif and cnpj_para_cosif != "00000000":
            valor_cosif = extrair_dado_cosif(df_cosif, cnpj_para_cosif, data_alvo, indicador_nome_cosif)
            resultados[f"COSIF_{indicador_nome_cosif.replace(' ', '_')}"] = valor_cosif
            print(f"COSIF - '{indicador_nome_cosif}': {valor_cosif} (usando CNPJ: {cnpj_para_cosif})")
        else:
            print(f"COSIF - Não foi possível determinar CNPJ válido para buscar '{indicador_nome_cosif}'.")
            resultados[f"COSIF_{indicador_nome_cosif.replace(' ', '_')}"] = None
            
    # Extrair dado IFDATA
    if indicador_nome_ifdata:
        cod_congl_para_ifdata = info_ent.get('cod_congl')
        # Adicionar verificação para pd.NA e string vazia para cod_congl_para_ifdata
        if cod_congl_para_ifdata and pd.notna(cod_congl_para_ifdata) and str(cod_congl_para_ifdata).strip() not in ["00000000", "", "nan", "None"]:
            valor_ifdata = extrair_dado_ifdata(df_ifdata, str(cod_congl_para_ifdata), data_alvo, indicador_nome_ifdata) # Garantir que cod_congl_para_ifdata é string
            resultados[f"IFDATA_{indicador_nome_ifdata.replace(' ', '_')}"] = valor_ifdata
            print(f"IFDATA - '{indicador_nome_ifdata}': {valor_ifdata} (usando COD_CONGL: {cod_congl_para_ifdata})")
        else:
            print(f"IFDATA - Não foi possível determinar COD_CONGL válido para buscar '{indicador_nome_ifdata}'. Detalhe do COD_CONGL: '{cod_congl_para_ifdata}'")
            resultados[f"IFDATA_{indicador_nome_ifdata.replace(' ', '_')}"] = None
            
    return resultados