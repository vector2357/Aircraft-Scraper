import os
import pandas as pd
from datetime import datetime

def exportar_para_excel(dados_pesquisa, resultados_aeronaves, nome_arquivo=None):
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
    
    # Criar DataFrame com dados da pesquisa
    df_pesquisa = pd.DataFrame([dados_pesquisa])
    
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

    # Criar arquivo Excel com múltiplas abas
    with pd.ExcelWriter(caminho_completo, engine='openpyxl') as writer:
        # Aba 1: Dados da Pesquisa
        df_pesquisa.to_excel(writer, sheet_name='Dados Pesquisa', index=False)
        
        # Aba 2: Resultados das Aeronaves
        df_aeronaves.to_excel(writer, sheet_name='Aeronaves', index=False)
    
    print(f"Planilha exportada com sucesso: {caminho_completo}")
    return caminho_completo