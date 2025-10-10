import pytest
import os
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

class TestFirecrawlScraperIntegration:
    """Testes de integração para FirecrawlScraper"""
    
    @pytest.mark.integration
    def test_filter_html_data_complete(self, scraper, sample_html_content):
        """Testa filtragem completa de dados HTML"""
        with patch.object(scraper, 'scrape_as_html') as mock_scrape:
            mock_scrape.return_value = sample_html_content
            
            result = scraper.filter_html_data("https://www.controller.com/listing/test")
            
            assert result is not None
            assert result['titulo'] == "Piper PA-28-181 Archer LX"
            assert result['preco'] == "USD $150,000"
            assert result['localizacao'] == "Orlando, FL"
            assert result['horas_totais'] == "2500"
            assert result['motor_1_horas'] == "1500"
            assert result['motor_1_tbo'] == "2000"
            assert result['vendedor'] == "Aircraft Sales Inc."
            assert result['telefone'] == "(123) 456-7890"
            assert "beautiful aircraft" in result['descricao']
    
    @pytest.mark.integration
    def test_filter_html_data_no_content(self, scraper):
        """Testa filtragem sem conteúdo HTML"""
        with patch.object(scraper, 'scrape_as_html') as mock_scrape:
            mock_scrape.return_value = None
            
            result = scraper.filter_html_data("https://www.controller.com/listing/test")
            
            assert result is None
    
    @pytest.mark.integration
    def test_filter_html_data_extraction_patterns(self, scraper):
        """Testa padrões de extração de dados"""
        test_html = """
        <html>
            <h1>1979 Cessna 172 Skyhawk</h1>
            <div>Price: $85,000 USD</div>
            <span>Location: Dallas, TX</span>
            <p>Total Time: 3200 hrs</p>
            <p>Engine Time: 1200 since overhaul</p>
            <div>Seller: Texas Aircraft Sales</div>
            <div>Phone: +1 (555) 123-4567</div>
        </html>
        """
        
        with patch.object(scraper, 'scrape_as_html') as mock_scrape:
            mock_scrape.return_value = test_html
            
            result = scraper.filter_html_data("https://www.controller.com/listing/test")
            
            assert result['titulo'] == "1979 Cessna 172 Skyhawk"
            assert "85000" in result['preco'] or "$85,000" in result['preco']
            assert "Dallas" in result['localizacao']
            assert result['ano'] == "1979"
            assert result['fabricante'] == "CESSNA"
            assert "172" in result['modelo']
            assert result['horas_totais'] == "3200"
    
    @pytest.mark.integration
    def test_full_workflow(self, scraper, sample_search_html, sample_html_content):
        """Testa fluxo completo: busca -> links -> filtragem"""
        # Mock da busca por links
        with patch.object(scraper, 'scrape_as_html') as mock_scrape:
            mock_scrape.side_effect = [
                sample_search_html,  # Primeira chamada: página de busca
                sample_html_content  # Segunda chamada: página de detalhes
            ]
            
            # Busca links
            links = scraper.get_listing_links("https://www.controller.com/search")
            assert len(links) > 0
            
            # Filtra dados do primeiro link
            first_link = links[0]
            result = scraper.filter_html_data(first_link)
            
            assert result is not None
            assert result['url'] == first_link
            assert 'Piper' in result['titulo']
    
    @pytest.mark.integration
    @patch('src.web_scraping.BeautifulSoup')
    def test_filter_html_data_parsing_error(self, mock_soup, scraper):
        """Testa tratamento de erro na análise HTML"""
        mock_soup.side_effect = Exception("HTML parsing failed")
        
        with patch.object(scraper, 'scrape_as_html') as mock_scrape:
            mock_scrape.return_value = "<html>test</html>"
            
            result = scraper.filter_html_data("https://www.controller.com/listing/test")
            
            assert result is None
    
    @pytest.mark.integration
    def test_phone_number_patterns(self, scraper):
        """Testa diferentes padrões de telefone"""
        test_cases = [
            ("(123) 456-7890", "(123) 456-7890"),
            ("123-456-7890", "123-456-7890"),
            ("+1 555 123 4567", "+1 555 123 4567"),
            ("Phone: 555.123.4567", "555.123.4567")
        ]
        
        for phone_text, expected in test_cases:
            test_html = f"""
            <html>
                <h1>Test Aircraft</h1>
                <div class="phone">{phone_text}</div>
            </html>
            """
            
            with patch.object(scraper, 'scrape_as_html') as mock_scrape:
                mock_scrape.return_value = test_html
                
                result = scraper.filter_html_data("https://www.controller.com/listing/test")
                
                # Verifica se encontrou algum telefone (pode variar)
                if expected in phone_text:
                    assert result['telefone'] != 'Não encontrado'