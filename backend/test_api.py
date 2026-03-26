import urllib.request, json
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/browniepoint2/predict', 
    data=json.dumps({'features':{'age':35},'explain':False}).encode('utf-8'), 
    headers={'Content-Type': 'application/json'}
)
try:
    res = urllib.request.urlopen(req)
    print(res.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
