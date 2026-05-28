# Documentação Técnica - Smart OBIA Plugin

## Visão Geral da Arquitetura

O plugin Smart OBIA segue a arquitetura padrão de plugins QGIS com suporte ao Processing Framework. A estrutura é organizada em camadas:

```
┌─────────────────────────────────────────────────────┐
│         QGIS User Interface                          │
├─────────────────────────────────────────────────────┤
│         Processing Framework                         │
├─────────────────────────────────────────────────────┤
│    SmartOBIAProvider (processing_provider.py)        │
├─────────────────────────────────────────────────────┤
│  SegmentationAlgorithm (segmentation_algorithm.py)  │
├─────────────────────────────────────────────────────┤
│  Core Processing (SLIC, K-Means, Watershed)        │
├─────────────────────────────────────────────────────┤
│  Dependencies (scikit-image, scikit-learn, scipy)   │
└─────────────────────────────────────────────────────┘
```

## Componentes Principais

### 1. Plugin Principal (`smart_obia_plugin.py`)

**Responsabilidades:**
- Inicialização do plugin no QGIS
- Registro do provedor de processamento
- Gerenciamento do ciclo de vida do plugin

**Métodos principais:**
- `__init__(iface)`: Inicializa o plugin com a interface QGIS
- `initGui()`: Registra o provedor de processamento
- `unload()`: Remove o provedor ao descarregar o plugin

### 2. Provedor de Processamento (`processing_provider.py`)

**Responsabilidades:**
- Registrar todos os algoritmos disponíveis
- Fornecer metadados do provedor
- Gerenciar o ciclo de vida dos algoritmos

**Métodos principais:**
- `loadAlgorithms()`: Carrega todos os algoritmos disponíveis
- `id()`: Retorna ID único do provedor
- `name()`: Retorna nome legível do provedor

### 3. Algoritmo de Segmentação (`segmentation_algorithm.py`)

**Responsabilidades:**
- Implementar a interface `QgsProcessingAlgorithm`
- Gerenciar parâmetros de entrada/saída
- Executar processamento de segmentação
- Extrair features dos segmentos

**Métodos principais:**
- `initAlgorithm()`: Define parâmetros do algoritmo
- `processAlgorithm()`: Executa o processamento
- `_read_raster()`: Lê dados raster
- `_segment_slic()`: Segmentação SLIC
- `_segment_kmeans()`: Segmentação K-Means
- `_segment_watershed()`: Segmentação Watershed
- `_save_raster()`: Salva raster de segmentação
- `_create_vector_layer()`: Cria camada vetorial com features

## Fluxo de Processamento

### 1. Leitura de Dados

```python
def _read_raster(self, raster_layer):
    """
    Lê dados raster em formato numpy array
    
    Entrada: QgsRasterLayer
    Saída: numpy.ndarray de forma (altura, largura, bandas)
    """
    provider = raster_layer.dataProvider()
    # Itera sobre cada banda
    # Converte para numpy array
    # Retorna array 3D
```

**Características:**
- Suporta múltiplas bandas
- Preserva metadados geográficos
- Normaliza dados para float32

### 2. Segmentação

#### SLIC (Simple Linear Iterative Clustering)

```python
def _segment_slic(self, data, num_segments, compactness):
    """
    Segmentação SLIC usando scikit-image
    
    Parâmetros:
    - data: numpy array (altura, largura, bandas)
    - num_segments: número desejado de segmentos
    - compactness: regularidade espacial (0.1-100)
    
    Saída: numpy array de IDs de segmentos
    """
    # Usa primeiras 3 bandas ou todas se < 3
    # Normaliza para 0-255
    # Aplica SLIC
    # Retorna segmentos com IDs começando em 1
```

**Algoritmo:**
1. Inicializa centros de cluster em grid regular
2. Itera atualizando clusters baseado em similaridade espectral + distância espacial
3. Refina iterativamente
4. Retorna mapa de segmentos

**Complexidade:**
- Tempo: O(n * k * i) onde n=pixels, k=segmentos, i=iterações
- Espaço: O(n)

#### K-Means

```python
def _segment_kmeans(self, data, num_clusters):
    """
    Segmentação K-Means usando scikit-learn
    
    Parâmetros:
    - data: numpy array (altura, largura, bandas)
    - num_clusters: número de clusters
    
    Saída: numpy array de IDs de clusters
    """
    # Reshape para (n_pixels, n_bands)
    # Remove valores NaN
    # Aplica K-Means
    # Reconstrói mapa de segmentação
```

**Algoritmo:**
1. Inicializa k centros aleatoriamente
2. Atribui cada pixel ao centro mais próximo
3. Atualiza centros
4. Repete até convergência

**Complexidade:**
- Tempo: O(n * k * i * d) onde d=dimensões
- Espaço: O(n * d)

#### Watershed

```python
def _segment_watershed(self, data, marker_band):
    """
    Segmentação Watershed usando scikit-image
    
    Parâmetros:
    - data: numpy array (altura, largura, bandas)
    - marker_band: índice da banda para marcadores
    
    Saída: numpy array de IDs de segmentos
    """
    # Extrai banda de marcador
    # Normaliza
    # Cria marcadores de mínimos locais
    # Cria mapa de elevação
    # Aplica watershed
```

**Algoritmo:**
1. Cria mapa de elevação (gradiente)
2. Identifica mínimos locais como marcadores
3. Expande marcadores usando watershed
4. Retorna segmentos

**Complexidade:**
- Tempo: O(n log n)
- Espaço: O(n)

### 3. Extração de Features

Para cada segmento, o algoritmo calcula:

#### Features Radiométricas

```python
for band_idx in range(raster_data.shape[2]):
    band_data = raster_data[:, :, band_idx]
    segment_values = band_data[mask]
    
    stats = {
        'mean': np.nanmean(segment_values),
        'std': np.nanstd(segment_values),
        'min': np.nanmin(segment_values),
        'max': np.nanmax(segment_values)
    }
```

**Interpretação:**
- **Mean**: Valor espectral médio (assinatura espectral)
- **Std**: Variabilidade espectral dentro do segmento
- **Min/Max**: Intervalo dinâmico do segmento

#### Features Espaciais

```python
area_pixels = np.sum(mask)
y_coords, x_coords = np.where(mask)
perimeter = len(np.where(np.diff(mask.astype(int), axis=0))[0])
```

**Interpretação:**
- **Area**: Tamanho do objeto em pixels
- **Perimeter**: Comprimento do perímetro (simplificado)

### 4. Criação de Camada Vetorial

```python
def _create_vector_layer(self, segments, raster_data, output_path, reference_raster):
    """
    Cria camada vetorial com features extraídas
    
    Processo:
    1. Cria camada em memória
    2. Define campos de atributos
    3. Para cada segmento:
       - Calcula features
       - Cria geometria (bounding box)
       - Adiciona feature
    4. Salva em arquivo Shapefile
    """
```

**Campos de Atributos:**
- `segment_id`: ID único do segmento
- `area_pixels`: Número de pixels
- `perimeter`: Perímetro (simplificado)
- `band_X_mean`: Média da banda X
- `band_X_std`: Desvio padrão da banda X
- `band_X_min`: Mínimo da banda X
- `band_X_max`: Máximo da banda X

### 5. Salvamento de Resultados

#### Raster de Segmentação

```python
def _save_raster(self, segments, output_path, reference_raster):
    """
    Salva raster de segmentação usando GDAL
    
    Características:
    - Formato: GeoTIFF
    - Tipo de dados: UInt32
    - Preserva geotransformação e projeção
    """
```

#### Camada Vetorial

```python
# Salva como Shapefile
QgsVectorFileWriter.writeAsVectorFormatV3(
    layer,
    output_path,
    context,
    save_options
)
```

## Tratamento de Dados

### Normalização

```python
# Para SLIC (0-255)
image_min = image.min(axis=(0, 1))
image_max = image.max(axis=(0, 1))
image_normalized = 255 * (image - image_min) / (image_max - image_min + 1e-8)

# Para K-Means/Watershed (0-1)
data_normalized = (data - data_min) / (data_max - data_min + 1e-8)
```

### Tratamento de NaN

```python
# Usa np.nanmean, np.nanstd, np.nanmin, np.nanmax
# Cria máscara de valores válidos
valid_mask = ~np.isnan(pixels).any(axis=1)
```

### Tratamento de Múltiplas Bandas

```python
# SLIC: usa primeiras 3 bandas ou todas se < 3
if data.shape[2] >= 3:
    image = data[:, :, :3]
else:
    image = data[:, :, :data.shape[2]]

# K-Means: usa todas as bandas
pixels = data.reshape(-1, bands)

# Watershed: usa banda específica para marcadores
marker_data = data[:, :, marker_band]
```

## Integração com QGIS

### Processing Framework

O plugin se integra com o QGIS Processing Framework através de:

1. **Provider**: Registra o provedor em `QgsApplication.processingRegistry()`
2. **Algorithm**: Implementa `QgsProcessingAlgorithm`
3. **Parameters**: Define entrada/saída usando `QgsProcessingParameter*`
4. **Execution**: Implementa `processAlgorithm()` para execução

### Feedback

```python
feedback.pushInfo('Mensagem informativa')
feedback.reportError('Mensagem de erro')
feedback.setProgress(50)  # 0-100
```

### Contexto

O contexto fornece:
- Transformação de coordenadas
- Acesso a projetos
- Configurações de processamento

## Performance e Otimizações

### Complexidade Algorítmica

| Algoritmo | Tempo | Espaço | Ideal para |
|-----------|-------|--------|-----------|
| SLIC | O(n*k*i) | O(n) | Imagens grandes |
| K-Means | O(n*k*i*d) | O(n*d) | Dados espectrais |
| Watershed | O(n log n) | O(n) | Imagens pequenas |

### Otimizações Implementadas

1. **Uso de numpy**: Operações vetorizadas
2. **Mascaramento booleano**: Evita loops
3. **Normalização eficiente**: Usa operações em lote
4. **Tratamento de NaN**: Usa funções nan-aware

### Limitações de Performance

1. **Imagens grandes**: > 5000x5000 pixels podem ser lentas
2. **Muitas bandas**: > 50 bandas aumentam tempo
3. **Muitos segmentos**: > 1000 segmentos aumentam tempo

### Recomendações

```python
# Para imagens grandes
# 1. Redimensione antes de processar
from skimage.transform import resize
small_image = resize(image, (image.shape[0]//2, image.shape[1]//2))

# 2. Use menos segmentos
num_segments = 50  # em vez de 1000

# 3. Use apenas bandas necessárias
image_subset = image[:, :, [0, 2, 4]]  # RGB + NIR
```

## Tratamento de Erros

### Erros Comuns

```python
# Erro: Módulo não encontrado
try:
    from skimage import segmentation
except ImportError:
    feedback.reportError('scikit-image não instalado')
    return {}

# Erro: Dados inválidos
if raster_data is None:
    feedback.reportError('Falha ao ler dados raster')
    return {}

# Erro: Segmentação falhou
if segments is None:
    feedback.reportError('Segmentação falhou')
    return {}
```

### Validação de Entrada

```python
# Validar número de segmentos
if num_segments < 10 or num_segments > 10000:
    feedback.reportError('Número de segmentos fora do intervalo')
    return {}

# Validar banda de marcador
if marker_band < 1 or marker_band > raster_data.shape[2]:
    feedback.reportError('Banda de marcador inválida')
    return {}
```

## Extensibilidade

### Adicionar Novo Algoritmo

```python
# 1. Criar método no SegmentationAlgorithm
def _segment_novo_algoritmo(self, data, param1, param2):
    """Implementar novo algoritmo"""
    # Lógica aqui
    return segments

# 2. Adicionar parâmetro em initAlgorithm()
self.addParameter(
    QgsProcessingParameterEnum(
        'NOVO_ALGORITMO',
        'Novo Algoritmo',
        options=['Algoritmo1', 'Algoritmo2']
    )
)

# 3. Adicionar branch em processAlgorithm()
elif method == 3:  # Novo algoritmo
    segments = self._segment_novo_algoritmo(raster_data, param1, param2)
```

### Adicionar Nova Feature

```python
# 1. Calcular feature
feature_value = calculate_feature(segment_values)

# 2. Adicionar campo
fields.append(QgsField('nova_feature', QVariant.Double))

# 3. Adicionar valor
attributes.append(feature_value)
```

## Testes

### Executar Testes

```bash
python -m pytest tests.py -v
python -m pytest tests.py::TestSegmentationAlgorithm -v
```

### Cobertura de Testes

```bash
pip install pytest-cov
pytest tests.py --cov=smart_obia --cov-report=html
```

## Debugging

### Ativar Modo Debug

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f'Dados raster shape: {raster_data.shape}')
logger.debug(f'Segmentos únicos: {np.unique(segments)}')
```

### Inspecionar Dados

```python
# No QGIS Python Console
from smart_obia.algorithms.segmentation_algorithm import SegmentationAlgorithm
algo = SegmentationAlgorithm()

# Testar leitura
layer = iface.activeLayer()
data = algo._read_raster(layer)
print(f'Shape: {data.shape}')
print(f'Min: {data.min()}, Max: {data.max()}')
```

## Referências

- [QGIS Processing Framework](https://docs.qgis.org/latest/en/docs/user_manual/processing/index.html)
- [scikit-image Segmentation](https://scikit-image.org/docs/stable/api/skimage.segmentation.html)
- [scikit-learn Clustering](https://scikit-learn.org/stable/modules/clustering.html)
- [GDAL/OGR Documentation](https://gdal.org/)

---

**Versão**: 0.1.0  
**Última Atualização**: Maio 2026
