#!/bin/bash

./uninstall.sh 2>/dev/null

install -d /usr/local/bin
install supershow.py /usr/local/bin/supershow
install supershow-converter.py /usr/local/bin/supershow-converter
chmod 755 /usr/local/bin/supershow
chmod 755 /usr/local/bin/supershow-converter

install -d /usr/local/share/supershow
install -d /usr/local/share/doc/supershow/html

install -d /usr/share/locale/es/LC_MESSAGES
install -d /usr/share/locale/fr/LC_MESSAGES

install po/es.mo /usr/share/locale/es/LC_MESSAGES/supershow.mo
install po/fr.mo /usr/share/locale/fr/LC_MESSAGES/supershow.mo
install po/gl.mo /usr/share/locale/gl/LC_MESSAGES/supershow.mo

install supershow.svg /usr/share/pixmaps/
install supershow.svg /usr/local/share/supershow
install supershow.desktop /usr/share/applications/supershow.desktop
install doc/* /usr/local/share/doc/supershow/html
install supershow.glade /usr/local/share/supershow
install script.base /usr/local/share/supershow
install FreeSansBold.ttf /usr/local/share/supershow

