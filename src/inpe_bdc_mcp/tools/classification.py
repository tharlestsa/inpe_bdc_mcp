"""Ferramentas MCP para workflows de classificação LULC inspirados no sits."""

from __future__ import annotations

from typing import Any

from ..catalogs import ALL_COLLECTIONS, COLLECTION_BAND_MAPPING
from ..models.classification import (
    AccuracyAssessmentGuide,
    ClassificationPlan,
    MLAlgorithmGuide,
    MLAlgorithmInfo,
    SampleDesignGuide,
    WorkflowStep,
)
from ..utils.brazil import resolve_bbox


# ------------------------------------------------------------------ #
# Algoritmos de ML para classificação
# ------------------------------------------------------------------ #

_ML_ALGORITHMS: dict[str, dict[str, Any]] = {
    "random_forest": {
        "name": "Random Forest",
        "sits_function": "sits_rfor()",
        "sklearn_class": "sklearn.ensemble.RandomForestClassifier",
        "pros": [
            "Robusto a overfitting",
            "Lida bem com dados de alta dimensionalidade",
            "Não requer normalização dos dados",
            "Indica importância de variáveis",
        ],
        "cons": [
            "Menos preciso que métodos mais complexos em problemas difíceis",
            "Árvores profundas podem ser lentas em predição",
        ],
        "best_for": "Classificações iniciais, exploração de dados, quando há muitas bandas/features.",
        "hyperparameters": {
            "n_estimators": "Número de árvores (100-500). Mais árvores = mais robusto, mais lento.",
            "max_depth": "Profundidade máxima (10-30). None = sem limite.",
            "min_samples_leaf": "Mínimo de amostras por folha (5-20).",
        },
    },
    "svm": {
        "name": "Support Vector Machine (SVM)",
        "sits_function": "sits_svm()",
        "sklearn_class": "sklearn.svm.SVC",
        "pros": [
            "Excelente para classificação com poucas amostras",
            "Eficaz em espaços de alta dimensionalidade",
            "Kernel RBF captura relações não-lineares",
        ],
        "cons": [
            "Lento para treinamento em grandes datasets",
            "Sensível à escala dos dados (requer normalização)",
            "Difícil interpretabilidade",
        ],
        "best_for": "Classificação com poucas amostras de treinamento, séries temporais complexas.",
        "hyperparameters": {
            "C": "Parâmetro de regularização (0.1-100). Maior = menos regularização.",
            "gamma": "Parâmetro do kernel RBF ('scale' ou 0.001-1).",
            "kernel": "Tipo de kernel ('rbf', 'linear', 'poly').",
        },
    },
    "xgboost": {
        "name": "XGBoost (Extreme Gradient Boosting)",
        "sits_function": "sits_xgboost()",
        "sklearn_class": "xgboost.XGBClassifier",
        "pros": [
            "Alta acurácia em problemas tabulares",
            "Rápido (implementação otimizada em C++)",
            "Regularização embutida (L1/L2)",
            "Lida com dados faltantes nativamente",
        ],
        "cons": [
            "Propenso a overfitting sem tuning cuidadoso",
            "Muitos hiperparâmetros para ajustar",
        ],
        "best_for": "Melhor acurácia geral, classificação com muitas amostras e features.",
        "hyperparameters": {
            "n_estimators": "Número de boosting rounds (100-1000).",
            "max_depth": "Profundidade das árvores (3-10). Menor = mais regularizado.",
            "learning_rate": "Taxa de aprendizado (0.01-0.3). Menor = mais robusto.",
            "subsample": "Fração de amostras por árvore (0.7-1.0).",
        },
    },
    "lightgbm": {
        "name": "LightGBM",
        "sits_function": "sits_lightgbm()",
        "sklearn_class": "lightgbm.LGBMClassifier",
        "pros": [
            "Mais rápido que XGBoost para grandes datasets",
            "Menor uso de memória",
            "Suporte a features categóricas nativas",
        ],
        "cons": [
            "Pode overfittar com poucos dados",
            "Sensível a hiperparâmetros",
        ],
        "best_for": "Datasets grandes (>100k amostras), velocidade de treinamento.",
        "hyperparameters": {
            "n_estimators": "Número de árvores (100-1000).",
            "num_leaves": "Número de folhas (31-255). Controla complexidade.",
            "learning_rate": "Taxa de aprendizado (0.01-0.3).",
        },
    },
    "deep_learning": {
        "name": "Deep Learning (TempCNN / ResNet)",
        "sits_function": "sits_tempcnn() / sits_resnet()",
        "sklearn_class": "torch (PyTorch) — via sits ou implementação custom",
        "pros": [
            "Captura padrões temporais complexos",
            "TempCNN: CNN 1D projetada para séries temporais de satélite",
            "ResNet: aprendizado de features residuais",
            "Estado da arte em classificação de séries temporais",
        ],
        "cons": [
            "Requer GPU para treinamento eficiente",
            "Necessita muitas amostras (>1000 por classe)",
            "Menos interpretável",
            "Mais complexo de configurar",
        ],
        "best_for": "Máxima acurácia com muitos dados, séries temporais longas e complexas.",
        "hyperparameters": {
            "epochs": "Épocas de treinamento (100-300).",
            "batch_size": "Tamanho do batch (32-128).",
            "learning_rate": "Taxa de aprendizado (0.001-0.01).",
            "optimizer": "Otimizador (Adam recomendado).",
        },
    },
}


def plan_classification_workflow(
    region: str | list[float],
    start_year: int = 2020,
    end_year: int = 2023,
    classes: list[str] | None = None,
    algorithm: str = "random_forest",
) -> dict[str, Any]:
    """Plano completo de classificação LULC inspirado no workflow sits.

    Args:
        region: Nome da região/bioma ou bbox.
        start_year: Ano inicial.
        end_year: Ano final.
        classes: Lista de classes LULC (ex: ["Forest", "Pasture", "Agriculture", "Water"]).
        algorithm: Algoritmo — "random_forest", "svm", "xgboost", "lightgbm", "deep_learning".
    """
    if classes is None:
        classes = ["Forest", "Pasture", "Agriculture", "Cerrado", "Water", "Urban"]

    if isinstance(region, str):
        bbox = resolve_bbox(region) or [-53.2, -19.5, -45.9, -12.4]
        region_name = region
    else:
        bbox = region
        region_name = "custom"

    algo_info = _ML_ALGORITHMS.get(algorithm, _ML_ALGORITHMS["random_forest"])
    collection = "LANDSAT-16D-1"
    bands = ["NDVI", "EVI", "RED", "NIR", "BLUE", "GREEN", "SWIR16", "SWIR22"]

    band_map = COLLECTION_BAND_MAPPING.get(collection, {})
    mapped_bands = [band_map.get(b.lower(), b) for b in bands if b.lower() in band_map]
    bands_r = ", ".join(f'"{b}"' for b in mapped_bands)

    steps = [
        WorkflowStep(step_number=1, name="Criar cubo de dados",
                     sits_function="sits_cube()", python_equivalent="pystac_client + rasterio",
                     description=f"Cubo STAC: {collection}, {start_year}-{end_year}, região {region_name}."),
        WorkflowStep(step_number=2, name="Regularizar cubo",
                     sits_function="sits_regularize()", python_equivalent="rasterio + scipy",
                     description="Garantir resolução temporal regular (16 dias para Landsat)."),
        WorkflowStep(step_number=3, name="Coletar amostras de treinamento",
                     sits_function="sits_get_data()", python_equivalent="rasterio.sample()",
                     description=f"Extrair séries temporais em pontos de amostra. Classes: {', '.join(classes)}."),
        WorkflowStep(step_number=4, name="Avaliar qualidade das amostras",
                     sits_function="sits_som()", python_equivalent="sklearn.manifold.TSNE",
                     description="Verificar separabilidade e ruídos nas amostras com SOM ou t-SNE."),
        WorkflowStep(step_number=5, name="Treinar modelo",
                     sits_function=algo_info["sits_function"], python_equivalent=algo_info["sklearn_class"],
                     description=f"Treinar {algo_info['name']} com validação cruzada k-fold."),
        WorkflowStep(step_number=6, name="Classificar cubo",
                     sits_function="sits_classify()", python_equivalent="model.predict()",
                     description="Aplicar modelo treinado pixel a pixel no cubo inteiro."),
        WorkflowStep(step_number=7, name="Pós-processamento",
                     sits_function="sits_smooth()", python_equivalent="scipy.ndimage / modal filter",
                     description="Suavização bayesiana ou filtro modal para remover ruído salt-and-pepper."),
        WorkflowStep(step_number=8, name="Gerar mapa final",
                     sits_function="sits_label_classification()", python_equivalent="rasterio.write()",
                     description="Atribuir rótulos e gerar mapa classificado."),
        WorkflowStep(step_number=9, name="Avaliar acurácia",
                     sits_function="sits_accuracy()", python_equivalent="sklearn.metrics",
                     description="Matriz de confusão, Overall Accuracy, Kappa, F1 por classe."),
    ]

    sits_code = f'''library(sits)

# ========================================================
# Workflow sits completo para classificação LULC
# Região: {region_name} | Período: {start_year}-{end_year}
# Algoritmo: {algo_info["name"]}
# ========================================================

# 1. Criar cubo STAC
Sys.setenv("BDC_ACCESS_KEY" = Sys.getenv("BDC_API_KEY"))

cube <- sits_cube(
  source     = "BDC",
  collection = "{collection}",
  bands      = c({bands_r}),
  roi        = c(lon_min = {bbox[0]}, lat_min = {bbox[1]},
                 lon_max = {bbox[2]}, lat_max = {bbox[3]}),
  start_date = "{start_year}-01-01",
  end_date   = "{end_year}-12-31"
)

# 2. Carregar amostras de treinamento
# Formato CSV: longitude, latitude, start_date, end_date, label
samples <- read.csv("training_samples.csv")

# 3. Extrair séries temporais nas amostras
ts <- sits_get_data(cube = cube, samples = samples)

# 4. Avaliar qualidade das amostras
sits_som_map <- sits_som(ts)
plot(sits_som_map)

# 5. Treinar modelo ({algo_info["name"]})
model <- {algo_info["sits_function"].rstrip("()")
          if algo_info["sits_function"] else "sits_rfor"}(ts)

# 6. Classificar cubo
classified <- sits_classify(
  data       = cube,
  ml_model   = model,
  output_dir = "./classification/",
  memsize    = 8,
  multicores = 4
)

# 7. Pós-processamento (suavização bayesiana)
smoothed <- sits_smooth(classified, type = "bayes", output_dir = "./smoothed/")

# 8. Gerar mapa de rótulos
labeled <- sits_label_classification(smoothed, output_dir = "./labeled/")

# 9. Avaliar acurácia
# validation_samples <- read.csv("validation_samples.csv")
# acc <- sits_accuracy(labeled, validation = validation_samples)
# print(acc)
# plot(acc)
'''

    python_code = f'''from pystac_client import Client
import rasterio
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import os

# 1. Conectar ao BDC
client = Client.open(
    "https://data.inpe.br/bdc/stac/v1/",
    headers={{"x-api-key": os.getenv("BDC_API_KEY", "")}}
)

# 2. Buscar itens do cubo
search = client.search(
    collections=["{collection}"],
    bbox={bbox},
    datetime="{start_year}-01-01/{end_year}-12-31",
    limit=500
)
items = sorted(search.items(), key=lambda i: i.datetime)
print(f"Total de composições: {{len(items)}}")

# 3. Extrair séries temporais em pontos de amostra
# samples_df: DataFrame com colunas [lon, lat, label]
samples_df = pd.read_csv("training_samples.csv")
bands = {[band_map.get(b.lower(), b) for b in ["NDVI", "EVI"]]}

X = []  # Features: série temporal concatenada
y = []  # Labels

for _, sample in samples_df.iterrows():
    features = []
    for item in items:
        for band in bands:
            if band in item.assets:
                with rasterio.open(item.assets[band].href) as src:
                    val = list(src.sample([(sample["lon"], sample["lat"])]))[0]
                    features.append(float(val[0]))
    if len(features) == len(items) * len(bands):
        X.append(features)
        y.append(sample["label"])

X = np.array(X)
y = np.array(y)

# 4. Treinar modelo
model = RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42)
scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"Acurácia CV: {{scores.mean():.3f}} ± {{scores.std():.3f}}")

model.fit(X, y)

# 5. Classificar (para implementação pixel a pixel, ver sits ou rasterio)
# Para classificação espacial completa, iterar por blocos do raster
'''

    return ClassificationPlan(
        workflow_name=f"Classificação LULC — {region_name} ({start_year}-{end_year})",
        target_region=region_name,
        target_period=f"{start_year}-{end_year}",
        recommended_collection=collection,
        steps=steps,
        sits_r_code=sits_code,
        python_code=python_code,
        estimated_complexity="high" if len(classes) > 5 else "medium",
        notes=(
            f"Workflow completo de classificação de uso e cobertura do solo para {region_name}. "
            f"Algoritmo recomendado: {algo_info['name']}. "
            f"Classes: {', '.join(classes)}. "
            "O sits (R) oferece o pipeline mais completo e integrado com BDC."
        ),
    ).model_dump()


def get_sample_design_guide(
    region: str,
    classes: list[str],
    total_samples: int | None = None,
) -> dict[str, Any]:
    """Guia de design amostral estratificado para classificação LULC.

    Args:
        region: Nome da região/bioma.
        classes: Lista de classes LULC esperadas.
        total_samples: Total de amostras desejado. Padrão: 50 por classe (mínimo sits).
    """
    n_classes = len(classes)
    if total_samples is None:
        total_samples = max(50 * n_classes, 300)

    samples_per_class = total_samples // n_classes

    return SampleDesignGuide(
        strategy="stratified",
        minimum_samples_per_class=max(50, samples_per_class),
        recommended_classes=classes,
        tips=[
            f"Mínimo recomendado pelo sits: 50 amostras por classe (total mínimo: {50 * n_classes}).",
            f"Distribuição sugerida: ~{samples_per_class} amostras por classe ({total_samples} total).",
            "Distribuir amostras espacialmente para cobrir variabilidade da região.",
            "Coletar amostras em diferentes datas para capturar variabilidade sazonal.",
            "Usar imagens de alta resolução (Google Earth, Planet) para validação visual.",
            "Reservar 30% das amostras para validação independente.",
            "Evitar autocorrelação espacial: manter distância mínima de 2-3 pixels entre amostras.",
            "Para classes raras (ex: água), sobre-amostrar proporcionalmente.",
        ],
        sits_snippet=f'''library(sits)

# Carregar amostras de um CSV
# Formato: longitude, latitude, start_date, end_date, label
samples <- read.csv("samples.csv")

# Verificar distribuição por classe
table(samples$label)

# Extrair séries temporais
ts <- sits_get_data(cube = cube, samples = samples)

# Avaliar qualidade com SOM (Self-Organizing Map)
som <- sits_som(ts)
plot(som)

# Remover amostras ruidosas
ts_clean <- sits_som_clean(som)
''',
        python_snippet=f'''import pandas as pd
import numpy as np

# Amostras estratificadas: {samples_per_class} por classe
classes = {classes}
samples = pd.read_csv("samples.csv")

# Verificar distribuição
print(samples["label"].value_counts())

# Separar treino/validação (70/30 estratificado)
from sklearn.model_selection import train_test_split

train, val = train_test_split(
    samples, test_size=0.3, stratify=samples["label"], random_state=42
)
print(f"Treino: {{len(train)}}, Validação: {{len(val)}}")

# Verificar cobertura espacial
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 8))
for cls in classes:
    subset = train[train["label"] == cls]
    ax.scatter(subset["lon"], subset["lat"], label=cls, alpha=0.6, s=10)
ax.legend()
ax.set_title("Distribuição espacial das amostras")
plt.show()
''',
    ).model_dump()


def get_ml_algorithm_guide(use_case: str | None = None) -> dict[str, Any]:
    """Comparação de algoritmos de ML para classificação de séries temporais.

    Args:
        use_case: Caso de uso — "few_samples", "high_accuracy", "fast", "large_area", "temporal".
            Se None, retorna guia completo.
    """
    algorithms = [
        MLAlgorithmInfo(**{k: v for k, v in algo.items()})
        for algo in _ML_ALGORITHMS.values()
    ]

    recommendation = ""
    if use_case:
        uc = use_case.lower()
        if "few" in uc or "pouc" in uc:
            recommendation = (
                "Para poucos dados de treinamento (<200 amostras por classe): "
                "SVM com kernel RBF é a melhor opção. Random Forest como segunda escolha."
            )
        elif "accura" in uc or "precis" in uc:
            recommendation = (
                "Para máxima acurácia: XGBoost ou TempCNN (Deep Learning). "
                "XGBoost com tuning de hiperparâmetros geralmente atinge >90% OA."
            )
        elif "fast" in uc or "rapid" in uc:
            recommendation = (
                "Para velocidade: LightGBM > Random Forest > XGBoost. "
                "LightGBM é 5-10x mais rápido que XGBoost em datasets grandes."
            )
        elif "large" in uc or "grande" in uc:
            recommendation = (
                "Para grandes áreas (>10M pixels): LightGBM ou Random Forest. "
                "Ambos são facilmente paralelizáveis e eficientes em memória."
            )
        elif "tempor" in uc or "serie" in uc:
            recommendation = (
                "Para séries temporais: TempCNN (sits_tempcnn) é estado da arte. "
                "Alternativa: XGBoost com features temporais derivadas."
            )
        else:
            recommendation = (
                "Recomendação geral: comece com Random Forest para baseline, "
                "depois otimize com XGBoost para melhorar acurácia."
            )
    else:
        recommendation = (
            "Fluxo recomendado: (1) Random Forest como baseline rápido → "
            "(2) XGBoost para melhorar acurácia → "
            "(3) TempCNN se acurácia insuficiente e dados abundantes. "
            "Sempre validar com cross-validation k-fold (k=5)."
        )

    return MLAlgorithmGuide(
        algorithms=algorithms,
        recommendation=recommendation,
        comparison_notes=(
            "Todos os algoritmos estão disponíveis no sits (R) via sits_rfor(), "
            "sits_svm(), sits_xgboost(), sits_lightgbm(), sits_tempcnn(), sits_resnet(). "
            "Em Python, usar scikit-learn (RF, SVM), xgboost, lightgbm ou PyTorch (TempCNN)."
        ),
    ).model_dump()


def get_accuracy_assessment_guide(n_classes: int | None = None) -> dict[str, Any]:
    """Guia de avaliação de acurácia para classificação LULC.

    Args:
        n_classes: Número de classes na classificação. Padrão: 6.
    """
    if n_classes is None:
        n_classes = 6

    return AccuracyAssessmentGuide(
        metrics=[
            "Overall Accuracy (OA) — Proporção total de pixels corretamente classificados.",
            "Kappa — Concordância corrigida pelo acaso. >0.8 = excelente.",
            "User's Accuracy (UA) — Precisão por classe (1 - erro de comissão).",
            "Producer's Accuracy (PA) — Sensibilidade por classe (1 - erro de omissão).",
            "F1-Score — Média harmônica de precisão e sensibilidade por classe.",
            "Allocation Disagreement — Erro por troca de rótulos entre classes.",
            "Quantity Disagreement — Erro por diferença de proporção entre classes.",
        ],
        validation_strategy=(
            f"Para {n_classes} classes:\n"
            f"- Mínimo de amostras de validação: {50 * n_classes} (50 por classe).\n"
            f"- Amostras de validação INDEPENDENTES do treinamento (não reutilizar).\n"
            "- Amostragem estratificada proporcional à área de cada classe.\n"
            "- Cross-validation k-fold (k=5) para estimativa de variância.\n"
            "- Verificação visual em amostra aleatória de pixels classificados."
        ),
        python_snippet=f'''from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, cohen_kappa_score, f1_score
)
import numpy as np

# y_true: rótulos de validação, y_pred: predições do modelo
y_true = [...]
y_pred = [...]
classes = {["Class_" + str(i+1) for i in range(n_classes)]}

# 1. Matriz de confusão
cm = confusion_matrix(y_true, y_pred)
print("Matriz de Confusão:")
print(cm)

# 2. Overall Accuracy
oa = accuracy_score(y_true, y_pred)
print(f"Overall Accuracy: {{oa:.4f}}")

# 3. Kappa
kappa = cohen_kappa_score(y_true, y_pred)
print(f"Kappa: {{kappa:.4f}}")

# 4. Relatório por classe (Precision = UA, Recall = PA, F1)
print(classification_report(y_true, y_pred, target_names=classes))

# 5. F1 macro (média ponderada por classe)
f1_macro = f1_score(y_true, y_pred, average="macro")
print(f"F1-Score (macro): {{f1_macro:.4f}}")
''',
        sits_snippet=f'''library(sits)

# Avaliação de acurácia no sits
# Requer amostras de validação independentes

# 1. Classificar pontos de validação
validation <- read.csv("validation_samples.csv")
val_ts <- sits_get_data(cube, validation)
val_pred <- sits_classify(val_ts, ml_model = model)

# 2. Calcular acurácia
acc <- sits_accuracy(val_pred)

# 3. Visualizar
print(acc)
plot(acc)

# 4. Relatório completo
# acc$overall  → OA e Kappa
# acc$byClass  → UA, PA e F1 por classe
''',
    ).model_dump()


def generate_sits_classification_code(
    collection_id: str,
    region: str | list[float],
    algorithm: str = "random_forest",
    classes: list[str] | None = None,
    start_year: int = 2020,
    end_year: int = 2023,
) -> str:
    """Gera código R sits completo para classificação LULC.

    Args:
        collection_id: ID da coleção BDC.
        region: Nome da região/bioma ou bbox.
        algorithm: Algoritmo — "random_forest", "svm", "xgboost", "lightgbm", "deep_learning".
        classes: Lista de classes LULC. Padrão: ["Forest", "Pasture", "Agriculture", "Water"].
        start_year: Ano inicial.
        end_year: Ano final.
    """
    if classes is None:
        classes = ["Forest", "Pasture", "Agriculture", "Water"]

    if isinstance(region, str):
        bbox = resolve_bbox(region) or [-53.2, -19.5, -45.9, -12.4]
        region_name = region
    else:
        bbox = region
        region_name = "custom"

    algo_info = _ML_ALGORITHMS.get(algorithm, _ML_ALGORITHMS["random_forest"])
    raw_fn = algo_info.get("sits_function", "sits_rfor()")
    # Para deep_learning que tem "sits_tempcnn() / sits_resnet()", usar só o primeiro
    sits_fn = raw_fn.split("/")[0].strip()

    band_map = COLLECTION_BAND_MAPPING.get(collection_id, {})
    available = [band_map.get(b, b) for b in ["ndvi", "evi", "red", "nir", "blue", "green"] if b in band_map]
    if not available:
        available = ["NDVI", "EVI"]
    bands_r = ", ".join(f'"{b}"' for b in available)

    classes_r = ", ".join(f'"{c}"' for c in classes)

    return f'''library(sits)

# ==============================================================
# Classificação LULC completa com sits
# Coleção: {collection_id} | Região: {region_name}
# Algoritmo: {algo_info["name"]}
# Classes: {", ".join(classes)}
# ==============================================================

# 1. Configuração
Sys.setenv("BDC_ACCESS_KEY" = Sys.getenv("BDC_API_KEY"))

# 2. Criar cubo
cube <- sits_cube(
  source     = "BDC",
  collection = "{collection_id}",
  bands      = c({bands_r}),
  roi        = c(lon_min = {bbox[0]}, lat_min = {bbox[1]},
                 lon_max = {bbox[2]}, lat_max = {bbox[3]}),
  start_date = "{start_year}-01-01",
  end_date   = "{end_year}-12-31"
)

cat("Cubo:", length(sits_timeline(cube)), "datas\\n")

# 3. Carregar amostras de treinamento
# CSV: longitude, latitude, start_date, end_date, label
# Labels devem ser: {classes_r}
samples <- read.csv("training_samples.csv")

# 4. Extrair séries temporais
ts <- sits_get_data(cube = cube, samples = samples)
cat("Amostras:", nrow(ts), "\\n")

# 5. Avaliar qualidade (SOM)
som <- sits_som(ts)
plot(som)
ts_clean <- sits_som_clean(som)

# 6. Treinar modelo ({algo_info["name"]})
model <- {sits_fn.rstrip("()")}(ts_clean)

# 7. Classificar
classified <- sits_classify(
  data       = cube,
  ml_model   = model,
  output_dir = "./classification/",
  memsize    = 8,
  multicores = 4
)

# 8. Pós-processamento (suavização bayesiana)
smoothed <- sits_smooth(
  cube       = classified,
  type       = "bayes",
  output_dir = "./smoothed/"
)

# 9. Rotular mapa
labeled <- sits_label_classification(
  cube       = smoothed,
  output_dir = "./labeled/"
)

# 10. Plotar resultado
plot(labeled)

# 11. Avaliar acurácia (com amostras de validação)
# val_samples <- read.csv("validation_samples.csv")
# val_ts <- sits_get_data(cube, val_samples)
# acc <- sits_accuracy(sits_classify(val_ts, model))
# print(acc)
'''
