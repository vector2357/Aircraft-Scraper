import time
import random
from firecrawl import FirecrawlApp
import re
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from urllib.parse import urljoin
from urllib.parse import urlencode, quote

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

    def carregar_paises(self):
        """Carrega os países do arquivo JSON"""
        try:
            with open('./src/util_datas/paises.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Arquivo não encontrado. Criando novo...")
            return {}
        except json.JSONDecodeError:
            print("Erro ao ler JSON. Verifique o formato.")
            return {}
        
    def normalizar_nome(self, nome):
        # Normaliza o nome do país para busca
        return nome.strip().lower().replace(' ', '_').replace('-', '_')
        
    def get_codigo_pais(self, nome_pais, paises):
        # Retorna o código numérico do país
        chave = self.normalizar_nome(nome_pais)
        return paises.get(chave)

    def build_search_url(self, manufacturer, model=None, country=None, year=None, price=None):
        """Construindo a url de busca, codificand os parametros"""

        try:
            base_url = "https://www.controller.com/listings/search"

            params = {'Manufacturer': manufacturer}

            if model:
                params['Model'] = model
            if country:
                paises = self.carregar_paises()
                params['Country'] = self.get_codigo_pais(country, paises)
            if year and isinstance(year, dict):
                params['Year'] = ""
                if 'min' in year:
                    params['Year'] += year['min']
                params['Year'] += '*'
                if 'max' in year:
                    params['Year'] += year['max']
            if price and isinstance(price, dict):
                params['Price'] = ""
                if 'min' in price:
                    params['Price'] += price['min']
                params['Price'] += '*'
                if 'max' in price:
                    params['Price'] += price['max']

            query_string = urlencode(params, quote_via=quote)

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
                relative_link += '?print=1'
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
        """Filtra dados específicos de anúncios de aeronaves do controller.com"""
        try:
            html_content = self.scrape_as_html(url, save_to_file=save_to_file)
            if not html_content:
                print("HTML content is empty. Cannot filter data.")
                return None

            soup = BeautifulSoup(html_content, 'html.parser')
            filtered_data = {
                'url': url,
                'titulo': 'Não encontrado',
                'preco': 'Não encontrado',
                'localizacao': 'Não encontrado',
                'ano': 'Não encontrado',
                'fabricante': 'Não encontrado',
                'modelo': 'Não encontrado',
                'horas_totais': 'Não encontrado',
                'motor_1_horas': 'Não encontrado',
                'motor_2_horas': 'Não encontrado',
                'motor_1_tbo': 'Não encontrado',
                'motor_2_tbo': 'Não encontrado',
                'vendedor': 'Não encontrado',
                'telefone': 'Não encontrado',
                'descricao': 'Não encontrado',
            }

            # 1. Título do anúncio
            title_selectors = ['h1', '.listing-title', '.title', '[class*="title"]']
            for selector in title_selectors:
                title_tag = soup.select_one(selector)
                if title_tag and title_tag.get_text(strip=True):
                    filtered_data['titulo'] = title_tag.get_text(strip=True)
                    break

            # 2. Preço
            price_selectors = ['.price', '.cost', '.amount', '[class*="price"]', '[class*="cost"]']
            price_patterns = [r'Call\s*for\s*price', r'USD\s*\$[\d,]+', r'\$[\d,]+']
            
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    for pattern in price_patterns:
                        match = re.search(pattern, price_text)
                        if match:
                            filtered_data['preco'] = match.group()
                            break
                    if filtered_data['preco'] != 'Não encontrado':
                        break
            
            # Se não encontrou por seletor, busca no texto completo
            if filtered_data['preco'] == 'Não encontrado':
                for pattern in price_patterns:
                    match = re.search(pattern, html_content)
                    if match:
                        filtered_data['preco'] = match.group()
                        break

            # 3. Localização
            location_selectors = [
                'a[href*="google.com/maps"]',
                'a[href*="maps.google.com"]',
                'a[href*="google.com/maps/search"]' 
            ]
            for selector in location_selectors:
                location_element = soup.select_one(selector)
                if location_element and location_element.get_text(strip=True):
                    filtered_data['localizacao'] = location_element.get_text(strip=True)
                    break

            # 4. Ano - procura por padrão de 4 dígitos (ano)
            year_match = re.search(r'\b(19|20)\d{2}\b', html_content)
            if year_match:
                filtered_data['ano'] = year_match.group()

            # 5. Fabricante e Modelo - extrai do título ou URL
            if filtered_data['titulo'] != 'Não encontrado':
                # Tenta extrair fabricante e modelo do título
                title = filtered_data['titulo'].upper()
                manufacturers = ['PIPER', 'CESSNA', 'BEECHCRAFT', 'BOEING', 'AIRBUS', 'CIRRUS', 'MOONEY']
                for manufacturer in manufacturers:
                    if manufacturer in title:
                        filtered_data['fabricante'] = manufacturer
                        # Tenta extrair modelo (parte após o fabricante)
                        model_part = title.split(manufacturer, 1)[-1].strip()
                        if model_part:
                            # Pega as primeiras palavras como modelo
                            words = model_part.split()[:3]
                            filtered_data['modelo'] = ' '.join(words)
                        break

            # 6. Horas totais e dos motores

            texto_sem_tags = re.sub(r'<[^>]+>', ' ', html_content)

            time_patterns = {
                'horas_totais': [
                    r'Total Time[^\d]*([\d,\.]+)',           
                    r'Total[^\d]*Time[^\d]*([\d,\.]+)', 
                    r'Total[^\d]*([\d,\.]+)\s*Hours',       
                    r'Total[^\d]*([\d,\.]+)\s*Hrs',         
                    r'TT[^\d]*([\d,\.]+)',                   
                    r'([\d,\.]+)\s*Total Time',           
                    r'Total[^\d]*([\d,\.]+)'                
                ],
                'motor_1_horas': [
                    r'Engine 1 Time[^\d]*([\d,\.]+)\s*([A-Z]+)',  # Captura número E texto
                    r'Eng 1 Time[^\d]*([\d,\.]+)\s*([A-Z]+)',
                    r'Left Engine[^\d]*([\d,\.]+)\s*([A-Z]+)',
                    # Padrões alternativos caso o texto venha antes
                    r'Engine 1 Time\s*([A-Z]+)[^\d]*([\d,\.]+)'
                ],
                'motor_2_horas': [
                    r'Engine 2 Time[^\d]*([\d,\.]+)\s*([A-Z]+)',
                    r'Eng 2 Time[^\d]*([\d,\.]+)\s*([A-Z]+)', 
                    r'Right Engine[^\d]*([\d,\.]+)\s*([A-Z]+)',
                    # Padrões alternativos
                    r'Engine 2 Time\s*([A-Z]+)[^\d]*([\d,\.]+)'
                ],
                'motor_1_tbo': [
                    r'Engine 1 TBO[^\d]*([\d,\.]+)',
                    r'Eng 1 TBO[^\d]*([\d,\.]+)',
                    r'Left Engine TBO[^\d]*([\d,\.]+)'
                ],
                'motor_2_tbo': [
                    r'Engine 2 TBO[^\d]*([\d,\.]+)',
                    r'Eng 2 TBO[^\d]*([\d,\.]+)',
                    r'Right Engine TBO[^\d]*([\d,\.]+)'
                ]
            }

            for field, patterns in time_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, texto_sem_tags, re.IGNORECASE)
                    if match:
                        numero_com_virgula = match.group(1)
                        texto = match.group(2) if len(match.groups()) > 1 else ''
                        numero_sem_virgula = numero_com_virgula.replace(',', '')  # Remove vírgulas
                        filtered_data[field] = {'horas': numero_sem_virgula, 'status': texto.strip()} if texto else numero_sem_virgula
                        print(f"✅ {field}: {numero_sem_virgula} {texto.strip() if texto else ''}")
                        break

            # 7. Informações do vendedor

            # Padrão para capturar contato do vendedor
            padroes = [
                r'Contact:([^<]+)<br/>', 
                r'Contact:\s*([^<\n]+)<br/>',    
                r'Contact:\s*([^<\n]+)(?:<br/>|$)', 
                r'Contact[^:]*:\s*([^<\n]+)'      
            ]
            
            for padrao in padroes:
                match = re.search(padrao, html_content, re.IGNORECASE)
                if match:
                    filtered_data['vendedor'] = match.group(1).strip()
            

            # 8. Telefone do vendedor

            # Tenta capturar do texto dentro da tag primeiro
            phone_patterns = [r'Phone:.*?<a[^>]*>([^<]+)</a>']
        
            for pattern in phone_patterns:
                match = re.search(pattern, html_content)
                if match:
                    filtered_data['telefone'] = match.group(1).strip()
                    break
                else:
                    # Fallback: captura do href
                    padrao_href = r'Phone:.*?<a href="tel:([^"]+)"'
                    match = re.search(padrao_href, html_content)
                    if match:
                        filtered_data['telefone'] = match.group(1).strip()
                        break

            # 9. Descrição - pega o primeiro parágrafo longo
            padroes = [
                r'Description<br/><br/>([^<]+)<br/>',           # Descrição básica
                r'Description<br/><br/>([^<]+)(?:<br/>|</)',    # Descrição com diferentes fechamentos
                r'Description\s*<br/><br/>([^<]+?)\s*(?:<br/>|</|$)',  # Com espaços e vários finais
                r'Description[^>]*>([^<]+)(?:<|$)',             # Formato mais genérico
                r'<br/><br/>([^<]+)<br/>'                       # Fallback para qualquer texto entre <br/>
            ]
            for padrao in padroes:
                match = re.search(padrao, html_content, re.IGNORECASE)
                if match:
                    descricao = match.group(1).strip()
                    # Remove espaços extras e quebras de linha
                    descricao = re.sub(r'\s+', ' ', descricao)
                    filtered_data['descricao'] = descricao
                    break

            print(f"✅ Dados extraídos: {filtered_data['fabricante']} {filtered_data['modelo']} - {filtered_data['ano']}")
            return filtered_data

        except Exception as e:
            print(f"🚨 Erro na filtragem HTML: {e}")
            import traceback
            traceback.print_exc()
            return None