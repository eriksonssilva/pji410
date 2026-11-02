"""Ingestão e tratamento dos dados abertos do TSE.

Lê os arquivos "Eleitorado por local de votação 2026" e "Perfil do eleitorado com
deficiência 2026" (um CSV por UF, separador ';', codificação Latin-1) e gera três
tabelas agregadas em dataset/:

- secoes.csv     uma linha por seção eleitoral (sem dados de eleitores com deficiência)
- locais.csv     uma linha por local de votação, com contagens de eleitores com deficiência
- municipios.csv uma linha por município, com os indicadores usados no agrupamento

Uso: python -m msa.build <pasta_locais> <pasta_deficiencia> [--saida dataset]
"""
import argparse
import glob
import os

import pandas as pd

TURNO = '1'  # o 1º turno cobre todos os municípios; a acessibilidade não muda entre turnos

COLS_LOCAL = [
    'NR_TURNO', 'SG_UF', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO',
    'DS_TIPO_SECAO_AGREGADA', 'NR_SECAO_PRINCIPAL', 'NR_LOCAL_VOTACAO', 'NM_LOCAL_VOTACAO',
    'DS_ENDERECO', 'NM_BAIRRO', 'NR_LATITUDE', 'NR_LONGITUDE',
    'DS_SITU_SECAO_ACESSIBILIDADE', 'QT_ELEITOR_SECAO',
]
COLS_PCD = ['SG_UF', 'CD_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'DS_TIPO_DEFICIENCIA']

TIPOS_PCD = {
    'DEFICIÊNCIA DE LOCOMOÇÃO': 'locomocao',
    'DEFICIÊNCIA VISUAL': 'visual',
    'DEFICIÊNCIA AUDITIVA': 'auditiva',
    'DIFICULDADE PARA O EXERCÍCIO DO VOTO': 'dificuldade_voto',
}
COLS_TIPOS = ['locomocao', 'visual', 'auditiva', 'dificuldade_voto', 'outros']


def arquivos_por_uf(pasta, prefixo):
    """Arquivos de cada UF, ignorando o consolidado BRASIL e o exterior (ZZ)."""
    caminhos = sorted(glob.glob(os.path.join(pasta, f'{prefixo}_*.csv')))
    return [c for c in caminhos if not c.endswith(('_BRASIL.csv', '_ZZ.csv'))]


def ler_csv_tse(caminho, colunas):
    return pd.read_csv(caminho, sep=';', encoding='latin-1', usecols=colunas, dtype=str)


def coordenada(valor):
    """O TSE usa vírgula decimal e '-1' para coordenada ausente."""
    if pd.isna(valor):
        return None
    v = float(str(valor).replace(',', '.'))
    return None if v == -1 else v


def montar_secoes(bruto):
    """Normaliza a tabela de seções do TSE (já filtrada ou não por turno)."""
    df = bruto[bruto['NR_TURNO'] == TURNO].copy()
    secoes = pd.DataFrame({
        'uf': df['SG_UF'],
        'cd_municipio': df['CD_MUNICIPIO'],
        'nm_municipio': df['NM_MUNICIPIO'],
        'nr_zona': df['NR_ZONA'].astype(int),
        'nr_secao': df['NR_SECAO'].astype(int),
        'agregada': df['DS_TIPO_SECAO_AGREGADA'].eq('Agregada'),
        'nr_secao_principal': pd.to_numeric(df['NR_SECAO_PRINCIPAL'], errors='coerce'),
        # o número do local se repete entre municípios de uma mesma zona
        'local_id': df['CD_MUNICIPIO'] + '-' + df['NR_ZONA'] + '-' + df['NR_LOCAL_VOTACAO'],
        'nm_local': df['NM_LOCAL_VOTACAO'],
        'endereco': df['DS_ENDERECO'],
        'bairro': df['NM_BAIRRO'],
        'lat': df['NR_LATITUDE'].map(coordenada),
        'lon': df['NR_LONGITUDE'].map(coordenada),
        'consta_acessivel': df['DS_SITU_SECAO_ACESSIBILIDADE'].eq('Com acessibilidade'),
        'qt_eleitores': df['QT_ELEITOR_SECAO'].astype(int),
    })
    secoes.loc[~secoes['agregada'], 'nr_secao_principal'] = pd.NA
    secoes['nr_secao_principal'] = secoes['nr_secao_principal'].astype('Int64')
    return secoes.drop_duplicates(['uf', 'nr_zona', 'nr_secao']).reset_index(drop=True)


def contar_pcd(bruto_pcd):
    """Conta eleitores com deficiência por seção e tipo (uma linha do TSE = um eleitor)."""
    df = pd.DataFrame({
        'uf': bruto_pcd['SG_UF'],
        'nr_zona': bruto_pcd['NR_ZONA'].astype(int),
        'nr_secao': bruto_pcd['NR_SECAO'].astype(int),
        'tipo': bruto_pcd['DS_TIPO_DEFICIENCIA'].map(TIPOS_PCD).fillna('outros'),
    })
    contagem = df.groupby(['uf', 'nr_zona', 'nr_secao', 'tipo']).size().unstack(fill_value=0)
    contagem = contagem.reindex(columns=COLS_TIPOS, fill_value=0)
    contagem['total'] = contagem[COLS_TIPOS].sum(axis=1)
    return contagem.add_prefix('pcd_').reset_index()


def montar_locais(secoes, pcd):
    """Agrega por local de votação. Contagens de deficiência só existem neste nível."""
    s = secoes.merge(pcd, on=['uf', 'nr_zona', 'nr_secao'], how='left')
    cols_pcd = [f'pcd_{c}' for c in COLS_TIPOS + ['total']]
    s[cols_pcd] = s[cols_pcd].fillna(0).astype(int)
    s['pcd_sem_acess'] = s['pcd_total'].where(~s['consta_acessivel'], 0)

    g = s.groupby('local_id')
    locais = g.agg(
        uf=('uf', 'first'), cd_municipio=('cd_municipio', 'first'), nm_municipio=('nm_municipio', 'first'),
        nr_zona=('nr_zona', 'first'), nm_local=('nm_local', 'first'), endereco=('endereco', 'first'),
        bairro=('bairro', 'first'), lat=('lat', 'first'), lon=('lon', 'first'),
        qt_secoes=('nr_secao', 'size'), qt_secoes_acessiveis=('consta_acessivel', 'sum'),
        qt_eleitores=('qt_eleitores', 'sum'), pcd_sem_acess=('pcd_sem_acess', 'sum'),
        **{c: (c, 'sum') for c in cols_pcd},
    ).reset_index()
    locais['status'] = 'parcial'
    locais.loc[locais['qt_secoes_acessiveis'] == locais['qt_secoes'], 'status'] = 'todas'
    locais.loc[locais['qt_secoes_acessiveis'] == 0, 'status'] = 'nenhuma'
    return locais


def montar_municipios(locais):
    """Indicadores por município, base do agrupamento (k-means)."""
    g = locais.groupby('cd_municipio')
    m = g.agg(
        uf=('uf', 'first'), nm_municipio=('nm_municipio', 'first'),
        # mediana: algumas coordenadas do TSE estão erradas (local em outro estado)
        lat=('lat', 'median'), lon=('lon', 'median'),
        qt_locais=('local_id', 'size'),
        qt_locais_sem_acess=('status', lambda s: int((s == 'nenhuma').sum())),
        qt_secoes=('qt_secoes', 'sum'), qt_secoes_acessiveis=('qt_secoes_acessiveis', 'sum'),
        qt_eleitores=('qt_eleitores', 'sum'),
        pcd_total=('pcd_total', 'sum'), pcd_sem_acess=('pcd_sem_acess', 'sum'),
    ).reset_index()
    m['pct_secoes_acessiveis'] = 100 * m['qt_secoes_acessiveis'] / m['qt_secoes']
    m['pct_locais_sem_acess'] = 100 * m['qt_locais_sem_acess'] / m['qt_locais']
    # sem eleitor com deficiência cadastrado, ninguém está "exposto": indicador = 0
    m['pct_pcd_sem_acess'] = (100 * m['pcd_sem_acess'] / m['pcd_total'].where(m['pcd_total'] > 0)).fillna(0)
    m['pcd_por_mil'] = 1000 * m['pcd_total'] / m['qt_eleitores']
    return m.round({'lat': 5, 'lon': 5, 'pct_secoes_acessiveis': 2, 'pct_locais_sem_acess': 2,
                    'pct_pcd_sem_acess': 2, 'pcd_por_mil': 3})


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('pasta_locais')
    ap.add_argument('pasta_deficiencia')
    ap.add_argument('--saida', default='dataset')
    a = ap.parse_args()

    secoes = pd.concat([montar_secoes(ler_csv_tse(c, COLS_LOCAL))
                        for c in arquivos_por_uf(a.pasta_locais, 'eleitorado_local_votacao_2026')])
    pcd = pd.concat([contar_pcd(ler_csv_tse(c, COLS_PCD))
                     for c in arquivos_por_uf(a.pasta_deficiencia, 'perfil_eleitor_deficiencia_2026')])
    pcd = pcd.groupby(['uf', 'nr_zona', 'nr_secao'], as_index=False).sum()
    locais = montar_locais(secoes, pcd)
    municipios = montar_municipios(locais)

    os.makedirs(a.saida, exist_ok=True)
    cols_secoes = ['uf', 'cd_municipio', 'nr_zona', 'nr_secao', 'agregada', 'nr_secao_principal',
                   'local_id', 'consta_acessivel', 'qt_eleitores']
    secoes[cols_secoes].to_csv(os.path.join(a.saida, 'secoes.csv'), index=False)
    locais.to_csv(os.path.join(a.saida, 'locais.csv'), index=False)
    municipios.to_csv(os.path.join(a.saida, 'municipios.csv'), index=False)
    print(f'{len(municipios)} municípios, {len(locais)} locais, {len(secoes)} seções, '
          f'{int(locais["pcd_total"].sum())} eleitores com deficiência')


if __name__ == '__main__':
    main()
