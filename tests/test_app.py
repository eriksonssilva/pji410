import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope='module')
def cliente(tmp_path_factory):
    os.environ['MSA_DB'] = str(tmp_path_factory.mktemp('db') / 'teste.sqlite')
    from msa.app import app
    with TestClient(app) as c:
        yield c


def test_health(cliente):
    assert cliente.get('/health').json() == {'status': 'ok'}


def test_secao_que_consta_como_acessivel(cliente):
    s = cliente.get('/api/secoes/SP/121/428').json()
    assert s['consta_acessivel'] is True and s['local']['nm_municipio'] == 'SÃO CARLOS'


def test_secao_que_nao_consta(cliente):
    r = cliente.get('/secao', params={'uf': 'mg', 'zona': 222, 'secao': 125})
    assert r.status_code == 200
    assert 'não</u> consta como acessível nos dados do TSE' in r.text


def test_secao_inexistente(cliente):
    assert cliente.get('/api/secoes/MG/999/1').status_code == 404
    r = cliente.get('/secao', params={'uf': 'MG', 'zona': 999, 'secao': 1})
    assert 'Seção não encontrada' in r.text


def test_entrada_invalida(cliente):
    assert cliente.get('/secao', params={'uf': 'MG', 'zona': 'abc', 'secao': 1}).status_code == 422


def test_numeros_de_sao_carlos_e_pocos_batem_com_o_tse(cliente):
    sc = cliente.get('/api/municipios/70793').json()
    assert (sc['qt_secoes'], sc['qt_secoes_acessiveis'], sc['pcd_total'], sc['pcd_sem_acess']) == (579, 71, 2123, 1265)
    pc = cliente.get('/api/municipios/50350').json()
    assert (pc['qt_secoes'], pc['qt_secoes_acessiveis'], pc['pcd_total'], pc['pcd_sem_acess']) == (449, 165, 2178, 911)


def test_mapa_tem_um_ponto_por_municipio_com_coordenada(cliente):
    geo = cliente.get('/api/mapa').json()
    assert geo['type'] == 'FeatureCollection' and len(geo['features']) > 5500
    assert {f['properties']['grupo'] for f in geo['features']} == {1, 2, 3, 4}


def test_paginas_html(cliente):
    for caminho in ['/', '/mapa', '/grupos', '/sobre', '/municipio/50350']:
        r = cliente.get(caminho)
        assert r.status_code == 200 and 'não foi verificada em campo' in r.text, caminho


def test_nenhuma_pagina_afirma_que_secao_e_acessivel(cliente):
    for caminho in ['/', '/secao?uf=SP&zona=121&secao=428', '/municipio/50350']:
        assert 'seção é acessível' not in cliente.get(caminho).text.replace('Minha Seção é Acessível', '')


def test_dataset_para_download(cliente):
    assert cliente.get('/dados/municipios.csv').status_code == 200
