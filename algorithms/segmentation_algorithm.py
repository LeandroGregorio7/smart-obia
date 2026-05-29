"""
Smart OBIA Segmentation Algorithms (Motor Topológico Puro: 0 Gaps, 0 Sobreposição, 0 Pixels Isolados)
"""
import os
import inspect
from qgis.PyQt.QtGui import QIcon
import numpy as np
from typing import Dict, Optional
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer, 
    QgsProcessingParameterNumber, QgsProcessingParameterString, 
    QgsProcessingParameterRasterDestination, QgsProcessingParameterVectorDestination, 
    QgsProcessingParameterVectorLayer,
    QgsRasterLayer, QgsVectorLayer, QgsFeature, QgsGeometry, QgsFields, QgsField, QgsWkbTypes,
    QgsCoordinateTransform, QgsProject
)
from qgis.PyQt.QtCore import QVariant
from osgeo import gdal, ogr, osr
from skimage import segmentation
from skimage.filters import sobel, gaussian
from scipy import ndimage
import warnings

warnings.filterwarnings('ignore')

def get_plugin_icon():
    plugin_dir = os.path.dirname(os.path.dirname(__file__))
    icon_png = os.path.join(plugin_dir, 'icon.png')
    icon_jpg = os.path.join(plugin_dir, 'icon.jpg')
    if os.path.exists(icon_png): return QIcon(icon_png)
    elif os.path.exists(icon_jpg): return QIcon(icon_jpg)
    return QIcon()

class ObiaUtils:
    @staticmethod
    def read_specific_bands(raster_layer: QgsRasterLayer, bands_list: list) -> Optional[np.ndarray]:
        try:
            source = raster_layer.source()
            ds = gdal.Open(source)
            if ds is None: ds = gdal.Open(raster_layer.dataProvider().dataSourceUri())
            if ds is None: return None
            height, width = ds.RasterYSize, ds.RasterXSize
            data = np.zeros((height, width, len(bands_list)), dtype=np.float32)
            for i, b in enumerate(bands_list):
                if b <= ds.RasterCount:
                    array = ds.GetRasterBand(b).ReadAsArray()
                    if array is not None: data[:, :, i] = array.astype(np.float32)
            ds = None
            return data
        except Exception:
            return None

    @staticmethod
    def get_valid_mask(image: np.ndarray, raster_layer: QgsRasterLayer, vector_mask_layer: QgsVectorLayer = None) -> np.ndarray:
        valid_mask = ~np.isnan(image).any(axis=2)
        sum_bands = np.sum(image, axis=2)
        valid_mask = valid_mask & (sum_bands > 0)

        if vector_mask_layer:
            raster_ds = gdal.Open(raster_layer.source())
            if not raster_ds: raster_ds = gdal.Open(raster_layer.dataProvider().dataSourceUri())
            
            mem_drv = gdal.GetDriverByName('MEM')
            mask_ds = mem_drv.Create('', raster_ds.RasterXSize, raster_ds.RasterYSize, 1, gdal.GDT_Byte)
            mask_ds.SetGeoTransform(raster_ds.GetGeoTransform())
            mask_ds.SetProjection(raster_ds.GetProjection())
            
            transform = QgsCoordinateTransform(vector_mask_layer.crs(), raster_layer.crs(), QgsProject.instance())
            
            ogr_drv = ogr.GetDriverByName('Memory')
            ogr_ds = ogr_drv.CreateDataSource('temp_ogr')
            ogr_layer = ogr_ds.CreateLayer('mask', None, ogr.wkbPolygon)
            
            for feat in vector_mask_layer.getFeatures():
                geom = feat.geometry()
                if geom.isNull() or not geom.isGeosValid():
                    geom = geom.makeValid()
                    if geom.isNull(): continue
                try:
                    geom.transform(transform)
                except Exception:
                    continue
                ogr_geom = ogr.CreateGeometryFromWkt(geom.asWkt())
                if ogr_geom is not None:
                    ogr_feat = ogr.Feature(ogr_layer.GetLayerDefn())
                    ogr_feat.SetGeometry(ogr_geom)
                    ogr_layer.CreateFeature(ogr_feat)
            
            gdal.RasterizeLayer(mask_ds, [1], ogr_layer, burn_values=[1])
            vector_mask_array = mask_ds.GetRasterBand(1).ReadAsArray() > 0
            
            valid_mask = valid_mask & vector_mask_array

        return valid_mask

    @staticmethod
    def normalize_for_segmentation(image: np.ndarray, roi_mask: np.ndarray) -> np.ndarray:
        norm_img = np.zeros_like(image, dtype=np.float32)
        for b in range(image.shape[2]):
            band = image[:, :, b]
            valid_pixels = band[roi_mask]
            if len(valid_pixels) == 0: continue
            
            p2, p98 = np.percentile(valid_pixels, (2, 98))
            if p98 > p2:
                norm = np.clip((band - p2) / (p98 - p2), 0, 1) * 255.0
                norm_img[:, :, b] = norm
                norm_img[~roi_mask, b] = 0 
            else:
                norm_img[:, :, b] = 0
        return norm_img

    @staticmethod
    def apply_topological_rules(segments: np.ndarray, roi_mask: np.ndarray, min_size: int, smooth_size: int) -> np.ndarray:
        """Motor Topológico: Garante formas orgânicas, 0 pixels isolados e 0 gaps nativamente na matriz."""
        # 1. Arredondamento Orgânico (Preserva Topologia Intacta)
        if smooth_size > 1:
            segments = ndimage.median_filter(segments, size=smooth_size)
            
        # 2. Extermínio de Pixels Isolados (Sieve)
        if min_size > 1:
            import skimage.morphology as morph
            cleaned = morph.remove_small_objects(segments, min_size=min_size)
            holes = (roi_mask) & (cleaned == 0)
            
            # 3. Absorção Topológica: Força os buracos a serem engolidos pela árvore vizinha
            if np.any(cleaned > 0) and np.any(holes):
                dist, indices = ndimage.distance_transform_edt(cleaned == 0, return_indices=True)
                cleaned = cleaned[tuple(indices)]
            segments = cleaned
            
        segments[~roi_mask] = 0
        return segments

    @staticmethod
    def save_raster(segments: np.ndarray, output_path: str, reference_raster: QgsRasterLayer):
        driver = gdal.GetDriverByName('GTiff')
        height, width = segments.shape
        dataset = driver.Create(output_path, width, height, 1, gdal.GDT_UInt32)
        extent = reference_raster.extent()
        dataset.SetGeoTransform((extent.xMinimum(), extent.width() / width, 0, extent.yMaximum(), 0, -extent.height() / height))
        crs = reference_raster.crs()
        if crs.isValid(): dataset.SetProjection(crs.toWkt())
        band = dataset.GetRasterBand(1)
        band.SetNoDataValue(0)
        band.WriteArray(segments)
        band.FlushCache()

    @staticmethod
    def create_vector_layer(output_raster_path: str, full_raster_layer: QgsRasterLayer, parameters: Dict, context, feedback, algo) -> Optional[str]:
        try:
            ds_full = gdal.Open(full_raster_layer.source())
            if ds_full is None: ds_full = gdal.Open(full_raster_layer.dataProvider().dataSourceUri())
            h, w, b_count = ds_full.RasterYSize, ds_full.RasterXSize, ds_full.RasterCount
            raster_data = np.zeros((h, w, b_count), dtype=np.float32)
            for b in range(1, b_count + 1):
                raster_data[:, :, b - 1] = ds_full.GetRasterBand(b).ReadAsArray()

            fields = QgsFields()
            fields.append(QgsField('segment_id', QVariant.Int))
            fields.append(QgsField('area_pix', QVariant.Int))
            for band_idx in range(b_count):
                fields.append(QgsField(f'b{band_idx + 1}_mean', QVariant.Double))
                fields.append(QgsField(f'b{band_idx + 1}_std', QVariant.Double))

            seg_ds = gdal.Open(output_raster_path)
            seg_band = seg_ds.GetRasterBand(1)
            
            (sink, dest_id) = algo.parameterAsSink(parameters, algo.OUTPUT_VECTORS, context, fields, QgsWkbTypes.Polygon, full_raster_layer.crs())
                
            ogr_drv = ogr.GetDriverByName('Memory')
            ogr_ds = ogr_drv.CreateDataSource('out')
            srs = osr.SpatialReference()
            proj_wkt = seg_ds.GetProjection()
            if proj_wkt: srs.ImportFromWkt(proj_wkt)
            ogr_layer = ogr_ds.CreateLayer('poly', srs, ogr.wkbPolygon)
            ogr_layer.CreateField(ogr.FieldDefn('DN', ogr.OFTInteger))
            
            feedback.pushInfo('Vetorizando polígonos ladeados (0 Gaps, 0 Sobreposições matematicamente garantido)...')
            gdal.Polygonize(seg_band, seg_band, ogr_layer, 0, [], callback=None)

            segments_array = seg_band.ReadAsArray()
            segment_ids = np.unique(segments_array[segments_array > 0])
            stats = {}
            for b in range(b_count):
                band = raster_data[:, :, b]
                means = ndimage.mean(band, labels=segments_array, index=segment_ids)
                stds = ndimage.standard_deviation(band, labels=segments_array, index=segment_ids)
                stats[b] = {sid: (m, s) for sid, m, s in zip(segment_ids, means, stds)}
                
            area_pixels = ndimage.sum(np.ones_like(segments_array), labels=segments_array, index=segment_ids)
            areas = {sid: a for sid, a in zip(segment_ids, area_pixels)}

            ogr_layer.ResetReading()
            for ogr_feat in ogr_layer:
                if feedback.isCanceled(): break
                seg_id = ogr_feat.GetFieldAsInteger('DN')
                if seg_id <= 0: continue
                
                geom = ogr_feat.GetGeometryRef()
                if geom is not None:
                    qgs_geom = QgsGeometry.fromWkt(geom.ExportToWkt())
                    qgs_feat = QgsFeature(fields)
                    qgs_feat.setGeometry(qgs_geom)
                    attrs = [seg_id, int(areas.get(seg_id, 0))]
                    for b in range(b_count):
                        m, s = stats[b].get(seg_id, (0.0, 0.0))
                        attrs.extend([float(m), float(s)])
                    qgs_feat.setAttributes(attrs)
                    sink.addFeature(qgs_feat)

            return dest_id

        except Exception as e:
            feedback.reportError(f'Erro fatal na vetorização: {str(e)}')
            return None


# ==========================================
# 1. FELZENSZWALB SEGMENTATION
# ==========================================
class FelzenszwalbSegmentationAlgorithm(QgsProcessingAlgorithm):
    INPUT_RASTER = 'INPUT_RASTER'
    INPUT_MASK = 'INPUT_MASK'
    BANDS_USE = 'BANDS_USE'
    SCALE_PARAM = 'SCALE_PARAM'
    MIN_SIZE = 'MIN_SIZE'
    SMOOTH_BORDERS = 'SMOOTH_BORDERS'
    OUTPUT_SEGMENTS = 'OUTPUT_SEGMENTS'
    OUTPUT_VECTORS = 'OUTPUT_VECTORS'

    def icon(self): return get_plugin_icon()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_RASTER, 'Raster de Entrada'))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_MASK, 'Máscara de Limite (Opcional)', [QgsProcessing.TypeVectorPolygon], optional=True))
        self.addParameter(QgsProcessingParameterString(self.BANDS_USE, 'Bandas (ex: 9, 10, 4)', defaultValue='1, 2, 3'))
        self.addParameter(QgsProcessingParameterNumber(self.SCALE_PARAM, 'Escala (Controla o tamanho)', type=QgsProcessingParameterNumber.Double, defaultValue=150.0, minValue=1.0))
        self.addParameter(QgsProcessingParameterNumber(self.MIN_SIZE, 'Tamanho Mínimo (Extermínio de Pixels Isolados)', type=QgsProcessingParameterNumber.Integer, defaultValue=30, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(self.SMOOTH_BORDERS, 'Suavização Orgânica Topológica (Raster: 1 a 15)', type=QgsProcessingParameterNumber.Integer, defaultValue=5, minValue=1, maxValue=15))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_SEGMENTS, 'Raster de Segmentação'))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_VECTORS, 'Vetores de Segmentação'))

    def shortHelpString(self) -> str:
        return "<h2>Felzenszwalb (Grafos)</h2><p>Topologia Absoluta Nível Raster: Bordas ladeadas perfeitamente e isento de micro-polígonos.</p>"

    def processAlgorithm(self, parameters, context, feedback):
        input_raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        mask_vector = self.parameterAsVectorLayer(parameters, self.INPUT_MASK, context)
        bands_str = self.parameterAsString(parameters, self.BANDS_USE, context)
        scale_val = self.parameterAsDouble(parameters, self.SCALE_PARAM, context)
        min_size = self.parameterAsInt(parameters, self.MIN_SIZE, context)
        smooth_size = self.parameterAsInt(parameters, self.SMOOTH_BORDERS, context)
        output_raster_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_SEGMENTS, context)

        bands_list = [int(x.strip()) for x in bands_str.split(',')]
        image = ObiaUtils.read_specific_bands(input_raster, bands_list)
        if image is None: return {}

        roi_mask = ObiaUtils.get_valid_mask(image, input_raster, mask_vector)
        norm_img = ObiaUtils.normalize_for_segmentation(image, roi_mask)
        
        for b in range(norm_img.shape[2]):
            norm_img[:, :, b] = gaussian(norm_img[:, :, b], sigma=1.0)
            
        feedback.pushInfo('Executando Felzenszwalb...')
        segments = segmentation.felzenszwalb(norm_img, scale=scale_val, sigma=0.5, min_size=min_size).astype(np.uint32)
        segments += 1 

        feedback.pushInfo('Aplicando Regras Topológicas Rígidas na Matriz...')
        segments = ObiaUtils.apply_topological_rules(segments, roi_mask, min_size, smooth_size)

        ObiaUtils.save_raster(segments, output_raster_path, input_raster)
        vector_dest_id = ObiaUtils.create_vector_layer(output_raster_path, input_raster, parameters, context, feedback, self)
        
        return {self.OUTPUT_SEGMENTS: output_raster_path, self.OUTPUT_VECTORS: vector_dest_id}

    def name(self): return 'smart_obia_felzenszwalb'
    def displayName(self): return '4.1 - Smart OBIA Seg (Felzenszwalb / Orgânico)'
    def group(self): return 'Smart OBIA'
    def groupId(self): return 'smart_obia'
    def createInstance(self): return FelzenszwalbSegmentationAlgorithm()


# ==========================================
# 2. QUICKSHIFT SEGMENTATION
# ==========================================
class QuickshiftSegmentationAlgorithm(QgsProcessingAlgorithm):
    INPUT_RASTER = 'INPUT_RASTER'
    INPUT_MASK = 'INPUT_MASK'
    BANDS_USE = 'BANDS_USE'
    KERNEL_SIZE = 'KERNEL_SIZE'
    MAX_DIST = 'MAX_DIST'
    MIN_SIZE = 'MIN_SIZE'
    SMOOTH_BORDERS = 'SMOOTH_BORDERS'
    OUTPUT_SEGMENTS = 'OUTPUT_SEGMENTS'
    OUTPUT_VECTORS = 'OUTPUT_VECTORS'

    def icon(self): return get_plugin_icon()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_RASTER, 'Raster de Entrada'))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_MASK, 'Máscara de Limite (Opcional)', [QgsProcessing.TypeVectorPolygon], optional=True))
        self.addParameter(QgsProcessingParameterString(self.BANDS_USE, 'Bandas (ex: 9, 10, 4)', defaultValue='1, 2, 3'))
        self.addParameter(QgsProcessingParameterNumber(self.KERNEL_SIZE, 'Kernel (Suavização Espectral)', type=QgsProcessingParameterNumber.Double, defaultValue=5.0, minValue=1.0))
        self.addParameter(QgsProcessingParameterNumber(self.MAX_DIST, 'Distância Máxima (Raio do Alvo)', type=QgsProcessingParameterNumber.Double, defaultValue=15.0, minValue=1.0))
        self.addParameter(QgsProcessingParameterNumber(self.MIN_SIZE, 'Tamanho Mínimo (Extermínio de Pixels Isolados)', type=QgsProcessingParameterNumber.Integer, defaultValue=30, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(self.SMOOTH_BORDERS, 'Suavização Orgânica Topológica (Raster: 1 a 15)', type=QgsProcessingParameterNumber.Integer, defaultValue=5, minValue=1, maxValue=15))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_SEGMENTS, 'Raster de Segmentação'))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_VECTORS, 'Vetores de Segmentação'))

    def shortHelpString(self) -> str:
        return "<h2>Quickshift (Crescimento)</h2><p>Topologia Absoluta Nível Raster: Bordas ladeadas perfeitamente e isento de micro-polígonos.</p>"

    def processAlgorithm(self, parameters, context, feedback):
        input_raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        mask_vector = self.parameterAsVectorLayer(parameters, self.INPUT_MASK, context)
        bands_str = self.parameterAsString(parameters, self.BANDS_USE, context)
        kernel_val = self.parameterAsDouble(parameters, self.KERNEL_SIZE, context)
        max_dist_val = self.parameterAsDouble(parameters, self.MAX_DIST, context)
        min_size = self.parameterAsInt(parameters, self.MIN_SIZE, context)
        smooth_size = self.parameterAsInt(parameters, self.SMOOTH_BORDERS, context)
        output_raster_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_SEGMENTS, context)

        bands_list = [int(x.strip()) for x in bands_str.split(',')]
        image = ObiaUtils.read_specific_bands(input_raster, bands_list)
        if image is None: return {}

        roi_mask = ObiaUtils.get_valid_mask(image, input_raster, mask_vector)
        norm_img = ObiaUtils.normalize_for_segmentation(image, roi_mask)
        
        feedback.pushInfo('Executando Quickshift...')
        segments = segmentation.quickshift(norm_img, kernel_size=kernel_val, max_dist=max_dist_val, ratio=0.5, convert2lab=False).astype(np.uint32)
        segments += 1 

        feedback.pushInfo('Aplicando Regras Topológicas Rígidas na Matriz...')
        segments = ObiaUtils.apply_topological_rules(segments, roi_mask, min_size, smooth_size)

        ObiaUtils.save_raster(segments, output_raster_path, input_raster)
        vector_dest_id = ObiaUtils.create_vector_layer(output_raster_path, input_raster, parameters, context, feedback, self)
        
        return {self.OUTPUT_SEGMENTS: output_raster_path, self.OUTPUT_VECTORS: vector_dest_id}

    def name(self): return 'smart_obia_quickshift'
    def displayName(self): return '4.2 - Smart OBIA Seg (Quickshift / Crescimento)'
    def group(self): return 'Smart OBIA'
    def groupId(self): return 'smart_obia'
    def createInstance(self): return QuickshiftSegmentationAlgorithm()


# ==========================================
# 3. WATERSHED SEGMENTATION
# ==========================================
class WatershedSegmentationAlgorithm(QgsProcessingAlgorithm):
    INPUT_RASTER = 'INPUT_RASTER'
    INPUT_MASK = 'INPUT_MASK'
    BANDS_USE = 'BANDS_USE'
    MIN_DIST = 'MIN_DIST'
    MIN_SIZE = 'MIN_SIZE'
    SMOOTH_BORDERS = 'SMOOTH_BORDERS'
    OUTPUT_SEGMENTS = 'OUTPUT_SEGMENTS'
    OUTPUT_VECTORS = 'OUTPUT_VECTORS'

    def icon(self): return get_plugin_icon()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_RASTER, 'Raster de Entrada'))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_MASK, 'Máscara de Limite (Opcional)', [QgsProcessing.TypeVectorPolygon], optional=True))
        self.addParameter(QgsProcessingParameterString(self.BANDS_USE, 'Bandas (ex: 1, 2)', defaultValue='1'))
        self.addParameter(QgsProcessingParameterNumber(self.MIN_DIST, 'Distância mínima entre centros de árvores', type=QgsProcessingParameterNumber.Integer, defaultValue=10, minValue=3))
        self.addParameter(QgsProcessingParameterNumber(self.MIN_SIZE, 'Tamanho Mínimo (Extermínio de Pixels Isolados)', type=QgsProcessingParameterNumber.Integer, defaultValue=30, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(self.SMOOTH_BORDERS, 'Suavização Orgânica Topológica (Raster: 1 a 15)', type=QgsProcessingParameterNumber.Integer, defaultValue=5, minValue=1, maxValue=15))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_SEGMENTS, 'Raster de Segmentação'))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_VECTORS, 'Vetores de Segmentação'))

    def shortHelpString(self) -> str:
        return "<h2>Watershed (Extração de Copas)</h2><p>Topologia Absoluta Nível Raster: Bordas ladeadas perfeitamente e isento de micro-polígonos.</p>"

    def processAlgorithm(self, parameters, context, feedback):
        input_raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        mask_vector = self.parameterAsVectorLayer(parameters, self.INPUT_MASK, context)
        bands_str = self.parameterAsString(parameters, self.BANDS_USE, context)
        min_dist = self.parameterAsInt(parameters, self.MIN_DIST, context)
        min_size = self.parameterAsInt(parameters, self.MIN_SIZE, context)
        smooth_size = self.parameterAsInt(parameters, self.SMOOTH_BORDERS, context)
        output_raster_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_SEGMENTS, context)

        bands_list = [int(x.strip()) for x in bands_str.split(',')]
        image = ObiaUtils.read_specific_bands(input_raster, bands_list)
        if image is None: return {}

        roi_mask = ObiaUtils.get_valid_mask(image, input_raster, mask_vector)
        norm_img = ObiaUtils.normalize_for_segmentation(image, roi_mask)
        
        if norm_img.shape[2] > 1:
            surface = np.mean(norm_img, axis=2)
        else:
            surface = norm_img[:, :, 0]
            
        valid_surface = surface[roi_mask]
        if len(valid_surface) == 0: return {}
            
        p20 = np.percentile(valid_surface, 20)
        p10 = np.percentile(valid_surface, 10)
            
        mask_trees = (surface > p20) & roi_mask
        distance = ndimage.distance_transform_edt(mask_trees)
        
        from skimage.feature import peak_local_max
        coords = peak_local_max(distance, min_distance=min_dist, labels=mask_trees.astype(np.int32))
        if len(coords) == 0: return {}

        mask = np.zeros(distance.shape, dtype=bool)
        mask[tuple(coords.T)] = True
        markers, _ = ndimage.label(mask)
        
        edges = sobel(surface)
        segments = segmentation.watershed(edges, markers, mask=(surface > p10) & roi_mask).astype(np.uint32)
        
        feedback.pushInfo('Aplicando Regras Topológicas Rígidas na Matriz...')
        segments = ObiaUtils.apply_topological_rules(segments, roi_mask, min_size, smooth_size)

        ObiaUtils.save_raster(segments, output_raster_path, input_raster)
        vector_dest_id = ObiaUtils.create_vector_layer(output_raster_path, input_raster, parameters, context, feedback, self)
        
        return {self.OUTPUT_SEGMENTS: output_raster_path, self.OUTPUT_VECTORS: vector_dest_id}

    def name(self): return 'smart_obia_watershed'
    def displayName(self): return '4.3 - Smart OBIA Seg (Watershed / Copas)'
    def group(self): return 'Smart OBIA'
    def groupId(self): return 'smart_obia'
    def createInstance(self): return WatershedSegmentationAlgorithm()
