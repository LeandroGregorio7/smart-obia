"""
Smart OBIA Plugin - Main Plugin Class
"""
import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingAlgorithm, QgsApplication
from qgis.gui import QgisInterface
from .processing_provider import SmartOBIAProvider


class SmartOBIAPlugin:
    """Main plugin class for Smart OBIA."""

    def __init__(self, iface: QgisInterface):
        """Initialize the plugin."""
        self.iface = iface
        self.provider = None

    def initGui(self):
        """Initialize the GUI elements."""
        self.provider = SmartOBIAProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        """Unload the plugin."""
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)

    def icon(self):
        # Aqui é só um dirname, porque o provider já está na mesma pasta do ícone
        plugin_dir = os.path.dirname(__file__)
        icon_path = os.path.join(plugin_dir, 'icon.png')
        return QIcon(icon_path)        
