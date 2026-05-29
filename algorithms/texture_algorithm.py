"""
Smart OBIA Texture Algorithm
Calculates GLCM (Gray Level Co-occurrence Matrix) texture features
"""
import os
from qgis.PyQt.QtGui import QIcon
import numpy as np
from typing import Dict, Optional
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterEnum,
    QgsProcessingParameterRasterDestination,
    QgsRasterLayer,
)
from skimage.feature import graycomatrix, graycoprops
from osgeo import gdal
import warnings

warnings.filterwarnings('ignore')


class TextureAlgorithm(QgsProcessingAlgorithm):
    """
    Calculate GLCM texture features from raster data.
    Supports Contrast, Dissimilarity, Homogeneity, Energy, Correlation, ASM, and Entropy.
    """

    INPUT_RASTER = 'INPUT_RASTER'
    BAND = 'BAND'
    WINDOW_SIZE = 'WINDOW_SIZE'
    DISTANCE = 'DISTANCE'
    ANGLES = 'ANGLES'
    FEATURES = 'FEATURES'
    OUTPUT_RASTER = 'OUTPUT_RASTER'

    # Dicionário de features disponíveis
    AVAILABLE_FEATURES = {
        'contrast': 'Contrast',
        'dissimilarity': 'Dissimilarity',
        'homogeneity': 'Homogeneity',
        'energy': 'Energy',
        'correlation': 'Correlation',
        'ASM': 'Angular Second Moment',
        'entropy': 'Entropy',
    }

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
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_RASTER, 'Input Raster Layer', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber(self.BAND, 'Band to Process (1-indexed)', type=QgsProcessingParameterNumber.Integer, defaultValue=1, minValue=1, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.WINDOW_SIZE, 'Window Size (pixels)', type=QgsProcessingParameterNumber.Integer, defaultValue=5, minValue=3, maxValue=51))
        self.addParameter(QgsProcessingParameterNumber(self.DISTANCE, 'Distance for GLCM', type=QgsProcessingParameterNumber.Integer, defaultValue=1, minValue=1, maxValue=10))
        
        self.addParameter(QgsProcessingParameterEnum(self.ANGLES, 'Angles to Calculate', options=['0°', '45°', '90°', '135°', 'All'], allowMultiple=True, defaultValue=[4]))
        
        feature_options = list(self.AVAILABLE_FEATURES.values())
        self.addParameter(QgsProcessingParameterEnum(self.FEATURES, 'Texture Features to Calculate', options=feature_options, allowMultiple=True, defaultValue=[0, 1, 2, 3, 4, 5, 6]))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, 'Output Texture Raster'))

    def helpString(self) -> str:
        return """<h2>Análise de Textura (GLCM) Turbo</h2>
        <p>Calcula a Matriz de Co-ocorrência (GLCM) para extração de características espaciais.</p>
        <h3>Entendendo os Parâmetros:</h3>
        <ul>
        <li><b>Window Size (Tamanho da Janela):</b> Define a área ao redor de cada pixel que será analisada. Janelas menores focam em bordas; janelas maiores focam em padrões gerais.</li>
        <li><b>Features (Estatísticas):</b>
            <ul>
                <li><b>Contrast / Dissimilarity:</b> Destaca bordas e transições abruptas.</li>
                <li><b>Homogeneity:</b> Destaca áreas lisas (lagos, asfalto).</li>
                <li><b>Energy / ASM:</b> Mede a uniformidade estrutural.</li>
                <li><b>Entropy (Entropia):</b> Mede o caos e a desordem (ex: Florestas densas).</li>
            </ul>
        </li>
        </ul>"""

    def processAlgorithm(self, parameters: Dict, context, feedback):
        input_raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        band = self.parameterAsInt(parameters, self.BAND, context) - 1
        window_size = self.parameterAsInt(parameters, self.WINDOW_SIZE, context)
        distance = self.parameterAsInt(parameters, self.DISTANCE, context)
        angles_indices = self.parameterAsEnums(parameters, self.ANGLES, context)
        features_indices = self.parameterAsEnums(parameters, self.FEATURES, context)
        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        feedback.pushInfo('Iniciando cálculo de textura otimizado...')
        raster_data = self._read_raster(input_raster)
        if raster_data is None:
            feedback.reportError('Falha ao ler os dados do raster.')
            return {}

        if band >= raster_data.shape[2]:
            feedback.reportError(f'Banda {band + 1} não encontrada. Bandas disponíveis: {raster_data.shape[2]}')
            return {}

        angle_options = [0, np.pi/4, np.pi/2, 3*np.pi/4]
        if 4 in angles_indices:
            angles = angle_options
        else:
            angles = [angle_options[i] for i in angles_indices]

        feature_keys = list(self.AVAILABLE_FEATURES.keys())
        selected_features = [feature_keys[i] for i in features_indices]

        texture_data = self._calculate_texture(raster_data[:, :, band], window_size, distance, angles, selected_features, feedback)

        if texture_data is None:
            return {}

        feedback.pushInfo('Salvando raster de saída com metadados...')
        self._save_raster(texture_data, output_raster, input_raster, angles, selected_features)
        
        return {self.OUTPUT_RASTER: output_raster}

    def _read_raster(self, raster_layer: QgsRasterLayer) -> Optional[np.ndarray]:
        try:
            from osgeo import gdal
            source = raster_layer.source()
            ds = gdal.Open(source)
            if ds is None: ds = gdal.Open(raster_layer.dataProvider().dataSourceUri())
            if ds is None: return None
            
            band_count, height, width = ds.RasterCount, ds.RasterYSize, ds.RasterXSize
            data = np.zeros((height, width, band_count), dtype=np.float32)
            
            for b in range(1, band_count + 1):
                array = ds.GetRasterBand(b).ReadAsArray()
                if array is not None: data[:, :, b - 1] = array.astype(np.float32)
                    
            ds = None
            return data
        except Exception as e:
            print(f'Erro lendo raster: {e}')
            return None

    def _calculate_texture(self, band_data, window_size, distance, angles, features, feedback):
        try:
            height, width = band_data.shape
            num_features = len(features) * len(angles)
            output = np.zeros((height, width, num_features), dtype=np.float32)

            # Normalização essencial para a biblioteca GLCM
            band_min, band_max = np.nanmin(band_data), np.nanmax(band_data)
            band_normalized = ((band_data - band_min) / (band_max - band_min + 1e-8) * 255).astype(np.uint8)

            half_window = window_size // 2
            
            total_rows = height - 2 * half_window
            current_row = 0

            feedback.pushInfo(f'Processando {len(features)} texturas em {len(angles)} ângulos simultaneamente (Otimização Ativada)...')

            for y in range(half_window, height - half_window):
                if feedback.isCanceled():
                    feedback.pushInfo('Cancelado pelo usuário.')
                    return None
                    
                for x in range(half_window, width - half_window):
                    window = band_normalized[
                        y - half_window:y + half_window + 1,
                        x - half_window:x + half_window + 1
                    ]

                    glcm = graycomatrix(
                        window, distances=[distance], angles=angles,
                        levels=256, symmetric=True, normed=True
                    )

                    feature_idx = 0
                    
                    for angle_idx in range(len(angles)):
                        for feature in features:
                            if feature == 'entropy':
                                p = glcm[:, :, 0, angle_idx]
                                feature_value = -np.sum(p * np.log2(p + 1e-10))
                            else:
                                feature_value = graycoprops(glcm, feature)[0, angle_idx]
                                
                            output[y, x, feature_idx] = feature_value
                            feature_idx += 1
                
                current_row += 1
                feedback.setProgress(int((current_row / total_rows) * 100))

            return output
            
        except Exception as e:
            import traceback
            feedback.reportError(f'Erro fatal ao calcular textura: {e}\n{traceback.format_exc()}')
            return None

    def _save_raster(self, texture_data, output_path, reference_raster, angles, selected_features):
        try:
            driver = gdal.GetDriverByName('GTiff')
            height, width, num_bands = texture_data.shape
            dataset = driver.Create(output_path, width, height, num_bands, gdal.GDT_Float32)

            ref_provider = reference_raster.dataProvider()
            extent = reference_raster.extent()
            
            # Parâmetros de projeção estruturados para evitar erros de leitura/cópia
            geotransform = (
                extent.xMinimum(),
                extent.width() / width,
                0,
                extent.yMaximum(),
                0,
                -extent.height() / height
            )
            dataset.SetGeoTransform(geotransform)

            crs = reference_raster.crs()
            if crs.isValid(): 
                dataset.SetProjection(crs.toWkt())

            band_idx = 0
            for angle in angles:
                angle_deg = int(np.degrees(angle))
                for feature in selected_features:
                    band = dataset.GetRasterBand(band_idx + 1)
                    band.WriteArray(texture_data[:, :, band_idx])
                    band.SetDescription(f'GLCM_{feature.capitalize()}_{angle_deg}deg')
                    band.FlushCache()
                    band_idx += 1

            dataset = None
        except Exception as e:
            print(f'Erro salvando raster: {e}')

    def name(self) -> str: return 'smart_obia_texture'
    def displayName(self) -> str: return '2 - Smart OBIA Texture (GLCM)'
    def group(self) -> str: return 'Smart OBIA'
    def groupId(self) -> str: return 'smart_obia'
    def shortHelpString(self) -> str: return 'Calcula texturas espaciais GLCM de maneira otimizada.'
    def createInstance(self): return TextureAlgorithm()