# Minha Seção é Acessível?

Este projeto analisa a acessibilidade das seções eleitorais do Brasil com os dados abertos do TSE das eleições de
2026. Um algoritmo de aprendizado de máquina (k-means) separa os municípios em quatro grupos, e um site mostra os
resultados.

Projeto Integrador em Computação IV (PJI410), Univesp, 2026.

Autor: Erikson Souza da Silva ([@eriksonssilva](https://github.com/eriksonssilva)).

O site tem quatro partes:

- A consulta por seção mostra se uma seção consta como acessível nos dados do TSE, a partir da UF, da zona e da seção.
- A página do município mostra os indicadores, a comparação com o grupo e com o Brasil, um mapa e a lista de locais de votação.
- O mapa do Brasil mostra os 5.571 municípios com a cor do grupo de cada um.
- A pasta `dataset/` tem o conjunto de dados tratado em CSV, com licença CC BY 4.0. O arquivo `dataset/README.md` descreve cada coluna.

A Justiça Eleitoral informa a situação de acessibilidade de cada seção. Essa informação não foi verificada em campo.

## Como rodar

```bash
uv sync --all-groups
uv run uvicorn msa.app:app --reload     # http://localhost:8000
uv run pytest
```

## Como gerar o dataset de novo

Baixe do [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/) os arquivos "Eleitorado por local de
votação 2026" e "Perfil do eleitorado com deficiência 2026", descompacte e rode:

```bash
uv run python -m msa.build <pasta_locais> <pasta_deficiencia>   # indicadores por seção, local e município
uv run python -m msa.cluster                                    # k-means, silhueta e grupos
```

## Estrutura

| caminho | o que faz |
|---|---|
| `src/msa/build.py` | lê os CSVs do TSE das 27 UFs e calcula os indicadores |
| `src/msa/cluster.py` | padroniza os indicadores, avalia de 2 a 8 grupos, roda o k-means e dá nome aos grupos |
| `src/msa/db.py` | carrega o dataset no SQLite e faz as consultas |
| `src/msa/app.py` | site e API, com FastAPI, Jinja2, Leaflet e Chart.js |
| `tests/` | testes do tratamento dos dados, do agrupamento e da API |
