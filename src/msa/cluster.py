"""Agrupamento dos municípios por perfil de acessibilidade eleitoral (k-means).

Indicadores usados (um por dimensão, para não repetir informação):
- pct_secoes_acessiveis  oferta: % de seções que constam como acessíveis
- pct_locais_sem_acess   concentração: % de locais sem nenhuma seção acessível
- pcd_por_mil            demanda: eleitores com deficiência cadastrados por mil eleitores (log)
- log_eleitores          porte do município (log10 do eleitorado)

O % de eleitores com deficiência em seções sem acessibilidade fica de fora do modelo porque
tem correlação de -0,95 com o primeiro indicador; ele é usado só para interpretar os grupos.

Uso: python -m msa.cluster [--dataset dataset]
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

INDICADORES = ['pct_secoes_acessiveis', 'pct_locais_sem_acess', 'pcd_por_mil', 'log_eleitores']
K_TESTADOS = range(2, 9)
K_ESCOLHIDO = 4
SEMENTE = 42

NOMES = {
    1: 'Baixa acessibilidade',
    2: 'Municípios maiores com acessibilidade parcial',
    3: 'Alta acessibilidade e mais eleitores com deficiência cadastrados',
    4: 'Alta acessibilidade e menos eleitores com deficiência cadastrados',
}


def matriz(municipios):
    """Indicadores transformados e padronizados (média 0, desvio 1)."""
    x = municipios[['pct_secoes_acessiveis', 'pct_locais_sem_acess', 'pcd_por_mil']].copy()
    x['pcd_por_mil'] = np.log1p(x['pcd_por_mil'])
    x['log_eleitores'] = np.log10(municipios['qt_eleitores'])
    return StandardScaler().fit_transform(x[INDICADORES])


def avaliar_k(x):
    """Inércia (método do cotovelo) e coeficiente de silhueta para cada k."""
    linhas = []
    for k in K_TESTADOS:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEMENTE).fit(x)
        linhas.append({'k': k, 'inercia': round(km.inertia_, 1),
                       'silhueta': round(silhouette_score(x, km.labels_), 4)})
    return pd.DataFrame(linhas)


def nomear(municipios, rotulos):
    """Converte os rótulos do k-means (arbitrários) em grupos 1..4 com nome fixo,
    a partir das medianas de cada grupo."""
    perfil = municipios.assign(r=rotulos).groupby('r').agg(
        acess=('pct_secoes_acessiveis', 'median'), eleitores=('qt_eleitores', 'median'),
        pcd=('pcd_por_mil', 'median'))
    mapa = {perfil['acess'].idxmin(): 1}
    resto = perfil.drop(index=list(mapa))
    mapa[resto['eleitores'].idxmax()] = 2
    resto = resto.drop(index=resto['eleitores'].idxmax())
    mapa[resto['pcd'].idxmax()] = 3
    mapa[resto['pcd'].idxmin()] = 4
    return pd.Series(rotulos).map(mapa).to_numpy()


def perfis(municipios):
    """Resumo de cada grupo, nas unidades originais, para a interface e o relatório."""
    g = municipios.groupby('grupo')
    p = g.agg(
        municipios=('cd_municipio', 'size'),
        mediana_pct_secoes_acessiveis=('pct_secoes_acessiveis', 'median'),
        mediana_pct_locais_sem_acess=('pct_locais_sem_acess', 'median'),
        mediana_pcd_por_mil=('pcd_por_mil', 'median'),
        mediana_eleitores=('qt_eleitores', 'median'),
        mediana_pct_pcd_sem_acess=('pct_pcd_sem_acess', 'median'),
        eleitores=('qt_eleitores', 'sum'),
        pcd_total=('pcd_total', 'sum'),
        pcd_sem_acess=('pcd_sem_acess', 'sum'),
    ).round(2).reset_index()
    p.insert(1, 'nome', p['grupo'].map(NOMES))
    return p


def agrupar(municipios):
    x = matriz(municipios)
    avaliacao = avaliar_k(x)
    km = KMeans(n_clusters=K_ESCOLHIDO, n_init=10, random_state=SEMENTE).fit(x)
    m = municipios.copy()
    m['grupo'] = nomear(m, km.labels_)
    resumo = {
        'k': K_ESCOLHIDO,
        'indicadores': INDICADORES,
        'silhueta': round(silhouette_score(x, km.labels_), 4),
        'semente': SEMENTE,
    }
    return m, avaliacao, perfis(m), resumo


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dataset', default='dataset')
    a = ap.parse_args()
    caminho = os.path.join(a.dataset, 'municipios.csv')
    municipios = pd.read_csv(caminho, dtype={'cd_municipio': str})
    municipios = municipios.drop(columns=['grupo'], errors='ignore')

    m, avaliacao, p, resumo = agrupar(municipios)
    m.to_csv(caminho, index=False)
    avaliacao.to_csv(os.path.join(a.dataset, 'kmeans_avaliacao.csv'), index=False)
    p.to_csv(os.path.join(a.dataset, 'grupos.csv'), index=False)
    with open(os.path.join(a.dataset, 'kmeans_resumo.json'), 'w') as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    print(avaliacao.to_string(index=False))
    print(p[['grupo', 'nome', 'municipios', 'mediana_pct_secoes_acessiveis', 'pcd_sem_acess']].to_string(index=False))
    print('silhueta k=%d: %.3f' % (resumo['k'], resumo['silhueta']))


if __name__ == '__main__':
    main()
