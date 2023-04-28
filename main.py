import requests
from environs import Env

env = Env()
env.read_env()



# data = {
#       "type": "custom_item",
#       "name": "blue fish",
#       "sku": "fish-001",
#       "description": "Sweet fish",
#       "quantity": "2",
#       "price": { "amount": 5000 }
# }


def fetch_access_token( client_id, client_secret ):

    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        "client_id": client_id,
        'client_secret': client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()['access_token']


def fetch_products(access_token):
    url = 'https://api.moltin.com/pcm/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_access_marker(client_id):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        "client_id": client_id,
        "grant_type": "implicit",
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()['access_token']


def get_branch(access_token):
    url = 'https://api.moltin.com/v2/carts/abcd'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['id']


def get_branch_f(access_token):
    url = 'https://api.moltin.com/v2/carts'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'x-moltin-customer-token': 'abcd'
    }
    data = {
        "data": {
            "name": "max cart",
            "description": "holidays"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def put_product_to_branch(marker, one_product, branch_url, client_id):
    if not marker:
        fetch_access_marker(client_id)
    url = f'https://api.moltin.com/v2/carts/{branch_url}/items'
    headers = {
        'Authorization': f'Bearer {marker}',
        'Content-Type': 'application/json',
    }
    payload = {
        'data': {
            'type': 'custom_item',
                'name': one_product.get('attributes').get('name'),
                'sku': one_product.get('attributes').get('sku'),
                'description': one_product.get('attributes').get('description', 'Нет описания'),
                'quantity': 1,
                'price': {
                    'amount': 200,
                },
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return True


def fetch_products_branch(marker, branch_url):
    url = f'https://api.moltin.com/v2/carts/{branch_url}/items'
    headers = {
        'Authorization': f'Bearer {marker}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response


def fetch_product_by_id(access_token, product_id):
    url = f'https://api.moltin.com/pcm/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def generate_client_token(access_token):
    url = 'https://api.moltin.com/v2/customers/tokens'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content- Type': 'application/json'
    }
    data = {
        'password': 123,
        'email': 'max@mail.ru',
        'type': 'token'
    }
    response = requests.post(url, headers, data)
    return response


def create_client(access_token, name, email, password, type):
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    data = {
        'type': type,
        'name': name,
        'email': email,
        'password': password

    }
    response = requests.post(url, headers=headers, data=data)


def add_product_to_cart(reference, access_token, client_id, one_product):
    url = f'https://api.moltin.com/v2/carts/:{reference}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers, json=one_product)
    return response


def main():
    client_id = env.str("CLIENT_ID")
    client_secret = env.str("SECRET_KEY")
    access_token = fetch_access_token(client_id, client_secret)
    print(access_token)
    products = fetch_products(access_token)
    print(products)
    one_product = products["data"][0]
    f = fetch_product_by_id(access_token, products["data"][0]['id'])
    marker = fetch_access_marker(client_id)
    branch_url = get_branch(marker)
    # cart = get_branch_f(access_token)
    z = put_product_to_branch(marker, one_product, branch_url, client_id)
    products_by_cart = fetch_products_branch(access_token, branch_url)
    client_token = generate_client_token(access_token)
    customer = create_client(access_token, 'max', 'max@mail.ru', '123qwe',
                        'customer')


    x = add_product_to_cart('reference', access_token, client_id, one_product)
    print(x)


if "__main__" == __name__:
      main()