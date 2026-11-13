import pytest
import psycopg2
import os
from app import app as flask_app, init_db


@pytest.fixture
def clean_db():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432'),
        user=os.environ.get('DB_USER', 'shortener'),
        password=os.environ.get('DB_PASSWORD', 'shortener_pass'),
        dbname=os.environ.get('DB_NAME', 'shortener_db'),
    )
    cur = conn.cursor()
    cur.execute("DELETE FROM urls")
    conn.commit()
    cur.close()
    conn.close()
    yield


@pytest.fixture
def client(clean_db):
    flask_app.config['TESTING'] = True
    init_db()
    with flask_app.test_client() as client:
        yield client


def test_shorten_returns_201(client):
    response = client.post('/shorten', json={'url':'https://example.com/test'})
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_code' in data
    assert 'short_url' in data

def test_redirect_works(client):
    create = client.post('/shorten', json={'url': 'https://example.com/redirect-test'})
    code = create.get_json()['short_code']

    response = client.get(f'/{code}')

    assert response.status_code == 302
    assert response.headers['Location'] == 'https://example.com/redirect-test'

def test_redirect_unknown_code_returns_404(client):
    response = client.get('/nonexistent-code-12345')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'not found'

def test_shorten_without_url_returns_400(client):
    response = client.post('/shorten', json={})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'url is required'