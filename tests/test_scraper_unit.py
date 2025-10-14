import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
import time
from src.web_scraping import FirecrawlScraper

class TestFirecrawlScraperUnit:
    """Testes unitários para FirecrawlScraper"""
    
    def test_init_with_api_key(self, mock_firecrawl_app):
        """Testa inicialização com API key"""
        scraper = FirecrawlScraper(api_key="test_key")
        
        mock_firecrawl_app.assert_called_once_with(api_key="test_key")
        assert scraper.app is not None
    
    def test_build_search_url_basic(self, scraper):
        """Testa construção de URL de busca básica"""
        url = scraper.build_search_url("PIPER")
        
        expected = "https://www.controller.com/listings/search?Manufacturer=PIPER"
        assert url == expected
    
    def test_build_search_url_with_multi_params(self, scraper):
        """Testa construção de URL de busca com modelo"""
        url = scraper.build_search_url("PIPER", "SENECA V", "USA", {"min": "2011", "max": "2012"}, {"min": "50000", "max": "800000"})
        
        expected = "https://www.controller.com/listings/search?Manufacturer=PIPER&Model=SENECA%20V&Country=178&Year=2011%2A2012&Price=50000%2A800000"
        assert url == expected
    
    def test_build_search_url_exception(self, scraper):
        """Testa tratamento de exceção na construção de URL"""
        with patch('src.web_scraping.urlencode') as mock_urlencode:
            mock_urlencode.side_effect = Exception("URL encode failed")
            
            url = scraper.build_search_url("PIPER")
            
            assert url is None
    
    def test_rate_limit_delay(self, scraper):
        """Testa o delay entre requisições"""
        start_time = time.time()
        
        scraper._rate_limit_delay()
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Verifica que houve um delay (pelo menos 6 segundos)
        assert elapsed >= 6.0
    
    def test_generate_custom_filename_html(self, scraper):
        """Testa geração de nome de arquivo HTML"""
        url = "https://www.controller.com/listings/search?Country=US&sort=price&keywords=cessna+172"
        filename = scraper._generate_custom_filename(url, 'html')
        
        assert filename.startswith("controller_com_")
        assert filename.endswith(".html")
        assert "US" in filename
        assert "price" in filename
        assert "cessna_172" in filename
    
    def test_generate_custom_filename_markdown(self, scraper):
        """Testa geração de nome de arquivo Markdown"""
        url = "https://www.controller.com/listings/search"
        filename = scraper._generate_custom_filename(url, 'md')
        
        assert filename.endswith(".md")
    
    def test_generate_custom_filename_exception(self, scraper):
        """Testa geração de nome com exceção"""
        with patch('src.web_scraping.urlparse') as mock_parse:
            mock_parse.side_effect = Exception("Parse failed")
            
            filename = scraper._generate_custom_filename("invalid_url", 'html')
            
            assert filename.startswith("fallback_")
            assert filename.endswith(".html")
    
    def test_markdown_to_html_conversion(self, scraper):
        """Testa conversão de markdown para HTML"""
        markdown = "# Title\n**Bold** and *italic* text"
        html = scraper._markdown_to_html(markdown)
        
        assert "<h1>Title</h1>" in html
        assert "<strong>Bold</strong>" in html
        assert "<em>italic</em>" in html
    
    def test_format_html_pretty(self, scraper):
        """Testa formatação de HTML"""
        ugly_html = "<html><body><div>test</div></body></html>"
        pretty_html = scraper._format_html(ugly_html)
        
        # BeautifulSoup adiciona quebras de linha na formatação
        assert "\n" in pretty_html
        assert "test" in pretty_html
    
    def test_format_html_exception(self, scraper):
        """Testa formatação de HTML com exceção"""
        with patch('src.web_scraping.BeautifulSoup') as mock_soup:
            mock_soup.side_effect = Exception("Parse error")
            
            result = scraper._format_html("<html>test</html>")
            
            assert result == "<html>test</html>"
    
    @patch('src.web_scraping.time.sleep')
    def test_scrape_as_html_success(self, mock_sleep, scraper, mock_firecrawl_app):
        """Testa scraping HTML bem-sucedido"""
        # Mock da resposta
        mock_result = MagicMock()
        mock_result.html = "<html>Test content</html>"
        mock_firecrawl_app.scrape.return_value = mock_result
        
        result = scraper.scrape_as_html("https://example.com")
        
        assert result == "<html>Test content</html>"
        mock_sleep.assert_called_once()
    
    @patch('src.web_scraping.time.sleep')
    def test_scrape_as_html_with_markdown(self, mock_sleep, scraper, mock_firecrawl_app):
        """Testa scraping com conversão de markdown"""
        mock_result = MagicMock()
        mock_result.markdown = "# Title\nTest content"
        mock_firecrawl_app.scrape.return_value = mock_result
        
        result = scraper.scrape_as_html("https://example.com")
        
        assert "<h1>Title</h1>" in result
        assert "Test content" in result
    
    @patch('src.web_scraping.time.sleep')
    def test_scrape_as_html_rate_limit_retry(self, mock_sleep, scraper, mock_firecrawl_app):
        """Testa retry automático em caso de rate limit"""
        mock_firecrawl_app.scrape.side_effect = [
            Exception("Rate Limit Exceeded - retry after 30s"),
            MagicMock(html="<html>Success</html>")
        ]
        
        result = scraper.scrape_as_html("https://example.com")
        
        assert result == "<html>Success</html>"
        assert mock_sleep.call_count == 2  # Delay inicial + retry
    
    @patch('src.web_scraping.time.sleep')
    def test_scrape_as_html_save_to_file(self, mock_sleep, scraper, mock_firecrawl_app, tmp_path):
        """Testa scraping com salvamento em arquivo"""
        mock_result = MagicMock()
        mock_result.html = "<html>Test content</html>"
        mock_firecrawl_app.scrape.return_value = mock_result
        
        output_dir = tmp_path / "html_files"
        result = scraper.scrape_as_html(
            "https://example.com", 
            save_to_file=True, 
            output_dir=str(output_dir)
        )
        
        assert result == "<html>Test content</html>"
        assert output_dir.exists()
        assert any(output_dir.iterdir())  # Verifica que arquivos foram criados
    
    def test_get_listing_links_success(self, scraper, sample_search_html):
        """Testa extração de links de listagem"""
        with patch.object(scraper, 'scrape_as_html') as mock_scrape:
            mock_scrape.return_value = sample_search_html
            
            links = scraper.get_listing_links("https://www.controller.com/search")
            
            assert len(links) == 2
            assert "https://www.controller.com/listing/piper-archer-123" in links
            assert "https://www.controller.com/listing/cessna-172-456" in links
    
    def test_get_listing_links_no_content(self, scraper):
        """Testa extração de links sem conteúdo"""
        with patch.object(scraper, 'scrape_as_html') as mock_scrape:
            mock_scrape.return_value = None
            
            links = scraper.get_listing_links("https://www.controller.com/search")
            
            assert links == []
    
    def test_get_listing_links_exception(self, scraper):
        """Testa extração de links com exceção"""
        with patch.object(scraper, 'scrape_as_html') as mock_scrape:
            mock_scrape.side_effect = Exception("Scraping failed")
            
            links = scraper.get_listing_links("https://www.controller.com/search")
            
            assert links == []