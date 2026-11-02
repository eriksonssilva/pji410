import numpy as np
import pandas as pd

from msa import cluster


def municipios_sinteticos(n=40):
    """Quatro perfis bem separados, um para cada nome de grupo."""
    rng = np.random.default_rng(0)
    perfis = {  # acess, locais_sem, pcd_por_mil, eleitores
        'baixa': (5, 90, 10, 8_000),
        'maiores': (40, 10, 12, 300_000),
        'alta_mais_pcd': (85, 0, 30, 8_000),
        'alta_menos_pcd': (85, 0, 4, 8_000),
    }
    linhas = []
    for nome, (acess, sem, pcd, el) in perfis.items():
        for i in range(n):
            linhas.append({
                'cd_municipio': f'{nome}-{i}', 'esperado': nome,
                'pct_secoes_acessiveis': acess + rng.normal(0, 2),
                'pct_locais_sem_acess': max(0, sem + rng.normal(0, 2)),
                'pcd_por_mil': pcd + rng.normal(0, 0.5),
                'qt_eleitores': int(el * rng.uniform(0.9, 1.1)),
                'pct_pcd_sem_acess': 100 - acess, 'pcd_total': 10, 'pcd_sem_acess': 5,
            })
    return pd.DataFrame(linhas)


def test_grupos_recebem_o_nome_do_perfil():
    m, _, _, _ = cluster.agrupar(municipios_sinteticos())
    grupo_por_perfil = m.groupby('esperado')['grupo'].agg(lambda s: s.mode()[0]).to_dict()
    assert grupo_por_perfil == {'baixa': 1, 'maiores': 2, 'alta_mais_pcd': 3, 'alta_menos_pcd': 4}
    assert m.groupby('esperado')['grupo'].nunique().eq(1).all()


def test_avaliacao_cobre_todos_os_k_e_silhueta_valida():
    _, avaliacao, perfis, resumo = cluster.agrupar(municipios_sinteticos())
    assert list(avaliacao['k']) == list(cluster.K_TESTADOS)
    assert avaliacao['silhueta'].between(-1, 1).all()
    assert resumo['k'] == 4 and resumo['silhueta'] > 0.5   # perfis sintéticos são bem separados
    assert list(perfis['grupo']) == [1, 2, 3, 4]


def test_resultado_e_reprodutivel():
    a, _, _, _ = cluster.agrupar(municipios_sinteticos())
    b, _, _, _ = cluster.agrupar(municipios_sinteticos())
    assert (a['grupo'] == b['grupo']).all()
