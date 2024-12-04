from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QComboBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTextEdit,
    QLabel,
)
from PyQt6.QtCore import QThread, pyqtSignal
import sys
from sacagawea.interface.capture import CaptureManager
from sacagawea.core.config import Config
from types import SimpleNamespace


class TranslationWorker(QThread):
    output_signal = pyqtSignal(str, str)

    def __init__(self, capture_manager):
        super().__init__()
        self.capture_manager = capture_manager
        self.is_running = True

    def run(self):
        self.capture_manager.start_capture(self.output_signal)

    def stop(self):
        self.is_running = False
        if self.capture_manager:
            self.capture_manager.stop_capture()
            self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Language should be no barrier")
        self.setMinimumSize(800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        control_layout = QHBoxLayout()

        self.from_lang = QComboBox()
        self.to_lang = QComboBox()
        languages = [
            ("Arabic", "ar"),
            ("Chinese", "zh"),
            ("English", "en"),
            ("Farsi", "fa"),
            ("French", "fr"),
            ("German", "de"),
            ("Hebrew", "he"),
            ("Hindi", "hi"),
            ("Italian", "it"),
            ("Japanese", "ja"),
            ("Korean", "ko"),
            ("Portuguese", "pt"),
            ("Russian", "ru"),
            ("Spanish", "es"),
            ("Turkish", "tr"),
        ]
        for lang_name, lang_code in languages:
            self.from_lang.addItem(lang_name, lang_code)
            self.to_lang.addItem(lang_name, lang_code)

        self.model_select = QComboBox()
        models = ["tiny", "base", "small", "medium", "large"]
        for model in models:
            self.model_select.addItem(model)

        self.toggle_button = QPushButton("Start")
        self.toggle_button.clicked.connect(self.toggle_translation)

        control_layout.addWidget(QLabel("From:"))
        control_layout.addWidget(self.from_lang)
        control_layout.addWidget(QLabel("To:"))
        control_layout.addWidget(self.to_lang)
        control_layout.addWidget(QLabel("Model:"))
        control_layout.addWidget(self.model_select)
        control_layout.addWidget(self.toggle_button)
        layout.addLayout(control_layout)

        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.translated_text = QTextEdit()
        self.translated_text.setReadOnly(True)

        layout.addWidget(QLabel("Original Text:"))
        layout.addWidget(self.original_text)
        layout.addWidget(QLabel("Translated Text:"))
        layout.addWidget(self.translated_text)

        self.capture_manager = CaptureManager()
        self.worker = None

    def toggle_translation(self):
        if self.toggle_button.text() == "Start":
            self.start_translation()
        else:
            self.stop_translation()

    def start_translation(self):
        from_code = self.from_lang.currentData()
        to_code = self.to_lang.currentData()
        model = self.model_select.currentText()

        args = SimpleNamespace(
            model=model,
            path=None,
            from_code=from_code,
            to_code=to_code,
        )
        config = Config(args)

        self.capture_manager.configure(
            from_code=from_code, to_code=to_code, model=model
        )

        self.worker = TranslationWorker(self.capture_manager)
        self.worker.output_signal.connect(self.update_output)
        self.worker.start()

        self.toggle_button.setText("Stop")

    def stop_translation(self):
        if self.worker:
            self.worker.stop()
            self.worker.deleteLater()
            self.worker = None
        self.toggle_button.setText("Start")

    def update_output(self, original, translated):
        self.original_text.append(original)
        self.translated_text.append(translated)

    def closeEvent(self, event):
        self.stop_translation()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
