from bs4 import BeautifulSoup
import requests


def scrape_product(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Charset': 'utf-8'
    }
    
    try:
        response = requests.get(url, headers=headers,)
        response.raise_for_status()
        response.encoding = 'utf-8'
        

        
        soup = BeautifulSoup(response.content.decode('latin1', errors='ignore'), 'html.parser')
        
        # Print the HTML to inspect the structure
        # print(soup.prettify())
        
        # Try different possible selectors for the title
        title = soup.select_one('.titulo')
        description = soup.select_one('.product-details')
        # pega a imagem do site dentro da tag img
        img = soup.select_one('.MagicZoomPlus').find('img')['src']
        imgs = soup.select_one('#mycarousel').find_all('a')
        
   
        imgs = [ 'https:' + x['href'] for x in imgs]
        product_data = {
            'title': title.text.strip(),
            'description': f'{description}'.replace('','"').replace('','"'),
            'img': f'https:{img}',
            'imgs': imgs
            
        }
        return product_data
        
    except requests.RequestException as e:
        raise Exception(f"Erro ao acessar a URL: {str(e)}")
    except ValueError as e:
        raise Exception(f"Erro ao extrair dados: {str(e)}")
    
    
    



