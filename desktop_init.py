import os

current_path = os.getcwd()

app_name = "RTSP Stream Viewer"
comment = (
    "This application allows you to view the video stream from the "
    "Goke GK7205V300 camera via RTSP protocol without the need for an SD card. "
    "The application is implemented in Python using the OpenCV library "
    "for video processing and PySide6 for the graphical interface.",
)
script_name = "main.py"
icon_name = "icon.png"

script_path = os.path.join(current_path, script_name)
icon_path = os.path.join(current_path, icon_name)

desktop_entry = f"""
[Desktop Entry]
Type=Application
Encoding=UTF-8
Name={app_name}
Comment={comment}
Exec=python3 {script_path}
Icon={icon_path}
Terminal=false
Categories=Development;
"""

desktop_filename = "RTSPStreamViewer.desktop"
with open(desktop_filename, "w") as desktop_file:
    desktop_file.write(desktop_entry)

print(f'Created {desktop_filename}')
