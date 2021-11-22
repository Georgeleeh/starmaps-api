from os import putenv
import requests
import argparse
from datetime import datetime

def get_base_url():
    parser = argparse.ArgumentParser(description='Test this Flask api')
    parser.add_argument(
        'url',
        metavar='-u',
        type=str,
        nargs='?',
        help='the host url to test',
        default='http://127.0.0.1:5000/'
        )

    base_url = parser.parse_args().url

    if base_url[-1] == '/':
        base_url = base_url[:-1]
    if base_url[:4] != 'http':
        raise parser.error('is the url http:// or https:// ?')
    
    return base_url

def test(url, method, response_code, json=None):
    print(f'Testing URL: {url}')
    
    switch = {
        'get' : requests.get,
        'put' : requests.put,
        'post' : requests.post,
        'patch' : requests.patch,
        'delete' : requests.delete
    }

    r = switch[method](url, json=json)

    print(f'Desired Code: {response_code}')
    print(f'Actual Code: {r.status_code}')

    if r.status_code == response_code:
        print('Success!\n')
    else:
        print('Failed!\n')
        raise Exception(f'{url} provided the wrong response:\n{r}')
    
    return r.json()


# The basic request URL - http://127.0.0.1 by default
base_url = get_base_url()

tested_urls = []

# Put all transactions
print('Put all transactions\n')
put_transactions = test(base_url+f'/transaction', 'put', 200) # Correct request
tested_urls.append(base_url+f'/transaction')
print(f'All transactions: {put_transactions}')
print()

# Get all transactions
print('Get all transactions\n')
all_transactions = test(base_url+f'/transaction', 'get', 200) # Correct request
tested_urls.append(base_url+f'/transaction')
print(f'All transactions: {[t["id"] for t in all_transactions]}')
print()

# Get all transactions
print('Get all open transactions\n')
all_open_transactions = test(base_url+f'/transaction/open', 'get', 200) # Correct request
tested_urls.append(base_url+f'/transaction/open')
print(f'All transactions: {[t["id"] for t in all_open_transactions]}')
print()

# Get all buyers
print('Get all buyers\n')
all_buyers =test(base_url+f'/buyer', 'get', 200) # Correct request
tested_urls.append(base_url+f'/buyer')
print(f'All buyers: {[b["id"] for b in all_buyers]}')
print()

# Get all posters
print('Get all posters\n')
all_posters = test(base_url+f'/poster', 'get', 200) # Correct request
tested_urls.append(base_url+f'/poster')
print(f'All posters: {[p["id"] for p in all_posters]}')
print()

# Get all responses
print('Get all responses\n')
all_responses = test(base_url+f'/response', 'get', 200) # Correct request
tested_urls.append(base_url+f'/response')
print(f'All responses: {[r["id"] for r in all_responses]}')
print()

transaction = all_transactions[0]
transaction_id = transaction['id']
buyer_id = transaction['buyer_id']
poster_id = transaction['posters'][0]['id']

# Get transaction
print(f"Get transaction {transaction_id}\n")
r = test(base_url+f"/transaction/{transaction_id}", 'get', 200) # Correct request
tested_urls.append(base_url+f"/transaction/{transaction_id}")
print()

# Get buyer
print(f"Get buyer {buyer_id}\n")
r = test(base_url+f"/buyer/{buyer_id}", 'get', 200) # Correct request
tested_urls.append(base_url+f"/buyer/{buyer_id}")
print()

# Get poster
print(f"Get poster {poster_id}\n")
gotten_poster = test(base_url+f"/poster/{poster_id}", 'get', 200) # Correct request
tested_urls.append(base_url+f"/poster/{poster_id}")
print()

# Get poster response
print(f"Get poster response {poster_id}\n")
r = test(base_url+f"/poster/{poster_id}/response", 'get', 200) # Correct request
tested_urls.append(base_url+f"/poster/{poster_id}/response")
print()

put_transaction_id = 2579003080

# Put transaction
print(f'Put transaction {put_transaction_id}\n')
put_transaction = test(base_url+f'/transaction/{put_transaction_id}', 'put', 200) # Correct request
tested_urls.append(base_url+f'/transaction/{put_transaction_id}')
print(f'Put transaction: {put_transaction}')
print()

# Delete transaction
print(f'Delete transaction {put_transaction_id}\n')
put_transaction = test(base_url+f'/transaction/{put_transaction_id}', 'delete', 200) # Correct request
tested_urls.append(base_url+f'/transaction/{put_transaction_id}')
print()

post_response = {
            'map_datetime': datetime(2020, 1, 1).timestamp(),
            'map_written_datetime': '1st Jan 2020',
            'message': 'test message',
            'map_address': 'the house',
            'map_written_address': 'my house',
            'size': '8x10',
            'latitude': 1.0,
            'longitude': 2.0,
            'colour': 'White',
            'font': 'Amatic SC'
            }

modified_response = {
            'map_datetime': datetime(2019, 4, 1).timestamp(),
            'latitude': 40.7142700,
            'longitude': -74.0059700,
            'colour': 'Black',
            'font': 'Snell Roundhand'
            }

if gotten_poster['response'] is None:

    # Post response
    print(f'Post response for poster {poster_id}\n')
    posted_response = test(base_url+f'/poster/{poster_id}/response', 'post', 200, json=post_response) # Correct request
    tested_urls.append(base_url+f'/poster/{poster_id}/response')
    print(f'Put response: {posted_response}')
    print()

# Post response
print(f'Post response for poster {poster_id}\n')
patched_response = test(base_url+f'/poster/{poster_id}/response', 'patch', 200, json=modified_response) # Correct request
tested_urls.append(base_url+f'/poster/{poster_id}/response')
print(f'Patched response: {patched_response}')
print()

print('Tested URLs:')
for u in tested_urls:
    print(u)

print('All good, G!')