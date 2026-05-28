# Smart OBIA Plugin para QGIS

Plugin avançado para **Object-Based Image Analysis (OBIA)** no QGIS, implementando segmentação de imagens multiespectrais com múltiplos algoritmos e extração automática de features radiométricas e espaciais.

## Características Principais

### 1. Algoritmos de Segmentação

O plugin implementa três algoritmos de segmentação de imagens:

#### **SLIC (Simple Linear Iterative Clustering)**
- Segmentação baseada em superpixels
- Parâmetros ajustáveis:
  - **Número de Segmentos**: Define a quantidade de segmentos desejados (10-10000)
  - **Compactness**: Controla a regularidade espacial dos segmentos (0.1-100.0)
- Ideal para: Análise de texturas, detecção de mudanças, classificação de cobertura do solo

#### **K-Means**
- Clustering espectral de pixels
- Parâmetros ajustáveis:
  - **Número de Clusters**: Define quantos clusters espectrais serão criados (2-500)
- Ideal para: Classificação espectral, separação de classes espectrais distintas

#### **Watershed**
- Segmentação baseada em gradiente e marcadores
- Parâmetros ajustáveis:
  - **Banda de Marcador**: Define qual banda será usada para criar marcadores (1-indexed)
- Ideal para: Delineamento de objetos, segmentação baseada em elevação

### 2. Extração Automática de Features

Para cada segmento, o plugin extrai:

#### **Features Radiométricas (por banda)**
- **Média**: Valor médio dos pixels do segmento
- **Desvio Padrão**: Variabilidade espectral dentro do segmento
- **Mínimo**: Valor mínimo da banda no segmento
- **Máximo**: Valor máximo da banda no segmento

#### **Features Espaciais**
- **Área em Pixels**: Número de pixels no segmento
- **Perímetro**: Comprimento do perímetro do segmento (simplificado)

### 3. Saídas

O plugin gera duas saídas principais:

1. **Raster de Segmentação**: Arquivo raster GeoTIFF com IDs dos segmentos
2. **Camada Vetorial**: Arquivo Shapefile com polígonos dos segmentos e todas as features extraídas

## Instalação

### Requisitos do Sistema

- **QGIS**: Versão 3.16 ou superior
- **Python**: 3.6 ou superior
- **Dependências Python**:
  ```bash
  pip install scikit-image scikit-learn scipy numpy
  ```

### Passos de Instalação

1. Clone ou copie o diretório `smart_obia` para a pasta de plugins do QGIS:
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`

2. Reinicie o QGIS

3. Ative o plugin em **Plugins > Manage and Install Plugins > Smart OBIA**

## Uso

### Acessando o Algoritmo

1. Abra o **Processing Toolbox** (Processamento > Caixa de Ferramentas)
2. Procure por **Smart OBIA > Smart OBIA Segmentation**
3. Configure os parâmetros conforme necessário

### Exemplo de Uso

#### Segmentação SLIC
```
Entrada: Imagem multiespectral (GeoTIFF)
Método: SLIC
Número de Segmentos: 100
Compactness: 10.0
Saída: segmentacao.tif e segmentacao.shp
```

#### Segmentação K-Means
```
Entrada: Imagem multiespectral (GeoTIFF)
Método: K-Means
Número de Clusters: 50
Saída: segmentacao.tif e segmentacao.shp
```

#### Segmentação Watershed
```
Entrada: Imagem multiespectral (GeoTIFF)
Método: Watershed
Banda de Marcador: 1 (primeira banda)
Saída: segmentacao.tif e segmentacao.shp
```

## Estrutura do Projeto

```
smart_obia/
├── __init__.py                 # Inicialização do plugin
├── metadata.txt                # Metadados do plugin
├── icon.png                    # Ícone do plugin
├── smart_obia_plugin.py        # Classe principal do plugin
├── processing_provider.py      # Provedor de processamento
└── algorithms/
    ├── __init__.py
    └── segmentation_algorithm.py  # Implementação dos algoritmos
```

## Detalhes Técnicos

### Leitura de Dados Raster

O plugin lê dados raster usando a API GDAL/OGR através do QGIS:
- Suporta múltiplas bandas
- Preserva georreferenciamento e projeção
- Normaliza dados para processamento

### Processamento de Segmentação

1. **Leitura**: Carrega todas as bandas da imagem
2. **Normalização**: Normaliza dados para intervalo 0-255 (SLIC) ou 0-1 (K-Means/Watershed)
3. **Segmentação**: Aplica o algoritmo escolhido
4. **Extração de Features**: Calcula estatísticas para cada segmento

### Criação de Camada Vetorial

- Converte segmentos raster em polígonos
- Cria geometrias bounding box para cada segmento
- Associa features extraídas como atributos
- Salva em formato Shapefile com projeção original

## Limitações Conhecidas

1. **Geometrias Simplificadas**: As geometrias dos segmentos são representadas como bounding boxes (retângulos), não como contornos exatos
2. **Performance**: Imagens muito grandes (> 5000x5000 pixels) podem ser lentas
3. **Memória**: Requer memória suficiente para carregar toda a imagem em RAM
4. **Bandas**: Suporta até 100 bandas, mas recomenda-se usar 3-10 bandas para melhor performance

## Melhorias Futuras

- [ ] Suporte para contornos exatos dos segmentos
- [ ] Cálculo de texturas GLCM
- [ ] Índices de forma (compacidade, alongamento)
- [ ] Processamento de imagens grandes com tiles
- [ ] Exportação para múltiplos formatos (GeoJSON, GeoPackage)
- [ ] Interface gráfica customizada
- [ ] Suporte para processamento em paralelo

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'skimage'"

**Solução**: Instale scikit-image
```bash
pip install scikit-image
```

### Erro: "ModuleNotFoundError: No module named 'sklearn'"

**Solução**: Instale scikit-learn
```bash
pip install scikit-learn
```

### Plugin não aparece no QGIS

**Solução**:
1. Verifique se o diretório está no local correto
2. Verifique se o arquivo `metadata.txt` está presente
3. Reinicie o QGIS
4. Verifique o log de plugins em **Plugins > Manage and Install Plugins > Installed**

### Segmentação muito lenta

**Solução**:
- Reduza o tamanho da imagem antes de processar
- Reduza o número de segmentos/clusters
- Use apenas as bandas necessárias

## Contribuindo

Para contribuir com melhorias:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## Autores

- Desenvolvimento: Smart OBIA Team
- Baseado em: QGIS Processing Framework, scikit-image, scikit-learn

## Referências

- [QGIS Documentation](https://docs.qgis.org/)
- [scikit-image](https://scikit-image.org/)
- [scikit-learn](https://scikit-learn.org/)
- [Object-Based Image Analysis (OBIA)](https://en.wikipedia.org/wiki/Object-based_image_analysis)

## Suporte

Para reportar bugs ou solicitar features, abra uma issue no repositório do projeto.

---

**Versão**: 0.1.0  
**Data de Atualização**: Maio 2026  
**Status**: Em Desenvolvimento
