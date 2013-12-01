#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2007 (C) Raster Software Vigo (Sergio Costas)

# SuperShow-converter is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# SuperShow-converter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os

def import_file(ifile,ofile):
	
	nlinea=1
	ofile.write("supershow\n")
	old_time=-1
	for linea in ifile:
		if (linea!="") and (linea!="\n"):
			pos1=linea.find(":")
			if pos1==-1:
				return nlinea
			pos2=linea.find(":",pos1+1)
			if pos2==-1:
				return nlinea
			try:
				thour=int(linea[:pos1])
				tmin=int(linea[pos1+1:pos2])
				tsec=float(linea[pos2+1:])
				tsec=int(tsec*1000)
			except:
				return nlinea
			quantity=thour*3600000+tmin*60000+tsec
			if (quantity<=old_time):
				print "The time in line "+str(nlinea)+" is smaller than the time in the previous line"
				sys.exit(1)
			ofile.write("time:"+str(quantity)+"\n")
			old_time=quantity
			nlinea+=1
	return 0


def time_convert(the_times):
	
	thour=the_times/3600000
	tmin=(the_times%3600000)/60000
	tsec=(float(the_times%60000))/1000.0
	return str(thour)+":"+str(tmin)+":"+str(tsec)


def export_file(ifile,ofile):
	
	first=ifile.readline()
	if first[-1]=="\n":
		first=first[:-1]
	if first!="supershow":
		return 1
	
	nlinea=2
	offset=0
	old_time=-1
	for linea in ifile:
		if (linea!="") and (linea!="\n"):
			if linea[:5]=="time:":
				quantity=time_convert(offset+int(linea[5:]))
				try:
					ofile.write(quantity)
					ofile.write("\n")
				except:
					return nlinea
					
			if linea[:7]=="offset:":
				try:
					offset=int(linea[7:])
				except:
					return nlinea
			nlinea+=1
	return 0

print "Supershow-converter. Version 1.0"
print

if (len(sys.argv)!=4) or ((sys.argv[1]!="import") and (sys.argv[1]!="export")):
	print "Usage: supershow-converter [import/export] input-filename output-filename"
	sys.exit(1)
	
try:
	ifile=open(sys.argv[2],"r")
except:
	print "Can't open input file "+str(sys.argv[2])
	sys.exit(1)
	
try:
	ofile=open(sys.argv[3],"w")
except:
	print "Can't open output file "+str(sys.argv[3])
	sys.exit(1)
	
if sys.argv[1]=="import":
	ret_val=import_file(ifile,ofile)
else:
	ret_val=export_file(ifile,ofile)

ifile.close()
ofile.close()
if ret_val!=0:
	os.remove(sys.argv[3])
	print "Syntax error in line "+str(ret_val)+" of file "+str(sys.argv[2])
	sys.exit(1)
