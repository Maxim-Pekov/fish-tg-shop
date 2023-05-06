import requests


def fetch_access_token(client_id, client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        "client_id": client_id,
        'client_secret': client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    access_token = response.json()
    return access_token['access_token'], access_token['expires']


def fetch_products(access_token):
    url = 'https://api.moltin.com/pcm/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def put_product_to_cart(marker, product, chat_id, price, product_count):
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    headers = {
        'Authorization': f'Bearer {marker}',
        'Content-Type': 'application/json',
    }
    description = product['data']['attributes'].get('description', 'Нет')
    payload = {
        'data': {
            'type': 'custom_item',
            'name': product.get('data').get('attributes').get('name'),
            'sku': product.get('data').get('attributes').get('sku'),
            'description': description,
            'quantity': int(product_count),
            'price': {
                'amount': price,
            },
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return True


def fetch_cart_products(access_token, chat_id):
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def remove_product_from_cart(access_token, chat_id, product_id):
    url = f"https://api.moltin.com/v2/carts/{chat_id}/items/{product_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return True


def fetch_product_by_id(access_token, product_id):
    url = f'https://api.moltin.com/pcm/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_product_photo_id(access_token, product_id):
    url = f'https://api.moltin.com/pcm/products/{product_id}/relationships/main_image'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['id']


def fetch_photo_by_id(access_token, photo_id):
    url = f'https://api.moltin.com/v2/files/{photo_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def fetch_prices_book(access_token):
    url = 'https://api.moltin.com/pcm/pricebooks/'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_product_prices(access_token, price_id):
    url = f'https://api.moltin.com/pcm/pricebooks/{price_id}/prices'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_product_stock(access_token, product_id):
    url = f'https://api.moltin.com/v2/inventories/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['available']


def create_client(access_token, name, email, password='', type='customer'):
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {access_token}',
        "Content-Type": "application/json"
    }
    payload = {
        'data': {
            'type': type,
            'name': name,
            'email': email,
            'password': password
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
