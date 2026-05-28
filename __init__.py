"""
Inicialização do plugin Smart OBIA.
O QGIS exige a função classFactory para carregar o plugin.
"""

def classFactory(iface):
    """Instancia a classe principal do plugin."""
    from .smart_obia_plugin import SmartOBIAPlugin
    return SmartOBIAPlugin(iface)