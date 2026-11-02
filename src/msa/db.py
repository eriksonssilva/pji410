"""Carrega o dataset (CSVs) em SQLite e oferece as consultas usadas pelo site."""
import csv
import json
import os
import sqlite3

TABELAS = {
    'secoes': ['uf', 'cd_municipio', 'nr_zona', 'nr_secao', 'agregada', 'nr_secao_principal',
               'local_id', 'consta_acessivel', 'qt_eleitores'],
    'locais': None,      # todas as colunas do CSV
    'municipios': None,
    'grupos': None,
    'kmeans_avaliacao': None,
}
INDICES = [
    'CREATE UNIQUE INDEX ix_secao ON secoes (uf, nr_zona, nr_secao)',
    'CREATE INDEX ix_local_mun ON locais (cd_municipio)',
    'CREATE UNIQUE INDEX ix_mun ON municipios (cd_municipio)',
    'CREATE INDEX ix_mun_uf ON municipios (uf, nm_municipio)',
]


def _valor(v):
    """Converte o texto do CSV para int/float/bool quando possível."""
    if v == '':
        return None
    if v in ('True', 'False'):
        return v == 'True'
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def carregar(pasta_dataset, caminho_db):
    """(Re)cria o banco a partir dos CSVs. Leva poucos segundos para o Brasil inteiro."""
    if os.path.exists(caminho_db):
        os.remove(caminho_db)
    os.makedirs(os.path.dirname(caminho_db) or '.', exist_ok=True)
    con = sqlite3.connect(caminho_db)
    for tabela, colunas in TABELAS.items():
        with open(os.path.join(pasta_dataset, f'{tabela}.csv'), encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            colunas = colunas or leitor.fieldnames
            con.execute(f'CREATE TABLE {tabela} ({", ".join(colunas)})')
            sql = f'INSERT INTO {tabela} VALUES ({", ".join("?" * len(colunas))})'
            texto = {'cd_municipio', 'local_id', 'uf', 'nm_municipio', 'nm_local', 'endereco', 'bairro', 'nome', 'status'}
            con.executemany(sql, ([linha[c] if c in texto else _valor(linha[c]) for c in colunas]
                                  for linha in leitor))
    for sql in INDICES:
        con.execute(sql)
    with open(os.path.join(pasta_dataset, 'kmeans_resumo.json'), encoding='utf-8') as f:
        con.execute('CREATE TABLE meta (chave, valor)')
        con.execute('INSERT INTO meta VALUES (?, ?)', ('kmeans', f.read()))
    con.commit()
    con.close()


class Banco:
    def __init__(self, caminho_db):
        self.con = sqlite3.connect(caminho_db, check_same_thread=False)
        self.con.row_factory = sqlite3.Row

    def _um(self, sql, *args):
        linha = self.con.execute(sql, args).fetchone()
        return dict(linha) if linha else None

    def _todos(self, sql, *args):
        return [dict(r) for r in self.con.execute(sql, args).fetchall()]

    def ufs(self):
        return [r['uf'] for r in self._todos('SELECT DISTINCT uf FROM municipios ORDER BY uf')]

    def municipios_da_uf(self, uf):
        return self._todos('SELECT cd_municipio, nm_municipio FROM municipios WHERE uf = ? '
                           'ORDER BY nm_municipio', uf.upper())

    def municipio(self, cd):
        return self._um('SELECT * FROM municipios WHERE cd_municipio = ?', cd)

    def locais_do_municipio(self, cd):
        return self._todos('SELECT * FROM locais WHERE cd_municipio = ? ORDER BY nm_local', cd)

    def secao(self, uf, zona, secao):
        s = self._um('SELECT * FROM secoes WHERE uf = ? AND nr_zona = ? AND nr_secao = ?',
                     uf.upper(), zona, secao)
        if s is None:
            return None
        s['agregada'], s['consta_acessivel'] = bool(s['agregada']), bool(s['consta_acessivel'])
        s['local'] = self._um('SELECT * FROM locais WHERE local_id = ?', s['local_id'])
        s['municipio'] = self.municipio(s['cd_municipio'])
        return s

    def grupos(self):
        return self._todos('SELECT * FROM grupos ORDER BY grupo')

    def grupo(self, n):
        return self._um('SELECT * FROM grupos WHERE grupo = ?', n)

    def avaliacao_k(self):
        return self._todos('SELECT * FROM kmeans_avaliacao ORDER BY k')

    def kmeans(self):
        return json.loads(self._um("SELECT valor FROM meta WHERE chave = 'kmeans'")['valor'])

    def brasil(self):
        b = self._um(
            'SELECT COUNT(*) AS municipios, SUM(qt_locais) AS locais, SUM(qt_secoes) AS secoes, '
            'SUM(qt_secoes_acessiveis) AS secoes_acessiveis, SUM(qt_eleitores) AS eleitores, '
            'SUM(pcd_total) AS pcd_total, SUM(pcd_sem_acess) AS pcd_sem_acess, '
            'SUM(qt_locais_sem_acess) AS locais_sem_acess FROM municipios')
        b['pct_secoes_acessiveis'] = round(100 * b['secoes_acessiveis'] / b['secoes'], 1)
        b['pct_pcd_sem_acess'] = round(100 * b['pcd_sem_acess'] / b['pcd_total'], 1)
        b['pct_locais_sem_acess'] = round(100 * b['locais_sem_acess'] / b['locais'], 1)
        b['pcd_por_mil'] = round(1000 * b['pcd_total'] / b['eleitores'], 1)
        return b

    def pontos_mapa(self):
        return self._todos('SELECT cd_municipio, nm_municipio, uf, lat, lon, grupo, '
                           'pct_secoes_acessiveis, pcd_sem_acess FROM municipios '
                           'WHERE lat IS NOT NULL')
