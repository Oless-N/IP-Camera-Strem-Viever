import json
import sys
import cv2
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
)
from PySide6.QtCore import QThread, Signal, Slot, Qt
from PySide6.QtGui import QImage, QPixmap, QIcon
from concurrent.futures import ThreadPoolExecutor


config_file = "./configuration.json"


class VideoThread(QThread):
    change_pixmap_signal = Signal(QImage)

    def __init__(self, rtsp_url):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.is_running = False

    def run(self):
        self.is_running = True
        self.executor.submit(self.capture_video)

    def stop(self):
        self.is_running = False
        self.quit()

    def capture_video(self):
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        while self.is_running and cap.isOpened():
            ret, cv_img = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(                        # noqa
                    rgb_image.data,
                    w,
                    h,
                    bytes_per_line,
                    QImage.Format_RGB888,
                )
                p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
                self.change_pixmap_signal.emit(p)


class AppWidget(QWidget):
    def __init__(self, rtsp_url):
        super().__init__()
        self.setWindowTitle("RTSP Stream")
        self.setMinimumSize(680, 500)
        self.disply_width = 640
        self.display_height = 480

        self.image_label = QLabel(self)
        self.image_label.setPixmap(QPixmap('img.png'))
        self.image_label.resize(self.disply_width, self.display_height)

        self.start_button = QPushButton('Start Stream')
        self.stop_button = QPushButton('Stop Stream')

        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.start_button)
        vbox.addWidget(self.stop_button)
        self.setLayout(vbox)

        self.thread = VideoThread(rtsp_url)
        self.start_button.clicked.connect(self.start_streaming)
        self.stop_button.clicked.connect(self.stop_streaming)
        self.thread.change_pixmap_signal.connect(self.update_image)

    @Slot(QImage)
    def update_image(self, qt_img):
        self.image_label.setPixmap(QPixmap.fromImage(qt_img))

    def start_streaming(self):
        if not self.thread.isRunning():
            self.thread.start()

    def stop_streaming(self):
        self.thread.stop()
        self.image_label.setPixmap(QPixmap('img.png'))


if __name__ == "__main__":
    with open(config_file, 'r') as file:
        conf = json.load(file)
        login = conf['login']
        password = conf["password"]
        host = conf["host"]
        port = conf["port"]
        page = conf["page"]
        rtsp_url = f'rtsp://{login}:{password}@{host}:{port}/{page}'
        app = QApplication(sys.argv)
        app_widget = AppWidget(rtsp_url)
        app.setWindowIcon(QIcon("icon.png"))
        app_widget.show()
        sys.exit(app.exec())
