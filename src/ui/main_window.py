"""
Main window for the KoeLingo application.
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QTextEdit, QSplitter, QComboBox)
from PySide6.QtCore import Qt, Slot, Signal, QSize, qVersion, QRect
from PySide6.QtGui import QFont, QIcon, QColor, QPalette, QPixmap, QPainter, QBrush

from .audio_visualizer import AudioVisualizer
from .resources import AppIcons


class MainWindow(QMainWindow):
    """Main window for the KoeLingo application."""

    # Signal for when recording state changes
    recordingStateChanged = Signal(bool)

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Set window properties
        self.setWindowTitle("KoeLingo Translator")
        self.resize(800, 600)

        # Set dark theme
        self._set_dark_theme()

        # Apply global stylesheet
        self._set_stylesheet()

        # Initialize recording state
        self._is_recording = False

        # Set up the central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout is vertical
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Create status bar
        self.statusBar().showMessage("Ready")

        # Create UI components
        self._create_title_area()
        self._create_input_area()
        self._create_control_panel()
        self._create_output_area()

        # Connect signals and slots
        self._connect_signals()

    def _set_dark_theme(self):
        """Set dark theme for the application."""
        palette = self.palette()

        # Define color mapping
        colors = {
            "Window": QColor(30, 30, 30),
            "WindowText": QColor(255, 255, 255),
            "Base": QColor(45, 45, 45),
            "AlternateBase": QColor(35, 35, 35),
            "Text": QColor(255, 255, 255),
            "Button": QColor(60, 60, 60),
            "ButtonText": QColor(255, 255, 255),
            "BrightText": QColor(255, 255, 255),
            "Highlight": QColor(42, 130, 70),
            "HighlightedText": QColor(255, 255, 255)
        }

        # Check Qt version and apply colors accordingly
        qt_version = qVersion().split('.')
        is_qt6 = int(qt_version[0]) >= 6

        for role_name, color in colors.items():
            if is_qt6:
                # Qt6 style with ColorRole enum
                palette.setColor(getattr(QPalette.ColorRole, role_name), color)
            else:
                # Qt5 style
                palette.setColor(getattr(QPalette, role_name), color)

        self.setPalette(palette)

    def _set_stylesheet(self):
        """Set global stylesheet for consistent styling."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #2d2d2d;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                color: #ffffff;
                border: none;
            }
            QComboBox {
                background-color: #2d2d2d;
                padding: 5px 10px;
                border-radius: 5px;
                min-height: 30px;
                color: #ffffff;
                border: none;
            }
            QComboBox::drop-down {
                width: 20px;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #42a846;
            }
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border-radius: 5px;
                padding: 5px 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
        """)

    def _create_title_area(self):
        """Create the title area with 'Translate' heading."""
        title_label = QLabel("Translate")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)

        self.main_layout.addWidget(title_label)

    def _create_input_area(self):
        """Create the input text area with language selection."""
        # Input text area and language selection container
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)

        # Text input
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter text to translate...")
        self.input_text.setMinimumHeight(150)

        # Source language selection
        self.source_language = QComboBox()
        self.source_language.addItem("Japanese")
        self.source_language.addItem("English")
        self.source_language.addItem("Chinese")
        self.source_language.addItem("Korean")
        self.source_language.setCurrentIndex(0)

        input_layout.addWidget(self.input_text)
        input_layout.addWidget(self.source_language)

        self.main_layout.addWidget(input_container)

    def _create_control_panel(self):
        """Create the control panel with buttons and audio visualizer."""
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # Create button container for arranging buttons in a row
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignCenter)

        # Download button
        self.download_button = QPushButton()
        self.download_button.setIcon(AppIcons.download_icon())
        self.download_button.setIconSize(QSize(24, 24))
        self.download_button.setFixedSize(50, 50)
        self.download_button.setToolTip("Save translation to file")
        self.download_button.setStatusTip("Save the current translation text to a file")
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                border-radius: 25px;
            }
        """)

        # Record button (main center button)
        self.record_button = QPushButton()
        self.record_button.setIcon(AppIcons.mic_icon())
        self.record_button.setIconSize(QSize(36, 36))
        self.record_button.setCheckable(True)
        self.record_button.setFixedSize(80, 80)
        self.record_button.setToolTip("Start listening (click to start/stop)")
        self.record_button.setStatusTip("Start or stop listening to microphone input for translation")
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;  /* Bright green like in the image */
                border-radius: 40px;        /* Perfectly round */
                border: none;
            }
            QPushButton:checked {
                background-color: #F44336;  /* Bright red like in the image */
            }
            QPushButton:hover {
                background-color: #43A047;  /* Slightly darker green on hover */
            }
            QPushButton:checked:hover {
                background-color: #E53935;  /* Slightly darker red on hover when checked */
            }
        """)

        # Swap languages button
        self.swap_button = QPushButton()
        self.swap_button.setIcon(AppIcons.swap_icon())
        self.swap_button.setIconSize(QSize(24, 24))
        self.swap_button.setFixedSize(50, 50)
        self.swap_button.setToolTip("Swap languages")
        self.swap_button.setStatusTip("Swap source and target languages")
        self.swap_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                border-radius: 25px;
            }
        """)

        # Speaker button
        self.speaker_button = QPushButton()
        self.speaker_button.setIcon(AppIcons.speaker_icon())
        self.speaker_button.setIconSize(QSize(24, 24))
        self.speaker_button.setFixedSize(50, 50)
        self.speaker_button.setToolTip("Text-to-Speech: Read translated text aloud")
        self.speaker_button.setStatusTip("Use text-to-speech to read the translated text aloud")
        self.speaker_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                border-radius: 25px;
            }
        """)

        # Add buttons to layout
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.swap_button)
        button_layout.addWidget(self.speaker_button)

        # Add button container to control panel
        control_layout.addStretch(1)
        control_layout.addWidget(button_container)

        # Add audio visualizer
        self.audio_visualizer = AudioVisualizer()
        self.audio_visualizer.setFixedHeight(60)
        self.audio_visualizer.setMinimumWidth(150)
        self.audio_visualizer.setToolTip("Microphone audio level indicator")
        self.audio_visualizer.setStatusTip("Shows microphone input level - green for normal speech, yellow for medium volume, red for high volume")
        control_layout.addWidget(self.audio_visualizer)

        control_layout.addStretch(1)

        # Add to main layout
        self.main_layout.addWidget(control_panel)

    def _create_output_area(self):
        """Create the output text area with target language selection."""
        # Output text area and language selection container
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(10)

        # Output text
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)

        # Target language selection
        self.target_language = QComboBox()
        self.target_language.addItem("English")
        self.target_language.addItem("Japanese")
        self.target_language.addItem("Chinese")
        self.target_language.addItem("Korean")
        self.target_language.setCurrentIndex(0)

        output_layout.addWidget(self.output_text)
        output_layout.addWidget(self.target_language)

        self.main_layout.addWidget(output_container)

    def _connect_signals(self):
        """Connect signals and slots."""
        self.record_button.clicked.connect(self._toggle_recording)
        self.swap_button.clicked.connect(self._swap_languages)
        self.speaker_button.clicked.connect(self._speak_text)

    @Slot(bool)
    def _toggle_recording(self, checked):
        """
        Toggle the recording state.

        Args:
            checked (bool): Whether the button is checked
        """
        self._is_recording = checked

        if checked:
            # Use the stop icon when recording
            self.record_button.setIcon(AppIcons.stop_icon())
            self.record_button.setToolTip("Stop Listening")
        else:
            self.record_button.setIcon(AppIcons.mic_icon())
            self.record_button.setToolTip("Start Listening")

        # Emit signal
        self.recordingStateChanged.emit(checked)

    @Slot()
    def _swap_languages(self):
        """Swap source and target languages."""
        source_index = self.source_language.currentIndex()
        target_index = self.target_language.currentIndex()

        self.source_language.setCurrentIndex(target_index)
        self.target_language.setCurrentIndex(source_index)

        # Also swap text if there's any content
        source_text = self.input_text.toPlainText()
        target_text = self.output_text.toPlainText()

        if source_text or target_text:
            self.input_text.setText(target_text)
            self.output_text.setText(source_text)

    @Slot()
    def _speak_text(self):
        """Speak the translated text using text-to-speech."""
        text = self.output_text.toPlainText()
        if not text:
            self.statusBar().showMessage("No text to speak", 3000)
            return

        # For now, just show a status message
        # In a real implementation, this would connect to a TTS engine
        self.statusBar().showMessage(f"Speaking: {text[:30]}..." if len(text) > 30 else f"Speaking: {text}", 3000)

    @Slot(float)
    def update_audio_level(self, level):
        """
        Update the audio level visualizer.

        Args:
            level (float): Audio level between 0.0 and 1.0
        """
        if hasattr(self, 'audio_visualizer'):
            self.audio_visualizer.update_level(level)

    @Slot(str)
    def update_input_text(self, text):
        """
        Update the input text.

        Args:
            text (str): The text to display in the input area
        """
        self.input_text.setText(text)

    @Slot(str)
    def update_output_text(self, text):
        """
        Update the output/translated text.

        Args:
            text (str): The text to display in the output area
        """
        self.output_text.setText(text)


# Example usage
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())