# Guia de Uso — INPE BDC MCP Server

Guia completo com prompts otimizados para todas as 68 ferramentas do servidor MCP. Cada seção contém a descrição da ferramenta, parâmetros disponíveis e exemplos de prompts prontos para uso com agentes de IA (Claude, etc.).

---

## Sumário

0. [Galeria de Resultados](#galeria-de-resultados)
1. [Catálogo](#1-catálogo)
2. [Coleções](#2-coleções)
3. [Busca de Itens](#3-busca-de-itens)
4. [Itens e Assets](#4-itens-e-assets)
5. [Data Cubes](#5-data-cubes)
6. [Satélites](#6-satélites)
7. [Biomas e Regiões](#7-biomas-e-regiões)
8. [Análise e Geração de Código](#8-análise-e-geração-de-código)
9. [Índices Espectrais](#9-índices-espectrais)
10. [Pré-processamento](#10-pré-processamento)
11. [Projeção CRS e Geometrias](#11-projeção-crs-e-geometrias)
12. [Séries Temporais](#12-séries-temporais)
13. [Classificação LULC](#13-classificação-lulc)
14. [Detecção de Mudanças](#14-detecção-de-mudanças)
15. [Administração](#15-administração)
16. [Workflows Combinados](#16-workflows-combinados)

---

## Galeria de Resultados

Os mapas abaixo ilustram resultados reais obtidos com os prompts deste guia, demonstrando as principais capacidades do servidor MCP.

### Biomas Brasileiros — `get_biome_bbox()`

![Mapa dos Biomas Brasileiros](docs/images/map_biomes.png)

### Busca Espacial — `search_items()`

![Busca LANDSAT-16D-1 no Cerrado](docs/images/map_search_items.png)

### Busca por Ponto — `search_by_point()`

![Busca por ponto em Goiania](docs/images/map_search_by_point.png)

### Tiles Mais Recentes — `search_latest_items()`

![CBERS4-WFI-16D-2 tiles recentes no Cerrado](docs/images/map_latest_cbers.png)

### Cobertura Nacional — `discover_collections_for_topic()`

![Cobertura de colecoes no Brasil](docs/images/map_collections_overview.png)

### Deteccao de Cicatrizes de Fogo — `plan_fire_scar_detection()`

![Deteccao de fogo na Chapada dos Veadeiros](docs/images/map_fire_scar.png)

### Filtragem de Series Temporais — `get_filtering_guide()`

![Filtragem Savitzky-Golay e Whittaker](docs/images/sits_filtering.png)

### Metricas Fenologicas — `plan_phenology_extraction()`

![Metricas fenologicas NDVI Cerrado](docs/images/sits_phenology.png)

### Classificacao LULC — `plan_classification_workflow()`

![Classificacao LULC Cerrado com Random Forest](docs/images/sits_classification.png)

### Workflow SITS Completo — `generate_sits_cube_code()`

![Workflow SITS completo com 4 etapas](docs/images/sits_cube_workflow.png)

### Catalogo de Mosaicos — `list_collections(category="mosaic")`

![7 colecoes de mosaicos BDC](docs/images/map_mosaics_overview.png)

### Mosaico Landsat Amazonia — `mosaic-landsat-amazon-3m-1`

![Mosaico Landsat da Amazonia com 132 tiles](docs/images/map_mosaic_amazon_landsat.png)

### Mosaico Sentinel-2 Amazonia — `mosaic-s2-amazon-3m-1`

![Mosaico Sentinel-2 da Amazonia com 916 tiles](docs/images/map_mosaic_amazon_s2.png)

### Mosaico Landsat Brasil — `mosaic-landsat-brazil-6m-1`

![Mosaico Landsat do Brasil inteiro](docs/images/map_mosaic_brazil.png)

### Mosaicos Regionais — Sao Paulo, Yanomami e Paraiba

![Mosaicos regionais do BDC](docs/images/map_mosaics_regional.png)

### Compostos Landsat — True Color, False Color, Agriculture

![Compostos Landsat True Color, False Color e Agriculture no Cerrado](docs/images/sat_landsat_composites.png)

### Compostos CBERS-4 — True Color, False Color

![Compostos CBERS-4 WFI True Color e False Color no Cerrado](docs/images/sat_cbers4_composites.png)

### Compostos Sentinel-2 — True Color, False Color, Agriculture

![Compostos Sentinel-2 True Color, False Color e Agriculture no Cerrado](docs/images/sat_sentinel2_composites.png)

---

## 1. Catálogo

### `catalog_info()`

Retorna versão STAC, total de coleções, endpoints e status de autenticação.

**Prompts:**

```
Mostre as informações gerais do catálogo STAC do INPE/BDC.

Qual a versão da STAC API do Brazil Data Cube? Quantas coleções estão disponíveis?

Verifique se minha API key está configurada corretamente no BDC.
```

---

### `list_conformance_classes()`

Lista as conformance classes OGC implementadas.

**Prompts:**

```
Quais conformance classes OGC a STAC API do BDC implementa?

A API do BDC suporta CQL2 para filtros avançados? Verifique as conformance classes.

Liste os padrões OGC suportados pela API de dados do INPE.
```

---

### `get_api_capabilities()`

Resume capacidades da API: CQL2, fields, sortby, autenticação, paginação.

**Prompts:**

```
Quais são as capacidades da STAC API do BDC? Suporta ordenação, paginação e filtros?

Posso usar sortby e fields na API do BDC? Quais capacidades ela oferece?

Resuma as funcionalidades avançadas da STAC API do INPE.
```

---

## 2. Coleções

### `list_collections(category, satellite, biome, data_type, keyword, limit)`

Lista coleções com filtros combinados.

> **Resultado visual (mosaicos):**
>
> ![Catalogo de mosaicos BDC](docs/images/map_mosaics_overview.png)

| Parâmetro | Valores |
|---|---|
| `category` | `raw_image`, `data_cube`, `mosaic`, `land_cover`, `modis`, `ocean`, `weather` |
| `satellite` | `CBERS-4`, `CBERS-4A`, `Amazonia-1`, `Sentinel-2`, `Landsat`, `MODIS`, `GOES-19` |
| `biome` | `cerrado`, `amazonia`, `mata_atlantica`, `pantanal`, `caatinga`, `pampa` |
| `data_type` | `SR` (surface reflectance), `DN` (digital numbers), `LCC` (land cover) |
| `keyword` | Texto livre |

**Prompts:**

```
Liste todos os data cubes disponíveis no BDC.

Quais coleções do satélite Sentinel-2 existem no BDC?

Liste as coleções de imagens brutas do CBERS-4A.

Quais coleções de classificação de uso do solo (LCC) estão disponíveis?

Busque coleções que mencionem "mosaico" ou "mosaic" no título.

Liste os mosaicos disponíveis para a Amazônia.

Quais coleções de dados meteorológicos existem no BDC?
```

---

### `get_collection_detail(collection_id)`

Metadados completos: bandas, extensão temporal/espacial, extensões STAC.

**Prompts:**

```
Mostre os detalhes completos da coleção LANDSAT-16D-1.

Qual a extensão temporal e espacial do data cube CBERS4-WFI-16D-2?

Detalhe a coleção S2_L2A-1 — resolução, bandas, cobertura e período disponível.

Quais metadados estão disponíveis para a coleção mosaic-landsat-amazon-3m-1?
```

---

### `get_collection_bands(collection_id)`

Informações de bandas: comprimento de onda, resolução, tipo de dado.

**Prompts:**

```
Quais bandas espectrais a coleção LANDSAT-16D-1 possui?

Liste as bandas do Sentinel-2 L2A (S2_L2A-1) com comprimento de onda e resolução.

Quais são as bandas disponíveis no data cube CBERS4-WFI-16D-2?

O LANDSAT-16D-1 tem NDVI pré-calculado? Quais bandas ele oferece?
```

---

### `compare_collections(collection_ids)`

Compara múltiplas coleções: bandas em comum, resolução, cobertura.

**Prompts:**

```
Compare as coleções LANDSAT-16D-1 e CBERS4-WFI-16D-2 para monitoramento de vegetação.

Qual a diferença entre S2_L2A-1 e LANDSAT-16D-1 em termos de bandas e resolução?

Compare os data cubes CBERS-WFI-8D-1 e CBERS4-WFI-16D-2 — qual tem melhor resolução temporal?

Compare LANDSAT-16D-1, CBERS4-WFI-16D-2 e S2_L2A-1 para análise multitemporal.
```

---

## 3. Busca de Itens

### `search_items(collections, bbox, datetime_range, cloud_cover_max, limit, sortby)`

Busca avançada cross-collection com filtros múltiplos.

> **Resultado visual:**
>
> ![Busca LANDSAT-16D-1 no Cerrado](docs/images/map_search_items.png)

**Prompts:**

```
Busque imagens Sentinel-2 do Cerrado em 2023 com menos de 10% de nuvem.

Encontre itens do LANDSAT-16D-1 para a bbox [-50, -15, -49, -14] entre 2020 e 2023.

Busque as 20 imagens mais recentes do CBERS4-WFI-16D-2 para Goiás.

Busque imagens Landsat e CBERS simultâneas para o Mato Grosso no segundo semestre de 2022.

Encontre composições do LANDSAT-16D-1 para a Amazônia entre junho e agosto de 2021.
```

---

### `search_by_point(lon, lat, collections, datetime_range, cloud_cover_max)`

Busca itens que contêm uma coordenada específica.

> **Resultado visual:**
>
> ![Busca por ponto em Goiania](docs/images/map_search_by_point.png)

**Prompts:**

```
Busque todas as imagens disponíveis no ponto -49.5, -15.7 (Goiânia) em 2023.

Encontre imagens Sentinel-2 que cobrem a coordenada -60.0, -3.1 (Manaus) com menos de 20% de nuvem.

Quais composições LANDSAT-16D-1 cobrem o ponto -46.63, -23.55 (São Paulo) em 2022?

Busque dados CBERS-4A que cobrem -55.0, -12.5 entre 2020 e 2023.
```

---

### `search_by_polygon(geojson_geometry, collections, datetime_range, cloud_cover_max)`

Busca itens que intersectam uma geometria GeoJSON.

**Prompts:**

```
Busque imagens Landsat que intersectam este polígono GeoJSON: {"type": "Polygon", "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]]}

Encontre composições do LANDSAT-16D-1 em 2022 que cobrem esta área de estudo: [insira GeoJSON]

Busque imagens Sentinel-2 com menos de 15% de nuvem para esta geometria de fazenda: [insira GeoJSON]
```

---

### `search_by_tile(collection_id, tile_id, datetime_range)`

Busca por tile BDC específico (formato 6 dígitos).

**Prompts:**

```
Busque todas as composições do tile 007004 no CBERS4-WFI-16D-2 em 2022.

Encontre os itens do tile 021019 na coleção LANDSAT-16D-1 entre janeiro e junho de 2023.

Liste todos os itens disponíveis para o tile BDC 013011 do LANDSAT-16D-1.
```

---

### `search_latest_items(collection_id, bbox, n, cloud_cover_max)`

Os N itens mais recentes de uma coleção.

> **Resultado visual:**
>
> ![CBERS4-WFI-16D-2 tiles recentes no Cerrado](docs/images/map_latest_cbers.png)

**Prompts:**

```
Mostre os 5 itens mais recentes do LANDSAT-16D-1 para o Cerrado.

Quais são as 10 composições mais recentes do CBERS4-WFI-16D-2 para Goiás?

Encontre a imagem Sentinel-2 mais recente para a Amazônia com menos de 10% de nuvem.

Últimas 3 composições do LANDSAT-16D-1 para o Mato Grosso do Sul.
```

---

### `search_cloud_free(collections, bbox, datetime_range, max_cloud)`

Imagens com menor cobertura de nuvens, ordenadas da mais limpa.

**Prompts:**

```
Encontre as imagens Sentinel-2 mais limpas (menos nuvens) para o Pantanal em 2023.

Busque composições do LANDSAT-16D-1 com máximo de 5% de nuvem para a Amazônia no período seco de 2022 (junho-outubro).

Quais imagens CBERS-4A têm menor cobertura de nuvens no Cerrado goiano em 2023?

Encontre as 20 imagens Landsat mais limpas para Mato Grosso entre 2020 e 2023.
```

---

### `get_all_pages(collections, bbox, datetime_range, cloud_cover_max, max_items)`

Itera todas as páginas de resultados (até 5000 itens).

**Prompts:**

```
Busque TODOS os itens do LANDSAT-16D-1 para o Cerrado de 2018 a 2023 (todas as páginas).

Quantos itens do CBERS4-WFI-16D-2 existem para a Amazônia? Busque até 5000 itens.

Colete o catálogo completo de composições Landsat para Goiás entre 2015 e 2023.
```

---

## 4. Itens e Assets

### `get_item(collection_id, item_id)`

Detalhes completos de um item: geometria, propriedades, assets.

**Prompts:**

```
Mostre os detalhes completos do item LANDSAT-16D-1-item-001.

Quais propriedades tem o item CBERS4-WFI-16D-2_007004_2023-06-15?

Detalhe o item [ID do item] da coleção S2_L2A-1 — cobertura de nuvem, geometria, data.
```

---

### `list_item_assets(collection_id, item_id)`

Lista assets com URLs, tipo MIME, bandas e se é COG.

**Prompts:**

```
Liste todos os assets disponíveis para o item [item_id] do LANDSAT-16D-1.

Quais bandas posso baixar do item [item_id] da coleção CBERS4-WFI-16D-2?

O item [item_id] do S2_L2A-1 tem dados em formato COG? Liste os assets.
```

---

### `get_asset_download_info(collection_id, item_id, asset_key)`

Gera snippets de download (curl, wget, Python, R).

**Prompts:**

```
Gere os comandos para baixar a banda NDVI do item [item_id] do LANDSAT-16D-1.

Como faço para baixar o asset RED do item [item_id] via Python e via curl?

Me dê o código R para acessar a banda NIR do item [item_id] do CBERS4-WFI-16D-2.

Gere snippet de download para o thumbnail do item [item_id].
```

---

### `get_thumbnail_url(collection_id, item_id)`

URL do thumbnail para visualização rápida.

**Prompts:**

```
Qual a URL do thumbnail do item [item_id] do LANDSAT-16D-1?

Mostre o link de preview do item [item_id] da coleção S2_L2A-1.
```

---

### `get_quicklook_bands(collection_id)`

Bandas usadas no quicklook/thumbnail.

**Prompts:**

```
Quais bandas são usadas para gerar o quicklook da coleção LANDSAT-16D-1?

Como é composto o thumbnail do CBERS4-WFI-16D-2? Quais bandas RGB?
```

---

### `get_stac_item_as_geojson(collection_id, item_id)`

Item como GeoJSON Feature puro para GIS.

**Prompts:**

```
Exporte o item [item_id] do LANDSAT-16D-1 como GeoJSON para usar no QGIS.

Converta o item [item_id] para GeoJSON Feature.
```

---

## 5. Data Cubes

### `list_data_cubes(satellite, temporal_period, biome)`

Lista data cubes BDC com filtros.

**Prompts:**

```
Quais data cubes estão disponíveis no BDC?

Liste os data cubes Landsat com resolução temporal de 16 dias.

Quais data cubes CBERS existem para a Amazônia?

Existem data cubes com composição mensal? Quais?

Liste os data cubes de 8 dias disponíveis.
```

---

### `get_bdc_grid_info(collection_id)`

Grade BDC: projeção, tamanho de tile, sobreposição.

**Prompts:**

```
Qual grade o LANDSAT-16D-1 usa? Projeção, tamanho de tile e sobreposição.

Explique o sistema de grades BDC para o CBERS4-WFI-16D-2.

Qual a projeção e resolução da grade usada pela coleção S2_L2A-1?
```

---

### `get_cube_quality_info(collection_id)`

Bandas de qualidade (CLEAROB, CMASK, TOTALOB).

**Prompts:**

```
Quais bandas de qualidade o LANDSAT-16D-1 possui e como interpretá-las?

Como usar a banda CMASK do CBERS4-WFI-16D-2 para mascarar nuvens?

Explique os valores da banda de qualidade CLEAROB do data cube Landsat.

O que significam os valores da CMASK? Como usar para filtrar pixels contaminados?
```

---

### `find_cube_for_analysis(region, start_year, end_year, min_resolution_m, required_indices)`

Recomenda o melhor data cube para uma análise.

**Prompts:**

```
Qual data cube usar para analisar série temporal de NDVI em Goiás de 2019 a 2023?

Recomende um data cube com resolução de até 30m para o Cerrado, que tenha NDVI e EVI.

Qual o melhor data cube para monitorar vegetação no Mato Grosso entre 2020 e 2024 com resolução mínima de 64m?

Preciso de um cubo de dados com NDVI para a Amazônia de 2015 a 2023. Qual usar?

Qual data cube tem a melhor resolução temporal para acompanhar safras em Goiás?
```

---

## 6. Satélites

### `get_cbers_collections(version)`

Coleções CBERS com sensores (PAN5M, PAN10M, MUX, WFI, HRC).

**Prompts:**

```
Quais coleções CBERS estão disponíveis no BDC?

Liste apenas as coleções do CBERS-4A com seus sensores e resoluções.

Quais sensores do CBERS-4 posso usar? PAN5M, MUX, WFI — qual a diferença?

O CBERS-2B ainda tem dados disponíveis no BDC?
```

> **Resultado visual:** Compostos CBERS-4 WFI com imagens reais — True Color e False Color no Cerrado (setembro/2023, 0% de nuvens):
>
> ![Compostos CBERS-4](docs/images/sat_cbers4_composites.png)

---

### `get_sentinel2_collections()`

Coleções Sentinel-2 disponíveis.

**Prompts:**

```
Quais coleções Sentinel-2 estão no BDC? Tem L1C e L2A?

Liste as coleções Sentinel-2 — imagens brutas, cubos e mosaicos.

Existe cubo de dados Sentinel-2 no BDC?
```

> **Resultado visual:** Compostos Sentinel-2 com imagens reais — True Color, False Color e Agriculture no Cerrado (setembro/2023):
>
> ![Compostos Sentinel-2](docs/images/sat_sentinel2_composites.png)

---

### `get_landsat_collections()`

Coleções Landsat disponíveis.

**Prompts:**

```
Quais coleções Landsat existem no BDC?

Liste todos os produtos Landsat — brutas, data cubes e mosaicos.

O BDC tem composições Landsat de 16 dias? E bimestrais?
```

> **Resultado visual:** Compostos Landsat com imagens reais — True Color, False Color e Agriculture no Cerrado (setembro/2023, 0.06% de nuvens):
>
> ![Compostos Landsat](docs/images/sat_landsat_composites.png)

---

### `get_goes19_info()`

Dados GOES-19 CMI.

**Prompts:**

```
Quais dados do GOES-19 estão disponíveis no BDC?

O BDC tem dados meteorológicos? Quais bandas do GOES-19?

Qual a frequência de aquisição do GOES-19 CMI?
```

---

### `get_amazonia1_collections()`

Satélite Amazonia-1 — 100% brasileiro.

**Prompts:**

```
Quais dados do satélite Amazonia-1 estão disponíveis?

Me conte sobre o Amazonia-1 — sensor, resolução, cobertura.

O Amazonia-1 tem dados no BDC? Qual resolução espacial?
```

---

### `get_sentinel3_info()`

Sentinel-3 OLCI — dados oceânicos/costeiros.

**Prompts:**

```
O BDC tem dados do Sentinel-3? Quais produtos?

Existem dados de cor do oceano disponíveis? Sentinel-3 OLCI?

Quais dados costeiros/oceânicos posso acessar via BDC?
```

---

## 7. Biomas e Regiões

### `get_biome_bbox(biome)`

Bounding box WGS84 de biomas, estados e regiões.

> **Resultado visual:**
>
> ![Biomas Brasileiros](docs/images/map_biomes.png)

| Tipo | Valores aceitos |
|---|---|
| Biomas | `amazonia`, `cerrado`, `mata_atlantica`, `caatinga`, `pantanal`, `pampa` |
| Estados | `goias`, `mato_grosso`, `para`, `minas_gerais`, `bahia`, etc. |
| Regiões | `matopiba`, `arco_desmatamento`, `norte`, `nordeste`, `sudeste`, `sul`, `centro_oeste` |

**Prompts:**

```
Qual a bounding box do Cerrado?

Me dê as coordenadas do Pantanal em WGS84.

Qual a bbox do MATOPIBA?

Coordenadas geográficas do arco do desmatamento.

Qual a extensão geográfica do estado de Goiás?

Me dê a bbox da região Norte do Brasil.
```

---

### `find_collections_for_biome(biome, category, satellite)`

Coleções com cobertura de um bioma.

**Prompts:**

```
Quais coleções cobrem o Cerrado?

Encontre data cubes disponíveis para a Amazônia.

Quais coleções Landsat cobrem o Pantanal?

Liste as coleções de imagens brutas disponíveis para a Caatinga.

Quais dados Sentinel-2 cobrem a Mata Atlântica?
```

---

### `get_cerrado_monitoring_collections()`

Pacote de monitoramento do Cerrado.

**Prompts:**

```
Quais coleções são recomendadas para monitorar o Cerrado?

Monte um kit de dados para monitoramento de uso do solo no Cerrado.

Quais dados usar para acompanhar o desmatamento no Cerrado?
```

---

### `get_amazon_monitoring_collections()`

Pacote de monitoramento da Amazônia.

**Prompts:**

```
Quais coleções usar para monitorar desmatamento na Amazônia?

Monte um kit de dados para monitoramento da Amazônia.

Quais dados o INPE recomenda para análise de degradação florestal na Amazônia?
```

---

### `get_deforestation_analysis_collections()`

Pacote completo para análise de desmatamento.

**Prompts:**

```
Quais coleções usar para uma análise completa de desmatamento?

Monte um pacote de dados para detectar e quantificar desmatamento.

Preciso de dados para comparar desmatamento entre biomas. Quais coleções?
```

---

## 8. Análise e Geração de Código

### `discover_collections_for_topic(topic)`

Sugere coleções por tema em linguagem natural.

> **Resultado visual:**
>
> ![Cobertura de colecoes no Brasil](docs/images/map_collections_overview.png)

**Prompts:**

```
Quais coleções usar para estudar desmatamento no Cerrado?

Sugira dados para monitoramento de qualidade da água costeira.

Preciso de dados para analisar expansão de soja no Mato Grosso. O que usar?

Quais coleções servem para estudar NDVI time series na Amazônia?

Dados para monitorar pastagens degradadas em Goiás.

Sugira coleções para análise de ilhas de calor urbano.
```

---

### `build_python_search_snippet(collections, bbox_or_biome, datetime_range, cloud_max, asset_keys)`

Gera código Python completo com pystac-client.

**Prompts:**

```
Gere código Python para buscar imagens LANDSAT-16D-1 no Cerrado de 2020 a 2023.

Me dê o snippet Python para acessar NDVI e EVI do CBERS4-WFI-16D-2 no Mato Grosso.

Código Python para buscar Sentinel-2 com menos de 10% de nuvem na bbox [-50, -15, -49, -14].

Gere código Python completo para baixar imagens do LANDSAT-16D-1 para a Amazônia em 2022.
```

---

### `build_r_snippet(collections, bbox_or_biome, datetime_range, cloud_max)`

Gera código R com rstac.

**Prompts:**

```
Gere código R usando rstac para buscar dados LANDSAT-16D-1 no Cerrado.

Me dê o snippet R para acessar composições CBERS no Pantanal em 2023.

Código R para buscar imagens Sentinel-2 na Amazônia com filtro de nuvens.
```

---

### `get_time_series_plan(collection_id, bbox_or_biome, start_year, end_year, band)`

Plano de série temporal: itens esperados, volume, snippet Python.

**Prompts:**

```
Monte um plano de série temporal de NDVI para o Cerrado usando LANDSAT-16D-1 de 2018 a 2024.

Quantas composições esperar do CBERS4-WFI-16D-2 para Goiás entre 2020 e 2023?

Planeje a extração de série temporal de EVI para o arco do desmatamento, 2019 a 2023.

Qual o volume de dados esperado para uma série temporal de NDVI na Amazônia?
```

---

## 9. Índices Espectrais

### `list_spectral_indices(category)`

Lista 20 índices com filtro por categoria.

| Categoria | Índices |
|---|---|
| `vegetation` | NDVI, EVI, EVI2, SAVI, MSAVI2, GNDVI, ARVI, SIPI, CRI1, NDMI |
| `water` | NDWI, MNDWI |
| `burn` | NBR, NBR2, BAI, MIRBI |
| `soil` | BSI, CMRI |
| `urban` | NDBI |
| `snow` | NDSI |

**Prompts:**

```
Liste todos os índices espectrais disponíveis.

Quais índices de vegetação estão disponíveis?

Liste os índices para detecção de queimadas.

Quais índices existem para monitoramento de água?

Mostre os índices de solo disponíveis.
```

---

### `get_spectral_index_info(index_name)`

Detalhes de um índice: fórmula, bandas, aplicações, referência.

**Prompts:**

```
Explique o índice NDVI — fórmula, bandas necessárias e aplicações.

Qual a diferença entre EVI e EVI2? Quando usar cada um?

Detalhe o índice NBR — para que serve, fórmula e range de valores.

Me explique o SAVI e quando ele é melhor que o NDVI.

O que é o MIRBI? Para que serve no Cerrado?

Qual a fórmula do BAI e como interpretar seus valores?
```

---

### `get_collection_index_availability(collection_id)`

Verifica quais índices são computáveis com as bandas de uma coleção.

**Prompts:**

```
Quais índices espectrais posso calcular com a coleção LANDSAT-16D-1?

O CBERS4-WFI-16D-2 tem bandas suficientes para calcular NBR?

Quais índices estão pré-calculados na coleção LANDSAT-16D-1?

Posso calcular MNDWI a partir do Sentinel-2 L2A?

Quais índices NÃO consigo calcular com as bandas do CBERS-4 WFI?
```

---

### `generate_index_code(index_name, collection_id, language)`

Gera código Python, R ou sits para calcular um índice.

**Prompts:**

```
Gere o código Python para calcular NDVI a partir do LANDSAT-16D-1.

Me dê o snippet R para calcular NBR usando dados do Sentinel-2.

Gere código sits para calcular EVI na coleção CBERS4-WFI-16D-2.

Como calcular SAVI em Python usando a coleção LANDSAT-16D-1?

Gere código para calcular o MNDWI a partir do LANDSAT-16D-1 em Python.

Me dê o código R para computar o BAI usando LANDSAT-16D-1.
```

---

### `suggest_indices_for_application(application)`

Sugere índices para uma aplicação específica.

| Aplicação | Índices sugeridos |
|---|---|
| `vegetacao` / `vegetation` | NDVI, EVI, EVI2, SAVI, GNDVI, NDMI |
| `fogo` / `fire` / `queimada` | NBR, NBR2, BAI, MIRBI |
| `agua` / `water` | NDWI, MNDWI |
| `desmatamento` / `deforestation` | NDVI, EVI, NBR, NDMI |
| `agricultura` / `agriculture` | NDVI, EVI, EVI2, GNDVI, SAVI |
| `pastagem` / `pasture` | NDVI, EVI2, SAVI, MSAVI2 |
| `seca` / `drought` | NDMI, NDVI, SAVI |
| `cerrado` | NDVI, EVI2, SAVI, MIRBI, NBR |
| `amazonia` | NDVI, EVI, NDMI, NBR |

**Prompts:**

```
Quais índices usar para monitorar queimadas no Cerrado?

Sugira índices espectrais para mapear pastagens degradadas.

Quais índices são mais adequados para detectar desmatamento?

Índices para monitoramento de seca e estresse hídrico?

Quais índices usar para mapear água em áreas urbanas?

Sugira índices para agricultura de precisão.
```

---

## 10. Pré-processamento

### `get_preprocessing_guide(collection_id)`

Nível de correção já aplicado, o que falta e recomendações.

**Prompts:**

```
Qual o nível de pré-processamento da coleção LANDSAT-16D-1? O que já está corrigido?

Os dados do CBERS4-WFI-16D-2 precisam de correção atmosférica?

Preciso de dados de reflectância de superfície. A coleção CB4-MUX-L2-DN-1 serve ou preciso corrigir?

Qual o guia de pré-processamento para imagens brutas do CBERS-4?

O data cube LANDSAT-16D-1 é ARD (Analysis Ready Data)? O que falta?
```

---

### `get_cloud_mask_strategy(collection_id)`

Estratégia de mascaramento de nuvens: CMASK, SCL, Fmask.

**Prompts:**

```
Como mascarar nuvens no LANDSAT-16D-1? Qual banda usar e quais valores?

Me dê o código Python para aplicar máscara de nuvens no CBERS4-WFI-16D-2 usando CMASK.

Qual a estratégia de cloud masking para Sentinel-2 L2A no BDC?

Gere código R para filtrar pixels de nuvem e sombra na coleção LANDSAT-16D-1.

O que significam os valores da banda CMASK? Como interpretar?
```

---

### `get_atmospheric_correction_info(collection_id)`

Algoritmo de correção atmosférica aplicado.

**Prompts:**

```
Qual algoritmo de correção atmosférica foi aplicado ao LANDSAT-16D-1?

A coleção CB4-WFI-L4-SR-1 já tem correção atmosférica? Qual?

As imagens Sentinel-2 L2A do BDC usam Sen2Cor?

Preciso corrigir atmosfericamente as imagens CB4-MUX-L2-DN-1?
```

---

### `get_pan_sharpening_guide(collection_id)`

Guia de pan-sharpening para CBERS pancromático.

**Prompts:**

```
Como fazer pan-sharpening do CBERS-4 PAN5M com MUX?

Gere um guia de fusão do PAN10M com WFI no CBERS-4A.

É possível combinar PAN5M e MUX do CBERS-4 para obter 5m multiespectral? Como?

Qual a melhor técnica de pan-sharpening para dados CBERS?
```

---

## 11. Projeção CRS e Geometrias

### `reproject_bbox(bbox, from_crs, to_crs)`

Reprojeção entre CRS: WGS84, BDC Albers, UTM, SIRGAS2000.

| Alias CRS | Descrição |
|---|---|
| `EPSG:4326` / `wgs84` | WGS84 (graus) |
| `bdc_albers` / `EPSG:100001` | BDC Albers Equal-Area (metros) |
| `EPSG:4674` / `sirgas2000` | SIRGAS 2000 |
| `EPSG:327xx` | UTM zona Sul |

**Prompts:**

```
Converta a bbox [-50, -15, -49, -14] de WGS84 para BDC Albers.

Reprojetar a bbox do Cerrado de coordenadas geográficas para UTM zona 22S.

Converter bbox de BDC Albers de volta para WGS84.

Transforme as coordenadas [-60, -12, -55, -8] para SIRGAS 2000.

Qual a extensão em metros da bbox [-50, -15, -49, -14] em BDC Albers?
```

---

### `calculate_area(bbox, geojson, crs)`

Calcula área em m², hectares e km².

**Prompts:**

```
Qual a área em hectares da bbox [-50, -15, -49, -14]?

Calcule a área desta região: [-53.2, -19.5, -45.9, -12.4] (Goiás).

Qual a área em km² deste polígono GeoJSON? {"type": "Polygon", "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]]}

Calcule a área da minha fazenda definida por este GeoJSON: [insira geometria]

Quanto mede em hectares a bbox do Pantanal?
```

---

### `get_utm_zone(lon, lat)`

Retorna zona UTM e EPSG para uma coordenada.

**Prompts:**

```
Qual a zona UTM para Goiânia (-49.25, -16.68)?

Em qual zona UTM fica Manaus (-60.02, -3.12)?

Qual o código EPSG da zona UTM que cobre São Paulo (-46.63, -23.55)?

Identifique a zona UTM para a coordenada -55.0, -12.5 no Mato Grosso.
```

---

### `convert_geometry_format(geometry, to_format)`

Converte entre GeoJSON e WKT.

**Prompts:**

```
Converta este GeoJSON para WKT: {"type": "Polygon", "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]]}

Converta este WKT para GeoJSON: POLYGON ((-50 -15, -49 -15, -49 -14, -50 -14, -50 -15))

Transforme meu polígono GeoJSON em formato WKT para usar no PostGIS.

Converter este WKT de área de estudo para GeoJSON para uso no STAC: [insira WKT]
```

---

## 12. Séries Temporais

### `plan_time_series_extraction(collection_id, bbox_or_biome, start_year, end_year, bands, output_format)`

Plano avançado com código sits e Python completos.

**Prompts:**

```
Monte um plano completo para extrair série temporal de NDVI e EVI do LANDSAT-16D-1 para o Cerrado, 2018 a 2023.

Planeje a extração de séries temporais de RED e NIR da Amazônia usando CBERS4-WFI-16D-2, 2020-2023.

Quero extrair série temporal de NDVI para a bbox [-50, -15, -49, -14] do LANDSAT-16D-1. Gere o plano com código Python e sits.

Monte um plano de extração de série temporal multibanda (NDVI, EVI, SWIR16) para Mato Grosso, 2019-2024, com saída em CSV.

Planeje série temporal de NDVI para o Pantanal usando composições bimestrais Landsat.
```

---

### `get_filtering_guide(method)`

Guia de métodos de filtragem com snippets.

> **Resultado visual:**
>
> ![Filtragem de series temporais NDVI](docs/images/sits_filtering.png)

| Método | Descrição |
|---|---|
| `savitzky_golay` | Filtro polinomial local, preserva picos fenológicos |
| `whittaker` | Suavizador com penalização, robusto a gaps |
| `cloud_filter` | Máscara de nuvem + interpolação |

**Prompts:**

```
Qual o melhor método de filtragem para séries temporais de NDVI?

Compare Savitzky-Golay e Whittaker para suavização de séries temporais.

Me dê o guia completo do filtro Whittaker com código Python, R e sits.

Como usar filtro Savitzky-Golay em séries temporais de satélite? Quais parâmetros?

Qual método de filtragem funciona melhor com séries com muitos gaps (nuvens)?

Liste todos os métodos de filtragem disponíveis com prós e contras.
```

---

### `plan_phenology_extraction(collection_id, bbox_or_biome, band)`

Métricas fenológicas: SOS, EOS, Peak, Amplitude, LOS.

> **Resultado visual:**
>
> ![Metricas fenologicas NDVI Cerrado](docs/images/sits_phenology.png)

**Prompts:**

```
Monte um plano para extrair métricas fenológicas do NDVI no Cerrado usando LANDSAT-16D-1.

Como extrair SOS (Start of Season) e EOS (End of Season) de séries temporais de NDVI na Amazônia?

Planeje análise fenológica para monitoramento de safras em Goiás usando EVI.

Gere código Python e sits para calcular amplitude fenológica e length of season no Mato Grosso.

Quero identificar a data de plantio e colheita via fenologia de NDVI. Monte o plano.
```

---

### `analyze_temporal_gaps(collection_id, bbox_or_biome, datetime_range)`

Análise de gaps temporais via busca STAC real.

**Prompts:**

```
Analise os gaps temporais do LANDSAT-16D-1 para o Mato Grosso em 2022.

A série temporal do CBERS4-WFI-16D-2 no Cerrado é completa de 2020 a 2023? Tem gaps?

Verifique a completude temporal da coleção LANDSAT-16D-1 para a Amazônia entre 2018 e 2023.

Quantas observações faltam na série LANDSAT-16D-1 para Goiás em 2021?

Analise gaps do LANDSAT-16D-1 na bbox [-50, -15, -49, -14] de 2020 a 2023.
```

---

### `generate_sits_cube_code(collection_id, bbox_or_biome, start_year, end_year, bands)`

Código R sits completo: sits_cube até sits_get_data.

> **Resultado visual:**
>
> ![Workflow SITS completo](docs/images/sits_cube_workflow.png)

**Prompts:**

```
Gere código sits completo para criar um cubo LANDSAT-16D-1 do Cerrado com NDVI e EVI, 2020 a 2023.

Código R sits para acessar dados CBERS4-WFI-16D-2 na Amazônia de 2019 a 2022.

Gere o workflow sits para criar cubo, regularizar e extrair séries temporais do LANDSAT-16D-1 em Mato Grosso.

Código sits para criar cubo com bandas RED, NIR, SWIR16 do LANDSAT-16D-1 para o Pantanal.

Gere código sits para cubo de dados bimestral Landsat na Amazônia.
```

---

## 13. Classificação LULC

### `plan_classification_workflow(region, start_year, end_year, classes, algorithm)`

Plano completo de classificação em 9 etapas com código sits e Python.

> **Resultado visual:**
>
> ![Classificacao LULC Cerrado](docs/images/sits_classification.png)

| Algoritmo | Chave |
|---|---|
| Random Forest | `random_forest` |
| SVM | `svm` |
| XGBoost | `xgboost` |
| LightGBM | `lightgbm` |
| TempCNN / ResNet | `deep_learning` |

**Prompts:**

```
Monte um workflow completo de classificação de uso do solo para o Cerrado de 2020 a 2023 com Random Forest.

Planeje uma classificação LULC da Amazônia com XGBoost, classes: Forest, Pasture, Agriculture, Water, Urban.

Crie um plano de classificação com SVM para o Pantanal, 2021-2023, com 4 classes de cobertura.

Monte workflow de classificação com Deep Learning (TempCNN) para Mato Grosso, 2019-2023.

Planeje classificação de uso do solo para o MATOPIBA com classes: Soja, Milho, Cerrado, Pastagem, Água.

Quero classificar o uso do solo em Goiás. Monte o plano completo com código sits e Python.
```

---

### `get_sample_design_guide(region, classes, total_samples)`

Design amostral estratificado.

**Prompts:**

```
Como planejar a amostragem para classificação com 6 classes no Cerrado?

Quantas amostras preciso por classe para uma classificação confiável?

Monte um plano amostral para classificação Forest/Pasture/Agriculture na Amazônia com 500 amostras.

Qual a estratégia amostral ideal para 8 classes LULC em Mato Grosso?

Como distribuir 1000 amostras entre 5 classes de uso do solo?

Gere código sits e Python para carregar e validar amostras de treinamento.
```

---

### `get_ml_algorithm_guide(use_case)`

Comparação de algoritmos com recomendações por caso de uso.

| Caso de uso | Chave |
|---|---|
| Poucas amostras | `few_samples` |
| Máxima acurácia | `high_accuracy` |
| Velocidade | `fast` |
| Grande área | `large_area` |
| Séries temporais | `temporal` |

**Prompts:**

```
Qual algoritmo de ML devo usar para classificação com poucas amostras (<200 por classe)?

Compare Random Forest, SVM e XGBoost para classificação de séries temporais.

Qual o melhor algoritmo para classificação de grande área (estado inteiro)?

Preciso de velocidade de treinamento. LightGBM ou XGBoost?

Quando vale a pena usar Deep Learning (TempCNN) ao invés de Random Forest?

Me dê um guia completo de todos os algoritmos com prós, contras e hiperparâmetros.
```

---

### `get_accuracy_assessment_guide(n_classes)`

Guia de avaliação: OA, Kappa, F1, matriz de confusão.

**Prompts:**

```
Como avaliar a acurácia da minha classificação com 6 classes?

Gere código Python para calcular matriz de confusão, Kappa e F1-score.

Qual o mínimo de amostras de validação para 8 classes?

Me dê o guia completo de avaliação de acurácia com código sits e Python.

Como interpretar Overall Accuracy vs Kappa? Qual valor é bom?

Gere código Python e R para gerar relatório de acurácia por classe.
```

---

### `generate_sits_classification_code(collection_id, region, algorithm, classes, start_year, end_year)`

Código R sits completo para classificação (10 etapas).

**Prompts:**

```
Gere código sits completo para classificar o Cerrado com Random Forest usando LANDSAT-16D-1, 2020-2023.

Código sits para classificação da Amazônia com XGBoost, classes Forest/Pasture/Agriculture/Water.

Gere o script sits completo para classificação com TempCNN no Mato Grosso.

Código R sits para classificação de uso do solo no Pantanal com LightGBM, 2021-2023.

Gere código sits para classificar Goiás com SVM usando LANDSAT-16D-1, classes: Soja, Milho, Cerrado, Pastagem, Água, 2020-2022.
```

---

## 14. Detecção de Mudanças

### `list_change_detection_methods()`

Lista métodos disponíveis: BFAST, LandTrendr, dNBR, NDVI Anomaly.

**Prompts:**

```
Quais métodos de detecção de mudanças estão disponíveis?

Liste os algoritmos para detectar mudanças na cobertura do solo.

Quais técnicas existem para identificar desmatamento em séries temporais?
```

---

### `plan_change_detection(method, region, start_year, end_year)`

Plano completo com código Python e R.

**Prompts:**

```
Monte um plano de detecção de mudanças com BFAST para a Amazônia, 2018-2023.

Planeje análise de anomalia NDVI para o Cerrado entre 2020 e 2023.

Crie plano de detecção de mudanças usando LandTrendr em Mato Grosso, 2010-2023.

Monte análise de mudanças com dNBR na Chapada dos Veadeiros, 2019-2023.

Planeje detecção de mudanças via anomalia NDVI para monitorar seca no semiárido nordestino.
```

---

### `plan_fire_scar_detection(region, event_date)`

Detecção de cicatrizes de fogo com dNBR e severidade USGS.

> **Resultado visual:**
>
> ![Deteccao de fogo na Chapada dos Veadeiros](docs/images/map_fire_scar.png)

**Prompts:**

```
Detecte cicatrizes de fogo no Cerrado próximo à data 2023-08-15.

Planeje análise de severidade de queimada na Amazônia para o evento de setembro de 2022.

Monte plano de detecção de área queimada na Chapada dos Veadeiros em outubro de 2023.

Analise queimadas no Pantanal próximo a agosto de 2020. Gere código com classificação de severidade.

Detecte fogo na bbox [-48, -16, -47, -15] próximo a julho de 2023.

Monte análise de queimada na Serra da Canastra em setembro de 2022.
```

---

### `plan_deforestation_detection(region, start_year, end_year, method)`

Detecção de desmatamento com BFAST ou LandTrendr.

**Prompts:**

```
Planeje detecção de desmatamento na Amazônia com BFAST, 2018 a 2023.

Monte análise de desmatamento no Cerrado com LandTrendr de 2010 a 2023.

Detecte desmatamento no arco do desmatamento usando BFAST, 2019-2024.

Planeje monitoramento de desmatamento no Pará com BFAST, 2020-2023.

Compare BFAST e LandTrendr para detectar desmatamento no Mato Grosso de 2015 a 2023.
```

---

## 15. Administração

### `get_api_metrics()`

Métricas de uso da API: chamadas, latência, cache hits.

**Prompts:**

```
Mostre as métricas de uso da API do BDC nesta sessão.

Quantas chamadas foram feitas à API? Qual a latência média?

Qual a taxa de acerto do cache?
```

---

### `invalidate_cache(namespace)`

Invalida cache por namespace ou completo.

| Namespace | Descrição |
|---|---|
| `collection` | Cache de coleções individuais |
| `collections_list` | Cache da lista de coleções |
| `item` | Cache de itens |
| (vazio) | Limpa todo o cache |

**Prompts:**

```
Limpe todo o cache do servidor MCP.

Invalide o cache de coleções para forçar atualização.

Limpe o cache de itens.
```

---

## 16. Workflows Combinados

Prompts que combinam múltiplas ferramentas para workflows completos.

### Workflow: Monitoramento de Pastagens Degradadas

```
Preciso monitorar pastagens degradadas em Goiás de 2019 a 2024. Monte o workflow completo:
1. Qual data cube usar?
2. Quais índices espectrais são ideais para pastagem?
3. Gere código sits para extrair série temporal de NDVI e SAVI.
4. Planeje a classificação com classes: Pastagem Boa, Pastagem Degradada, Agricultura, Cerrado, Água.
5. Como avaliar a acurácia?
```

### Workflow: Análise Completa de Queimadas

```
Houve incêndios no Cerrado goiano em agosto de 2023. Monte análise completa:
1. Detecte cicatrizes de fogo usando dNBR.
2. Quais índices usar para análise complementar de queimada?
3. Analise se há gaps temporais no LANDSAT-16D-1 neste período.
4. Gere código Python e R completo.
5. Calcule a área queimada em hectares.
```

### Workflow: Classificação LULC da Amazônia

```
Classifique uso do solo no sul do Pará, 2020-2023:
1. Recomende o melhor data cube.
2. Monte o plano de classificação com XGBoost.
3. Quais classes usar (Forest, Pasture, Agriculture, Water, Urban)?
4. Design amostral para 1000 amostras.
5. Gere código sits completo.
6. Guia de avaliação de acurácia.
```

### Workflow: Série Temporal para Fenologia Agrícola

```
Quero analisar a fenologia de safras de soja em Mato Grosso:
1. Qual data cube e quais bandas usar?
2. Monte plano de extração de série temporal de NDVI e EVI, 2018-2024.
3. Qual filtro usar para suavizar a série?
4. Extraia métricas fenológicas (SOS como data de plantio, EOS como colheita).
5. Gere código sits e Python.
```

### Workflow: Monitoramento de Desmatamento na Amazônia

```
Monte um sistema completo de monitoramento de desmatamento na Amazônia:
1. Quais coleções usar (dados BDC + referência PRODES/DETER)?
2. Analise gaps temporais do LANDSAT-16D-1 para a Amazônia.
3. Planeje detecção com BFAST, 2018-2024.
4. Gere código Python e R.
5. Como validar contra dados PRODES do INPE?
```

### Workflow: Comparação Multissensor

```
Compare dados Landsat, CBERS e Sentinel-2 para monitoramento do Cerrado:
1. Compare as coleções LANDSAT-16D-1, CBERS4-WFI-16D-2 e S2_L2A-1.
2. Quais bandas e índices cada uma oferece?
3. Qual tem melhor resolução temporal e espacial?
4. Gere código para buscar dados das três fontes simultaneamente.
```

### Workflow: Análise de Impacto de Seca

```
Analise o impacto da seca no semiárido nordestino:
1. Quais índices usar para monitorar seca (NDMI, NDVI, SAVI)?
2. Monte plano de detecção de anomalia NDVI para a Caatinga, 2019-2023.
3. Gere série temporal de NDMI e NDVI.
4. Identifique períodos de anomalia severa.
5. Calcule a área afetada.
```

---

## Dicas de Uso

### Nomes de Regiões Aceitos

O servidor reconhece biomas, estados e regiões especiais como bbox:

- **Biomas**: `amazonia`, `cerrado`, `mata_atlantica`, `caatinga`, `pantanal`, `pampa`
- **Estados**: `goias`, `mato_grosso`, `para`, `minas_gerais`, `bahia`, `sao_paulo`, `rio_de_janeiro`, `tocantins`, `maranhao`, `piaui`, `mato_grosso_do_sul`, etc.
- **Regiões**: `matopiba`, `arco_desmatamento`, `norte`, `nordeste`, `sudeste`, `sul`, `centro_oeste`

### Formato de Datas

Sempre use ISO 8601: `"2020-01-01/2023-12-31"`

### Formato de Bbox

Array com 4 valores: `[min_lon, min_lat, max_lon, max_lat]` (WGS84)

Exemplo: `[-50.0, -15.0, -49.0, -14.0]`

### IDs de Coleções Mais Usados

| Uso | Coleção |
|---|---|
| Série temporal Landsat 30m | `LANDSAT-16D-1` |
| Série temporal CBERS 64m | `CBERS4-WFI-16D-2` |
| Alta resolução 10m | `S2_L2A-1` |
| Cobertura rápida 8 dias | `CBERS-WFI-8D-1` |
| Composição bimestral | `landsat-tsirf-bimonthly-1` |
| Mosaico Amazônia | `mosaic-landsat-amazon-3m-1` |
| NDVI MODIS 250m | `mod13q1-6.1` |
