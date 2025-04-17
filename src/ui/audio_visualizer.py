"""
Audio visualizer component for displaying microphone levels.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Signal, Slot, Property
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QPaintEvent


class AudioLevelMeter(QWidget):
    """A widget that displays audio levels as a meter."""

    # Signal emitted when the audio level changes
    levelChanged = Signal(float)

    def __init__(self, parent=None):
        """Initialize the audio level meter widget."""
        super().__init__(parent)

        # Set minimum size for the widget
        self.setMinimumSize(200, 30)

        # Initialize properties
        self._level = 0.0  # Current audio level (0.0 to 1.0)
        self._peak_level = 0.0  # Peak level
        self._decay_rate = 0.05  # How quickly the peak level decays

        # Colors
        self._background_color = QColor(40, 40, 40)
        self._low_color = QColor(0, 200, 0)  # Green for low levels
        self._mid_color = QColor(200, 200, 0)  # Yellow for mid levels
        self._high_color = QColor(200, 0, 0)  # Red for high levels
        self._peak_color = QColor(255, 255, 255)  # White for peak indicator

        # Set up a timer for animations
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_peak)
        self._timer.start(50)  # Update every 50ms

    def _update_peak(self):
        """Update the peak level with a decay effect."""
        # Decay the peak level
        if self._peak_level > self._level:
            self._peak_level -= self._decay_rate
            if self._peak_level < self._level:
                self._peak_level = self._level
            self.update()  # Trigger a repaint

    @Slot(float)
    def set_level(self, level):
        """
        Set the current audio level.

        Args:
            level (float): Audio level between 0.0 and 1.0
        """
        # Ensure level is between 0.0 and 1.0
        level = max(0.0, min(1.0, level))

        if level != self._level:
            self._level = level

            # Update peak level if needed
            if level > self._peak_level:
                self._peak_level = level

            # Emit signal
            self.levelChanged.emit(level)

            # Update the widget
            self.update()

    def paintEvent(self, event: QPaintEvent):
        """Paint the audio level meter."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), self._background_color)

        # Calculate dimensions
        width = self.width()
        height = self.height()

        # Draw the level meter
        if self._level > 0:
            # Calculate level width
            level_width = int(width * self._level)

            # Create gradient for different level zones
            green_zone = int(width * 0.6)  # 0-60% is green
            yellow_zone = int(width * 0.8)  # 60-80% is yellow

            # Draw green zone
            if level_width > 0:
                green_width = min(level_width, green_zone)
                painter.fillRect(0, 0, green_width, height, self._low_color)

            # Draw yellow zone
            if level_width > green_zone:
                yellow_width = min(level_width - green_zone, yellow_zone - green_zone)
                painter.fillRect(green_zone, 0, yellow_width, height, self._mid_color)

            # Draw red zone
            if level_width > yellow_zone:
                red_width = level_width - yellow_zone
                painter.fillRect(yellow_zone, 0, red_width, height, self._high_color)

        # Draw peak indicator
        if self._peak_level > 0:
            peak_x = int(width * self._peak_level)
            painter.setPen(QPen(self._peak_color, 2))
            painter.drawLine(peak_x, 0, peak_x, height)

    # Property for level
    level = Property(float, lambda self: self._level, set_level)


class AudioVisualizer(QWidget):
    """A widget that visualizes audio input levels."""

    def __init__(self, parent=None):
        """Initialize the audio visualizer widget."""
        super().__init__(parent)

        # Set up the layout
        layout = QVBoxLayout(self)

        # Add a label
        self.label = QLabel("Microphone Level")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Add the level meter
        self.level_meter = AudioLevelMeter()
        layout.addWidget(self.level_meter)

        # Set layout margins
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Set the layout
        self.setLayout(layout)

    @Slot(float)
    def update_level(self, level):
        """
        Update the audio level display.

        Args:
            level (float): Audio level between 0.0 and 1.0
        """
        self.level_meter.set_level(level)


# Example usage
if __name__ == "__main__":
    import sys
    import random
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    visualizer = AudioVisualizer()
    visualizer.resize(300, 100)
    visualizer.show()

    # Simulate changing audio levels
    def simulate_audio():
        level = random.random() * 0.8  # Random level between 0 and 0.8
        visualizer.update_level(level)

    # Update every 100ms
    timer = QTimer()
    timer.timeout.connect(simulate_audio)
    timer.start(100)

    sys.exit(app.exec_())