import pytest
api = pytest.importorskip('flask')
from api.app import app, generate_orders


def test_api_determinism():
    assert generate_orders('2026-04-07') == generate_orders('2026-04-07')
    assert generate_orders('2026-04-07') != generate_orders('2026-04-08')


def test_api_auth_protects_orders(monkeypatch):
    monkeypatch.setenv('MARKETPLACE_API_TOKEN','un-secret-local')
    client = app.test_client()
    assert client.get('/orders?date=2026-04-07').status_code == 401
    assert client.get('/orders?date=2026-04-07',headers={
        'Authorization':'Bearer un-secret-local'}).status_code == 200


def test_api_invalid_date(monkeypatch):
    monkeypatch.setenv('MARKETPLACE_API_TOKEN','test')
    assert app.test_client().get('/orders?date=bad',headers={
        'Authorization':'Bearer test'}).status_code == 400
