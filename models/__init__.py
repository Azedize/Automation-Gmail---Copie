# models/__init__.py

"""
Module models - Contient les modèles de données et gestionnaires pour l'application
"""

from .browser_manager import BrowserManager
from .extension_manager import ExtensionManager

# Créer une instance globale du gestionnaire de navigateurs

# Classes exportées
__all__ = [
    'BrowserManager',
    'ExtensionManager'
    ]