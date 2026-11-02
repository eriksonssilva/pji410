# Dataset: acessibilidade das seções eleitorais no Brasil (2026)

Dados derivados dos arquivos abertos do Tribunal Superior Eleitoral (dadosabertos.tse.jus.br):
"Eleitorado por local de votação – 2026" e "Perfil do eleitorado com deficiência – 2026", 1º turno.
Eleitores no exterior não estão incluídos. Licença: CC BY 4.0 (cite o TSE como fonte original).

**Limitações.** A acessibilidade é declarada pela Justiça Eleitoral e não foi verificada em campo:
`consta_acessivel = True` significa que a seção *consta* como acessível nos dados do TSE. O cadastro de
deficiência inclui apenas os eleitores que informaram essa condição ao TSE.

**Privacidade.** Nenhum arquivo contém informação individual. As contagens de eleitores com deficiência
estão agregadas por local de votação e por município, nunca por seção.

Gerado por `python -m msa.build` e `python -m msa.cluster`.

## secoes.csv (uma linha por seção)
| coluna | descrição |
|---|---|
| uf | sigla da UF |
| cd_municipio | código do município no TSE |
| nr_zona, nr_secao | zona e seção eleitoral |
| agregada | a seção foi agregada a outra |
| nr_secao_principal | seção à qual foi agregada (vazio se não for agregada) |
| local_id | identificador do local de votação (`cd_municipio-zona-local`) |
| consta_acessivel | a seção consta como acessível nos dados do TSE |
| qt_eleitores | eleitores aptos na seção |

## locais.csv (uma linha por local de votação)
| coluna | descrição |
|---|---|
| local_id, uf, cd_municipio, nm_municipio, nr_zona | identificação |
| nm_local, endereco, bairro | nome e endereço informados pelo TSE |
| lat, lon | coordenadas (vazio quando o TSE não informa) |
| qt_secoes, qt_secoes_acessiveis | seções do local e quantas constam como acessíveis |
| status | `todas`, `parcial` ou `nenhuma` seção acessível |
| qt_eleitores | eleitores aptos no local |
| pcd_total | eleitores com deficiência cadastrada no local |
| pcd_locomocao, pcd_visual, pcd_auditiva, pcd_dificuldade_voto, pcd_outros | por tipo de deficiência |
| pcd_sem_acess | eleitores com deficiência em seções do local que não constam como acessíveis |

## municipios.csv (uma linha por município)
| coluna | descrição |
|---|---|
| cd_municipio, uf, nm_municipio | identificação |
| lat, lon | centro (média) dos locais de votação |
| qt_locais, qt_locais_sem_acess | locais e locais sem nenhuma seção acessível |
| qt_secoes, qt_secoes_acessiveis, qt_eleitores | totais |
| pcd_total, pcd_sem_acess | eleitores com deficiência (total e em seções sem acessibilidade) |
| pct_secoes_acessiveis | % de seções que constam como acessíveis |
| pct_locais_sem_acess | % de locais sem nenhuma seção acessível |
| pct_pcd_sem_acess | % dos eleitores com deficiência em seções sem acessibilidade |
| pcd_por_mil | eleitores com deficiência a cada mil eleitores |
| grupo | perfil atribuído pelo k-means (1 a 4, ver grupos.csv) |

## grupos.csv, kmeans_avaliacao.csv, kmeans_resumo.json
Resumo de cada grupo (medianas e totais), silhueta e inércia para k = 2 a 8, e parâmetros do modelo
(indicadores, k escolhido, semente).
