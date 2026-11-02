import pandas as pd
import pytest

from msa import build

FIX = 'tests/fixtures'


@pytest.fixture(scope='module')
def tabelas():
    secoes = pd.concat([build.montar_secoes(build.ler_csv_tse(c, build.COLS_LOCAL))
                        for c in build.arquivos_por_uf(FIX, 'eleitorado_local_votacao_2026')])
    pcd = pd.concat([build.contar_pcd(build.ler_csv_tse(c, build.COLS_PCD))
                     for c in build.arquivos_por_uf(FIX, 'perfil_eleitor_deficiencia_2026')])
    locais = build.montar_locais(secoes, pcd)
    return secoes, locais, build.montar_municipios(locais)


def test_ignora_exterior_e_consolidado():
    assert [c.rsplit('_', 1)[1] for c in build.arquivos_por_uf(FIX, 'eleitorado_local_votacao_2026')] == ['XX.csv']


def test_coordenada_com_virgula_e_ausente():
    assert build.coordenada('-21,98') == -21.98
    assert build.coordenada('-1') is None


def test_secoes_usam_so_um_turno(tabelas):
    secoes, _, _ = tabelas
    assert len(secoes) == 6


def test_secao_agregada_aponta_para_principal(tabelas):
    secoes, _, _ = tabelas
    agregada = secoes.set_index('nr_secao').loc[7]
    assert agregada['agregada'] and agregada['nr_secao_principal'] == 5
    assert pd.isna(secoes.set_index('nr_secao').loc[1, 'nr_secao_principal'])


def test_local_nao_mistura_municipios_da_mesma_zona(tabelas):
    _, locais, _ = tabelas
    assert set(locais['local_id']) == {'00001-100-10', '00001-100-20', '00002-100-10'}


def test_status_do_local(tabelas):
    _, locais, _ = tabelas
    status = locais.set_index('local_id')['status'].to_dict()
    assert status == {'00001-100-10': 'todas', '00001-100-20': 'parcial', '00002-100-10': 'nenhuma'}


def test_pcd_agregado_por_local_e_tipo(tabelas):
    _, locais, _ = tabelas
    l20 = locais.set_index('local_id').loc['00001-100-20']
    assert (l20['pcd_total'], l20['pcd_locomocao'], l20['pcd_sem_acess']) == (2, 2, 2)
    l10b = locais.set_index('local_id').loc['00002-100-10']
    assert (l10b['pcd_auditiva'], l10b['pcd_outros']) == (1, 1)


def test_secoes_nao_publicam_pcd(tabelas):
    secoes, _, _ = tabelas
    assert not [c for c in secoes.columns if c.startswith('pcd')]


def test_indicadores_do_municipio(tabelas):
    _, _, municipios = tabelas
    a = municipios.set_index('cd_municipio').loc['00001']
    assert a['pct_secoes_acessiveis'] == 75.0
    assert a['pct_locais_sem_acess'] == 0.0
    assert round(a['pct_pcd_sem_acess'], 2) == 66.67   # 2 dos 3 eleitores com deficiência
    b = municipios.set_index('cd_municipio').loc['00002']
    assert (b['pct_secoes_acessiveis'], b['pct_locais_sem_acess']) == (0.0, 100.0)
    assert pd.isna(b['lat'])
