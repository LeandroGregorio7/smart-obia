# Smart OBIA Plugin para QGIS - Versão Completa

Plugin avançado para **Object-Based Image Analysis (OBIA)** no QGIS com suporte a **4 módulos principais** para processamento completo de imagens multiespectrais.

## 🎯 Características Principais

### ✅ 4 Módulos de Processamento

```
┌─────────────────────────────────────────────────────┐
│           Smart OBIA Plugin v0.2.0                   │
├─────────────────────────────────────────────────────┤
│  1. Band Stacking (Empilhamento de Bandas)          │
│  2. Radiometric Indices (10 índices espectrais)     │
│  3. Texture (GLCM - 6 features de textura)          │
│  4. Segmentation (SLIC, K-Means, Watershed)         │
└─────────────────────────────────────────────────────┘
```

### 1️⃣ Band Stacking
- Combina múltiplas camadas raster em um único arquivo multiband
- Organiza bandas de diferentes fontes
- Preserva georreferenciamento e projeção

### 2️⃣ Radiometric Indices
**10 Índices Espectrais Disponíveis:**

**Vegetação:**
- NDVI (Normalized Difference Vegetation Index)
- SAVI (Soil-Adjusted Vegetation Index)
- GNDVI (Green NDVI)
- EVI (Enhanced Vegetation Index)
- ARVI (Atmospherically Resistant Vegetation Index)

**Água:**
- NDWI (Normalized Difference Water Index)
- MNDWI (Modified NDWI)

**Solo/Construído:**
- NDBI (Normalized Difference Built-up Index)
- NDII (Normalized Difference Infrared Index)
- NDMI (Normalized Difference Moisture Index)

### 3️⃣ Texture (GLCM)
**6 Features de Textura:**
- Contrast (Contraste)
- Dissimilarity (Dissimilaridade)
- Homogeneity (Homogeneidade)
- Energy (Energia)
- Correlation (Correlação)
- ASM (Angular Second Moment)

**Configurações:**
- Window Size: 3-51 pixels
- Distance: 1-10
- Angles: 0°, 45°, 90°, 135°, ou Todas

### 4️⃣ Segmentation
**3 Algoritmos de Segmentação:**
- **SLIC**: Superpixels rápidos e regulares
- **K-Means**: Clustering espectral flexível
- **Watershed**: Delineamento preciso baseado em gradiente

**Features Extraídas Automaticamente:**
- Estatísticas radiométricas (média, std, min, max) por banda
- Área em pixels
- Perímetro

## 📊 Fluxo de Processamento Completo

```
Imagens Sentinel-2/Landsat
        ↓
[1] Band Stacking
        ↓
Imagem multiband organizada
        ↓
[2] Radiometric Indices
        ↓
Índices espectrais (NDVI, NDWI, etc)
        ↓
[3] Texture (GLCM)
        ↓
Features de textura
        ↓
[4] Segmentation
        ↓
Segmentos com features extraídas
        ↓
Análise / Classificação / Mudanças
```

## 🚀 Instalação Rápida

### Requisitos
- QGIS >= 3.16
- Python >= 3.6
- scikit-image, scikit-learn, scipy, numpy

### Passos

1. **Extraia o plugin:**
   ```bash
   tar -xzf smart_obia_plugin.tar.gz
   ```

2. **Copie para QGIS:**
   ```bash
   cp -r smart_obia ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
   ```

3. **Instale dependências (via OSGeo4W Shell como Admin):**
   ```bash
   python -m pip install scikit-image scikit-learn
   ```

4. **Reinicie QGIS**

5. **Ative em Plugins > Manage and Install Plugins > Smart OBIA**

## 📖 Documentação

- **README.md**: Guia básico de instalação e uso
- **MODULES_DOCUMENTATION.md**: Documentação detalhada de cada módulo
- **EXAMPLE_USAGE.md**: Exemplos práticos com código
- **TECHNICAL_DOCUMENTATION.md**: Detalhes técnicos e arquitetura
- **PROJECT_SUMMARY.md**: Resumo geral do projeto

## 💡 Exemplos de Uso

### Exemplo 1: Análise de Vegetação
```
1. Band Stacking: Empilhe R, G, B, NIR, SWIR
2. Indices: Calcule NDVI, SAVI, EVI
3. Texture: Calcule Contrast, Homogeneity
4. Segmentation: SLIC com 150 segmentos
5. Resultado: Segmentos com features de vegetação
```

### Exemplo 2: Detecção de Água
```
1. Band Stacking: R, G, B, NIR, SWIR
2. Indices: NDWI, MNDWI
3. Texture: Energy, Homogeneity
4. Segmentation: K-Means com 10 clusters
5. Resultado: Classificação de água
```

### Exemplo 3: Análise Urbana
```
1. Band Stacking: R, G, B, NIR, SWIR
2. Indices: NDBI, NDVI
3. Texture: Contrast, Dissimilarity
4. Segmentation: Watershed
5. Resultado: Delineamento de áreas urbanas
```

### Exemplo 4: Análise de Mudanças
```
1. Processe imagem T1: Índices + Texturas + Segmentação
2. Processe imagem T2: Mesmos parâmetros
3. Compare features entre T1 e T2
4. Identifique segmentos com mudanças significativas
```

## 🎛️ Parâmetros Recomendados

### Band Stacking
- Selecione todas as bandas de interesse
- Ordem importa para interpretação posterior

### Radiometric Indices
- **Red Band**: Geralmente banda 4 (Sentinel-2)
- **NIR Band**: Geralmente banda 8 (Sentinel-2)
- **SWIR Band**: Geralmente banda 11 (Sentinel-2)

### Texture
- **Window Size**: 5-7 para melhor balance
- **Distance**: 1 para análise local
- **Angles**: Todas para análise completa

### Segmentation
- **SLIC**: 50-200 segmentos para imagens típicas
- **K-Means**: 5-50 clusters para classificação
- **Watershed**: Bom para delineamento de objetos

## 📈 Performance

| Operação | Tempo (1000x1000px) | Complexidade |
|----------|-------------------|-------------|
| Band Stacking | < 1s | O(n) |
| Indices | 1-5s | O(n) |
| Texture | 10-60s | O(n*w²) |
| Segmentation | 5-30s | O(n*k*i) |
| **Total** | **~30-100s** | - |

## 🔧 Requisitos Técnicos

### Dependências Obrigatórias
```
numpy>=1.19.0
scipy>=1.5.0
scikit-image>=0.17.0
scikit-learn>=0.24.0
Pillow>=8.0.0
```

### Dependências Opcionais (desenvolvimento)
```
pytest>=6.0
pytest-cov>=2.10
black>=20.8b1
flake8>=3.8
```

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'skimage'"
```bash
# Via OSGeo4W Shell (como Admin)
python -m pip install scikit-image
```

### Erro: "Band index out of range"
- Verifique o número de bandas da imagem
- Ajuste os índices de banda nos parâmetros

### Processamento muito lento
- Reduza o tamanho da imagem
- Diminua o número de segmentos
- Use menos features de textura

### Segmentos muito pequenos/grandes
- Ajuste o número de segmentos (SLIC)
- Ajuste o número de clusters (K-Means)
- Ajuste a banda de marcador (Watershed)

## 📁 Estrutura do Projeto

```
smart_obia_plugin/
├── smart_obia/
│   ├── __init__.py
│   ├── metadata.txt
│   ├── icon.png
│   ├── smart_obia_plugin.py
│   ├── processing_provider.py
│   └── algorithms/
│       ├── __init__.py
│       ├── stacking_algorithm.py      (Band Stacking)
│       ├── indices_algorithm.py       (Radiometric Indices)
│       ├── texture_algorithm.py       (GLCM Texture)
│       └── segmentation_algorithm.py  (Segmentation)
├── README.md
├── README_UPDATED.md
├── MODULES_DOCUMENTATION.md
├── EXAMPLE_USAGE.md
├── TECHNICAL_DOCUMENTATION.md
├── PROJECT_SUMMARY.md
├── requirements.txt
├── setup.py
├── tests.py
└── .gitignore
```

**Total: 3.785 linhas de código + documentação**

## 🎓 Casos de Uso

### 1. Monitoramento Ambiental
- Detectar mudanças de cobertura vegetal
- Monitorar qualidade de água
- Identificar áreas degradadas

### 2. Planejamento Urbano
- Mapear áreas urbanas
- Detectar expansão urbana
- Analisar padrões de ocupação

### 3. Agricultura de Precisão
- Avaliar vigor de culturas
- Detectar estresse hídrico
- Otimizar aplicação de insumos

### 4. Gestão de Desastres
- Mapear danos após eventos
- Monitorar recuperação
- Análise de risco

### 5. Pesquisa Acadêmica
- Validação de metodologias
- Análise de mudanças temporais
- Estudos de cobertura do solo

## 📚 Referências

- [QGIS Documentation](https://docs.qgis.org/)
- [scikit-image](https://scikit-image.org/)
- [scikit-learn](https://scikit-learn.org/)
- [Spectral Indices Database](https://www.indexdatabase.de/)
- [GLCM Texture Analysis](https://en.wikipedia.org/wiki/Co-occurrence_matrix)
- [OBIA - Wikipedia](https://en.wikipedia.org/wiki/Object-based_image_analysis)

## 📝 Changelog

### v0.2.0 (Maio 2026) - Versão Completa
- ✅ Módulo Band Stacking
- ✅ Módulo Radiometric Indices (10 índices)
- ✅ Módulo Texture (GLCM com 6 features)
- ✅ Módulo Segmentation (3 algoritmos)
- ✅ Extração automática de features
- ✅ Documentação completa
- ✅ Exemplos de uso
- ✅ Testes unitários

### v0.1.0 (Maio 2026) - Versão Inicial
- Segmentação SLIC, K-Means, Watershed
- Extração de features radiométricas

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork do repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

MIT License - Veja LICENSE para detalhes

## 👥 Autores

- **Smart OBIA Team** - Desenvolvimento
- Baseado em: QGIS, scikit-image, scikit-learn, scipy

## 💬 Suporte

Para dúvidas, bugs ou sugestões:
- Abra uma issue no repositório
- Consulte a documentação completa
- Verifique os exemplos de uso

---

**Versão**: 0.2.0  
**Data**: Maio 2026  
**Status**: ✅ Completo e Funcional  
**Total de Código**: 3.785 linhas  
**Módulos**: 4 (Band Stacking, Indices, Texture, Segmentation)  
**Índices**: 10 (NDVI, SAVI, NDWI, NDBI, NDII, GNDVI, MNDWI, NDMI, ARVI, EVI)  
**Features de Textura**: 6 (Contrast, Dissimilarity, Homogeneity, Energy, Correlation, ASM)  
**Algoritmos de Segmentação**: 3 (SLIC, K-Means, Watershed)
