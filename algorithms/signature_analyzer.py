"""
Smart OBIA Spectral Signature Analyzer
Extrai pixels das amostras e gera gráficos interativos de separabilidade de classes com Assistente de Bandas.
"""
import os
import numpy as np
from typing import Dict
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer, 
    QgsProcessingParameterVectorLayer, QgsProcessingParameterField, 
    QgsProcessingParameterFileDestination, QgsFeature, QgsGeometry,
    QgsCoordinateTransform, QgsProject
)
from osgeo import gdal, ogr
import warnings
warnings.filterwarnings('ignore')

class SpectralSignatureAnalyzer(QgsProcessingAlgorithm):
    INPUT_RASTER = 'INPUT_RASTER'
    TRAIN_VECTOR = 'TRAIN_VECTOR'
    CLASS_FIELD = 'CLASS_FIELD'
    OUTPUT_REPORT = 'OUTPUT_REPORT'

    def icon(self):
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        for ext in ['png', 'jpg']:
            icon_path = os.path.join(plugin_dir, f'icon.{ext}')
            if os.path.exists(icon_path): return QIcon(icon_path)
        return QIcon()

    def initAlgorithm(self, config: Dict = None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_RASTER, 'Raster de Estudo (Stack)'))
        self.addParameter(QgsProcessingParameterVectorLayer(self.TRAIN_VECTOR, 'Polígonos de Amostra (Treinamento)'))
        self.addParameter(QgsProcessingParameterField(self.CLASS_FIELD, 'Campo Numérico com ID da Classe', '', self.TRAIN_VECTOR, QgsProcessingParameterField.Numeric))
        self.addParameter(QgsProcessingParameterFileDestination(
            self.OUTPUT_REPORT,
            'Salvar Relatório Interativo (HTML)',
            fileFilter='Relatório Interativo (*.html)'
        ))

    def shortHelpString(self) -> str:
        return """
        <style>.help-box { border: 1px solid #d3d3d3; padding: 10px; background-color: #f7f7f7; }</style>
        <h2>Análise de Assinatura Espectral</h2>
        <div class="help-box">
            <p>Descubra matematicamente quais bandas separam perfeitamente o seu alvo (Ex: Baru) do resto da paisagem!</p>
            <p>O relatório HTML agora inclui um assistente inteligente que calcula a máxima divergência espectral para você.</p>
        </div>"""

    def processAlgorithm(self, parameters: Dict, context, feedback):
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        train_layer = self.parameterAsVectorLayer(parameters, self.TRAIN_VECTOR, context)
        user_field = self.parameterAsString(parameters, self.CLASS_FIELD, context)
        report_path = self.parameterAsFileOutput(parameters, self.OUTPUT_REPORT, context)

        # CORREÇÃO 1: Tratar Case Sensitive do Campo de ID (ID, id, Id, classe)
        class_field = user_field
        for field in train_layer.fields():
            if field.name().lower() == user_field.lower():
                class_field = field.name()
                break

        # 1. Preparar o Raster
        raster_ds = gdal.Open(raster_layer.source())
        if not raster_ds: raster_ds = gdal.Open(raster_layer.dataProvider().dataSourceUri())
        
        geo_transform = raster_ds.GetGeoTransform()
        proj = raster_ds.GetProjection()
        cols, rows, bands = raster_ds.RasterXSize, raster_ds.RasterYSize, raster_ds.RasterCount

        feedback.pushInfo(f"⏳ Lendo imagem de {cols}x{rows} com {bands} bandas usando campo de classe '{class_field}'...")

        transform = QgsCoordinateTransform(train_layer.crs(), raster_layer.crs(), QgsProject.instance())

        # 2. Criar OGR Layer em memória
        ogr_drv = ogr.GetDriverByName('Memory')
        ogr_ds = ogr_drv.CreateDataSource('temp_ogr')
        ogr_layer = ogr_ds.CreateLayer('samples', None, ogr.wkbPolygon)
        ogr_layer.CreateField(ogr.FieldDefn(class_field, ogr.OFTInteger))

        feat_count = 0
        for feat in train_layer.getFeatures():
            if feedback.isCanceled(): break
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
                try:
                    ogr_feat.SetField(class_field, int(feat[class_field]))
                    ogr_layer.CreateFeature(ogr_feat)
                    feat_count += 1
                except (ValueError, TypeError, KeyError):
                    continue

        if feat_count == 0:
            feedback.reportError("Nenhum polígono pôde ser processado. Verifique a camada de amostras ou o nome do campo.")
            return {}

        # 3. Criar Raster de Máscara e Rasterizar
        mem_drv = gdal.GetDriverByName('MEM')
        mask_ds = mem_drv.Create('', cols, rows, 1, gdal.GDT_Int32)
        mask_ds.SetGeoTransform(geo_transform)
        mask_ds.SetProjection(proj)

        gdal.RasterizeLayer(mask_ds, [1], ogr_layer, options=[f"ATTRIBUTE={class_field}"])
        mask_array = mask_ds.GetRasterBand(1).ReadAsArray()
        
        unique_classes = np.unique(mask_array)
        valid_classes = unique_classes[unique_classes > 0]
        
        if len(valid_classes) == 0:
            feedback.reportError("Erro de interseção. As amostras não tocam os pixels.")
            return {}

        # 4. Extrair Pixels
        raster_array = raster_ds.ReadAsArray()
        
        class_stats = {}
        for c in valid_classes:
            pixels = raster_array[:, mask_array == c]
            valid_pixels = pixels[:, ~np.isnan(pixels).any(axis=0)]
            
            if valid_pixels.shape[1] > 0:
                class_stats[int(c)] = {
                    'mean': valid_pixels.mean(axis=1).tolist(),
                    'count': valid_pixels.shape[1]
                }

        # 5. GERAR O HTML COM A FUNÇÃO INTERATIVA (CORREÇÃO 2)
        band_labels = [f"Banda {i+1}" for i in range(bands)]
        colors = ['#2ecc71', '#e74c3c', '#3498db', '#f1c40f', '#9b59b6', '#e67e22', '#34495e', '#1abc9c']

        # Montando dados para o JS
        options_html = ""
        raw_data_js = "{"
        for c, stats in class_stats.items():
            options_html += f"<option value='{c}'>Classe {c}</option>"
            raw_data_js += f"'{c}': {stats['mean']},"
        raw_data_js += "}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Assinatura Espectral OBIA</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 30px; color: #333; }}
                .container {{ background: #fff; max-width: 1000px; margin: auto; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .chart-container {{ position: relative; height: 500px; width: 100%; margin-top: 20px; }}
                .info-box {{ background: #ecf0f1; padding: 15px; border-left: 5px solid #3498db; margin-top: 20px; font-size: 0.9em; }}
                .ai-box {{ background: #e8f8f5; padding: 20px; border-left: 5px solid #1abc9c; margin-top: 20px; border-radius: 4px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 0.9em; }}
                th, td {{ border-bottom: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #34495e; color: white; }}
                button {{ background: #1abc9c; color: white; border: none; padding: 10px 15px; font-size: 14px; border-radius: 4px; cursor: pointer; transition: 0.3s; }}
                button:hover {{ background: #16a085; }}
                select {{ padding: 8px; font-size: 14px; border-radius: 4px; border: 1px solid #ccc; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📈 Assinatura Espectral das Classes</h2>
                
                <div class="ai-box">
                    <h3 style="margin-top: 0; color: #16a085;">🧠 Assistente de Separação Inteligente</h3>
                    <p>Qual classe é o seu <b>alvo principal</b>? (Ex: Baru)</p>
                    <select id="targetClass">
                        {options_html}
                    </select>
                    <button onclick="calculateBestBands()">Descobrir Melhores Bandas</button>
                    <div id="recommendationOutput" style="margin-top: 15px; font-size: 15px;"></div>
                </div>

                <div class="chart-container">
                    <canvas id="spectralChart"></canvas>
                </div>

                <div class="info-box">
                    <strong>Contagem de Pixels Coletados por Classe:</strong>
                    <table><tr><th>Classe</th><th>Pixels Úteis Extraídos</th></tr>
        """
        
        for c, stats in class_stats.items():
            html += f"<tr><td>Classe <b>{c}</b></td><td>{stats['count']} pixels</td></tr>"
        html += "</table></div></div>"

        datasets = []
        color_idx = 0
        for c, stats in class_stats.items():
            color = colors[color_idx % len(colors)]
            datasets.append({
                'label': f'Classe {c}',
                'data': stats['mean'],
                'borderColor': color,
                'backgroundColor': color,
                'borderWidth': 3,
                'pointRadius': 4,
                'tension': 0.1
            })
            color_idx += 1

        html += f"""
            <script>
                const ctx = document.getElementById('spectralChart').getContext('2d');
                const spectralChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {band_labels},
                        datasets: {datasets}
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{ mode: 'index', intersect: false }},
                        scales: {{
                            y: {{ title: {{ display: true, text: 'Valor Médio' }} }},
                            x: {{ title: {{ display: true, text: 'Bandas do Stack' }} }}
                        }}
                    }}
                }});

                const rawData = {raw_data_js};
                const bandLabels = {band_labels};

                function calculateBestBands() {{
                    const targetId = document.getElementById("targetClass").value;
                    const targetMeans = rawData[targetId];
                    let separability = [];

                    if (Object.keys(rawData).length <= 1) {{
                        document.getElementById("recommendationOutput").innerHTML = "<span style='color: #e74c3c;'>É necessário ter amostras de pelo menos 2 classes diferentes para comparar!</span>";
                        return;
                    }}

                    // Calcula a menor distância (pior caso) entre o alvo e as outras classes para cada banda
                    for (let i = 0; i < bandLabels.length; i++) {{
                        let minDiff = Infinity;
                        for (const [id, means] of Object.entries(rawData)) {{
                            if (id === targetId) continue;
                            let diff = Math.abs(targetMeans[i] - means[i]);
                            if (diff < minDiff) minDiff = diff;
                        }}
                        separability.push({{ index: i, bandName: bandLabels[i], diff: minDiff }});
                    }}

                    // Ordena da maior diferença de separabilidade para a menor
                    separability.sort((a, b) => b.diff - a.diff);

                    // Pega o Top 3
                    const topBands = separability.slice(0, 3);
                    const bandNumbers = topBands.map(b => b.bandName.replace('Banda ', '')).join(", ");
                    const bandNamesHtml = topBands.map(b => "<b>" + b.bandName + "</b>").join(" | ");

                    document.getElementById("recommendationOutput").innerHTML = 
                        "✅ As 3 melhores bandas para separar a <b>Classe " + targetId + "</b> de todas as outras são:<br>" +
                        "<span style='font-size: 1.3em; color: #27ae60;'>" + bandNamesHtml + "</span><br><br>" +
                        "💡 <b>Como usar isso:</b> Copie os números <b>" + bandNumbers + "</b> e cole no campo de Bandas da ferramenta de Segmentação (SLIC)!";
                }}
            </script>
        </body></html>
        """

        if report_path:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(report_path))
            except Exception:
                pass

        return {self.OUTPUT_REPORT: report_path}

    def name(self) -> str: return 'smart_obia_signature_analyzer'
    def displayName(self) -> str: return '3.5 - Smart OBIA Spectral Signature'
    def group(self) -> str: return 'Smart OBIA'
    def groupId(self): return 'smart_obia'
    def createInstance(self): return SpectralSignatureAnalyzer()
