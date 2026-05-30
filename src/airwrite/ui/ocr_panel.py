from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class OcrPanel(QWidget):
    candidate_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ocr_panel")
        self._candidate_buttons: list[QPushButton] = []
        self._current_selection = ""

        layout = QVBoxLayout(self)
        self.title_label = QLabel("OCR")
        self.status_label = QLabel("Session: IDLE")
        self.stroke_count_label = QLabel("Strokes: 0")
        self.selection_label = QLabel("Selected: --")
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.stroke_count_label)
        layout.addWidget(self.selection_label)
        layout.addStretch(1)

    def set_session_info(self, *, phase: str, stroke_count: int) -> None:
        self.status_label.setText(f"Session: {phase}")
        self.stroke_count_label.setText(f"Strokes: {stroke_count}")

    def set_candidates(self, candidates: list[str]) -> None:
        self.clear_candidates()
        layout = self.layout()
        for candidate in candidates:
            button = QPushButton(candidate)
            button.clicked.connect(lambda _checked=False, text=candidate: self._select_candidate(text))
            self._candidate_buttons.append(button)
            layout.insertWidget(layout.count() - 1, button)

    def clear_candidates(self) -> None:
        layout = self.layout()
        for button in self._candidate_buttons:
            layout.removeWidget(button)
            button.deleteLater()
        self._candidate_buttons = []

    def candidate_texts(self) -> list[str]:
        return [button.text() for button in self._candidate_buttons]

    def candidate_buttons(self) -> list[QPushButton]:
        return list(self._candidate_buttons)

    def current_selection_text(self) -> str:
        return self._current_selection

    def set_selected_text(self, text: str) -> None:
        self._current_selection = text
        label_text = text if text else "--"
        self.selection_label.setText(f"Selected: {label_text}")

    def reset(self) -> None:
        self.clear_candidates()
        self.set_selected_text("")
        self.set_session_info(phase="IDLE", stroke_count=0)

    def _select_candidate(self, text: str) -> None:
        self.set_selected_text(text)
        self.candidate_selected.emit(text)
