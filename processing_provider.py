"""
Smart OBIA Processing Provider
Registers all processing algorithms for the plugin
"""

import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

# Importações dos Algoritmos de Apoio e Preparação
from .algorithms.parameter_assistant import SegmentationCalculatorAlgorithm
from .algorithms.indices_algorithm import IndicesAlgorithm
from .algorithms.texture_algorithm import TextureAlgorithm
from .algorithms.stacking_algorithm import StackingAlgorithm
from .algorithms.signature_analyzer import SpectralSignatureAnalyzer

# Importações dos Algoritmos de Segmentação (ATUALIZADOS)
from .algorithms.segmentation_algorithm import (
    FelzenszwalbSegmentationAlgorithm,
    QuickshiftSegmentationAlgorithm,
    WatershedSegmentationAlgorithm
)

# Importação do Algoritmo de Classificação
from .algorithms.classification_algorithm import ClassificationAlgorithm


class SmartOBIAProvider(QgsProcessingProvider):
    """Provider for Smart OBIA processing algorithms."""

    def loadAlgorithms(self):
        """Load all available algorithms in a logical workflow order."""
        # 1. Preparação de Dados e Extração de Atributos Espectrais/Espaciais
        self.addAlgorithm(IndicesAlgorithm())
        self.addAlgorithm(TextureAlgorithm())
        self.addAlgorithm(StackingAlgorithm())
        
        # 2. Ferramentas Analíticas e Auxiliares de Segmentação
        self.addAlgorithm(SpectralSignatureAnalyzer())
        self.addAlgorithm(SegmentationCalculatorAlgorithm())
        
        # 3. Motores de Segmentação Baseados em Objetos (ATUALIZADOS)
        self.addAlgorithm(FelzenszwalbSegmentationAlgorithm())
        self.addAlgorithm(QuickshiftSegmentationAlgorithm())
        self.addAlgorithm(WatershedSegmentationAlgorithm())
        
        # 4. Motor de Inteligência Artificial de Classificação Final
        self.addAlgorithm(ClassificationAlgorithm())

    def id(self):
        """Return the unique ID of the provider."""
        return 'smart_obia'

    def name(self):
        """Return the human-readable name of the provider."""
        return 'Smart OBIA'

    def icon(self):
        """Return the icon for the provider (Pasta Principal)."""
        plugin_dir = os.path.dirname(__file__)
        icon_png = os.path.join(plugin_dir, 'icon.png')
        icon_jpg = os.path.join(plugin_dir, 'icon.jpg')
        
        if os.path.exists(icon_png):
            return QIcon(icon_png)
        elif os.path.exists(icon_jpg):
            return QIcon(icon_jpg)
        return QIcon()

    def longName(self):
        """Return the long name of the provider."""
        return 'Smart OBIA - Object-Based Image Analysis'
