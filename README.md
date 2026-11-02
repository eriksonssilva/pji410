# Minha Seção é Acessível?

Análise em escala da acessibilidade das seções eleitorais brasileiras, a partir dos dados abertos do TSE (eleições
2026), com agrupamento dos municípios por aprendizado de máquina (k-means) e um site para visualizar os resultados.

Projeto Integrador em Computação IV (PJI410), Univesp, 2026.

- **Consulta por seção:** informe UF, zona e seção e veja se ela *consta como acessível* nos dados do TSE.
- **Painel do município:** indicadores, comparação com o grupo e com o Brasil, mapa e lista de locais de votação.
- **Mapa do Brasil:** os 5.571 municípios coloridos pelo perfil encontrado pelo k-means.
- **Conjunto de dados aberto:** `dataset/` (CSV, CC BY 4.0), com dicionário de dados em `dataset/README.md`.

> A acessibilidade é declarada pela Justiça Eleitoral e não foi verificada em campo.

## Como rodar

```bash
uv sync --all-groups
uv run uvicorn msa.app:app --reload     # http://localhost:8000
uv run pytest
```

## Como regenerar o dataset

Baixe do [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/) os arquivos "Eleitorado por local de
votação – 2026" e "Perfil do eleitorado com deficiência – 2026", descompacte e rode:

```bash
uv run python -m msa.build <pasta_locais> <pasta_deficiencia>   # indicadores por seção, local e município
uv run python -m msa.cluster                                    # k-means, silhueta e perfis
```

## Estrutura

| caminho | o que faz |
|---|---|
| `src/msa/build.py` | ingestão dos CSVs do TSE (27 UFs) e cálculo dos indicadores |
| `src/msa/cluster.py` | padronização, escolha de k (cotovelo e silhueta), k-means e nomeação dos grupos |
| `src/msa/db.py` | carrega o dataset em SQLite e faz as consultas |
| `src/msa/app.py` | site e API (FastAPI + Jinja2 + Leaflet + Chart.js) |
| `tests/` | testes do tratamento, do agrupamento e da API |
