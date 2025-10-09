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
            print(f"⏱️  Horas Totais: {anuncio.get('horas_totais', 'N/A')}")
            print(f"🔧 Motor 1 Horas: {anuncio.get('motor_1_horas', 'N/A')}")
            print(f"🔧 Motor 2 Horas: {anuncio.get('motor_2_horas', 'N/A')}")
            print(f"⚙️  Motor 1 TBO: {anuncio.get('motor_1_tbo', 'N/A')}")
            print(f"⚙️  Motor 2 TBO: {anuncio.get('motor_2_tbo', 'N/A')}")
            print(f"👤 Vendedor: {anuncio.get('vendedor', 'N/A')}")
            print(f"📞 Telefone: {anuncio.get('telefone', 'N/A')}")
            print(f"📝 Descrição: {anuncio.get('descricao', 'N/A')[:200]}...")  # Mostra apenas os primeiros 200 caracteres
            print(f"🖼️  Número de Imagens: {len(anuncio.get('imagens', []))}")
            print(f"🔗 URL: {anuncio.get('url', 'N/A')}")

    import json
    from datetime import datetime
    
    if dados_anuncios:
        # Criar diretório de resultados se não existir
        resultados_dir = './scraped_data/resultados'
        os.makedirs(resultados_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resultados_{manufacturer_to_search}_{model_to_search.replace(' ', '_')}_{timestamp}.json"
        filepath = os.path.join(resultados_dir, filename)
        
        # Salvar em JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados_anuncios, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Todos os dados salvos em: {filepath}")
    
    print(f"\n✅ Processo concluído! {len(dados_anuncios)} anúncios processados com sucesso.")


if __name__ == "__main__":
    main()