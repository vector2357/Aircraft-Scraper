import os
from dotenv import load_dotenv
from web_scraping import FirecrawlScraper
from sheets import exportar_para_google_sheets
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

app = FastAPI(title="Web Scraping API", version="1.0.0")

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
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    country: Optional[str] = None
    year: Optional[YearRange] = None
    price: Optional[PriceRange] = None

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

@app.post("/scrape", response_model=List[ScrapingResult])
async def scrape_aircraft_data(search_data: SearchData):
    """
    Endpoint para realizar web scraping baseado nos dados de pesquisa
    """
    try:
        logger.info(f"Iniciando scraping com dados: {search_data}")

        search_datas = {
            'manufacturer': search_data.manufacturer,
            'model': search_data.model,
            'country': search_data.country,
            'year': {
                "min": search_data.year.min if search_data.year else None,
                "max": search_data.year.max if search_data.year else None
            },
            'price': {
                "min": search_data.price.min if search_data.price else None,
                "max": search_data.price.max if search_data.price else None
            }
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
    api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not api_key:
        print("🚨 Erro: A chave FIRECRAWL_API_KEY não foi encontrada. Verifique o seu ficheiro .env.")
        return

    # Crie uma instância do nosso scraper
    scraper = FirecrawlScraper(api_key)

    # 1. Construa a URL de pesquisa
    search_url = scraper.build_search_url(search_datas)

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

            dados = scraper.filter_html_data(link, save_to_file=True)
            if dados:
                dados_anuncios.append(dados)
                print(f"✅ Dados extraídos com sucesso ({i}/{len(listing_links)})")
            else:
                print(f"❌ Falha ao extrair dados ({i}/{len(listing_links)})")

    print(f"\n✅ Processo concluído! {len(dados_anuncios)} anúncios processados com sucesso.")

    # 4. MOSTRAR TODOS OS RESULTADOS APÓS O PROCESSAMENTO
    print("\n" + "="*80)
    print("📊 RELATÓRIO COMPLETO DE TODOS OS ANÚNCIOS PROCESSADOS")
    print("="*80)
    
    if not dados_anuncios:
        print("❌ Nenhum dado foi extraído com sucesso.")
    else:
        for i, anuncio in enumerate(dados_anuncios, 1):
            print(f"\n{'='*60}")
            print(f"📋 ANÚNCIO {i}/{len(dados_anuncios)}")
            print(f"{'='*60}")
            print(f"🏷️  Título: {anuncio.get('titulo', 'N/A')}")
            print(f"💰 Preço: {anuncio.get('preco', 'N/A')}")
            print(f"📍 Localização: {anuncio.get('localizacao', 'N/A')}")
            print(f"📅 Ano: {anuncio.get('ano', 'N/A')}")
            print(f"✈️  Fabricante: {anuncio.get('fabricante', 'N/A')}")
            print(f"🛩️  Modelo: {anuncio.get('modelo', 'N/A')}")
            print(f"🔧 Motor 1 Horas Restantes: {anuncio.get('motor_1_left', 'N/A')}")
            print(f"🔧 Motor 2 Horas Restantes: {anuncio.get('motor_2_left', 'N/A')}")
            print(f"⏱️  Horas Totais: {anuncio.get('horas_totais', 'N/A')}")
            print(f"🔧 Motor 1 Horas: {anuncio.get('motor_1_horas', 'N/A')}")
            print(f"🔧 Motor 2 Horas: {anuncio.get('motor_2_horas', 'N/A')}")
            print(f"⚙️  Motor 1 TBO: {anuncio.get('motor_1_tbo', 'N/A')}")
            print(f"⚙️  Motor 2 TBO: {anuncio.get('motor_2_tbo', 'N/A')}")
            print(f"👤 Vendedor: {anuncio.get('vendedor', 'N/A')}")
            print(f"📞 Telefone: {anuncio.get('telefone', 'N/A')}")
            print(f"🔗 URL: {anuncio.get('url', 'N/A')}")

    import json
    from datetime import datetime
    
    if dados_anuncios:
        # Criar diretório de resultados se não existir
        resultados_dir = './scraped_data/resultados'
        os.makedirs(resultados_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resultados_{search_datas['manufacturer']}_{search_datas['model'].replace(' ', '_')}_{timestamp}.json"
        filepath = os.path.join(resultados_dir, filename)

        # Salavmento na planilha
        # exportar_para_google_sheets(search_datas, dados_anuncios)
        
        # Salvar em JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados_anuncios, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Todos os dados salvos em: {filepath}")
    
    print(f"\n✅ Processo concluído! {len(dados_anuncios)} anúncios processados com sucesso.")

    return dados_anuncios


if __name__ == "__main__":
    import uvicorn
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', 8000))
    
    uvicorn.run(app, host=host, port=port)