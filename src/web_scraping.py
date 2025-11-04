import requests  # 🔥 NOVO: Substitui Firecrawl
import re
from bs4 import BeautifulSoup
import os
import sys
import json
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from urllib.parse import urljoin
from urllib.parse import urlencode, quote

# Adicionar o diretório pai ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.engine import engine_left_time

class ZenRowsScraper:
    def __init__(self):
        self.api_key = os.getenv('ZENROWS_API_KEY')
        self.base_url = "https://api.zenrows.com/v1/"

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
        return paises.get(chave, None)

    def build_search_url(self, search):
        """Construindo a url de busca, codificand os parametros"""
        try:
            base_url = "https://www.controller.com/listings/search"

            params = {}

            # Parâmetro manufacturer
            """ if search['manufacturer']:
                params['Manufacturer'] = search['manufacturer']

            # Parâmetro model
            if search['model']:
                params['Model'] = search['model']
            """

            # Parâmetro keywords
            if search['keywords']:
                params['keywords'] = search['keywords']

            # Parâmetro country
            if search['country']:
                paises = self.carregar_paises()
                codigo_pais = self.get_codigo_pais(search['country'], paises)
                if codigo_pais:
                    params['Country'] = str(codigo_pais)
                else:
                    print(f"⚠️  País '{search['country']}' não encontrado na lista. Ignorando filtro de país.")
                    return None

            # Parâmetro year
            if search['year'] and isinstance(search['year'], dict) and (search['year']['min'] or search['year']['max']):
                params['Year'] = ""
                if search['year']['min']:
                    params['Year'] += search['year']['min']
                params['Year'] += '*'
                if search['year']['max']:
                    params['Year'] += search['year']['max']

            # Parâmetro price
            if search['price'] and isinstance(search['price'], dict) and (search['price']['min'] or search['price']['max']):
                params['Price'] = ""
                if search['price']['min']:
                    params['Price'] += search['price']['min']
                params['Price'] += '*'
                if search['price']['max']:
                    params['Price'] += search['price']['max']

            query_string = urlencode(params, quote_via=quote)

            final_url = f"{base_url}?{query_string}"
        
            return final_url
        
        except Exception as e:
            print(f"Erro na construção da url: {e}")
            return None

    def scrape_as_html(self, url, save_to_file=True, pretty_print=True, output_dir='./scraped_data/html_files'):
        """Scraping usando ZenRows"""
        try:
            # delay(random.uniform(5, 10))  # Delay entre 5 a 10 segundos antes da requisição
            
            print(f"🔄 Iniciando scraping ZenRows de: {url}")
            
            params = {
                'url': url,
                'apikey': self.api_key,
                'js_render': 'false',           # Renderiza JavaScript
                'antibot': 'true',             # Ativa proteção anti-bot
                'premium_proxy': 'false',       # Usa proxies residenciais
                'wait': '5000',                # Espera 5 segundos
            }
            
            response = requests.get(self.base_url, params=params, timeout=60)
            print(response.text[:500])
            
            if response.status_code == 200:
                html_content = response.text
                print("✅ ZenRows success!")
                
                # Verificar se ainda está bloqueado
                if "Pardon Our Interruption" in html_content:
                    print("❌ Ainda bloqueado pelo Distil Networks")
                    return None
                
                # Salvar se solicitado
                if save_to_file and html_content:
                    pretty_html = html_content
                    if pretty_print:
                        pretty_html = self._format_html(html_content)
                    filename = 'teste10.html'  # 🔥 MANTIDO SEU NOME
                    filepath = os.path.join(output_dir, filename)
                    
                    os.makedirs(output_dir, exist_ok=True)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(pretty_html)
                    print(f"💾 HTML salvo em: {filepath}")
                
                return html_content
            else:
                print(f"❌ ZenRows error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"🚨 Erro no scraping ZenRows: {e}")
            return None

    def get_listing_links(self, search_url):
        """Pegando todos os links de uma página de busca - MANTIDA SUA LÓGICA"""
        try:
            print(f"A procurar links na página de pesquisa: {search_url}")

            # Buscar a página (agora usando ZenRows)
            html_content = self.scrape_as_html(search_url)

            if not html_content:
                print("Não foi possível obter o conteúdo HTML da página de pesquisa.")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')

            # DEBUG: Verificar estrutura da página
            print(f"📊 Título da página: {soup.title.string if soup.title else 'Não encontrado'}")
            
            # Tentar diferentes seletores para encontrar os links
            link_tags = []

            if soup.find('h1', text=re.compile(r'No Listings Found', re.IGNORECASE)):
                print("❌ Nenhum anúncio encontrado na página de pesquisa.")
                return []
            
            # Seletor original (MANTIDA SUA LÓGICA)
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
                'motor_1_left': 'Não encontrado',
                'motor_2_left': 'Não encontrado',
                'horas_totais': 'Não encontrado',
                'motor_1_horas': {
                    'horas': 'Não encontrado',
                    'status': 'Desconhecido'
                },
                'motor_2_horas': {
                    'horas': 'Não encontrado',
                    'status': 'Desconhecido'
                },
                'motor_1_tbo': 'Não encontrado',
                'motor_2_tbo': 'Não encontrado',
                'vendedor': 'Não encontrado',
                'telefone': 'Não encontrado',
            }

            # 1. Título do anúncio
            title_selectors = ['h1', '.detail-title', '.listing-title', '.title', '[class*="title"]']
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

            # Se não encontrou ainda, busca pela classe
            if filtered_data['preco'] == 'Não encontrado':
                price = soup.find('strong', class_='listing-prices__retail-price')
                if price:
                    filtered_data['preco'] = price.get_text(strip=True)

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

            # Se não encontrou por seletor, busca pela classe da tag
            if filtered_data['localizacao'] == 'Não encontrado':
                location = soup.find('div', class_='dealer-contact__location')
                if location:
                    filtered_data['localizacao'] = location.get_text(strip=True)
                else:
                    location = soup.find('p', class_='dealer-contact__location')
                    if location:
                        filtered_data['localizacao'] = location.get_text(strip=True)

            # Seletores da tabela de dados no html
            table_data_list = soup.find_all('span', class_='print-data-label')

            # 4. Ano - procura por padrão de 4 dígitos (ano)
            year_match = re.search(r'\b(19|20)\d{2}\b', html_content)
            if year_match:
                filtered_data['ano'] = year_match.group()

            # Se não encontrou ainda, extrair por classe da tag
            if filtered_data['ano'] == 'Não encontrado':
                for year_head in table_data_list:
                    if year_head and 'Year' in year_head.get_text():
                        year = year_head.find_next_sibling('span')
                        if year and len(year.get_text(strip=True)) == 4 and year.get_text(strip=True).isdigit():
                            filtered_data['ano'] = year.get_text(strip=True)
                            break

            # 5. Fabricante e Modelo - extrai por classe na tag do html
            for manufacturer_head in table_data_list:
                if manufacturer_head and 'Manufacturer' in manufacturer_head.get_text():
                    manufacturer = manufacturer_head.find_next_sibling('span')
                    if manufacturer:
                        filtered_data['fabricante'] = manufacturer.get_text(strip=True)
                        break

            for model_head in table_data_list:
                if model_head and 'Model' in model_head.get_text():
                    model = model_head.find_next_sibling('span')
                    if model:
                        filtered_data['modelo'] = model.get_text(strip=True)
                        break

            # Se não encontrou Fabricante ou Modelo - extrai do título ou URL
            if filtered_data['fabricante'] == 'Não encontrado' or filtered_data['modelo'] == 'Não encontrado':
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
            for total_time_head in table_data_list:
                if total_time_head and 'Total Time' in total_time_head.get_text():
                    total_time = total_time_head.find_next_sibling('span')
                    if total_time:
                        numero_com_virgula = total_time.get_text(strip=True)
                        filtered_data['horas_totais'] = numero_com_virgula.replace(',', '')
                        break

            for engine1_time_head in table_data_list:
                if engine1_time_head and 'Engine 1 Time' in engine1_time_head.get_text() or 'Engine Time' in engine1_time_head.get_text():
                    engine1_time = engine1_time_head.find_next_sibling('span')
                    if engine1_time:
                        partes = engine1_time.get_text(strip=True).split()
                        numero_com_virgula = partes[0]
                        status_text = partes[1] if len(partes) > 1 else 'Desconhecido'
                        filtered_data['motor_1_horas']['horas'] = numero_com_virgula.replace(',', '')
                        filtered_data['motor_1_horas']['status'] = status_text
                        break

            for engine2_time_head in table_data_list:
                if engine2_time_head and 'Engine 2 Time' in engine2_time_head.get_text():
                    engine2_time = engine2_time_head.find_next_sibling('span')
                    if engine2_time:
                        partes = engine2_time.get_text(strip=True).split()
                        numero_com_virgula = partes[0]
                        status_text = partes[1] if len(partes) > 1 else 'Desconhecido'
                        filtered_data['motor_2_horas']['horas'] = numero_com_virgula.replace(',', '')
                        filtered_data['motor_2_horas']['status'] = status_text
                        break

            for engine1_TBO_time_head in table_data_list:
                if engine1_TBO_time_head and 'Engine 1 TBO' in engine1_TBO_time_head.get_text() or 'Engine TBO' in engine1_TBO_time_head.get_text():
                    engine1_TBO_time = engine1_TBO_time_head.find_next_sibling('span')
                    if engine1_TBO_time:
                        numero_com_virgula = engine1_TBO_time.get_text(strip=True)
                        filtered_data['motor_1_tbo'] = numero_com_virgula.replace(',', '')
                        break

            for engine2_TBO_time_head in table_data_list:
                if engine2_TBO_time_head and 'Engine 2 TBO' in engine2_TBO_time_head.get_text():
                    engine2_TBO_time = engine2_TBO_time_head.find_next_sibling('span')
                    if engine2_TBO_time:
                        numero_com_virgula = engine2_TBO_time.get_text(strip=True)
                        filtered_data['motor_2_tbo'] = numero_com_virgula.replace(',', '')
                        break

            # 7. Informações do vendedor
            # Encontra o elemento pela classe
            elemento = soup.find('p', class_='dealer-contact__name')
            if elemento:
                texto = elemento.get_text(strip=True)
                texto_limpo = texto.split(':')[-1].strip()
                filtered_data['vendedor'] = texto_limpo

            if filtered_data['vendedor'] == 'Não encontrado':
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
            numero = soup.find('span', 'dealer-contact__link-text')
            if numero:
                filtered_data['telefone'] = numero.get_text(strip=True)

            if filtered_data['telefone'] == 'Não encontrado':
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

            # Cálculo das horas restantes
            # Motor 1
            if (filtered_data['motor_1_horas']['horas'] != 'Não encontrado' and
                filtered_data['motor_1_horas']['status'] != 'Desconhecido'):
                
                motor_1_tbo_value = filtered_data['motor_1_tbo']
                if motor_1_tbo_value != 'Não encontrado':
                    try:
                        filtered_data['motor_1_left'] = engine_left_time(
                            motor_1_tbo_value, 
                            filtered_data['motor_1_horas']['horas']
                        )
                    except (ValueError, TypeError) as e:
                        print(f"⚠️ Erro ao calcular motor_1_left: {e}")
                        filtered_data['motor_1_left'] = 'Erro no cálculo'

            # Motor 2  
            if (filtered_data['motor_2_horas']['horas'] != 'Não encontrado' and
                filtered_data['motor_2_horas']['status'] != 'Desconhecido'):
                
                motor_2_tbo_value = filtered_data['motor_2_tbo']
                if motor_2_tbo_value != 'Não encontrado':
                    try:
                        filtered_data['motor_2_left'] = engine_left_time(
                            motor_2_tbo_value, 
                            filtered_data['motor_2_horas']['horas']
                        )
                    except (ValueError, TypeError) as e:
                        print(f"⚠️ Erro ao calcular motor_2_left: {e}")
                        filtered_data['motor_2_left'] = 'Erro no cálculo'

            print(f"✅ Dados extraídos: {filtered_data['fabricante']} {filtered_data['modelo']} - {filtered_data['ano']}")
            return filtered_data

        except Exception as e:
            print(f"🚨 Erro na filtragem HTML: {e}")
            import traceback
            traceback.print_exc()
            return None