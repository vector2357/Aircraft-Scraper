# 🛩️ Web Scraper de Aeronaves

Scraper automatizado para extrair dados de anúncios de aeronaves.

## 🚀 Como Usar

### Com Docker (Recomendado):
```bash
# Configurar ambiente
cp .env.example .env
# Editar .env com sua API key

# Na pasta do seu projeto (onde está o Dockerfile)
docker build -t aircraft-scraper .

# Versão básica
docker run aircraft-scraper

# Com variáveis de ambiente
docker run -e FIRECRAWL_API_KEY="sua_chave_aqui" aircraft-scraper

# Com .env file
docker run --rm -it --env-file .env -v "$(pwd)/scraped_data:/app/scraped_data" aircraft-scraper    # ESSE SERÁ O MAIS UTILIZADO

# Executar apenas testes unitários
docker run --rm aircraft-scraper python -m pytest tests/test_scraper_unit.py -v

# Executar apenas testes de integração
docker run --rm aircraft-scraper python -m pytest tests/test_scraper_integration.py -v -m integration

# Executar testes específicos
docker run --rm aircraft-scraper python -m pytest tests/test_scraper_unit.py::TestFirecrawlScraperUnit::test_build_search_url_basic -v

# Opção de mensagem de testes com cores
docker run --rm aircraft-scraper python -m pytest tests/test_scraper_unit.py::TestFirecrawlScraperUnit::test_build_search_url_basic -v --color=yes --tb=short