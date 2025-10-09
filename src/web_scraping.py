from firecrawl import FirecrawlApp
import re
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

class FirecrawlScraper:
    def __init__(self, api_key):
        self.app = FirecrawlApp(api_key=api_key)
    
    def scrape_as_md(self, url, save_to_file=False, output_dir='./scraped_data/markdown_files'):
        """Scraping completo de um site"""
        try:
            print(f"Iniciando scraping de: {url}")

            # Gerar nome do arquivo
            filename = self._generate_custom_filename(url, 'md')
            filepath = os.path.join(output_dir, filename)
            
            # Criar diretório se não existir
            os.makedirs(output_dir, exist_ok=True)
            
            # Executar scraping
            result = self.app.scrape(url)
            
            # Extrair e salvar conteúdo markdown
            if hasattr(result, 'markdown') and result.markdown:
                content = result.markdown
                print("✅ Conteúdo markdown encontrado!")
                
                if save_to_file:
                    # Salva arquivo
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"💾 Conteúdo salvo em: {filepath}")
                
                return content
            else:
                print("Nenhum conteúdo extraído")
                return None
                
        except Exception as e:
            print(f"Erro no scraping: {e}")
            return None
    
    def scrape_as_html(self, url, save_to_file=False, pretty_print=True, output_dir='./scraped_data/html_files'):
        """Retorna o conteúdo em HTML"""
        try:
            print(f"🔄 Iniciando scraping HTML de: {url}")
            
            # Solicitar especificamente HTML
            result = self.app.scrape(url)
            
            print(f"📦 Tipo do resultado: {type(result)}")
            
            # Tentar obter HTML de diferentes formas
            html_content = None
            
            if hasattr(result, 'html') and result.html:
                html_content = result.html
                print("✅ HTML encontrado diretamente!")
            elif hasattr(result, 'markdown') and result.markdown:
                # Converter markdown para HTML (simples)
                html_content = self._markdown_to_html(result.markdown)
                print("✅ Convertido markdown para HTML!")
            else:
                print("❌ Nenhum conteúdo disponível")
                return None
            
            # Salvar se solicitado
            if save_to_file and html_content:
                pretty_html = html_content
                # Formatar HTML
                if pretty_print:
                    pretty_html = self._format_html(html_content)
                # filename = f"scraped_{url.split('//')[-1].split('/')[0]}.html"
                # Gerar nome do arquivo
                filename = self._generate_custom_filename(url, 'html')
                filepath = os.path.join(output_dir, filename)
                
                # Criar diretório se não existir
                os.makedirs(output_dir, exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    print("TESTEEEE")
                    f.write(pretty_html)
                print(f"💾 HTML salvo em: {filepath}")
            
            return html_content
                
        except Exception as e:
            print(f"🚨 Erro no scraping HTML: {e}")
            return None

    def _generate_custom_filename(self, url, extension):
        """Gera nome no padrão: dominio_pais_ordenacao_palavrachave.md (ou .html)"""
        try:
            parsed_url = urlparse(url)
            # Extrair domínio
            domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
            domain = domain.replace('_com', '').replace('_org', '').replace('_net', '')
            
            query_params = parse_qs(parsed_url.query)
            
            # Extrair parâmetros com fallback
            country = query_params.get('Country', [''])[0] or '_'
            sort_order = query_params.get('sort', [''])[0] or '_'
            keywords = query_params.get('keywords', [''])[0] or '_'
            
            # Processar keywords
            if keywords != '_':
                # Decodificar URL
                keywords = keywords.replace('%20', ' ').replace('%2C', ',').replace('%26', 'and')
                # Limpar e formatar
                keywords = re.sub(r'[^\w\s]', '', keywords)  # Remove caracteres especiais
                keywords = re.sub(r'\s+', '_', keywords.strip().lower())  # Padroniza
            
            # Montar filename
            filename = f"{domain}_{country}_{sort_order}_{keywords}."

            if extension == 'html':
                filename += "html"
            else:
                filename += "md"
            
            return filename
            
        except Exception as e:
            print(f"⚠️  Erro no filename, usando fallback: {e}")
            return f"fallback_{hash(url) % 10000}.md"
    
    def _markdown_to_html(self, markdown_text):
        """Converte markdown básico para HTML"""
        # Conversões simples
        html = markdown_text
        html = re.sub(r'# (.*?)\n', r'<h1>\1</h1>', html)
        html = re.sub(r'## (.*?)\n', r'<h2>\1</h2>', html)
        html = re.sub(r'### (.*?)\n', r'<h3>\1</h3>', html)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1">', html)
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        html = re.sub(r'\n', r'<br>', html)
        
        return f"<html><body>{html}</body></html>"
    
    def _format_html(self, html_content):
        """Formata o HTML para ficar bem identado"""
        try:
            # Usar BeautifulSoup para formatar
            soup = BeautifulSoup(html_content, 'html.parser')
            pretty_html = soup.prettify()  # 🔥 Esta função faz a identação automática
            
            return pretty_html
            
        except Exception as e:
            print(f"⚠️  Erro na formatação, retornando HTML original: {e}")
            return html_content
        
    def filter_markdown_data(self, url):
        """Filtra dados específicos do markdown"""
        try:
            result = self.app.scrape(url)
            
            if not hasattr(result, 'markdown') or not result.markdown:
                return None
            
            content = result.markdown
            
            # Dicionário para armazenar dados filtrados
            filtered_data = {}
            
            # 1. Extrair título principal
            title_match = re.search(r'# (.*?)\n', content)
            filtered_data['titulo'] = title_match.group(1) if title_match else "Não encontrado"
            
            # 2. Extrair preço
            price_match = re.search(r'USD \$([\d,]+)', content)
            filtered_data['preco'] = f"USD ${price_match.group(1)}" if price_match else "Não encontrado"
            
            # 3. Extrair localização
            location_match = re.search(r'Aircraft Location: \[(.*?)\]', content)
            filtered_data['localizacao'] = location_match.group(1) if location_match else "Não encontrado"
            
            # 4. Extrair ano
            year_match = re.search(r'Year\n\n(\d{4})', content)
            filtered_data['ano'] = year_match.group(1) if year_match else "Não encontrado"
            
            # 5. Extrair horas totais
            total_time_match = re.search(r'Total Time\n\n([\d,]+)', content)
            filtered_data['horas_totais'] = total_time_match.group(1) if total_time_match else "Não encontrado"
            
            # 6. Extrair horas dos motores
            engine1_match = re.search(r'Engine 1 Time\n\n(.*?)\n', content)
            engine2_match = re.search(r'Engine 2 Time\n\n(.*?)\n', content)
            filtered_data['motor_1_horas'] = engine1_match.group(1) if engine1_match else "Não encontrado"
            filtered_data['motor_2_horas'] = engine2_match.group(1) if engine2_match else "Não encontrado"

            # 7. Extrair TBO dos motores
            tbo1_match = re.search(r'Engine 1 TBO\n\n(.*?)\n', content)
            tbo2_match = re.search(r'Engine 2 TBO\n\n(.*?)\n', content)
            filtered_data['motor_1_tbo'] = tbo1_match.group(1) if tbo1_match else "Não encontrado"
            filtered_data['motor_2_tbo'] = tbo2_match.group(1) if tbo2_match else "Não encontrado"
            
            # 8. Extrair informações do vendedor
            seller_match = re.search(r'Seller Information\n\n(.*?)\n\n', content, re.DOTALL)
            filtered_data['vendedor'] = seller_match.group(1).strip() if seller_match else "Não encontrado"
            
            # 9. Extrair todas as imagens
            images = re.findall(r'!\[(.*?)\]\((.*?)\)', content)
            filtered_data['imagens'] = [img[1] for img in images]  # Lista de URLs de imagens
            
            # 10. Extrair descrição (primeiro parágrafo após o título)
            desc_match = re.search(r'# .*?\n\n(.*?)\n\n', content, re.DOTALL)
            filtered_data['descricao'] = desc_match.group(1).strip() if desc_match else "Não encontrado"
            
            return filtered_data
            
        except Exception as e:
            print(f"🚨 Erro na filtragem markdown: {e}")
            return None
        
    def filter_html_data(self, url):
        """Filtra dados específicos do HTML usando BeautifulSoup (Versão Segura)"""
        try:
            html_content = self.scrape_as_html(url)
            if not html_content:
                print("HTML content is empty. Cannot filter data.")
                return None

            soup = BeautifulSoup(html_content, 'html.parser')
            filtered_data = {}

            # 1. Título (com fallback e verificação)
            title_tag = soup.find('title')
            if title_tag and title_tag.get_text():
                filtered_data['titulo_pagina'] = title_tag.get_text().strip()
            else:
                h1_tag = soup.find('h1')
                if h1_tag and h1_tag.get_text():
                    filtered_data['titulo_pagina'] = h1_tag.get_text().strip()
                else:
                    filtered_data['titulo_pagina'] = "Não encontrado"

            # 2. Headings (H1, H2, H3)
            headings = {}
            for i in range(1, 4):
                h_tags = soup.find_all(f'h{i}')
                # Verifica se h_tags não é None antes de iterar
                if h_tags:
                    # Verifica se cada 'h' não é None e tem texto antes de chamar get_text()
                    headings[f'h{i}'] = [h.get_text().strip() for h in h_tags if h and h.get_text()]
            filtered_data['headings'] = headings

            # 3. Parágrafos
            paragraphs_tags = soup.find_all('p')
            if paragraphs_tags:
                filtered_data['paragrafos'] = [p.get_text().strip() for p in paragraphs_tags if p and p.get_text()]
            else:
                filtered_data['paragrafos'] = []

            # 4. Links
            links = []
            link_tags = soup.find_all('a', href=True)
            if link_tags:
                for link in link_tags:
                    # Garante que o link não é None
                    if link:
                        links.append({
                            'texto': link.get_text().strip() if link.get_text() else '',
                            'url': link['href']
                        })
            filtered_data['links'] = links

            # 5. Imagens
            images = []
            img_tags = soup.find_all('img', src=True)
            if img_tags:
                for img in img_tags:
                    if img:
                        images.append({
                            'alt': img.get('alt', 'Sem descrição'),
                            'src': img['src']
                        })
            filtered_data['imagens'] = images
            
            # ... (as partes de tabelas e metadados já são relativamente seguras, mas pode adicionar verificações se necessário) ...
            
            return filtered_data

        except Exception as e:
            # Captura qualquer outro erro inesperado e informa qual foi
            print(f"🚨 Erro na filtragem HTML: {e}")
            import traceback
            traceback.print_exc() # Imprime o rastreamento completo do erro
            return None
    
    def scrape_multiple_as_html(self, urls, output_dir="./scraped_data/html_files"):
        """Scraping em lote com nomes personalizados"""
        results = {}
        
        for url in urls:
            print(f"\n📄 Processando: {os.path.basename(url)}")
            result = self.scrape_as_html(url, output_dir)
            results[url] = result
        
        return results
    
    def scrape_multiple_as_md(self, urls, output_dir="./scraped_data/markdown_files"):
        """Scraping em lote com nomes personalizados"""
        results = {}
        
        for url in urls:
            print(f"\n📄 Processando: {os.path.basename(url)}")
            result = self.scrape_as_md(url, output_dir)
            results[url] = result
        
        return results

def clear_terminal():
    """Limpa o terminal de forma compatível com qualquer SO"""
    os.system('cls' if os.name == 'nt' else 'clear')

# Uso
if __name__ == "__main__":
    clear_terminal()

    # Carrega variáveis do arquivo .env
    load_dotenv()

    # Chave da API do Firecrawl
    API_KEY = os.getenv('FIRECRAWL_API_KEY')

    scraper = FirecrawlScraper(API_KEY)

    #url = "https://www.controller.com/listings/search?Country=178&sort=4&keywords=seneca%20V"
    url = "https://www.controller.com/listing/for-sale/247962673/2002-piper-seneca-v-piston-twin-aircraft"
    
    print("=" * 60)
    print("🎯 SCRAPING AVANÇADO - TODOS OS FORMATOS")
    print("=" * 60)
    
    # 1. Obter HTML
    print("\n1. 🎯 OBTENDO HTML...")
    html_content = scraper.scrape_as_html(url, save_to_file=True)
    if html_content:
        print(f"   ✅ HTML obtido: {len(html_content)} caracteres")

    # 2. Obter Markdown
    print("\n2. 🎯 OBTENDO MARKDOWN...")
    markdown_content = scraper.scrape_as_md(url, save_to_file=True)
    if markdown_content:
        print(f"   ✅ Markdown obtido: {len(markdown_content)} caracteres")

    # 3. Filtrar dados do Markdown
    print("\n3. 🎯 FILTRANDO MARKDOWN...")
    dados_markdown = scraper.filter_markdown_data(url)
    if dados_markdown:
        print("   ✅ Dados do Markdown extraídos:")
        for chave, valor in list(dados_markdown.items())[:10]:
            print(f"      • {chave}: {valor}")
    
    # 4. Filtrar dados do HTML
    print("\n4. 🎯 FILTRANDO HTML...")
    dados_html = scraper.filter_html_data(url)
    if dados_html:
        print("   ✅ Dados do HTML extraídos:")
        print(f"      • Título: {dados_html.get('titulo_pagina', 'N/A')}")
        print(f"      • Headings H1: {len(dados_html.get('headings', {}).get('h1', []))}")
        print(f"      • Parágrafos: {len(dados_html.get('paragrafos', []))}")
        print(f"      • Links: {len(dados_html.get('links', []))}")
        print(f"      • Imagens: {len(dados_html.get('imagens', []))}")
    
    print("\n" + "=" * 60)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 60)

    # 5. 