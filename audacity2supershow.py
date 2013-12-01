#/usr/bin/env python 
# -*- coding: UTF-8 -*-

# Copyright 2008 (C) Ralph Zajac

# audacity2supershow is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# audacity2supershow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""Audacity to SuperShow converter, by Ralph Zajac
get labels file exported from Audacity and convert time stamps and labels to
SuperShow readable style"""

import sys

def importAudacity(audaFile):
    "Read Audacity labels file and return list"

    myList = []
    fileObj = file(audaFile, 'r')
    for eachLine in fileObj:
        timeCode = str(int(float(eachLine.split()[0]) * 1000))
        myList.append(timeCode)
    fileObj.close()
    return myList

def writeSupershowFile(newFileName, myList):
    "Write SuperShow readable time stamps file"

    newFile = file(newFileName+'.supershow', 'w')
    newFile.write('supershow\n')
    for timeCode in myList:
        newFile.write('time:'+timeCode+'\n')

def startHere():
    "Start Here"

    if len(sys.argv!=3):
        print "Audacity2SuperShow converter."
	print "Get labels file exported from Audacity and convert time stamps and labels to SuperShow readable style."
	print
	print "Usage: audacity2supershow.py INPUT-FILENAME"
	sys.exit(1)
    fileName = sys.argv[1]
    myList = importAudacity(fileName)
    writeSupershowFIle(fileName, myList)

if __name__ == '__main__':
    startHere()
