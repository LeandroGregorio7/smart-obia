# Documentação dos Módulos do Smart OBIA Plugin

## Visão Geral

O plugin Smart OBIA agora possui **4 módulos principais** para processamento completo de imagens multiespectrais:

```
Smart OBIA Plugin
├── 1. Band Stacking (Empilhamento)
├── 2. Radiometric Indices (Índices)
├── 3. Texture (Texturas GLCM)
└── 4. Segmentation (Segmentação)
```

## 1. Band Stacking (Empilhamento de Bandas)

### Objetivo
Combinar múltiplas camadas raster em um único arquivo multiband.

### Quando Usar
- Organizar bandas de diferentes fontes
- Preparar dados para processamento posterior
- Criar composições personalizadas de bandas

### Parâmetros
- **Input Raster Layers**: Selecione múltiplas camadas raster
- **Output Stacked Raster**: Caminho do arquivo de saída

### Exemplo de Uso
```
1. Importe as bandas individuais do Sentinel-2
2. Selecione todas as bandas de interesse
3. Execute o algoritmo
4. Resultado: Um arquivo GeoTIFF com todas as bandas organizadas
```

### Saída
- Arquivo GeoTIFF multiband com todas as bandas empilhadas
- Preserva georreferenciamento e projeção

---

## 2. Radiometric Indices (Índices Radiométricos)

### Objetivo
Calcular índices espectrais que realçam características específicas da imagem.

### Índices Disponíveis

#### Vegetação
| Índice | Fórmula | Interpretação |
|--------|---------|---------------|
| **NDVI** | (NIR - Red) / (NIR + Red) | Vigor da vegetação (-1 a +1) |
| **SAVI** | ((NIR - Red) * (1 + L)) / (NIR + Red + L) | NDVI ajustado para solo (L=0.5) |
| **GNDVI** | (NIR - Green) / (NIR + Green) | NDVI usando banda verde |
| **EVI** | 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1) | Índice de vegetação melhorado |
| **ARVI** | (NIR - Red_corrected) / (NIR + Red_corrected) | Resistente a atmosfera |

#### Água
| Índice | Fórmula | Interpretação |
|--------|---------|---------------|
| **NDWI** | (NIR - SWIR) / (NIR + SWIR) | Conteúdo de água (-1 a +1) |
| **MNDWI** | (Green - SWIR) / (Green + SWIR) | NDWI modificado para água |

#### Construído/Solo
| Índice | Fórmula | Interpretação |
|--------|---------|---------------|
| **NDBI** | (SWIR - NIR) / (SWIR + NIR) | Áreas construídas |
| **NDII** | (NIR - SWIR) / (NIR + SWIR) | Índice de infrared |
| **NDMI** | (NIR - SWIR) / (NIR + SWIR) | Umidade do solo |

### Parâmetros
- **Input Raster Layer**: Imagem multiespectral
- **Red Band**: Banda vermelha (1-indexed)
- **NIR Band**: Banda infravermelha próxima
- **Green Band**: Banda verde
- **Blue Band**: Banda azul
- **SWIR Band**: Banda infravermelha de ondas curtas
- **Indices to Calculate**: Selecione quais índices calcular
- **Output Indices Raster**: Arquivo de saída

### Exemplo de Uso
```
1. Carregue uma imagem Sentinel-2
2. Configure as bandas (Red=4, NIR=8, Green=3, Blue=2, SWIR=11)
3. Selecione NDVI, NDWI e NDBI
4. Execute
5. Resultado: Arquivo com 3 bandas (NDVI, NDWI, NDBI)
```

### Interpretação dos Resultados

**NDVI:**
- -1.0 a -0.1: Água, nuvens
- -0.1 a 0.0: Solo nu
- 0.0 a 0.3: Vegetação esparsa
- 0.3 a 0.6: Vegetação moderada
- 0.6 a 1.0: Vegetação densa

**NDWI:**
- -1.0 a -0.5: Vegetação densa
- -0.5 a 0.0: Solo/construído
- 0.0 a 0.5: Água superficial
- 0.5 a 1.0: Água profunda

---

## 3. Texture (Texturas GLCM)

### Objetivo
Calcular características de textura usando GLCM (Gray Level Co-occurrence Matrix).

### Conceito
GLCM analisa a relação espacial entre pixels para quantificar texturas na imagem.

### Features de Textura Disponíveis

| Feature | Interpretação | Intervalo |
|---------|---------------|-----------|
| **Contrast** | Diferença local entre pixels | 0 a ∞ |
| **Dissimilarity** | Média das diferenças | 0 a ∞ |
| **Homogeneity** | Proximidade dos valores | 0 a 1 |
| **Energy** | Uniformidade/ordem | 0 a 1 |
| **Correlation** | Dependência linear | -1 a 1 |
| **ASM** | Angular Second Moment | 0 a 1 |

### Parâmetros
- **Input Raster Layer**: Imagem para análise
- **Band to Process**: Qual banda usar
- **Window Size**: Tamanho da janela (3-51 pixels)
- **Distance**: Distância para GLCM (1-10)
- **Angles**: Direções (0°, 45°, 90°, 135°, ou Todas)
- **Texture Features**: Quais features calcular
- **Output Texture Raster**: Arquivo de saída

### Exemplo de Uso
```
1. Carregue uma imagem de satélite
2. Selecione a banda de interesse (ex: banda vermelha)
3. Configure: Window Size=5, Distance=1, Angles=All
4. Selecione: Contrast, Homogeneity, Energy
5. Execute
6. Resultado: Arquivo com 12 bandas (3 features × 4 ângulos)
```

### Interpretação dos Resultados

**Contrast Alto:**
- Indica mudanças abruptas de valores
- Texturas ásperas/heterogêneas

**Homogeneity Alto:**
- Indica valores similares próximos
- Texturas suaves/homogêneas

**Energy Alto:**
- Indica padrões repetitivos
- Texturas ordenadas

**Correlation Alto:**
- Indica dependência linear entre pixels
- Estruturas lineares

---

## 4. Segmentation (Segmentação)

### Objetivo
Dividir a imagem em segmentos homogêneos e extrair features.

### Algoritmos de Segmentação

#### SLIC (Simple Linear Iterative Clustering)
- **Vantagem**: Rápido, segmentos regulares
- **Desvantagem**: Menos flexível
- **Ideal para**: Análise de texturas, mudanças
- **Parâmetros**:
  - Número de Segmentos: 10-10000
  - Compactness: 0.1-100.0

#### K-Means
- **Vantagem**: Flexível, interpretável
- **Desvantagem**: Pode ser lento
- **Ideal para**: Classificação espectral
- **Parâmetros**:
  - Número de Clusters: 2-500

#### Watershed
- **Vantagem**: Preciso, baseado em gradiente
- **Desvantagem**: Sensível a ruído
- **Ideal para**: Delineamento de objetos
- **Parâmetros**:
  - Banda de Marcador: 1-100

### Parâmetros Comuns
- **Input Raster Layer**: Imagem para segmentar
- **Segmentation Method**: SLIC, K-Means ou Watershed
- **Output Segmentation Raster**: Arquivo raster com IDs
- **Output Segment Vectors**: Arquivo shapefile com polígonos

### Features Extraídas

**Radiométricas (por banda):**
- Mean: Valor médio
- Std: Desvio padrão
- Min: Valor mínimo
- Max: Valor máximo

**Espaciais:**
- area_pixels: Número de pixels
- perimeter: Perímetro (simplificado)

### Exemplo de Uso
```
1. Carregue a imagem empilhada
2. Calcule índices (NDVI, NDWI)
3. Calcule texturas (Contrast, Homogeneity)
4. Execute segmentação SLIC com 100 segmentos
5. Resultado: Raster + Shapefile com features
```

---

## Fluxo Completo de Processamento OBIA

### Passo 1: Preparação
```
Imagens Sentinel-2 (múltiplas bandas)
        ↓
Band Stacking
        ↓
Imagem multiband organizada
```

### Passo 2: Pré-processamento
```
Imagem multiband
        ↓
Radiometric Indices (NDVI, NDWI, NDBI)
        ↓
Texture Features (GLCM)
        ↓
Imagem com índices e texturas
```

### Passo 3: Segmentação
```
Imagem com índices e texturas
        ↓
Segmentation (SLIC/K-Means/Watershed)
        ↓
Segmentos com features extraídas
```

### Passo 4: Análise
```
Segmentos com features
        ↓
Classificação / Análise Estatística
        ↓
Resultados finais
```

---

## Recomendações de Uso

### Para Análise de Vegetação
1. Stack: Bandas R, G, B, NIR, SWIR
2. Índices: NDVI, SAVI, EVI
3. Textura: Contrast, Homogeneity
4. Segmentação: SLIC (100-200 segmentos)

### Para Detecção de Água
1. Stack: Bandas R, G, B, NIR, SWIR
2. Índices: NDWI, MNDWI
3. Textura: Energy, Homogeneity
4. Segmentação: K-Means (5-10 clusters)

### Para Análise Urbana
1. Stack: Bandas R, G, B, NIR, SWIR
2. Índices: NDBI, NDVI
3. Textura: Contrast, Dissimilarity
4. Segmentação: Watershed

### Para Análise de Mudanças
1. Stack: Bandas multitemporais
2. Índices: NDVI, NDWI (para cada data)
3. Textura: Cálcular para cada data
4. Segmentação: Usar mesmos parâmetros para ambas

---

## Otimizações e Performance

### Dicas para Melhor Performance
1. **Redimensione imagens grandes** antes de processar
2. **Use apenas bandas necessárias** no stacking
3. **Ajuste window size** para texturas (5-7 é geralmente bom)
4. **Reduza número de segmentos** se processar for lento

### Complexidade Computacional
| Operação | Complexidade | Tempo Aprox. |
|----------|-------------|-------------|
| Stacking | O(n) | < 1s |
| Índices | O(n) | 1-5s |
| Texturas | O(n*w²) | 10-60s |
| Segmentação | O(n*k*i) | 5-30s |

---

## Troubleshooting

### Erro: "Band index out of range"
**Solução**: Verifique o número de bandas da imagem e ajuste os índices

### Erro: "ModuleNotFoundError: No module named 'skimage'"
**Solução**: Instale scikit-image via OSGeo4W Shell

### Processamento muito lento
**Solução**: Reduza tamanho da imagem ou número de segmentos

### Segmentos muito pequenos/grandes
**Solução**: Ajuste número de segmentos ou compactness

---

## Referências

- [QGIS Processing Framework](https://docs.qgis.org/latest/en/docs/user_manual/processing/)
- [scikit-image Documentation](https://scikit-image.org/)
- [GLCM Texture Features](https://en.wikipedia.org/wiki/Co-occurrence_matrix)
- [Spectral Indices](https://www.indexdatabase.de/)

---

**Versão**: 0.2.0  
**Data**: Maio 2026  
**Status**: Completo
