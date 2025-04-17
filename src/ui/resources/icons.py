"""
Icons and resources for the KoeLingo Translator application.
"""

import os
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize

# Base directory for resources
RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(RESOURCE_DIR, 'icons')

# Create directory if it doesn't exist
os.makedirs(ICONS_DIR, exist_ok=True)

class AppIcons:
    """Helper class for application icons"""
    @staticmethod
    def get_icon(name, color="#42a846"):
        """Get an icon for the application"""
        # Dictionary of built-in SVG icons
        svg_icons = {
            "mic": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <path fill="{color}" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path fill="{color}" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>""",

            "mic_off": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <path fill="{color}" d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l1.66 1.66c-.71.33-1.5.52-2.31.52-2.76 0-5.3-2.1-5.3-5.1H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c.91-.13 1.77-.45 2.54-.9L19.73 21 21 19.73 4.27 3z"/>
            </svg>""",

            "stop": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <rect fill="{color}" x="6" y="6" width="12" height="12"/>
            </svg>""",

            "microphone": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <path fill="white" d="M12,2c-1.7,0-3,1.3-3,3v7c0,1.7,1.3,3,3,3s3-1.3,3-3V5C15,3.3,13.7,2,12,2z"/>
                <path fill="white" d="M19,10v1c0,3.9-3.1,7-7,7s-7-3.1-7-7v-1H3v1c0,4.4,3.2,8,7.2,8.7V22h3.6v-2.3c4-0.7,7.2-4.3,7.2-8.7v-1H19z"/>
            </svg>""",

            "swap": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <path fill="{color}" d="M16 17.01V10h-2v7.01h-3L15 21l4-3.99h-3zM9 3L5 6.99h3V14h2V6.99h3L9 3z"/>
            </svg>""",

            "download": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <path fill="{color}" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>""",

            "speaker": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <path fill="{color}" d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </svg>"""
        }

        # If icon is in dictionary, create from SVG
        if name in svg_icons:
            # Create a pixmap from the SVG string
            svg_data = svg_icons[name]
            pixmap = QPixmap(QSize(64, 64))
            pixmap.fill("transparent")
            pixmap.loadFromData(svg_data.encode('utf-8'), 'svg')
            return QIcon(pixmap)

        # Default fallback
        return QIcon.fromTheme(name)

    @staticmethod
    def mic_icon():
        """Get mic icon"""
        return AppIcons.get_icon("microphone")

    @staticmethod
    def stop_icon():
        """Get stop icon"""
        return AppIcons.get_icon("stop", "#ffffff")

    @staticmethod
    def mic_off_icon():
        """Get mic-off icon"""
        return AppIcons.get_icon("mic_off", "#d32f2f")

    @staticmethod
    def swap_icon():
        """Get swap icon"""
        return AppIcons.get_icon("swap", "#ffffff")

    @staticmethod
    def download_icon():
        """Get download icon"""
        return AppIcons.get_icon("download", "#ffffff")

    @staticmethod
    def speaker_icon():
        """Get speaker icon"""
        return AppIcons.get_icon("speaker", "#ffffff")