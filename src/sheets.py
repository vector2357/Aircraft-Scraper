"""
    Arquivo para criação/atualização de planilhas locais
"""

import os
import pandas as pd
from datetime import datetime

def exportar_para_google_sheets(dados_pesquisa, resultados_aeronaves, nome_arquivo='resultados_aeronaves.xlsx'):
    """
    Exporta dados de pesquisa e resultados para planilha Excel
    
    Args:
        dados_pesquisa (dict): Dados da pesquisa (Manufacturer, Model, etc)
        resultados_aeronaves (list): Lista de dicionários com dados das aeronaves
        nome_arquivo (str): Nome do arquivo de saída (opcional)
    """

    if not os.path.exists('./planilhas/'):
        os.makedirs('./planilhas/')
    
    if nome_arquivo is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"resultados_aeronaves_{timestamp}.xlsx"

    # Caminho completo do arquivo
    caminho_completo = os.path.join('./planilhas/', nome_arquivo)

    # Preparar dados da pesquisa para planilha
    dados_pesquisa_lista = []

    linha = {
        'Fabricante': dados_pesquisa.get('manufacturer', ''),
        'Modelo': dados_pesquisa.get('model', ''),
        'País': dados_pesquisa.get('country', ''),
        'Ano Mínimo': dados_pesquisa.get('year', {}).get('min', ''),
        'Ano Máximo': dados_pesquisa.get('year', {}).get('max', ''),
        'Preço Mínimo': dados_pesquisa.get('price', {}).get('min', ''),
        'Preço Máximo': dados_pesquisa.get('price', {}).get('max', '')
    }
    dados_pesquisa_lista.append(linha)
    
    # Criar DataFrame com dados da pesquisa
    df_pesquisa = pd.DataFrame(dados_pesquisa_lista)
    
    # Preparar dados das aeronaves para planilha
    dados_planilha = []
    
    for aeronave in resultados_aeronaves:
        linha = {
            'URL': aeronave.get('url', ''),
            'Título': aeronave.get('titulo', ''),
            'Preço': aeronave.get('preco', ''),
            'Localização': aeronave.get('localizacao', ''),
            'Ano': aeronave.get('ano', ''),
            'Fabricante': aeronave.get('fabricante', ''),
            'Modelo': aeronave.get('modelo', ''),
            'Horas Totais': aeronave.get('horas_totais', ''),
            'Motor 1 Horas': aeronave.get('motor_1_horas', {}).get('horas', ''),
            'Motor 1 Status': aeronave.get('motor_1_horas', {}).get('status', ''),
            'Motor 2 Horas': aeronave.get('motor_2_horas', {}).get('horas', ''),
            'Motor 2 Status': aeronave.get('motor_2_horas', {}).get('status', ''),
            'Motor 1 TBO': aeronave.get('motor_1_tbo', ''),
            'Motor 2 TBO': aeronave.get('motor_2_tbo', ''),
            'Vendedor': aeronave.get('vendedor', ''),
            'Telefone': aeronave.get('telefone', ''),
            'Descrição': aeronave.get('descricao', '')
        }
        dados_planilha.append(linha)
    
    df_aeronaves = pd.DataFrame(dados_planilha)

    with pd.ExcelWriter(caminho_completo, engine='openpyxl') as writer:
        # Escrever primeiro DataFrame começando na linha 0
        df_pesquisa.to_excel(writer, sheet_name='Dados Consolidados', index=False, startrow=0)
        
        # Calcular onde começar o segundo DataFrame
        # Linha inicial + número de linhas do primeiro DataFrame + 1 linha vazia
        start_row_second = len(df_pesquisa) + 2
        
        # Escrever segundo DataFrame começando na posição calculada
        df_aeronaves.to_excel(writer, sheet_name='Dados Consolidados', index=False, startrow=start_row_second)

        # Aplicar o ajuste automático
        worksheet = writer.sheets['Dados Consolidados']
        auto_ajustar_colunas(worksheet)
    
    print(f"Planilha exportada com sucesso: {caminho_completo}")
    return caminho_completo

def auto_ajustar_colunas(worksheet):
    """
    Ajusta automaticamente a largura de todas as colunas
    baseada no maior conteúdo de cada coluna
    """
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        
        for cell in column:
            try:
                # Considerar o cabeçalho também
                if cell.value:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            except:
                pass
        
        # Adicionar margem de segurança
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column_letter].width = adjusted_width