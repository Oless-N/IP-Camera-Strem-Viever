import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon, QPixmap

from config_ui import CameraAddDialog


def load_camera_settings(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("JSON file not found")
        return None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stream Recorder")
        self.setMinimumSize(680, 500)
        self.camera_settings = load_camera_settings("configuration.json")
        self.camera = None
        self.is_recording = False
        self.writer = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.setup_ui()
        self.setup_camera_selection()
        self.recording_update_timer = QTimer()
        self.recording_update_timer.timeout.connect(
            self.update_recording_status)

    def setup_ui(self):
        self.video_label = QtWidgets.QLabel()
        self.video_label.setPixmap(QPixmap('img.png'))
        self.record_button = QtWidgets.QPushButton("Record")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.save_file_dialog = QtWidgets.QFileDialog()
        self.camera_selector = QtWidgets.QComboBox()
        self.mode_combobox = QtWidgets.QComboBox()
        self.recording_label = QtWidgets.QLabel("Not Recording")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.record_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.camera_selector)
        layout.addWidget(self.mode_combobox)
        layout.addWidget(self.recording_label)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.record_button.clicked.connect(self.on_record_button_clicked)
        self.stop_button.clicked.connect(self.on_stop_button_clicked)
        self.camera_selector.currentIndexChanged.connect(
            self.on_camera_selected)
        self.mode_combobox.addItems(["Grayscale", "BGR", "RGB", "Thermal"])
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_image)
        self.update_timer.start(30)  # Update at ~33 fps
        self.add_camera_button = QtWidgets.QPushButton("Settings")
        layout.addWidget(self.add_camera_button)
        self.add_camera_button.clicked.connect(self.add_camera)

    def setup_camera_selection(self):
        self.camera_selector.addItem("Default Camera", 0)
        if self.camera_settings:
            rtsp_url = self.format_rtsp_url(**self.camera_settings)
            future = self.executor.submit(
                self.check_camera_availability,
                rtsp_url,
            )
            future.add_done_callback(self.on_camera_check_result)

    def check_camera_availability(self, rtsp_url):
        cap = cv2.VideoCapture(rtsp_url)
        available = cap.isOpened()
        cap.release()
        return available, rtsp_url

    def on_camera_check_result(self, future):
        is_available, rtsp_url = future.result()
        if is_available:
            self.camera_selector.addItem("IP Camera", rtsp_url)
        else:
            self.recording_label.setText(
                f"IP Camera is not accessible."
                f"\nFalling back to default camera.",
            )
        self.on_camera_selected(0)

    def format_rtsp_url(self, login, password, host, port, page):
        return f'rtsp://{login}:{password}@{host}:{port}/{page}'

    def on_camera_selected(self, index):
        if self.camera:
            self.camera.release()
        camera_source = self.camera_selector.itemData(index)
        self.camera = cv2.VideoCapture(camera_source)
        if not self.camera.isOpened():
            self.recording_label.setText("Failed to open ip camera.")

    def on_record_button_clicked(self):
        if not self.is_recording:
            filename, _ = self.save_file_dialog.getSaveFileName(
                self,
                "Save Video",
                "",
                "MP4 (*.mp4)")
            if filename:
                self.is_recording = True
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                frame_size = (
                    int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                )
                self.writer = cv2.VideoWriter(filename, fourcc, 30.0,
                                              frame_size, isColor=True)
                self.start_time = time.time()
                self.recording_update_timer.start(1000)  # 1 sec
                self.update_recording_status()

    def update_image(self):
        ret, frame = self.camera.read()
        if ret:
            frame = self.process_frame(frame,
                                       self.mode_combobox.currentIndex())
            image = QtGui.QImage(  # noqa
                frame.data, frame.shape[1], frame.shape[0],
                QtGui.QImage.Format_RGB888).scaled(
                self.video_label.size(),
                QtCore.Qt.KeepAspectRatio,
            )
            self.video_label.setPixmap(QtGui.QPixmap.fromImage(image))
            if self.is_recording and self.writer:
                self.writer.write(frame)

    def process_frame(self, frame, mode):
        if mode == 0:  # Grayscale
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif mode == 2:  # RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif mode == 3:  # Thermal
            frame = cv2.applyColorMap(frame, cv2.COLORMAP_HOT)
        return frame

    def on_stop_button_clicked(self):
        if self.is_recording:
            self.video_label.setPixmap(QPixmap('img.png'))
            self.is_recording = False
            self.recording_update_timer.stop()
            self.update_recording_status()
            if self.writer:
                self.writer.release()
                self.writer = None
            self.start_time = None
        self.video_label.setPixmap(QtGui.QPixmap('img.png'))

    def update_recording_status(self):
        if self.is_recording:
            elapsed_time = int(time.time() - self.start_time)
            self.recording_label.setText(f"Recording... {elapsed_time} sec")
        else:
            self.recording_label.setText("Not Recording")
            self.recording_update_timer.stop()

    def closeEvent(self, event):
        if self.camera:
            self.camera.release()
        if self.writer:
            self.writer.release()
        self.executor.shutdown(wait=False)
        super().closeEvent(event)

    def add_camera(self):
        dialog = CameraAddDialog(self)
        if dialog.exec():
            camera_info = dialog.get_camera_info()
            print("Camera info:", camera_info)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.png"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
