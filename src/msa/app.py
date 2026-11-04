"""Site "Minha Seção é Acessível?" (FastAPI).

Rodar localmente: uv run uvicorn msa.app:app --reload
Variáveis de ambiente:
  MSA_DATASET  pasta com os CSVs do dataset (padrão: dataset)
  MSA_DB       arquivo SQLite gerado na inicialização (padrão: data/msa.sqlite)
  MSA_ROOT     pasta com templates/ e static/ (padrão: raiz do repositório)
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from msa import db

RAIZ = Path(os.environ.get('MSA_ROOT', Path(__file__).resolve().parents[2]))
DATASET = os.environ.get('MSA_DATASET', str(RAIZ / 'dataset'))
CAMINHO_DB = os.environ.get('MSA_DB', str(RAIZ / 'data' / 'msa.sqlite'))

CORES = {1: '#D55E00', 2: '#E69F00', 3: '#56B4E9', 4: '#009E73'}  # paleta Okabe-Ito (daltonismo)
DESCRICOES = {
    1: 'Quase nenhuma seção consta como acessível. Na maioria dos locais de votação, todas as seções '
       'estão sem acessibilidade. A maior parte desses municípios é pequena.',
    2: 'Municípios médios e grandes, com parte das seções acessível. Eles têm a maioria dos eleitores '
       'do país e, por isso, a maioria dos eleitores com deficiência que votam em seções sem '
       'acessibilidade.',
    3: 'A maioria das seções consta como acessível. Esses municípios têm mais eleitores com '
       'deficiência cadastrados a cada mil eleitores do que os do grupo 4.',
    4: 'A maioria das seções consta como acessível. Esses municípios têm menos eleitores com '
       'deficiência cadastrados a cada mil eleitores do que os do grupo 3.',
}

banco: db.Banco | None = None


@asynccontextmanager
async def lifespan(_app):
    global banco
    db.carregar(DATASET, CAMINHO_DB)
    banco = db.Banco(CAMINHO_DB)
    yield


app = FastAPI(title='Minha Seção é Acessível?', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=RAIZ / 'static'), name='static')
app.mount('/dados', StaticFiles(directory=DATASET), name='dados')
templates = Jinja2Templates(directory=RAIZ / 'templates')
templates.env.globals.update(cores=CORES, descricoes=DESCRICOES)
templates.env.filters['br'] = lambda v, casas=0: (
    f'{v:,.{casas}f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if v is not None else 'sem dado')


def pagina(request, nome, **ctx):
    return templates.TemplateResponse(request, nome, ctx)


# ---------- páginas ----------

@app.get('/', response_class=HTMLResponse)
def inicio(request: Request):
    return pagina(request, 'inicio.html', brasil=banco.brasil(), ufs=banco.ufs(), grupos=banco.grupos())


@app.get('/secao', response_class=HTMLResponse)
def pagina_secao(request: Request, uf: str = Query(min_length=2, max_length=2),
                 zona: int = Query(ge=1), secao: int = Query(ge=1)):
    s = banco.secao(uf, zona, secao)
    if s is None:
        return pagina(request, 'nao_encontrada.html', uf=uf.upper(), zona=zona, secao=secao,
                      ufs=banco.ufs())
    return pagina(request, 'secao.html', s=s, grupo=banco.grupo(s['municipio']['grupo']))


@app.get('/municipio/{cd}', response_class=HTMLResponse)
def pagina_municipio(request: Request, cd: str):
    m = banco.municipio(cd)
    if m is None:
        raise HTTPException(404, 'Município não encontrado')
    return pagina(request, 'municipio.html', m=m, locais=banco.locais_do_municipio(cd),
                  grupo=banco.grupo(m['grupo']), brasil=banco.brasil())


@app.get('/mapa', response_class=HTMLResponse)
def pagina_mapa(request: Request):
    return pagina(request, 'mapa.html', grupos=banco.grupos())


@app.get('/grupos', response_class=HTMLResponse)
def pagina_grupos(request: Request):
    return pagina(request, 'grupos.html', grupos=banco.grupos(), avaliacao=banco.avaliacao_k(),
                  kmeans=banco.kmeans())


@app.get('/sobre', response_class=HTMLResponse)
def pagina_sobre(request: Request):
    return pagina(request, 'sobre.html', brasil=banco.brasil())


# ---------- API ----------

@app.get('/api/municipios')
def api_municipios(uf: str = Query(min_length=2, max_length=2)):
    return banco.municipios_da_uf(uf)


@app.get('/api/municipios/{cd}')
def api_municipio(cd: str):
    m = banco.municipio(cd)
    if m is None:
        raise HTTPException(404, 'Município não encontrado')
    return m


@app.get('/api/secoes/{uf}/{zona}/{secao}')
def api_secao(uf: str, zona: int, secao: int):
    s = banco.secao(uf, zona, secao)
    if s is None:
        raise HTTPException(404, 'Seção não encontrada')
    return s


@app.get('/api/mapa')
def api_mapa():
    """GeoJSON com um ponto por município (centro dos locais de votação)."""
    return {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [p['lon'], p['lat']]},
            'properties': {k: p[k] for k in ('cd_municipio', 'nm_municipio', 'uf', 'grupo',
                                             'pct_secoes_acessiveis', 'pcd_sem_acess')},
        } for p in banco.pontos_mapa()],
    }


@app.get('/api/grupos')
def api_grupos():
    return {'kmeans': banco.kmeans(), 'avaliacao_k': banco.avaliacao_k(), 'grupos': banco.grupos()}


@app.get('/api/locais/{cd}')
def api_locais(cd: str):
    return banco.locais_do_municipio(cd)


@app.get('/health')
def health():
    return {'status': 'ok'}
