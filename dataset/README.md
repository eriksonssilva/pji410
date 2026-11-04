# Dataset: acessibilidade das seções eleitorais no Brasil, eleições de 2026

Os arquivos vêm de dois conjuntos de dados abertos do Tribunal Superior Eleitoral (dadosabertos.tse.jus.br):
"Eleitorado por local de votação 2026" e "Perfil do eleitorado com deficiência 2026", 1º turno. Os eleitores que
votam no exterior ficaram de fora. Licença CC BY 4.0. Cite o TSE como fonte original.

## Limitações

A Justiça Eleitoral informa a situação de acessibilidade de cada seção, e essa informação não foi verificada em campo. Assim,
`consta_acessivel = True` quer dizer que a seção consta como acessível nos dados do TSE. O cadastro de deficiência
inclui só os eleitores que informaram essa condição ao TSE.

## Privacidade

Nenhum arquivo traz informação individual. Os eleitores com deficiência aparecem só em totais por local de votação e
por município, nunca por seção.

Os comandos `python -m msa.build` e `python -m msa.cluster` geram todos os arquivos.

## secoes.csv, uma linha por seção

| coluna | descrição |
|---|---|
| uf | sigla da UF |
| cd_municipio | código do município no TSE |
| nr_zona, nr_secao | zona e seção eleitoral |
| agregada | indica se o TSE juntou a seção a outra |
| nr_secao_principal | seção à qual o TSE juntou esta, vazio quando a seção não é agregada |
| local_id | identificador do local de votação, no formato `cd_municipio-zona-local` |
| consta_acessivel | indica se a seção consta como acessível nos dados do TSE |
| qt_eleitores | eleitores aptos na seção |

## locais.csv, uma linha por local de votação

| coluna | descrição |
|---|---|
| local_id, uf, cd_municipio, nm_municipio, nr_zona | identificação |
| nm_local, endereco, bairro | nome e endereço informados pelo TSE |
| lat, lon | coordenadas, vazias quando o TSE não as informa |
| qt_secoes, qt_secoes_acessiveis | seções do local e quantas constam como acessíveis |
| status | `todas`, `parcial` ou `nenhuma`, conforme as seções que constam como acessíveis |
| qt_eleitores | eleitores aptos no local |
| pcd_total | eleitores com deficiência cadastrada no local |
| pcd_locomocao, pcd_visual, pcd_auditiva, pcd_dificuldade_voto, pcd_outros | eleitores com deficiência, por tipo |
| pcd_sem_acess | eleitores com deficiência em seções do local que não constam como acessíveis |

## municipios.csv, uma linha por município

| coluna | descrição |
|---|---|
| cd_municipio, uf, nm_municipio | identificação |
| lat, lon | mediana das coordenadas dos locais de votação |
| qt_locais, qt_locais_sem_acess | locais e locais sem nenhuma seção acessível |
| qt_secoes, qt_secoes_acessiveis, qt_eleitores | totais |
| pcd_total, pcd_sem_acess | eleitores com deficiência, no total e em seções sem acessibilidade |
| pct_secoes_acessiveis | percentual de seções que constam como acessíveis |
| pct_locais_sem_acess | percentual de locais sem nenhuma seção acessível |
| pct_pcd_sem_acess | percentual dos eleitores com deficiência que votam em seções sem acessibilidade |
| pcd_por_mil | eleitores com deficiência a cada mil eleitores |
| grupo | grupo atribuído pelo k-means, de 1 a 4, descrito em grupos.csv |

## Outros arquivos

`grupos.csv` resume cada grupo com medianas e totais. `kmeans_avaliacao.csv` traz a silhueta e a inércia de 2 a 8
grupos. `kmeans_resumo.json` guarda os parâmetros do modelo: indicadores, número de grupos e semente.
