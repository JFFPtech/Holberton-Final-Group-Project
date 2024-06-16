import requests
from bs4 import BeautifulSoup

def scrape_product_data(product_url):
    response = requests.get(product_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    product_data = {}
    product_data['title'] = soup.find('h1', class_='product-title').text.strip()  # Adjust selector
    product_data['price'] = soup.find('span', class_='product-price').text.strip()  # Adjust selector

    return product_data
