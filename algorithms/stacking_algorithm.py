"""
Smart OBIA Band Stacking Algorithm
Stacks multiple raster bands into a single multiband raster sequentially
"""
import os
from qgis.PyQt.QtGui import QIcon
import numpy as np
from typing import Dict, Optional
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterRasterDestination,
    QgsRasterLayer,
)
from osgeo import gdal
import warnings

warnings.filterwarnings('ignore')


class StackingAlgorithm(QgsProcessingAlgorithm):
    """
    Sequential Band Stacking Tool.
    Allows explicit ordering of input layers for the multi-band stack.
    """

    # Nomes dos parâmetros por slots sequenciais de posição
    INPUT_1 = 'INPUT_1'
    INPUT_2 = 'INPUT_2'
    INPUT_3 = 'INPUT_3'
    INPUT_4 = 'INPUT_4'
    INPUT_5 = 'INPUT_5'
    INPUT_6 = 'INPUT_6'
    OUTPUT_RASTER = 'OUTPUT_RASTER'

    def icon(self):
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        icon_png = os.path.join(plugin_dir, 'icon.png')
        icon_jpg = os.path.join(plugin_dir, 'icon.jpg')
        if os.path.exists(icon_png): 
            return QIcon(icon_png)
        elif os.path.exists(icon_jpg): 
            return QIcon(icon_jpg)
        return QIcon()

    def initAlgorithm(self, config: Dict = None):
        """Cria os slots sequenciais na interface do QGIS para controle total da ordem."""
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_1, '1ª Camada da Sequência (Base / Imagem Multibanda)', optional=False))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_2, '2ª Camada da Sequência (Ex: Índice / Textura)', optional=False))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_3, '3ª Camada da Sequência (Opcional)', optional=True))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_4, '4ª Camada da Sequência (Opcional)', optional=True))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_5, '5ª Camada da Sequência (Opcional)', optional=True))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_6, '6ª Camada da Sequência (Opcional)', optional=True))
        
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, 'Output Stacked Raster'))

    def helpString(self) -> str:
        """Retorna o texto de ajuda detalhado em HTML para o painel lateral."""
        return """<h2>3 - Band Stacking (Empilhamento Sequencial)</h2>
        <p>Esta ferramenta junta imagens e índices em um único arquivo multiespectral, permitindo que você configure a <b>ordem exata</b> de entrada das bandas.</p>
        <h3>Como Funciona o Posicionamento:</h3>
        <ul>
        <li><b>1ª Camada:</b> Ficará posicionada nas primeiras bandas do arquivo final. Se você colocar uma imagem de 4 bandas aqui, elas ocuparão as bandas 1, 2, 3 e 4.</li>
        <li><b>2ª Camada:</b> Entrará logo em seguida. No exemplo acima, ocupará a banda 5 do arquivo final.</li>
        <li><b>Camadas Opcionais:</b> Adicione mais índices ou texturas nos slots subsequentes para complementar seu Stack.</li>
        </ul>
        <p><i>Requisito Crítico: Todos os rasters selecionados precisam cobrir a mesma região geográfica e possuir o mesmo tamanho de pixels (linhas e colunas).</i></p>"""

    def processAlgorithm(self, parameters: Dict, context, feedback):
        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        # Coleta as camadas respeitando rigorosamente a ordem dos slots preenchidos
        layers = []
        for i in range(1, 7):
            layer = self.parameterAsRasterLayer(parameters, f'INPUT_{i}', context)
            if layer is not None:
                layers.append(layer)

        if len(layers) < 2:
            feedback.reportError('Erro: Você precisa selecionar pelo menos as duas primeiras camadas para realizar o empilhamento!')
            return {}

        feedback.pushInfo('Abrindo os arquivos originais via GDAL...')
        src_datasets = []
        total_bands = 0
        reference_ds = None

        for layer in layers:
            source = layer.source()
            ds = gdal.Open(source)
            if ds is None: 
                ds = gdal.Open(layer.dataProvider().dataSourceUri())
            if ds is None:
                feedback.reportError(f'Não foi possível abrir o arquivo do raster: {layer.name()}')
                return {}
            
            src_datasets.append((ds, layer.name()))
            total_bands += ds.RasterCount
            if reference_ds is None:
                reference_ds = ds

        # Validação geométrica estrita
        width = reference_ds.RasterXSize
        height = reference_ds.RasterYSize
        geotransform = reference_ds.GetGeoTransform()
        projection = reference_ds.GetProjection()

        for ds, name in src_datasets:
            if ds.RasterXSize != width or ds.RasterYSize != height:
                feedback.reportError(f'O raster "{name}" possui tamanho ({ds.RasterXSize}x{ds.RasterYSize}) incompatível com o raster base ({width}x{height}).')
                return {}

        feedback.pushInfo(f'Criando imagem GeoTIFF de saída com {total_bands} bandas totais (Float32)...')
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(output_raster, width, height, total_bands, gdal.GDT_Float32)
        out_ds.SetGeoTransform(geotransform)
        out_ds.SetProjection(projection)

        # Loop de Piping Direto de Bandas com correção de Estatísticas
        out_band_idx = 1
        for ds, name in src_datasets:
            for b in range(1, ds.RasterCount + 1):
                feedback.pushInfo(f'Transferindo banda {b} de "{name}" para a banda {out_band_idx} do arquivo final...')
                
                src_band = ds.GetRasterBand(b)
                # Converte explicitamente para Float32 para não dar conflito na gravação
                data = src_band.ReadAsArray().astype(np.float32)
                
                out_band = out_ds.GetRasterBand(out_band_idx)
                out_band.WriteArray(data)
                
                # CORREÇÃO 1: Copia o valor "NoData" (evita que a borda preta estrague a imagem)
                nodata = src_band.GetNoDataValue()
                if nodata is not None:
                    out_band.SetNoDataValue(nodata)
                
                # CORREÇÃO 2: Força o cálculo das estatísticas de Min/Max para o QGIS renderizar a cor certa!
                out_band.ComputeStatistics(False)
                
                # Preserva o nome original da banda ou cria um metadado descritivo amigável
                desc = src_band.GetDescription()
                if not desc:
                    desc = f'{name}_B{b}'
                out_band.SetDescription(desc)
                out_band.FlushCache()
                
                out_band_idx += 1

        # Fecha e salva todos os datasets de forma segura no disco
        out_ds = None
        for ds, name in src_datasets:
            ds = None

        feedback.pushInfo('Band Stacking sequencial concluído com sucesso!')
        return {self.OUTPUT_RASTER: output_raster}

    def name(self) -> str: return 'smart_obia_stacking'
    def displayName(self) -> str: return '3 - Smart OBIA Band Stacking'
    def group(self) -> str: return 'Smart OBIA'
    def groupId(self) -> str: return 'smart_obia'
    def shortHelpString(self) -> str: return 'Empilha múltiplas bandas raster em uma sequência controlada pelo usuário.'
    def createInstance(self): return StackingAlgorithm()