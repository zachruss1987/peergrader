sudo pip install -r requirements.txt
sudo cp *.py /home/www/peergrader/.
sudo cp -a static/. /home/www/peergrader/static/
sudo cp -a templates/. /home/www/peergrader/templates/
sudo restart peergrader
