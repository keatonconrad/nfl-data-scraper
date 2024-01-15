from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
)
from transformers import Transformer
from game_getter import GameGetter

game_getter = GameGetter()
transformer = Transformer()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NFL Data Scraper")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        # Add a label and buttons for Transform Options
        layout.addWidget(QLabel("Transform Options"))
        self.add_button(
            layout,
            "Perform All Transformations",
            transformer.perform_all_transformations,
        )
        self.add_button(layout, "Expand Team Stats", transformer.expand_team_stats)
        self.add_button(layout, "Split Team Stats", transformer.split_team_stats)
        self.add_button(layout, "Stagger Team Stats", transformer.stagger_team_stats)
        self.add_button(
            layout, "Preprocess Team Stats", transformer.preprocess_team_stats
        )

        # Add a separator label
        layout.addWidget(QLabel("------"))

        # Add a label and buttons for Scrape Options
        layout.addWidget(QLabel("Scrape Options"))
        self.add_button(layout, "Get All Games", game_getter.get_all_games)
        self.add_button(
            layout, "Get Most Recent Games", game_getter.get_most_recent_games
        )

        # Set the layout to the central widget
        self.central_widget.setLayout(layout)

    def add_button(self, layout, text, function):
        button = QPushButton(text)
        button.clicked.connect(function)
        layout.addWidget(button)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
