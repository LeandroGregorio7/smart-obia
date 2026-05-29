"""
Smart OBIA Classification Algorithm with Feature Importance & Report Export
"""
import os
import numpy as np
from typing import Dict
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer, 
    QgsProcessingParameterVectorLayer, QgsProcessingParameterField, 
    QgsProcessingParameterEnum, QgsProcessingParameterVectorDestination, 
    QgsProcessingParameterRasterDestination, QgsProcessingParameterFileDestination,
    QgsRasterLayer, QgsVectorLayer, QgsSpatialIndex, QgsFields, QgsField, 
    QgsFeature, QgsGeometry, QgsWkbTypes
)
from osgeo import gdal, ogr
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.mixture import GaussianMixture
import warnings
warnings.filterwarnings('ignore')

class ClassificationAlgorithm(QgsProcessingAlgorithm):
    INPUT_SEGMENTS_VECTOR = 'INPUT_SEGMENTS_VECTOR'
    INPUT_SEGMENTS_RASTER = 'INPUT_SEGMENTS_RASTER'
    TRAIN_VECTOR = 'TRAIN_VECTOR'
    CLASS_FIELD = 'CLASS_FIELD'
    CLASSIFIER = 'CLASSIFIER'
    OUTPUT_VECTOR = 'OUTPUT_VECTOR'
    OUTPUT_RASTER = 'OUTPUT_RASTER'
    OUTPUT_REPORT = 'OUTPUT_REPORT'

    CLASSIFIERS_LIST = ['Random Forest', 'Extra Trees', 'SVM', 'GMM', 'CatBoost']

    def icon(self):
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        icon_png = os.path.join(plugin_dir, 'icon.png')
        icon_jpg = os.path.join(plugin_dir, 'icon.jpg')
        if os.path.exists(icon_png): return QIcon(icon_png)
        elif os.path.exists(icon_jpg): return QIcon(icon_jpg)
        return QIcon()

    def initAlgorithm(self, config: Dict = None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_SEGMENTS_VECTOR, '1. Vetor de Segmentação', [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_SEGMENTS_RASTER, '2. Raster de Segmentação'))
        self.addParameter(QgsProcessingParameterVectorLayer(self.TRAIN_VECTOR, '3. Amostras de Treinamento', [QgsProcessing.TypeVectorAnyGeometry]))
        self.addParameter(QgsProcessingParameterField(self.CLASS_FIELD, '4. Campo com ID da Classe', '', self.TRAIN_VECTOR, QgsProcessingParameterField.Numeric))
        self.addParameter(QgsProcessingParameterEnum(self.CLASSIFIER, '5. Algoritmo', options=self.CLASSIFIERS_LIST, defaultValue=0))
        
        self.addParameter(QgsProcessingParameterFileDestination(
            self.OUTPUT_REPORT,
            '6. Exportar Relatório Analítico (Opcional - HTML ou CSV)',
            fileFilter='Relatório Visual (*.html);;Planilha Excel (*.csv)',
            optional=True
        ))
        
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_VECTOR, 'Saída Vetorial (Opcional)', optional=True))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, 'Saída Raster (Recomendado)'))

    def shortHelpString(self) -> str: 
        return """<h2>Classificador OBIA</h2>
        <p>Treina e classifica a imagem segmentada.</p>
        <p><b>NOVIDADE:</b> Salve o relatório de importância das bandas em HTML ou CSV (Excel) para TODOS os algoritmos, incluindo SVM e GMM!</p>"""

    def processAlgorithm(self, parameters: Dict, context, feedback):
        segments_layer = self.parameterAsVectorLayer(parameters, self.INPUT_SEGMENTS_VECTOR, context)
        segment_raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT_SEGMENTS_RASTER, context)
        train_layer = self.parameterAsVectorLayer(parameters, self.TRAIN_VECTOR, context)
        class_field = self.parameterAsString(parameters, self.CLASS_FIELD, context)
        classifier_idx = self.parameterAsEnum(parameters, self.CLASSIFIER, context)
        report_path = self.parameterAsFileOutput(parameters, self.OUTPUT_REPORT, context)

        seg_ds = gdal.Open(segment_raster_layer.source())
        if not seg_ds: seg_ds = gdal.Open(segment_raster_layer.dataProvider().dataSourceUri())

        train_geoms = {f.id(): (f.geometry(), f[class_field]) for f in train_layer.getFeatures() if f.geometry()}
        train_index = QgsSpatialIndex(train_layer.getFeatures())

        ignore_fields = ['segment_id', 'id', 'fid', 'dn'] 
        feature_indices = []
        feature_names = []
        for i, field in enumerate(segments_layer.fields()):
            if field.name().lower() not in ignore_fields and field.isNumeric():
                feature_indices.append(i)
                feature_names.append(field.name())

        seg_id_idx = segments_layer.fields().lookupField('segment_id')
        if seg_id_idx == -1: seg_id_idx = segments_layer.fields().lookupField('DN')

        X_train, y_train, X_all, seg_ids_all, all_features = [], [], [], [], []

        for feat in segments_layer.getFeatures():
            seg_id = feat.attributes()[seg_id_idx]
            if not seg_id: continue
            geom = feat.geometry()
            if geom.isNull(): continue
            
            attrs = [0.0 if a is None else float(a) for a in [feat.attributes()[i] for i in feature_indices]]
            X_all.append(attrs)
            seg_ids_all.append(int(seg_id))
            all_features.append(feat)
            
            assigned_class = None
            for tid in train_index.intersects(geom.boundingBox()):
                t_geom, t_class = train_geoms[tid]
                if geom.intersects(t_geom):
                    assigned_class = t_class
                    break
            if assigned_class is not None:
                X_train.append(attrs)
                y_train.append(int(assigned_class))

        if not X_train: return {}

        X_train, y_train, X_all = np.array(X_train), np.array(y_train), np.array(X_all)

        model = None
        gmms = None
        classes = None

        if classifier_idx == 0:
            model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1).fit(X_train, y_train)
        elif classifier_idx == 1:
            model = ExtraTreesClassifier(n_estimators=100, random_state=42, n_jobs=-1).fit(X_train, y_train)
        elif classifier_idx == 2:
            model = SVC(kernel='rbf', probability=False, random_state=42).fit(X_train, y_train)
        elif classifier_idx == 3:
            classes = np.unique(y_train)
            gmms = {c: GaussianMixture(n_components=1, random_state=42).fit(X_train[y_train == c]) for c in classes}
        elif classifier_idx == 4:
            from catboost import CatBoostClassifier
            model = CatBoostClassifier(iterations=100, task_type="CPU", silent=True, random_seed=42).fit(X_train, y_train)

        # Função Helper Universal de Previsão
        def predict_func(X_data):
            if classifier_idx == 3:
                s = np.zeros((X_data.shape[0], len(classes)))
                for idx_c, c in enumerate(classes):
                    s[:, idx_c] = gmms[c].score_samples(X_data)
                return classes[np.argmax(s, axis=1)]
            else:
                return np.ravel(model.predict(X_data))

        # =========================================================
        # GERAÇÃO DO RANKING (AGORA SUPORTA TODOS OS ALGORITMOS)
        # =========================================================
        has_importances = False
        importances = np.zeros(len(feature_names))

        if model is not None or classifier_idx == 3:
            if classifier_idx in [0, 1, 4] and hasattr(model, 'feature_importances_'):
                # Algoritmos que fornecem pesos nativos (Árvores)
                importances = model.feature_importances_
            else:
                # Algoritmos geométricos (SVM, GMM): Importância por Permutação (Magia Matemática!)
                feedback.pushInfo("\n⚙️ Calculando pesos do SVM/GMM via Importância por Permutação...")
                np.random.seed(42)
                baseline_pred = predict_func(X_train)
                baseline_acc = np.mean(baseline_pred == y_train)
                
                for i in range(X_train.shape[1]):
                    X_shuff = X_train.copy()
                    np.random.shuffle(X_shuff[:, i])
                    shuff_acc = np.mean(predict_func(X_shuff) == y_train)
                    importances[i] = max(0.0, baseline_acc - shuff_acc) # O quanto o modelo piorou sem essa banda
            
            # Normaliza para 100%
            if np.sum(importances) > 0:
                importances = importances / np.sum(importances)
            else:
                importances = np.ones(len(feature_names)) / len(feature_names)
                
            indices = np.argsort(importances)[::-1]
            has_importances = True

        if has_importances:
            feedback.pushInfo("\n" + "="*50)
            feedback.pushInfo("📊 RELATÓRIO DE IMPORTÂNCIA DAS VARIÁVEIS")
            feedback.pushInfo("="*50)
            for f in range(len(feature_names)):
                feat_name = feature_names[indices[f]]
                importance_val = importances[indices[f]] * 100
                bar_length = int(importances[indices[f]] * 50) 
                bar = '█' * bar_length
                feedback.pushInfo(f"{feat_name.ljust(12)} | {bar} ({importance_val:.1f}%)")
            feedback.pushInfo("="*50 + "\n")

        # Salva o Arquivo HTML/CSV Universal
        if report_path and has_importances:
            try:
                if report_path.lower().endswith('.csv'):
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write("Banda_ou_Metrica,Importancia_Percentual\n")
                        for f_idx in range(len(feature_names)):
                            feat_name = feature_names[indices[f_idx]]
                            importance_val = importances[indices[f_idx]] * 100
                            f.write(f"{feat_name},{importance_val:.2f}\n")
                    feedback.pushInfo(f"✅ Relatório CSV salvo em: {report_path}")

                elif report_path.lower().endswith('.html'):
                    max_val = importances[indices[0]] * 100
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write("<html><head><meta charset='utf-8'><title>Relatório OBIA</title>")
                        f.write("<style>body{font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin:30px; color:#333; background-color:#f4f7f6;} ")
                        f.write(".container{background:#fff; padding:20px; border-radius:8px; box-shadow:0 4px 8px rgba(0,0,0,0.1); max-width:800px; margin:auto;} ")
                        f.write("h2{color:#2c3e50; border-bottom:2px solid #3498db; padding-bottom:10px;} ")
                        f.write("table{border-collapse:collapse; width:100%; margin-top:20px;} ")
                        f.write("th,td{border-bottom:1px solid #ddd; padding:12px; text-align:left;} ")
                        f.write("th{background-color:#ecf0f1; color:#2c3e50;} ")
                        f.write(".bar-bg{background-color:#e0e0e0; width:100%; border-radius:4px; overflow:hidden;} ")
                        f.write(".bar-fill{background-color:#3498db; height:20px;} ")
                        f.write("</style></head><body><div class='container'>")
                        f.write(f"<h2>📊 Relatório Analítico (Algoritmo: {self.CLASSIFIERS_LIST[classifier_idx]})</h2>")
                        
                        f.write("<table><tr><th style='width:20%'>Banda / Métrica</th><th style='width:15%'>Peso (%)</th><th>Gráfico de Relevância</th></tr>")
                        for f_idx in range(len(feature_names)):
                            feat_name = feature_names[indices[f_idx]]
                            importance_val = importances[indices[f_idx]] * 100
                            relative_width = (importance_val / max_val) * 100 if max_val > 0 else 0
                            f.write(f"<tr><td><b>{feat_name}</b></td><td>{importance_val:.2f}%</td>")
                            f.write(f"<td><div class='bar-bg'><div class='bar-fill' style='width:{relative_width}%;'></div></div></td></tr>")
                        f.write("</table>")
                        f.write("</div></body></html>")
                    feedback.pushInfo(f"✅ Relatório HTML salvo com sucesso!")
            except Exception as e:
                feedback.reportError(f"Erro ao salvar relatório: {e}")

        # PREVISÃO FINAL E EXPORTAÇÃO (Vetor e Raster)
        y_pred = predict_func(X_all)
        results = {}

        output_vector = self.parameterAsOutputLayer(parameters, self.OUTPUT_VECTOR, context)
        if output_vector and output_vector != 'TEMPORARY_OUTPUT':
            new_fields = QgsFields()
            for f in segments_layer.fields(): new_fields.append(f)
            new_fields.append(QgsField('Class_OBIA', QVariant.Int))
            
            (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT_VECTOR, context, new_fields, segments_layer.wkbType(), segments_layer.crs())
            if sink is not None:
                for feat, pred in zip(all_features, y_pred):
                    new_feat = QgsFeature(new_fields)
                    new_feat.setGeometry(feat.geometry())
                    attrs = feat.attributes()
                    attrs.append(int(pred))
                    new_feat.setAttributes(attrs)
                    sink.addFeature(new_feat)
                results[self.OUTPUT_VECTOR] = dest_id

        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)
        if output_raster:
            seg_array = seg_ds.GetRasterBand(1).ReadAsArray()
            mapping = np.full(int(np.max(seg_array)) + 1, -9999, dtype=np.int16)
            mapping[seg_ids_all] = y_pred
            
            out_ds = gdal.GetDriverByName('GTiff').Create(output_raster, seg_ds.RasterXSize, seg_ds.RasterYSize, 1, gdal.GDT_Int16)
            out_ds.SetGeoTransform(seg_ds.GetGeoTransform())
            out_ds.SetProjection(seg_ds.GetProjection())
            out_band = out_ds.GetRasterBand(1)
            out_band.SetNoDataValue(-9999)
            out_band.WriteArray(mapping[seg_array])
            out_band.FlushCache()
            results[self.OUTPUT_RASTER] = output_raster

        if report_path:
            results[self.OUTPUT_REPORT] = report_path
            
            # Abertura nativa pelo QGIS (Se o HTML foi gerado com sucesso)
            if report_path.lower().endswith('.html') and has_importances:
                try:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(report_path))
                except Exception:
                    pass

        return results

    def name(self) -> str: return 'smart_obia_classification'
    def displayName(self) -> str: return '5 - Smart OBIA Classification'
    def group(self) -> str: return 'Smart OBIA'
    def groupId(self): return 'smart_obia'
    def createInstance(self): return ClassificationAlgorithm()
