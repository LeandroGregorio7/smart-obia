"""
Smart OBIA Segmentation Calculator
Helps users calculate the exact parameters for Felzenszwalb, Quickshift, and Watershed.
"""
import os
import math
from qgis.PyQt.QtGui import QIcon
from typing import Dict
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterEnum
)

class SegmentationCalculatorAlgorithm(QgsProcessingAlgorithm):
    RESOLUTION = 'RESOLUTION'
    TARGET_TYPE = 'TARGET_TYPE'

    TARGETS = [
        'Árvore Nativa / Copa Larga (~6 metros de diâmetro)',
        'Árvore de Plantio / Copa Fina (~3 metros de diâmetro)',
        'Casa / Edificação Pequena (~10 metros de largura)',
        'Veículo / Carro (~4 metros de comprimento)',
        'Talhão Agrícola / Quadra Urbana (~100 metros de largura)'
    ]

    def icon(self):
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        icon_png = os.path.join(plugin_dir, 'icon.png')
        icon_jpg = os.path.join(plugin_dir, 'icon.jpg')
        if os.path.exists(icon_png): return QIcon(icon_png)
        elif os.path.exists(icon_jpg): return QIcon(icon_jpg)
        return QIcon()

    def initAlgorithm(self, config: Dict = None):
        self.addParameter(QgsProcessingParameterNumber(
            self.RESOLUTION, 
            'Resolução Espacial da Imagem (Metros por Pixel)', 
            type=QgsProcessingParameterNumber.Double, 
            defaultValue=1.0, 
            minValue=0.01, 
            maxValue=1000.0
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.TARGET_TYPE, 
            'O que você deseja mapear?', 
            options=self.TARGETS, 
            defaultValue=0
        ))

    def shortHelpString(self) -> str:
        return """
        <style>
            .help-box { border: 1px solid #d3d3d3; border-radius: 4px; padding: 10px; margin-bottom: 15px; background-color: #f7f7f7; }
            .help-title { font-weight: bold; color: #2c3e50; margin-bottom: 8px; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px; }
        </style>
        <h2 style="color: #2c3e50;">Calculadora de Segmentação OBIA</h2>
        <p>Não sabe como preencher os parâmetros (Escala, Kernel, Distância) nos novos segmentadores? Esta ferramenta traduz o tamanho real do seu alvo para a matemática dos algoritmos.</p>
        
        <div class="help-box">
            <div class="help-title">📐 Como usar:</div>
            <p>Insira a resolução real da sua imagem (Ex: 1.0m para imagens aéreas comuns ou 0.1m para VANTs) e selecione o seu alvo na lista.</p>
            <p>Abra a aba <b>LOG</b> após rodar: o QGIS imprimirá os valores exatos para você copiar e colar no Felzenszwalb, Quickshift ou Watershed, junto com um dicionário explicando cada campo!</p>
        </div>"""

    def processAlgorithm(self, parameters: Dict, context, feedback):
        resolution = self.parameterAsDouble(parameters, self.RESOLUTION, context)
        target_idx = self.parameterAsEnum(parameters, self.TARGET_TYPE, context)

        # Base de Conhecimento: Diâmetro estimado (m) e Área estimada (m²)
        knowledge_base = {
            0: {"name": "Árvore Nativa", "diameter_m": 6.0, "area_m2": 28.0},
            1: {"name": "Árvore de Plantio", "diameter_m": 3.0, "area_m2": 7.0},
            2: {"name": "Casa/Edificação", "diameter_m": 10.0, "area_m2": 100.0},
            3: {"name": "Veículo", "diameter_m": 4.0, "area_m2": 16.0},
            4: {"name": "Talhão Agrícola", "diameter_m": 100.0, "area_m2": 10000.0}
        }

        target = knowledge_base[target_idx]
        
        # Geometria Básica do Alvo em Pixels
        pixel_area_m2 = resolution * resolution
        target_area_px = target["area_m2"] / pixel_area_m2
        target_diam_px = target["diameter_m"] / resolution

        # -------------------------------------------------------------
        # MATEMÁTICA DOS ALGORITMOS
        # -------------------------------------------------------------
        
        # 4.1 FELZENSZWALB
        # A Escala é brutalmente sensível à quantidade de pixels. Usamos uma constante empírica baseada na área.
        fz_scale = min(1000, max(10, int(target_area_px * 1.5)))
        fz_min_size = min(500, max(5, int(target_area_px * 0.25)))

        # 4.2 QUICKSHIFT
        # Kernel depende da resolução (imagens VANT com muito detalhe foliar precisam de mais suavização)
        if resolution <= 0.15: qs_kernel = 7.0
        elif resolution <= 0.5: qs_kernel = 5.0
        else: qs_kernel = 3.0
        # Max dist reflete o diâmetro do objeto que queremos abraçar
        qs_max_dist = max(5.0, round(target_diam_px * 1.2, 1))

        # 4.3 WATERSHED (Copas)
        # A distância mínima entre picos é basicamente o raio da árvore
        wat_min_dist = max(3, int(target_diam_px / 2.0))

        # -------------------------------------------------------------
        # IMPRESSÃO DO RELATÓRIO NO LOG
        # -------------------------------------------------------------
        feedback.pushInfo("\n" + "="*70)
        feedback.pushInfo("🚀 TRADUTOR DE PARÂMETROS DE SEGMENTAÇÃO 🚀")
        feedback.pushInfo("="*70)
        feedback.pushInfo(f"Alvo Selecionado...: {target['name']}")
        feedback.pushInfo(f"Resolução da Imagem: {resolution} metros/pixel")
        feedback.pushInfo(f"Tamanho do Alvo....: ~{int(target_area_px)} pixels de área | ~{int(target_diam_px)} pixels de diâmetro")
        
        feedback.pushInfo("\n" + "-"*70)
        feedback.pushInfo("🟢 4.1 - FELZENSZWALB (Segmentador Orgânico Principal)")
        feedback.pushInfo("-" * 70)
        feedback.pushInfo(f"▶ Escala.........: {fz_scale}")
        feedback.pushInfo("  [Dicionário] Controla o nível de agregação dos grafos. Valores maiores geram polígonos maiores (ignora bordas fracas).")
        feedback.pushInfo(f"▶ Tamanho Mínimo.: {fz_min_size}")
        feedback.pushInfo("  [Dicionário] Força o algoritmo a juntar 'farelos' isolados (sal e pimenta) ao polígono vizinho maior.")

        feedback.pushInfo("\n" + "-"*70)
        feedback.pushInfo("🔵 4.2 - QUICKSHIFT (Crescimento de Região Espectral)")
        feedback.pushInfo("-" * 70)
        feedback.pushInfo(f"▶ Kernel (Suavização)...: {qs_kernel}")
        feedback.pushInfo("  [Dicionário] Nível de desfoque aplicado antes de agrupar. Imagens de VANT precisam de kernel alto (5 a 7) para ignorar o sombreamento entre as folhas.")
        feedback.pushInfo(f"▶ Distância Máxima......: {qs_max_dist}")
        feedback.pushInfo("  [Dicionário] Raio máximo (em pixels) que o algoritmo usa para 'puxar' cores parecidas. Reflete o diâmetro da copa do Baru.")

        feedback.pushInfo("\n" + "-"*70)
        feedback.pushInfo("🟠 4.3 - WATERSHED (Isolador de Copas Brilhantes)")
        feedback.pushInfo("-" * 70)
        feedback.pushInfo(f"▶ Distância Mínima: {wat_min_dist}")
        feedback.pushInfo("  [Dicionário] Raio mínimo (em pixels) esperado entre os troncos de duas árvores. Impede que uma copa muito grande e iluminada seja fatiada ao meio.")
        feedback.pushInfo("="*70 + "\n")

        return {}

    def name(self) -> str: return 'smart_obia_segmentation_calculator'
    def displayName(self) -> str: return '4.0 - Smart OBIA Segmentation Calculator'
    def group(self) -> str: return 'Smart OBIA'
    def groupId(self) -> str: return 'smart_obia'
    def createInstance(self): return SegmentationCalculatorAlgorithm()
