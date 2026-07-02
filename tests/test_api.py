import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_predict():
    payload = {"features": {"age":39,"workclass":"Private","fnlwgt":77516,"education":"Bachelors","education_num":13,"marital_status":"Never-married","occupation":"Tech-support","relationship":"Not-in-family","race":"White","sex":"Male","capital_gain":2174,"capital_loss":0,"hours_per_week":40,"native_country":"United-States"}}
    r = client.post('/predict', json=payload)
    assert r.status_code == 200
    assert 'probability_over_50k' in r.json()
