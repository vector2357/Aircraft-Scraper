import os
from dotenv import load_dotenv
from web_scraping import ZenRowsScraper  
from sheets import exportar_para_google_sheets
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import random
import sys

# Adicionar o diretório pai ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.delay import delay

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

app = FastAPI(title="Web Scraping API", version="1.0.0")

@app.get("/health")
async def health_check():
    """
    Endpoint simples usado para verificar se o servidor está ativo.
    Retorna status 200 se o app estiver rodando corretamente.
    """
    return {"status": "ok", "message": "API está saudável!"}

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class YearRange(BaseModel):
    min: Optional[str] = None
    max: Optional[str] = None

class PriceRange(BaseModel):
    min: Optional[str] = None
    max: Optional[str] = None

class SearchData(BaseModel):
    # manufacturer: Optional[str] = None
    # model: Optional[str] = None
    keywords: Optional[str] = None
    country: Optional[str] = None
    year: Optional[YearRange] = None
    price: Optional[PriceRange] = None
    engine_left_time_min: Optional[str] = "0"
    engine_left_time_max: Optional[str] = "1000000000"

class MotorHoras(BaseModel):
    horas: Optional[str] = None
    status: Optional[str] = None

class ScrapingResult(BaseModel):
    url: Optional[str] = None
    titulo: Optional[str] = None
    preco: Optional[str] = None
    localizacao: Optional[str] = None
    ano: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    motor_1_left: Optional[str] = None
    motor_2_left: Optional[str] = None
    horas_totais: Optional[str] = None
    motor_1_horas: Optional[MotorHoras] = None
    motor_2_horas: Optional[MotorHoras] = None
    motor_1_tbo: Optional[str] = None
    motor_2_tbo: Optional[str] = None
    vendedor: Optional[str] = None
    telefone: Optional[str] = None

# Converter dados para o modelo ScrapingResult
def convert_to_scraping_result(dados: dict) -> ScrapingResult:
    """Converte dados do scraping para o modelo ScrapingResult"""
    
    # Agora motor_horas é sempre dicionário
    def parse_motor_horas(motor_data):
        if not motor_data or motor_data.get('horas') == 'Não encontrado':
            return None
        else:
            return MotorHoras(
                horas=motor_data.get('horas'),
                status=motor_data.get('status', 'Desconhecido')
            )
    
    return ScrapingResult(
        url=dados.get('url'),
        titulo=dados.get('titulo'),
        preco=dados.get('preco'),
        localizacao=dados.get('localizacao'),
        ano=dados.get('ano'),
        fabricante=dados.get('fabricante'),
        modelo=dados.get('modelo'),
        motor_1_left=dados.get('motor_1_left'),
        motor_2_left=dados.get('motor_2_left'),
        horas_totais=dados.get('horas_totais'),
        motor_1_horas=parse_motor_horas(dados.get('motor_1_horas', {})),
        motor_2_horas=parse_motor_horas(dados.get('motor_2_horas', {})),
        motor_1_tbo=dados.get('motor_1_tbo'),
        motor_2_tbo=dados.get('motor_2_tbo'),
        vendedor=dados.get('vendedor'),
        telefone=dados.get('telefone')
    )

@app.post("/scrape", response_model=List[ScrapingResult])
async def scrape_aircraft_data(search_data: SearchData):
    """
    Endpoint para realizar web scraping baseado nos dados de pesquisa
    """
    try:
        logger.info(f"Iniciando scraping com dados: {search_data}")

        search_datas = {
            # 'manufacturer': search_data.manufacturer,
            # 'model': search_data.model,
            'keywords': search_data.keywords,
            'country': search_data.country,
            'year': {
                "min": search_data.year.min if search_data.year else None,
                "max": search_data.year.max if search_data.year else None
            },
            'price': {
                "min": search_data.price.min if search_data.price else None,
                "max": search_data.price.max if search_data.price else None
            },
            'engine_left_time_min': search_data.engine_left_time_min,
            'engine_left_time_max': search_data.engine_left_time_max
        }
        
        # Aqui você chama sua função de scraping existente
        results = await execute_scraping(search_datas)
        
        logger.info(f"Scraping concluído. {len(results)} resultados encontrados.")
        return results
        
    except Exception as e:
        logger.error(f"Erro durante scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

async def execute_scraping(search_datas: dict) -> List[ScrapingResult]:
    """Função principal para executar o processo de scraping."""

    print("🚀 Iniciando o scraper de aeronaves...")
    
    # Crie uma instância do nosso scraper
    scraper = ZenRowsScraper()

    # 1. Construa a URL de pesquisa
    search_url = scraper.build_search_url(search_datas)

    print(f"🔍 URL construída: {search_url}")

    if not search_url:
        return []
    
    # 2. Obtenha a lista de links de anúncios individuais da página de pesquisa
    listing_links = scraper.get_listing_links(search_url)

    dados_anuncios = []

    # 3. Itere sobre cada link e processe-o
    if not listing_links:
        print("Nenhum link de anúncio encontrado para processar.")
    else:
        print(f"✅ Encontrados {len(listing_links)} links. A iniciar o scraping individual...")
        for i, link in enumerate(listing_links, 1):
            print("-" * 40)
            print(f"🔍 A processar {i}/{len(listing_links)}: {link}")

            # DELAY (opcional)
            # if i > 1:
                # delay(random.uniform(5, 10))  # Delay entre 5 a 10 segundos

            dados = scraper.filter_html_data(link, save_to_file=True)

            if dados:
                # Cálculo simples - se não encontrado, segue normalmente
                try:
                    # Inicializar com lista vazia
                    engine_left_times = []
                    
                    # Adicionar motor_1_left se for válido
                    motor_1_left = dados.get('motor_1_left', 'Não encontrado')
                    if motor_1_left != 'Não encontrado':
                        try:
                            engine_left_times.append(float(motor_1_left))
                        except (ValueError, TypeError):
                            print(f"⚠️ Valor inválido para motor_1_left: {motor_1_left}")
                    
                    # Adicionar motor_2_left se for válido
                    motor_2_left = dados.get('motor_2_left', 'Não encontrado')
                    if motor_2_left != 'Não encontrado':
                        try:
                            engine_left_times.append(float(motor_2_left))
                        except (ValueError, TypeError):
                            print(f"⚠️ Valor inválido para motor_2_left: {motor_2_left}")
                    
                    # Se temos pelo menos um valor válido, calcular o mínimo
                    if engine_left_times:
                        min_engine_left_time = min(engine_left_times)
                        
                        # Verificar se está dentro do range
                        try:
                            engine_min = float(search_datas.get('engine_left_time_min', 0))
                            engine_max = float(search_datas.get('engine_left_time_max', 1000000000))
                            
                            if min_engine_left_time >= engine_min and min_engine_left_time <= engine_max:
                                dados_anuncios.append(dados)
                                print(f"✅ Dados extraídos com sucesso ({i}/{len(listing_links)}) - Horas: {min_engine_left_time}")
                            else:
                                print(f"⏭️ Anúncio {i} fora do range - Horas: {min_engine_left_time}")
                                
                        except (ValueError, TypeError) as e:
                            print(f"⚠️ Erro ao verificar range do motor: {e}")
                            # Em caso de erro no range, inclui o anúncio
                            dados_anuncios.append(dados)
                            print(f"✅ Dados extraídos com sucesso ({i}/{len(listing_links)})")
                    else:
                        # Se nenhum motor foi encontrado, inclui o anúncio normalmente
                        dados_anuncios.append(dados)
                        print(f"✅ Dados extraídos com sucesso ({i}/{len(listing_links)}) - Sem dados de motor")
                        
                except Exception as e:
                    print(f"🚨 Erro ao processar dados do anúncio {i}: {e}")
                    # Em caso de erro grave, ainda assim inclui o anúncio
                    dados_anuncios.append(dados)
                    print(f"✅ Dados extraídos com sucesso ({i}/{len(listing_links)}) - (com erro no processamento)")
            else:
                print(f"❌ Falha ao extrair dados ({i}/{len(listing_links)})")

    print(f"\n✅ Processo concluído! {len(dados_anuncios)} anúncios processados com sucesso.")

    # Converter para o modelo ScrapingResult antes de retornar
    resultados_validados = []
    for dados in dados_anuncios:
        try:
            resultado = convert_to_scraping_result(dados)
            resultados_validados.append(resultado)
        except Exception as e:
            print(f"🚨 Erro ao validar dados para o modelo: {e}")
            # Se houver erro na conversão, cria um resultado básico
            resultados_validados.append(ScrapingResult(
                url=dados.get('url'),
                titulo=dados.get('titulo'),
                preco=dados.get('preco'),
                localizacao=dados.get('localizacao'),
                ano=dados.get('ano'),
                fabricante=dados.get('fabricante'),
                modelo=dados.get('modelo')
            ))

    # 4. MOSTRAR TODOS OS RESULTADOS APÓS O PROCESSAMENTO
    print("\n" + "="*80)
    print("📊 RELATÓRIO COMPLETO DE TODOS OS ANÚNCIOS PROCESSADOS")
    print("="*80)
    
    if not resultados_validados:
        print("❌ Nenhum dado foi extraído com sucesso.")
    else:
        for i, anuncio in enumerate(resultados_validados, 1):
            print(f"\n{'='*60}")
            print(f"📋 ANÚNCIO {i}/{len(resultados_validados)}")
            print(f"{'='*60}")
            print(f"🏷️  Título: {anuncio.titulo or 'N/A'}")
            print(f"💰 Preço: {anuncio.preco or 'N/A'}")
            print(f"📍 Localização: {anuncio.localizacao or 'N/A'}")
            print(f"📅 Ano: {anuncio.ano or 'N/A'}")
            print(f"✈️  Fabricante: {anuncio.fabricante or 'N/A'}")
            print(f"🛩️  Modelo: {anuncio.modelo or 'N/A'}")
            print(f"🔧 Motor 1 Horas Restantes: {anuncio.motor_1_left or 'N/A'}")
            print(f"🔧 Motor 2 Horas Restantes: {anuncio.motor_2_left or 'N/A'}")
            print(f"⏱️  Horas Totais: {anuncio.horas_totais or 'N/A'}")
            
            # ✅ CORREÇÃO: Exibição segura de motor_horas
            if anuncio.motor_1_horas:
                print(f"🔧 Motor 1 Horas: {anuncio.motor_1_horas.horas or 'N/A'} - Status: {anuncio.motor_1_horas.status or 'N/A'}")
            else:
                print(f"🔧 Motor 1 Horas: N/A")
                
            if anuncio.motor_2_horas:
                print(f"🔧 Motor 2 Horas: {anuncio.motor_2_horas.horas or 'N/A'} - Status: {anuncio.motor_2_horas.status or 'N/A'}")
            else:
                print(f"🔧 Motor 2 Horas: N/A")
            
            print(f"⚙️  Motor 1 TBO: {anuncio.motor_1_tbo or 'N/A'}")
            print(f"⚙️  Motor 2 TBO: {anuncio.motor_2_tbo or 'N/A'}")
            print(f"👤 Vendedor: {anuncio.vendedor or 'N/A'}")
            print(f"📞 Telefone: {anuncio.telefone or 'N/A'}")
            print(f"🔗 URL: {anuncio.url or 'N/A'}")

    import json
    from datetime import datetime
    
    if dados_anuncios:
        # Criar diretório de resultados se não existir
        resultados_dir = './scraped_data/resultados'
        os.makedirs(resultados_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # manufacturer = search_datas.get('manufacturer', 'unknown')
        # model = search_datas.get('model', 'unknown').replace(' ', '_')
        keyword = search_datas.get('keywords', 'unknown').replace(' ', '_')
        filename = f"resultados_{keyword}_{timestamp}.json"
        filepath = os.path.join(resultados_dir, filename)

        # Salavmento na planilha
        # exportar_para_google_sheets(search_datas, dados_anuncios)
        
        # Salvar em JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados_anuncios, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Todos os dados salvos em: {filepath}")
    
    print(f"\n✅ Processo concluído! {len(resultados_validados)} anúncios processados com sucesso.")

    return resultados_validados


if __name__ == "__main__":
    import uvicorn
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', 8000))
    
    uvicorn.run(app, host=host, port=port)