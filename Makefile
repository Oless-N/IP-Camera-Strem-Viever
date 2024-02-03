run:
	python3 ip_cameras_viewer.py

init_desktop_icon:
	pip3 install -r requirements.txt
	python3 desktop_init.py
	sudo chmod +x RTSPStreamViewer.desktop
	sudo cp RTSPStreamViewer.desktop ~/.local/share/applications/
	sudo cp RTSPStreamViewer.desktop /usr/share/applications/