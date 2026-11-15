from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from backend.deployment import create_deployment


def test_prefix_preserves_api_static_files_and_lifespan_for_both_proxy_styles(tmp_path):
    events = []

    @asynccontextmanager
    async def lifecycle(app):
        events.append('started')
        yield
        events.append('stopped')

    app = FastAPI(lifespan=lifecycle)

    @app.get('/api/health')
    def health():
        return {'status': 'ok'}

    (tmp_path/'index.html').write_text('prepared viewer')
    (tmp_path/'test.css').write_text('body{color:red}')
    app.mount('/', StaticFiles(directory=tmp_path, html=True))
    deployed = create_deployment(app, '/spherex', ['https://owner.github.io'])
    with TestClient(deployed) as client:
        assert events == ['started']
        for prefix in ('', '/spherex'):
            assert client.get(prefix+'/api/health').json() == {'status': 'ok'}
            assert client.get(prefix+'/').text == 'prepared viewer'
            assert client.get(prefix+'/test.css').status_code == 200
        headers = {'Origin': 'https://owner.github.io', 'Access-Control-Request-Method': 'POST',
                   'Access-Control-Request-Headers': 'content-type'}
        allowed = client.options('/spherex/api/health', headers=headers)
        assert allowed.status_code == 200
        assert allowed.headers['access-control-allow-origin'] == 'https://owner.github.io'
        headers['Origin'] = 'https://other.example'
        assert client.options('/spherex/api/health', headers=headers).status_code == 400
    assert events == ['started', 'stopped']
