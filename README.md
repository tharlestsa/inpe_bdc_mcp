# INPE BDC MCP Server

MCP Server para a **STAC API do INPE/Brazil Data Cube** — acesso a imagens de satélite, data cubes compostos, mosaicos, classificações de uso do solo, índices espectrais, séries temporais e workflows de classificação LULC para agentes de IA.

## Visão Geral

O [Brazil Data Cube (BDC)](https://brazildatacube.dpi.inpe.br/) é um projeto do INPE que produz e disponibiliza dados de observação da Terra prontos para análise (Analysis-Ready Data — ARD). O catálogo inclui:

- **Satélites brasileiros**: CBERS-4, CBERS-4A, Amazonia-1
- **Satélites internacionais**: Sentinel-2, Sentinel-3, Landsat, MODIS, GOES-19
- **Data cubes temporais**: composições de 8, 16 dias ou mensais com NDVI/EVI
- **Mosaicos regionais**: Amazônia, São Paulo, Paraíba, Brasil inteiro
- **Classificações de uso do solo**: Cerrado, Mata Atlântica, Pantanal
- **Dados oceânicos**: clorofila-a, cor do oceano (MODIS-Aqua)
- **Dados meteorológicos**: GOES-19 CMI

**STAC API base:** `https://data.inpe.br/bdc/stac/v1/`

O servidor expõe **68 ferramentas**, **7 prompts** e **7 resources** organizados em 12 módulos temáticos, cobrindo desde descoberta de dados até workflows completos de classificação de uso do solo inspirados no pacote R [sits](https://e-sensing.github.io/sitsbook/).

## Pré-requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recomendado)

## Instalação

```bash
# Com uv (recomendado)
cd inpe-bdc-mcp
uv sync

# Ou com pip
pip install -e .
```

## Autenticação

A autenticação é **opcional** para coleções públicas. Para coleções restritas, obtenha uma API key no [portal BDC](https://brazildatacube.dpi.inpe.br/).

```bash
export BDC_API_KEY="sua-chave-aqui"
```

## Registro no Claude Code

### Via CLI (recomendado)

```bash
claude mcp add -s user -t stdio inpe-bdc -e BDC_API_KEY="sua-chave-aqui" -- uv run --directory /caminho/para/inpe-bdc-mcp python -m inpe_bdc_mcp
```

### Via settings.json

Adicione ao seu `~/.claude/settings.json` ou `.claude/settings.json` do projeto:

```json
{
  "mcpServers": {
    "inpe-bdc": {
      "command": "uv",
      "args": ["run", "--directory", "/caminho/para/inpe-bdc-mcp", "python", "-m", "inpe_bdc_mcp"],
      "env": {
        "BDC_API_KEY": ""
      }
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "inpe-bdc": {
      "command": "uv",
      "args": ["run", "--directory", "/caminho/para/inpe-bdc-mcp", "python", "-m", "inpe_bdc_mcp"],
      "env": {
        "BDC_API_KEY": ""
      }
    }
  }
}
```

## Arquitetura

```
src/inpe_bdc_mcp/
├── server.py               # Entrypoint FastMCP — registra 68 tools + 7 prompts + 7 resources
├── client.py               # Cliente HTTP singleton para STAC API (httpx)
├── auth.py                 # Autenticação (API key)
├── catalogs.py             # Catálogo estático de coleções, bandas e constantes
├── models/                 # Modelos Pydantic
│   ├── collection.py       #   Coleções STAC
│   ├── item.py             #   Itens STAC
│   ├── search.py           #   Busca e séries temporais
│   ├── spectral.py         #   Índices espectrais
│   ├── preprocessing.py    #   Pré-processamento
│   ├── classification.py   #   Classificação LULC
│   └── change_detection.py #   Detecção de mudanças e fenologia
├── tools/                  # Módulos de ferramentas (lógica de negócio)
│   ├── catalog.py          #   Catálogo e conformance
│   ├── collections.py      #   Coleções e bandas
│   ├── search.py           #   Busca de itens
│   ├── items.py            #   Itens e assets
│   ├── datacube.py         #   Data cubes
│   ├── satellites.py       #   Satélites
│   ├── biomes.py           #   Biomas e regiões
│   ├── analysis.py         #   Análise e geração de código
│   ├── spectral.py         #   Índices espectrais (20 índices)
│   ├── preprocessing.py    #   Pré-processamento de imagens
│   ├── projection.py       #   Projeção CRS e geometrias
│   ├── timeseries.py       #   Séries temporais (sits)
│   ├── classification.py   #   Classificação LULC (sits)
│   └── change_detection.py #   Detecção de mudanças
├── resources/              # MCP Resources
│   ├── catalog.py
│   └── collections.py
└── utils/                  # Utilitários
    ├── brazil.py           #   Biomas, estados e regiões do Brasil
    ├── bdc_grid.py         #   Grade BDC
    ├── cache.py            #   Cache TTL em memória
    ├── geo.py              #   Utilitários geoespaciais
    └── metrics.py          #   Métricas de uso da API
```

## Ferramentas (68 Tools)

### Catálogo (3)

| Ferramenta | Descrição |
|---|---|
| `catalog_info()` | Informações gerais do catálogo: versão STAC, total de coleções, endpoints |
| `list_conformance_classes()` | Conformance classes OGC implementadas |
| `get_api_capabilities()` | Capacidades da API: CQL2, fields, sortby, autenticação |

### Coleções (4)

| Ferramenta | Descrição |
|---|---|
| `list_collections(category, satellite, biome, data_type, keyword, limit)` | Lista coleções com filtros múltiplos |
| `get_collection_detail(collection_id)` | Metadados completos de uma coleção |
| `get_collection_bands(collection_id)` | Bandas espectrais detalhadas |
| `compare_collections(collection_ids)` | Compara múltiplas coleções |

### Busca de Itens (7)

| Ferramenta | Descrição |
|---|---|
| `search_items(collections, bbox, datetime_range, cloud_cover_max, limit, sortby)` | Busca avançada com filtros |
| `search_by_point(lon, lat, collections, datetime_range, cloud_cover_max)` | Busca por coordenada |
| `search_by_polygon(geojson_geometry, collections, datetime_range)` | Busca por geometria GeoJSON |
| `search_by_tile(collection_id, tile_id, datetime_range)` | Busca por tile BDC |
| `search_latest_items(collection_id, bbox, n)` | N itens mais recentes |
| `search_cloud_free(collections, bbox, datetime_range, max_cloud)` | Imagens com menor cobertura de nuvens |
| `get_all_pages(collections, bbox, datetime_range, max_items)` | Todas as páginas de resultados |

### Itens e Assets (6)

| Ferramenta | Descrição |
|---|---|
| `get_item(collection_id, item_id)` | Detalhes completos de um item |
| `list_item_assets(collection_id, item_id)` | Assets com URLs e metadados |
| `get_asset_download_info(collection_id, item_id, asset_key)` | Snippets de download (curl, Python, R) |
| `get_thumbnail_url(collection_id, item_id)` | URL do thumbnail |
| `get_quicklook_bands(collection_id)` | Bandas usadas no quicklook |
| `get_stac_item_as_geojson(collection_id, item_id)` | Item como GeoJSON Feature |

### Data Cubes (4)

| Ferramenta | Descrição |
|---|---|
| `list_data_cubes(satellite, temporal_period, biome)` | Lista data cubes compostos |
| `get_bdc_grid_info(collection_id)` | Info da grade BDC (projeção, tile size) |
| `get_cube_quality_info(collection_id)` | Bandas de qualidade (CLEAROB, CMASK) |
| `find_cube_for_analysis(region, start_year, end_year, min_resolution_m, required_indices)` | Recomenda data cube |

### Satélites (6)

| Ferramenta | Descrição |
|---|---|
| `get_cbers_collections(version)` | Coleções CBERS com descrição de sensores |
| `get_sentinel2_collections()` | Coleções Sentinel-2 (L1C, L2A, cubes) |
| `get_landsat_collections()` | Coleções Landsat |
| `get_goes19_info()` | Dados GOES-19 CMI meteorológicos |
| `get_amazonia1_collections()` | Satélite Amazonia-1 (100% brasileiro) |
| `get_sentinel3_info()` | Sentinel-3 OLCI dados oceânicos |

### Biomas e Regiões (5)

| Ferramenta | Descrição |
|---|---|
| `get_biome_bbox(biome)` | Bbox WGS84 de bioma/estado/região |
| `find_collections_for_biome(biome, category, satellite)` | Coleções para um bioma |
| `get_cerrado_monitoring_collections()` | Pacote para monitoramento do Cerrado |
| `get_amazon_monitoring_collections()` | Pacote para monitoramento da Amazônia |
| `get_deforestation_analysis_collections()` | Pacote para análise de desmatamento |

### Análise e Código (4)

| Ferramenta | Descrição |
|---|---|
| `discover_collections_for_topic(topic)` | Sugere coleções por tema em linguagem natural |
| `build_python_search_snippet(collections, bbox_or_biome, datetime_range)` | Gera código Python (pystac-client) |
| `build_r_snippet(collections, bbox_or_biome, datetime_range)` | Gera código R (rstac) |
| `get_time_series_plan(collection_id, bbox_or_biome, start_year, end_year, band)` | Plano de série temporal |

### Índices Espectrais (5)

| Ferramenta | Descrição |
|---|---|
| `list_spectral_indices(category)` | Lista 20 índices (vegetation, water, soil, burn, snow, urban) |
| `get_spectral_index_info(index_name)` | Fórmula, bandas, aplicações, valor range, referência |
| `get_collection_index_availability(collection_id)` | Índices pré-calculados vs computáveis vs impossíveis |
| `generate_index_code(index_name, collection_id, language)` | Snippet Python/R/sits para calcular o índice |
| `suggest_indices_for_application(application)` | Sugere índices para "vegetação", "água", "fogo", etc. |

**Índices incluídos:** NDVI, EVI, EVI2, SAVI, MSAVI2, NDWI, MNDWI, NDBI, NBR, NBR2, NDMI, NDSI, BSI, GNDVI, BAI, MIRBI, CMRI, ARVI, SIPI, CRI1.

### Pré-processamento (4)

| Ferramenta | Descrição |
|---|---|
| `get_preprocessing_guide(collection_id)` | O que já está corrigido, o que falta, recomendações |
| `get_cloud_mask_strategy(collection_id)` | Banda de máscara (CMASK/SCL/Fmask), valores, snippets |
| `get_atmospheric_correction_info(collection_id)` | Algoritmo usado (LaSRC, Sen2Cor, etc.) |
| `get_pan_sharpening_guide(collection_id)` | Guia para CBERS PAN5M/PAN10M + MUX/WFI |

### Projeção CRS e Geometrias (4)

| Ferramenta | Descrição |
|---|---|
| `reproject_bbox(bbox, from_crs, to_crs)` | Reprojeção WGS84 ↔ BDC Albers ↔ UTM |
| `calculate_area(bbox, geojson, crs)` | Área em m², hectares e km² |
| `get_utm_zone(lon, lat)` | Zona UTM e código EPSG para coordenada |
| `convert_geometry_format(geometry, to_format)` | Conversão GeoJSON ↔ WKT |

### Séries Temporais (5)

Inspirado no workflow [sits](https://e-sensing.github.io/sitsbook/): `sits_cube` → `sits_regularize` → `sits_get_data` → `sits_filter`.

| Ferramenta | Descrição |
|---|---|
| `plan_time_series_extraction(collection_id, bbox_or_biome, start_year, end_year, bands, output_format)` | Plano avançado com código sits e Python |
| `get_filtering_guide(method)` | Savitzky-Golay, Whittaker, Cloud Filter — parâmetros e snippets |
| `plan_phenology_extraction(collection_id, bbox_or_biome, band)` | Métricas fenológicas (SOS, EOS, Peak, Amplitude, LOS) |
| `analyze_temporal_gaps(collection_id, bbox_or_biome, datetime_range)` | Análise de gaps temporais via busca STAC real |
| `generate_sits_cube_code(collection_id, bbox_or_biome, start_year, end_year, bands)` | Código R sits completo |

### Classificação LULC (5)

Mapeia o workflow sits completo: `sits_train` → `sits_classify` → `sits_smooth` → `sits_label_classification`.

| Ferramenta | Descrição |
|---|---|
| `plan_classification_workflow(region, start_year, end_year, classes, algorithm)` | Plano completo LULC em 9 passos |
| `get_sample_design_guide(region, classes, total_samples)` | Design amostral estratificado |
| `get_ml_algorithm_guide(use_case)` | Comparação RF vs SVM vs XGBoost vs LightGBM vs DL |
| `get_accuracy_assessment_guide(n_classes)` | Matriz de confusão, OA, Kappa, F1 |
| `generate_sits_classification_code(collection_id, region, algorithm, classes, start_year, end_year)` | Código R sits completo |

**Algoritmos suportados:** Random Forest, SVM, XGBoost, LightGBM, Deep Learning (TempCNN/ResNet).

### Detecção de Mudanças (4)

| Ferramenta | Descrição |
|---|---|
| `list_change_detection_methods()` | BFAST, LandTrendr, dNBR, Anomalia NDVI |
| `plan_change_detection(method, region, start_year, end_year)` | Plano completo com código Python e R |
| `plan_fire_scar_detection(region, event_date)` | dNBR com classificação de severidade USGS |
| `plan_deforestation_detection(region, start_year, end_year, method)` | BFAST/LandTrendr para desmatamento |

### Administração (2)

| Ferramenta | Descrição |
|---|---|
| `get_api_metrics()` | Métricas de uso da API (requisições, cache hits, latência) |
| `invalidate_cache(namespace)` | Invalida cache por namespace ou completo |

## MCP Resources (7)

| URI | Descrição |
|---|---|
| `stac://inpe-bdc/catalog` | Landing page do catálogo |
| `stac://inpe-bdc/collections` | Índice categorizado de coleções |
| `stac://inpe-bdc/satellites` | Catálogo de satélites |
| `stac://inpe-bdc/biomes` | Biomas com bboxes |
| `stac://inpe-bdc/guide` | Guia de uso completo |
| `stac://inpe-bdc/collection/{collection_id}` | Metadados de uma coleção |
| `stac://inpe-bdc/item/{collection_id}/{item_id}` | Detalhes de um item |

## MCP Prompts (7)

| Prompt | Descrição |
|---|---|
| `search_images(satellite, region, period)` | Busca guiada de imagens de satélite |
| `deforestation_analysis(biome, start_year, end_year)` | Análise de desmatamento |
| `time_series_workflow(collection_id, region, band)` | Workflow de série temporal |
| `mosaic_exploration(region, satellite)` | Exploração de mosaicos |
| `sits_classification_workflow(region, start_year, end_year, algorithm)` | Classificação LULC com sits |
| `change_detection_workflow(method, region, start_year, end_year)` | Detecção de mudanças |
| `spectral_analysis(application, collection_id)` | Análise espectral |

## Catálogo de Coleções

### Satélites Brasileiros (Imagens Brutas)

| ID | Satélite | Sensor | Resolução |
|---|---|---|---|
| CB4-PAN5M-L2-DN-1 | CBERS-4 | PAN5M | 5m |
| CB4-PAN10M-L2-DN-1 | CBERS-4 | PAN10M | 10m |
| CB4-MUX-L2-DN-1 | CBERS-4 | MUX | 20m |
| CB4-WFI-L4-SR-1 | CBERS-4 | WFI | 64m |
| CB4A-MUX-L4-DN-1 | CBERS-4A | MUX | 20m |
| CB4A-WFI-L4-DN-1 | CBERS-4A | WFI | 55m |
| CB2B-HRC-L2-DN-1 | CBERS-2B | HRC | 2.5m |
| AMZ1-WFI-L2-DN-1 | Amazonia-1 | WFI | 60m |

### Data Cubes

| ID | Satélite | Período | Resolução |
|---|---|---|---|
| CBERS4-WFI-16D-2 | CBERS-4 | 16 dias | 64m |
| CBERS-WFI-8D-1 | CBERS/WFI | 8 dias | 64m |
| LANDSAT-16D-1 | Landsat | 16 dias | 30m |
| landsat-tsirf-bimonthly-1 | Landsat | 2 meses | 30m |
| S2_L2A-1 | Sentinel-2 | — | 10m |

### Mosaicos

| ID | Região | Satélite |
|---|---|---|
| mosaic-landsat-amazon-3m-1 | Amazônia | Landsat |
| mosaic-s2-amazon-3m-1 | Amazônia | Sentinel-2 |
| mosaic-landsat-brazil-6m-1 | Brasil | Landsat |

### Classificação (LCC)

| ID | Bioma |
|---|---|
| LCC_L8_30_16D_STK_Cerrado-1 | Cerrado |
| LCC_L8_30_16D_STK_MataAtlantica-1 | Mata Atlântica |
| LCC_L8_30_16D_STK_Pantanal-1 | Pantanal |

### MODIS / Especiais

| ID | Produto | Domínio |
|---|---|---|
| mod13q1-6.1 | NDVI Terra 250m | Vegetação |
| myd13q1-6.1 | NDVI Aqua 250m | Vegetação |
| MODISA-OCSMART-CHL-MONTHLY-1 | Clorofila-a | Oceano |
| GOES19-L2-CMI-1 | CMI | Meteorologia |

## Índices Espectrais Suportados

| Índice | Nome Completo | Categoria | Bandas |
|---|---|---|---|
| NDVI | Normalized Difference Vegetation Index | vegetation | NIR, RED |
| EVI | Enhanced Vegetation Index | vegetation | NIR, RED, BLUE |
| EVI2 | Enhanced Vegetation Index 2 | vegetation | NIR, RED |
| SAVI | Soil Adjusted Vegetation Index | vegetation | NIR, RED |
| MSAVI2 | Modified SAVI 2 | vegetation | NIR, RED |
| GNDVI | Green NDVI | vegetation | NIR, GREEN |
| ARVI | Atmospherically Resistant VI | vegetation | NIR, RED, BLUE |
| SIPI | Structure Insensitive Pigment Index | vegetation | NIR, BLUE, RED |
| CRI1 | Carotenoid Reflectance Index 1 | vegetation | BLUE, GREEN |
| NDMI | Normalized Difference Moisture Index | vegetation | NIR, SWIR16 |
| NDWI | Normalized Difference Water Index | water | GREEN, NIR |
| MNDWI | Modified NDWI | water | GREEN, SWIR16 |
| NDBI | Normalized Difference Built-up Index | urban | SWIR16, NIR |
| NBR | Normalized Burn Ratio | burn | NIR, SWIR22 |
| NBR2 | Normalized Burn Ratio 2 | burn | SWIR16, SWIR22 |
| BAI | Burned Area Index | burn | RED, NIR |
| MIRBI | Mid-Infrared Burn Index | burn | SWIR22, SWIR16 |
| BSI | Bare Soil Index | soil | SWIR16, RED, NIR, BLUE |
| CMRI | Clay Minerals Ratio Index | soil | SWIR16, SWIR22 |
| NDSI | Normalized Difference Snow Index | snow | GREEN, SWIR16 |

## Exemplos de Uso

### Descoberta e Busca

```
"Busque imagens Sentinel-2 com menos de 10% de nuvem para o Cerrado em 2023"

"Qual data cube usar para analisar série temporal de NDVI em Goiás de 2019 a 2023?"

"Liste os mosaicos disponíveis para a Amazônia"

"Me dê o snippet Python para baixar uma cena CBERS-4A do Pantanal"

"Compare as coleções CBERS-4 WFI e Sentinel-2 L2A para monitoramento de desmatamento"
```

### Índices Espectrais

```
"Quais índices posso calcular com a coleção LANDSAT-16D-1?"

"Sugira índices espectrais para monitoramento de queimadas no Cerrado"

"Gere o código Python para calcular NBR a partir do Landsat"
```

### Séries Temporais

```
"Monte um plano de série temporal de EVI para o arco do desmatamento de 2018 a 2024"

"Gere código sits para criar um cubo LANDSAT-16D-1 da Amazônia"

"Qual método de filtragem usar para suavizar série temporal de NDVI?"

"Analise os gaps temporais do LANDSAT-16D-1 para o Mato Grosso em 2022"
```

### Classificação LULC

```
"Monte um workflow completo de classificação de uso do solo para o Cerrado com XGBoost"

"Qual algoritmo de ML devo usar para classificação com poucas amostras?"

"Gere o código sits completo para classificação com Random Forest"

"Como avaliar a acurácia da minha classificação com 8 classes?"
```

### Detecção de Mudanças

```
"Planeje detecção de desmatamento na Amazônia com BFAST de 2018 a 2023"

"Detecte cicatrizes de fogo no Cerrado próximo a agosto de 2023"

"Quais métodos de detecção de mudanças estão disponíveis?"
```

### Projeção e Geometrias

```
"Converta esta bbox de WGS84 para BDC Albers"

"Qual a área em hectares desta região?"

"Qual a zona UTM para as coordenadas de Manaus?"
```

## Testes

```bash
# Executar todos os testes
uv run pytest tests/ -v

# Testes por módulo
uv run pytest tests/test_spectral.py -v
uv run pytest tests/test_projection.py -v
uv run pytest tests/test_timeseries.py -v
uv run pytest tests/test_classification.py -v
uv run pytest tests/test_change_detection.py -v
```

Os testes utilizam [respx](https://lundberg.github.io/respx/) para mock de chamadas HTTP à STAC API, garantindo execução offline e determinística.

## Dependências

| Pacote | Uso |
|---|---|
| `mcp[cli]` | Framework MCP (FastMCP) |
| `httpx` | Cliente HTTP assíncrono |
| `pystac-client` | Cliente STAC |
| `pystac` | Modelos STAC |
| `shapely` | Operações geométricas |
| `pyproj` | Projeções cartográficas (CRS) |
| `pydantic` | Validação de dados |

## Notas Técnicas

### CRS BDC Albers (EPSG:100001)

O Brazil Data Cube utiliza o sistema de coordenadas Albers Equal-Area customizado (EPSG:100001), não reconhecido pelo pyproj. O servidor resolve internamente via Proj4 string:

```
+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22
+x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs
```

Os aliases `bdc_albers`, `epsg:100001` e `wgs84` são resolvidos automaticamente pelas ferramentas de projeção.

### Workflow sits (R)

As ferramentas de classificação e séries temporais geram código para o pacote R [sits](https://e-sensing.github.io/sitsbook/), que implementa o pipeline completo:

1. `sits_cube()` — Criar cubo STAC
2. `sits_regularize()` — Regularizar resolução temporal
3. `sits_get_data()` — Extrair séries temporais
4. `sits_filter()` — Filtrar ruídos (Whittaker/Savitzky-Golay)
5. `sits_som()` — Avaliar qualidade das amostras
6. `sits_train()` — Treinar modelo (RF/SVM/XGBoost/TempCNN)
7. `sits_classify()` — Classificar cubo
8. `sits_smooth()` — Pós-processamento bayesiano
9. `sits_label_classification()` — Gerar mapa final

### Natureza das Ferramentas

As ferramentas de análise geoespacial (índices espectrais, classificação, detecção de mudanças) geram **informação, orientação e snippets de código** — o servidor MCP **não processa rasters diretamente**. O processamento de dados ocorre no ambiente do usuário via os snippets Python ou R gerados.

## Limitações Conhecidas

- Algumas coleções restritas requerem API key — configure `BDC_API_KEY`
- A API BDC pode ter latência variável dependendo da carga do servidor
- Paginação limitada a 1000 itens por página
- Filtros CQL2 avançados dependem das conformance classes do servidor
- Sortby pode não funcionar para todos os campos em todas as coleções
- O servidor não processa rasters — gera código e orientação para processamento no ambiente do usuário

## Citação

Se utilizar dados do Brazil Data Cube em publicações, cite:

> Ferreira, K.R.; Queiroz, G.R.; Vinhas, L.; Marujo, R.F.B.; Simoes, R.E.O.; Picoli, M.C.A.; Camara, G.; Cartaxo, R.; Gomes, V.C.F.; Santos, L.A.; Sanchez, A.H.; Arcanjo, J.S.; Fronza, J.G.; Noronha, C.A.; Costa, R.W.; Zaglia, M.C.; Zioti, F.; Korting, T.S.; Soares, A.R.; Chaves, M.E.D.; Fonseca, L.M.G. Earth Observation Data Cubes for Brazil: Requirements, Methodology and Products. Remote Sensing, 12, 4033, 2020. DOI: 10.3390/rs12244033

## Créditos

### Dados e Infraestrutura

- **[INPE — Instituto Nacional de Pesquisas Espaciais](https://www.gov.br/inpe/)** — Produção e disponibilização dos dados de observação da Terra
- **[Brazil Data Cube (BDC)](https://brazildatacube.dpi.inpe.br/)** — Plataforma de data cubes ARD e STAC API
- **[STAC — SpatioTemporal Asset Catalog](https://stacspec.org/)** — Especificação de catálogo de dados geoespaciais

### Referências Científicas

- **sits (Satellite Image Time Series)** — Simoes, R.; Camara, G.; Queiroz, G.; Souza, F.; Andrade, P.R.; Santos, L.; Carvalho, A.; Ferreira, K. *Satellite Image Time Series Analysis on Earth Observation Data Cubes*. [sits R package](https://e-sensing.github.io/sitsbook/)
- **BFAST** — Verbesselt, J.; Hyndman, R.; Newnham, G.; Culvenor, D. *Detecting Trend and Seasonal Changes in Satellite Image Time Series*. Remote Sensing of Environment, 2010.
- **LandTrendr** — Kennedy, R.E.; Yang, Z.; Cohen, W.B. *Detecting Trends in Forest Disturbance and Recovery*. Remote Sensing of Environment, 2010.

### Tecnologias

- **[MCP — Model Context Protocol](https://modelcontextprotocol.io/)** — Protocolo de comunicação entre agentes de IA e ferramentas
- **[FastMCP](https://github.com/jlowin/fastmcp)** — Framework Python para servidores MCP
- **[pyproj](https://pyproj4.github.io/pyproj/)** — Transformações cartográficas
- **[Shapely](https://shapely.readthedocs.io/)** — Operações geométricas
- **[pystac-client](https://pystac-client.readthedocs.io/)** — Cliente STAC para Python

## Licença

MIT
