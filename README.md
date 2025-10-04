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
docker run -it --env-file .env aircraft-scraper     # ESSE SERÁ O MAIS UTILIZADO