# Exemplos de Uso do Plugin Smart OBIA

Este documento fornece exemplos práticos de como usar o plugin Smart OBIA em diferentes cenários.

## Exemplo 1: Segmentação SLIC Básica

### Cenário
Você tem uma imagem multiespectral de satélite (Sentinel-2) e deseja segmentá-la em 100 superpixels para análise de cobertura do solo.

### Passos

1. **Abrir a imagem no QGIS**
   ```
   Arquivo > Abrir Camada Raster > selecionar imagem Sentinel-2
   ```

2. **Acessar o algoritmo**
   ```
   Processamento > Caixa de Ferramentas > Smart OBIA > Smart OBIA Segmentation
   ```

3. **Configurar parâmetros**
   - **Input Raster Layer**: Selecione a camada Sentinel-2
   - **Segmentation Method**: SLIC
   - **Number of Segments**: 100
   - **Compactness**: 10.0
   - **Output Segmentation Raster**: `segmentacao_slic.tif`
   - **Output Segment Vectors**: `segmentacao_slic.shp`

4. **Executar**
   - Clique em "Executar"
   - Aguarde a conclusão

5. **Visualizar resultados**
   - A camada vetorial será adicionada automaticamente ao mapa
   - Abra a tabela de atributos para ver as features extraídas

### Saída Esperada

| segment_id | area_pixels | band_1_mean | band_1_std | band_2_mean | band_2_std | ... |
|------------|-------------|-------------|------------|-------------|------------|-----|
| 1          | 1250        | 145.3       | 25.4       | 156.2       | 28.1       | ... |
| 2          | 980         | 78.5        | 15.2       | 82.1        | 18.3       | ... |
| 3          | 1100        | 200.1       | 35.6       | 210.5       | 38.2       | ... |

## Exemplo 2: Segmentação K-Means para Classificação Espectral

### Cenário
Você deseja classificar uma imagem em 5 classes espectrais distintas usando K-Means clustering.

### Passos

1. **Preparar a imagem**
   - Certifique-se de que as bandas estão normalizadas
   - Se necessário, aplique uma máscara para remover áreas de interesse

2. **Acessar o algoritmo**
   ```
   Processamento > Caixa de Ferramentas > Smart OBIA > Smart OBIA Segmentation
   ```

3. **Configurar parâmetros**
   - **Input Raster Layer**: Selecione a imagem
   - **Segmentation Method**: K-Means
   - **Number of Clusters**: 5
   - **Output Segmentation Raster**: `classificacao_kmeans.tif`
   - **Output Segment Vectors**: `classificacao_kmeans.shp`

4. **Executar e analisar**
   - Execute o algoritmo
   - Visualize os clusters resultantes
   - Use a tabela de atributos para entender as características espectrais de cada cluster

### Interpretação dos Resultados

Os valores `band_X_mean` representam a assinatura espectral média de cada cluster:
- Valores altos em bandas do infravermelho próximo (NIR) = vegetação
- Valores altos em bandas visíveis = solo ou água
- Padrões espectrais ajudam a identificar tipos de cobertura

## Exemplo 3: Segmentação Watershed para Delineamento de Objetos

### Cenário
Você tem um MDE (Modelo Digital de Elevação) e deseja delinear bacias hidrográficas.

### Passos

1. **Preparar o MDE**
   - Carregue o MDE no QGIS
   - Aplique suavização se necessário (Raster > Análise > Suavizar)

2. **Acessar o algoritmo**
   ```
   Processamento > Caixa de Ferramentas > Smart OBIA > Smart OBIA Segmentation
   ```

3. **Configurar parâmetros**
   - **Input Raster Layer**: Selecione o MDE
   - **Segmentation Method**: Watershed
   - **Marker Band**: 1 (primeira banda do MDE)
   - **Output Segmentation Raster**: `bacias.tif`
   - **Output Segment Vectors**: `bacias.shp`

4. **Analisar bacias**
   - Visualize as bacias delineadas
   - Use a tabela de atributos para calcular área de cada bacia
   - Exporte para análise hidrológica

## Exemplo 4: Análise de Texturas com GLCM

### Cenário
Você deseja extrair features de textura de uma imagem para análise de mudanças.

### Passos

1. **Segmentar a imagem**
   - Use SLIC com número moderado de segmentos (50-200)

2. **Extrair features**
   - As features radiométricas (média, std, min, max) já são calculadas
   - Para texturas GLCM, você pode usar a tabela de atributos para cálculos adicionais

3. **Análise de mudanças**
   - Compare features entre datas diferentes
   - Identifique segmentos com mudanças significativas

### Exemplo de Análise em Python

```python
import geopandas as gpd
import pandas as pd

# Carregar camada vetorial
segmentos = gpd.read_file('segmentacao_slic.shp')

# Calcular índice de mudança
segmentos['mudanca'] = abs(segmentos['band_1_mean'] - segmentos['band_2_mean'])

# Filtrar segmentos com mudança significativa
mudancas_significativas = segmentos[segmentos['mudanca'] > 50]

# Exportar resultado
mudancas_significativas.to_file('mudancas.shp')
```

## Exemplo 5: Processamento em Lote (Batch Processing)

### Cenário
Você tem múltiplas imagens e deseja segmentá-las todas com os mesmos parâmetros.

### Passos usando o Model Designer

1. **Abrir Model Designer**
   ```
   Processamento > Model Designer
   ```

2. **Criar modelo**
   - Adicione "Input Raster Layer" como entrada
   - Adicione algoritmo "Smart OBIA Segmentation"
   - Configure parâmetros fixos
   - Salve o modelo como `batch_segmentacao.model3`

3. **Executar em lote**
   ```
   Processamento > Batch Processing > Selecione o modelo
   ```

4. **Configurar lote**
   - Adicione todas as imagens de entrada
   - Configure diretórios de saída
   - Execute

## Exemplo 6: Integração com Classificação

### Cenário
Você deseja usar os segmentos como base para classificação supervisionada.

### Passos

1. **Segmentar a imagem**
   ```
   Use SLIC com parâmetros apropriados
   ```

2. **Extrair features dos segmentos**
   ```
   A tabela de atributos já contém as features
   ```

3. **Treinar classificador**
   ```python
   from sklearn.ensemble import RandomForestClassifier
   import geopandas as gpd
   
   # Carregar dados
   segmentos = gpd.read_file('segmentacao_slic.shp')
   
   # Preparar features
   feature_cols = [col for col in segmentos.columns if 'band_' in col]
   X = segmentos[feature_cols]
   
   # Treinar (assumindo que você tem labels)
   clf = RandomForestClassifier()
   clf.fit(X, segmentos['classe'])
   
   # Prever
   segmentos['classe_predita'] = clf.predict(X)
   ```

4. **Visualizar classificação**
   - Carregue a camada no QGIS
   - Aplique simbologia baseada em `classe_predita`

## Dicas e Boas Práticas

### 1. Escolha do Algoritmo

| Algoritmo | Melhor para | Vantagens | Desvantagens |
|-----------|------------|-----------|--------------|
| SLIC | Análise de texturas, mudanças | Rápido, regular | Menos flexível |
| K-Means | Classificação espectral | Flexível, interpretável | Pode ser lento |
| Watershed | Delineamento de objetos | Preciso, baseado em gradiente | Sensível a ruído |

### 2. Ajuste de Parâmetros

**SLIC**
- Aumentar segmentos = mais detalhe, mais tempo
- Aumentar compactness = segmentos mais regulares

**K-Means**
- Aumentar clusters = mais classes, mais tempo
- Use PCA para reduzir dimensionalidade se necessário

**Watershed**
- Escolha banda com bom contraste para marcadores
- Aplique suavização antes se houver muito ruído

### 3. Pré-processamento

```python
# Normalizar imagem
from rasterio.plot import show
import numpy as np

# Remover outliers
data_clipped = np.clip(data, np.percentile(data, 2), np.percentile(data, 98))

# Normalizar para 0-1
data_normalized = (data_clipped - data_clipped.min()) / (data_clipped.max() - data_clipped.min())
```

### 4. Validação de Resultados

```python
# Calcular métricas de qualidade
from skimage.metrics import adapted_rand_error

# Comparar com segmentação de referência
error = adapted_rand_error(referencia, resultado)
print(f"Erro Rand Adaptado: {error}")
```

## Troubleshooting

### Problema: Segmentação muito grosseira
**Solução**: Aumente o número de segmentos/clusters

### Problema: Segmentação muito fina
**Solução**: Diminua o número de segmentos/clusters

### Problema: Segmentos irregulares (SLIC)
**Solução**: Aumente o parâmetro Compactness

### Problema: Processamento muito lento
**Solução**: Reduza o tamanho da imagem ou número de segmentos

## Referências

- [QGIS Processing Documentation](https://docs.qgis.org/latest/en/docs/user_manual/processing/index.html)
- [scikit-image Segmentation](https://scikit-image.org/docs/stable/api/skimage.segmentation.html)
- [Object-Based Image Analysis](https://en.wikipedia.org/wiki/Object-based_image_analysis)

---

Para mais exemplos e suporte, consulte a documentação completa em README.md
