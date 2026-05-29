"""
Smart OBIA Radiometric Indices Algorithm
Calculates vegetation, water, and soil indices from multispectral images
"""
import os
from qgis.PyQt.QtGui import QIcon
import numpy as np
from typing import Dict, Optional, Tuple
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsRasterLayer,
)
from osgeo import gdal
import warnings

warnings.filterwarnings('ignore')

class IndicesAlgorithm(QgsProcessingAlgorithm):
    """
    Calculate radiometric indices from multispectral raster data.
    Supports a wide array of vegetation, water, and RGB-based soil indices.
    """

    INPUT_RASTER = 'INPUT_RASTER'
    RED_BAND = 'RED_BAND'
    NIR_BAND = 'NIR_BAND'
    SWIR_BAND = 'SWIR_BAND'
    BLUE_BAND = 'BLUE_BAND'
    GREEN_BAND = 'GREEN_BAND'
    INDICES = 'INDICES'
    OUTPUT_RASTER = 'OUTPUT_RASTER'

    # Dicionário atualizado com todos os índices requisitados
    AVAILABLE_INDICES = {
        'NDVI': 'Normalized Difference Vegetation Index',
        'SAVI': 'Soil-Adjusted Vegetation Index',
        'RVI': 'Ratio Vegetation Index',
        'NDWI': 'Normalized Difference Water Index',
        'MNDWI': 'Modified Normalized Difference Water Index',
        'NDBI': 'Normalized Difference Built-up Index',
        'NDII': 'Normalized Difference Infrared Index',
        'GNDVI': 'Green Normalized Difference Vegetation Index',
        'NDMI': 'Normalized Difference Moisture Index',
        'ARVI': 'Atmospherically Resistant Vegetation Index',
        'EVI': 'Enhanced Vegetation Index',
        'INT': 'Color Intensity Index',
        'IKAW': 'Kawashima Index',
        'VARI': 'Visible Atmospheric Resistant Index',
        'GLI': 'Green Leaf Index',
        'NGRDI': 'Normalized Green Red Difference Index',
        'NGBDI': 'Normalized Green Blue Difference Index',
        'MGRVI': 'Modified Green Red Vegetation Index',
        'RGBVI': 'Red Green Blue Vegetation Index',
        'RGRI': 'Red-Green Ratio Index',
        'EXG': 'Excess Green Vegetation Index',
        'EXR': 'Excess Red Vegetation Index',
        'EXGR': 'Excess Green minus Excess Red Index',
        'BI': 'Bare Soil Index',
        'NDTI': 'Normalized Difference Turbidity Index'
    }

    def icon(self):
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        icon_png = os.path.join(plugin_dir, 'icon.png')
        icon_jpg = os.path.join(plugin_dir, 'icon.jpg')
        if os.path.exists(icon_png): return QIcon(icon_png)
        elif os.path.exists(icon_jpg): return QIcon(icon_jpg)
        return QIcon()

    def initAlgorithm(self, config: Dict = None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_RASTER, 'Input Raster Layer', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber(self.RED_BAND, 'Red Band (1-indexed)', type=QgsProcessingParameterNumber.Integer, defaultValue=1, minValue=1, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.NIR_BAND, 'NIR Band (1-indexed)', type=QgsProcessingParameterNumber.Integer, defaultValue=2, minValue=1, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.GREEN_BAND, 'Green Band (1-indexed)', type=QgsProcessingParameterNumber.Integer, defaultValue=3, minValue=1, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.BLUE_BAND, 'Blue Band (1-indexed)', type=QgsProcessingParameterNumber.Integer, defaultValue=4, minValue=1, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.SWIR_BAND, 'SWIR Band (1-indexed)', type=QgsProcessingParameterNumber.Integer, defaultValue=5, minValue=1, maxValue=100))
        
        index_options = list(self.AVAILABLE_INDICES.keys())
        self.addParameter(QgsProcessingParameterEnum(self.INDICES, 'Indices to Calculate', options=index_options, allowMultiple=True, defaultValue=[0]))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, 'Output Indices Raster'))

    def helpString(self) -> str:
        return """<h2>Cálculo de Índices Radiométricos</h2>
        <p>Realiza álgebra de mapas para realçar feições específicas.</p>
        <h3>Novos Índices RGB (Para imagens de Drone/RGB):</h3>
        <ul>
        <li><b>INT, GLI, VARI, EXG, EXGR, etc:</b> Excelentes para realçar agricultura e vegetação usando apenas bandas visíveis (Red, Green, Blue) quando não se tem infravermelho.</li>
        </ul>
        <h3>Índices Multiespectrais:</h3>
        <ul>
        <li><b>BI (Bare Soil Index):</b> Realça solo exposto usando SWIR.</li>
        <li><b>NDTI:</b> Realça a turbidez da água.</li>
        </ul>"""

    def processAlgorithm(self, parameters: Dict, context, feedback):
        input_raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        red_band = self.parameterAsInt(parameters, self.RED_BAND, context) - 1
        nir_band = self.parameterAsInt(parameters, self.NIR_BAND, context) - 1
        green_band = self.parameterAsInt(parameters, self.GREEN_BAND, context) - 1
        blue_band = self.parameterAsInt(parameters, self.BLUE_BAND, context) - 1
        swir_band = self.parameterAsInt(parameters, self.SWIR_BAND, context) - 1
        indices_indices = self.parameterAsEnums(parameters, self.INDICES, context)
        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        feedback.pushInfo('Reading raster data (GDAL)...')
        raster_data = self._read_raster(input_raster)
        if raster_data is None:
            feedback.reportError('Failed to read raster data')
            return {}

        index_options = list(self.AVAILABLE_INDICES.keys())
        selected_indices = [index_options[i] for i in indices_indices]

        feedback.pushInfo(f'Calculating {len(selected_indices)} indices...')
        indices_data = self._calculate_indices(raster_data, red_band, nir_band, green_band, blue_band, swir_band, selected_indices, feedback)

        if indices_data is None: return {}

        feedback.pushInfo('Saving output raster...')
        self._save_raster(indices_data, output_raster, input_raster, selected_indices)
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
            print(f'Error reading raster with GDAL: {e}')
            return None

    def _calculate_indices(self, data, r_idx, n_idx, g_idx, b_idx, s_idx, indices, feedback):
        try:
            height, width, bands = data.shape
            max_req_band = max(r_idx, n_idx, g_idx, b_idx, s_idx)
            if max_req_band >= bands:
                feedback.reportError(f'Atenção: Você selecionou uma banda ({max_req_band+1}) que não existe na imagem. A imagem tem apenas {bands} bandas.')
                return None

            R = data[:, :, r_idx].astype(np.float32)
            N = data[:, :, n_idx].astype(np.float32)
            G = data[:, :, g_idx].astype(np.float32)
            B = data[:, :, b_idx].astype(np.float32)
            S = data[:, :, s_idx].astype(np.float32)

            out = np.zeros((height, width, len(indices)), dtype=np.float32)

            for idx, name in enumerate(indices):
                if name == 'NDVI': out[:, :, idx] = self._safe_divide(N - R, N + R)
                elif name == 'SAVI': out[:, :, idx] = self._safe_divide((N - R) * 1.5, N + R + 0.5)
                elif name == 'RVI': out[:, :, idx] = self._safe_divide(N, R)
                elif name == 'NDWI': out[:, :, idx] = self._safe_divide(G - N, G + N) # Usando Green e NIR padrão clássico McFeeters
                elif name == 'MNDWI': out[:, :, idx] = self._safe_divide(G - S, G + S)
                elif name == 'NDBI': out[:, :, idx] = self._safe_divide(S - N, S + N)
                elif name == 'NDII': out[:, :, idx] = self._safe_divide(N - S, N + S)
                elif name == 'GNDVI': out[:, :, idx] = self._safe_divide(N - G, N + G)
                elif name == 'NDMI': out[:, :, idx] = self._safe_divide(N - S, N + S)
                elif name == 'ARVI': 
                    R_c = R - (B - R)
                    out[:, :, idx] = self._safe_divide(N - R_c, N + R_c)
                elif name == 'EVI': out[:, :, idx] = self._safe_divide(2.5 * (N - R), N + 6.0 * R - 7.5 * B + 1.0)
                # Novos índices RGB
                elif name == 'INT': out[:, :, idx] = (R + G + B) / 3.0
                elif name == 'IKAW': out[:, :, idx] = self._safe_divide(R - B, R + B)
                elif name == 'VARI': out[:, :, idx] = self._safe_divide(G - R, G + R - B)
                elif name == 'GLI': out[:, :, idx] = self._safe_divide(2*G - R - B, 2*G + R + B)
                elif name == 'NGRDI': out[:, :, idx] = self._safe_divide(G - R, G + R)
                elif name == 'NGBDI': out[:, :, idx] = self._safe_divide(G - B, G + B)
                elif name == 'MGRVI': out[:, :, idx] = self._safe_divide(G**2 - R**2, G**2 + R**2)
                elif name == 'RGBVI': out[:, :, idx] = self._safe_divide(G**2 - B*R, G**2 + B*R)
                elif name == 'RGRI': out[:, :, idx] = self._safe_divide(R, G)
                elif name == 'EXG': out[:, :, idx] = 2*G - R - B
                elif name == 'EXR': out[:, :, idx] = 1.4*R - G
                elif name == 'EXGR': 
                    exg = 2*G - R - B
                    exr = 1.4*R - G
                    out[:, :, idx] = exg - exr
                elif name == 'BI': 
                    # Bare Soil Index
                    out[:, :, idx] = self._safe_divide((S + R) - (N + B), (S + R) + (N + B))
                elif name == 'NDTI':
                    # Normalized Difference Turbidity Index
                    out[:, :, idx] = self._safe_divide(R - G, R + G)

                feedback.pushInfo(f'Calculated {name}')
            return out
        except Exception as e:
            print(f'Error calculating indices: {e}')
            return None

    @staticmethod
    def _safe_divide(num: np.ndarray, den: np.ndarray) -> np.ndarray:
        res = np.zeros_like(num)
        mask = den != 0
        res[mask] = num[mask] / den[mask]
        return res

    def _save_raster(self, indices_data: np.ndarray, output_path: str, reference_raster: QgsRasterLayer, selected_indices: list):
        try:
            driver = gdal.GetDriverByName('GTiff')
            height, width, num_indices = indices_data.shape
            dataset = driver.Create(output_path, width, height, num_indices, gdal.GDT_Float32)
            
            ref_provider = reference_raster.dataProvider()
            extent = reference_raster.extent()
            dataset.SetGeoTransform((extent.xMinimum(), extent.width() / width, 0, extent.yMaximum(), 0, -extent.height() / height))
            
            crs = reference_raster.crs()
            if crs.isValid(): dataset.SetProjection(crs.toWkt())

            for band_idx in range(num_indices):
                band = dataset.GetRasterBand(band_idx + 1)
                band.WriteArray(indices_data[:, :, band_idx])
                band.SetDescription(selected_indices[band_idx]) 
                band.FlushCache()
            dataset = None
        except Exception as e:
            print(f'Error saving raster: {e}')

    def name(self) -> str: return 'smart_obia_indices'
    def displayName(self) -> str: return '1 - Smart OBIA Radiometric Indices'
    def group(self) -> str: return 'Smart OBIA'
    def groupId(self) -> str: return 'smart_obia'
    def shortHelpString(self) -> str: return 'Calcula uma extensa lista de índices (Vegetação, RGB, Solo e Água).'
    def createInstance(self): return IndicesAlgorithm()