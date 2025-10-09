import time
import random
from firecrawl import FirecrawlApp
import re
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from urllib.parse import urljoin
from urllib.parse import urlencode

class FirecrawlScraper:
    def __init__(self, api_key):
        self.app = FirecrawlApp(api_key=api_key)

    def _rate_limit_delay(self):
        """Delay fixo entre requisições para containers"""
        # Como não podemos manter estado entre execuções, usamos um delay fixo
        # que garante ficar abaixo do limite de 10 req/minuto
        base_delay = random.uniform(7, 12)  # 7-12 segundos = ~5-8 req/minuto
        print(f"⏳ Aguardando {base_delay:.1f} segundos entre requisições...")
        time.sleep(base_delay)

    def build_search_url(self, manufacturer, model=None):
        """Construindo a url de busca, codificand os parametros"""

        try:
            base_url = "https://www.controller.com/listings/search"

            params = {'Manufacturer': manufacturer}

            if model:
                params['Model'] = model

            query_string = urlencode(params)

            final_url = f"{base_url}?{query_string}"
        
            return final_url
        
        except Exception as e:
            print(f"Erro na construção da url: {e}")
            return None
        

    def get_listing_links(self, search_url):
        """Pegando todos os links de uma página de busca"""
        try:
            print(f"A procurar links na página de pesquisa: {search_url}")

            # Buscar a página
            html_content = self.scrape_as_html(search_url)

            if not html_content:
                print("Não foi possível obter o conteúdo HTML da página de pesquisa.")
                return []
            
            # Analisar o html
            soup = BeautifulSoup(html_content, 'html.parser')

            # DEBUG: Verificar estrutura da página
            print(f"📊 Título da página: {soup.title.string if soup.title else 'Não encontrado'}")
            
            # Tentar diferentes seletores para encontrar os links
            link_tags = []
            
            # Seletor original
            link_tags = soup.find_all('a', class_='list-listing-title-link')
            print(f"🔍 Tentativa 1 - Classe 'list-listing-title-link': {len(link_tags)} links")
            
            # Se não encontrar, tentar outros seletores
            if not link_tags:
                link_tags = soup.find_all('a', href=lambda href: href and '/listing/' in href)
                print(f"🔍 Tentativa 2 - Links com '/listing/': {len(link_tags)} links")
            
            if not link_tags:
                # Buscar por qualquer link que possa ser um anúncio
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if '/listing/' in href and href.split('/listing/')[1].strip('/').replace('-', '').isalnum():
                        link_tags.append(link)
                print(f"🔍 Tentativa 3 - Filtro por padrão de URL: {len(link_tags)} links")

            absolut_links = []
            base_domain = "https://www.controller.com"

            # Extraindo apenas o link das tags que estão em href
            for tag in link_tags:
                relative_link = tag.get('href')
                if relative_link:
                    full_link = urljoin(base_domain, relative_link)
                    absolut_links.append(full_link)
                    print(f"   ✅ Link encontrado: {full_link}")
            
            # Remover duplicatas
            absolut_links = list(set(absolut_links))
            
            print(f"Encontramos {len(absolut_links)} links únicos.")

            return absolut_links
        
        except Exception as e:
            print(f"Erro no scraping: {e}")
            return []

    def scrape_as_html(self, url, save_to_file=False, pretty_print=True, output_dir='./scraped_data/html_files'):
        """Retorna o conteúdo em HTML"""
        try:
            self._rate_limit_delay()
            
            print(f"🔄 Iniciando scraping HTML de: {url}")
            
            # Solicitar especificamente HTML
            result = self.app.scrape(url)
            
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
                # Gerar nome do arquivo
                filename = self._generate_custom_filename(url, 'html')
                filepath = os.path.join(output_dir, filename)
                
                # Criar diretório se não existir
                os.makedirs(output_dir, exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(pretty_html)
                print(f"💾 HTML salvo em: {filepath}")
            
            return html_content
                
        except Exception as e:
            print(f"🚨 Erro no scraping HTML: {e}")
        
            # ADICIONADO: Retry automático em caso de rate limit
            if "Rate Limit Exceeded" in str(e):
                # Extrai o tempo de espera da mensagem de erro
                try:
                    # Procura por "retry after Xs" no erro
                    import re
                    match = re.search(r'retry after (\d+)s', str(e))
                    if match:
                        wait_time = int(match.group(1)) + 2  # +2 segundos de segurança
                    else:
                        wait_time = 60  # fallback
                    
                    print(f"🔄 Rate limit detectado, tentando novamente após {wait_time} segundos...")
                    time.sleep(wait_time)
                    return self.scrape_as_html(url, save_to_file, pretty_print, output_dir)
                except:
                    print("🔄 Rate limit detectado, tentando novamente após 60 segundos...")
                    time.sleep(60)
                    return self.scrape_as_html(url, save_to_file, pretty_print, output_dir)
            
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
            pretty_html = soup.prettify()
            
            return pretty_html
            
        except Exception as e:
            print(f"⚠️  Erro na formatação, retornando HTML original: {e}")
            return html_content
        
    def filter_html_data(self, url, save_to_file=False):
        """Filtra dados específicos do HTML usando BeautifulSoup (Versão Segura)"""
        try:
            html_content = self.scrape_as_html(url, save_to_file=save_to_file)
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
                if h_tags:
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
            
            return filtered_data

        except Exception as e:
            print(f"🚨 Erro na filtragem HTML: {e}")
            import traceback
            traceback.print_exc()
            return None