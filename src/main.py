import os
from dotenv import load_dotenv
from web_scraping import FirecrawlScraper

def main():
    """Função principal para executar o processo de scraping."""

    print("🚀 Iniciando o scraper de aeronaves...")
    load_dotenv()
    api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not api_key:
        print("🚨 Erro: A chave FIRECRAWL_API_KEY não foi encontrada. Verifique o seu ficheiro .env.")
        return

    # --- Defina aqui o que você quer procurar ---
    manufacturer_to_search = "PIPER"
    model_to_search = "SENECA V" 
    # model_to_search = None # Para pesquisar todos os PIPER

    # Crie uma instância do nosso scraper
    scraper = FirecrawlScraper(api_key)

    # 1. Construa a URL de pesquisa
    search_url = scraper.build_search_url(manufacturer_to_search, model_to_search)
    
    # 2. Obtenha a lista de links de anúncios individuais da página de pesquisa
    listing_links = scraper.get_listing_links(search_url)

    dados_anunios = []

    # 3. Itere sobre cada link e processe-o
    if not listing_links:
        print("Nenhum link de anúncio encontrado para processar.")
    else:
        print(f"✅ Encontrados {len(listing_links)} links. A iniciar o scraping individual...")
        for link in listing_links:
            print("-" * 40)
            print(f"🔍 A processar: {link}")

            dados_anunios.append(scraper.filter_html_data(link,save_to_file=True))
            
    
    

if __name__ == "__main__":
    main()