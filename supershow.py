#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2007-2008 (C) Raster Software Vigo (Sergio Costas)

# SuperShow is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# SuperShow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import pygtk # for testing GTK version number
pygtk.require ('2.0')
import gtk
import gtk.glade
import gobject
import subprocess
import locale
import gettext
import time
import pygst
pygst.require("0.10")
import gst
import shutil
import signal
import glob


class show_error:

	def __init__(self,msg_error,exit_at_end=False):
		
		global globaldir
		
		self.arbol=gtk.glade.XML(globaldir+"supershow.glade","error_dialog",domain="supershow")
		self.arbol.signal_autoconnect(self)
		self.ventana=self.arbol.get_widget("error_dialog")
		etiqueta=self.arbol.get_widget("error_label")
		etiqueta.set_text(msg_error)
		self.ventana.show()
		self.ventana.run()
		if exit_at_end:
			gtk.main_quit()
		self.ventana.hide()
		self.ventana.destroy()
		self.ventana=None
		self.arbol=None


class generate:

	""" creates the SWF file itself """

	def __init__(self,output,fichero_pdf,fichero_audio,tiempos,backend,dpi=72,quality=85,audio_delay=0,show_buttons=True,play_again=True,autohide=True):

		global globaldir

		print "Backend: "+str(backend)

		self.fichero_pdf=fichero_pdf
		self.output=output
		self.tiempos=[]
		if show_buttons:
			self.add_buttons=1
		else:
			self.add_buttons=0
		if play_again:
			self.play_again=1
		else:
			self.play_again=0
		if autohide:
			self.autohide_buttons=1
		else:
			self.autohide_buttons=0
		for elemento in tiempos:
			self.tiempos.append(elemento+audio_delay)
		self.quality=quality
		
		self.arbol=gtk.glade.XML(globaldir+"supershow.glade","process_dialog",domain="supershow")
		self.ventana=self.arbol.get_widget("process_dialog")
		
		self.backend=backend

		if backend=="gs":
			slides=prepare()
			if False==slides.prepare_slides(fichero_pdf,output,resolution=dpi,deletedir=False):
				return
			self.gen_script(quality,False)
			self.slides_done=False
		else:
			self.slides_done=False
			self.gen_script(0,True)

		
		self.playwav=False
		self.tiempo=self.arbol.get_widget("timelabel")
		self.time_format = gst.Format(gst.FORMAT_TIME)
		
		try:
			fichero=open(self.output+'.tmp/salida.wav')
			fichero.close()
		except:
			self.playwav=True
			self.gen_sound(fichero_audio)

		
		self.ventana.show()
		self.status_label=self.arbol.get_widget("creating_label")
		self.status_label.set_text(_("Converting audio"))
		self.progreso=self.arbol.get_widget("pulse_creating")
		self.proceso=None
		self.temporizador=gobject.timeout_add(500,self.temporizador)
		retv=self.ventana.run()
		self.ventana.hide()
		self.ventana.destroy()
		self.progreso=None
		self.ventana=None
		self.arbol=None
		print "finalizado"
		if retv==1:
			self.mierror=show_error(_("Slideshow sucessfully created"))
		elif retv==2:
			self.mierror=show_error(_("Failed to create the SWF file"))
		elif retv==3:
			self.mierror=show_error(_("PDF2SWF failed. Try to use GhostScript as backend instead"))
		else:
			gobject.source_remove(self.temporizador)
			self.mierror=show_error(_("Canceled by the user"))
		print "salgo"


	def launch_program(self,program):
		
		print "Launching "+program
		return subprocess.Popen(program,shell=True,bufsize=8129)


	def temporizador(self):
		
		self.progreso.pulse()
		
		if self.playwav==True:
			v1,v2,v3=self.player.get_state()
			if v2==gst.STATE_NULL: # ended the play
				self.playwav=False
		
		if (self.playwav==False) and (self.proceso==None):
			if self.slides_done:
				self.status_label.set_text(_("Generating SWF"))
				self.proceso=self.launch_program('swfc "'+self.output+'.tmp/script.sc"')
			else:
				self.status_label.set_text(_("Creating slides"))
				if self.backend=="gs":
					self.proceso=self.launch_program('swfc "'+self.output+'.tmp/script_slides.sc"')
				else:
					self.proceso=self.launch_program('pdf2swf -s filloverlap -s linksopennewwindow  -j '+str(self.quality)+' "'+self.fichero_pdf+'" -o "'+self.output+'.tmp/slides.swf"')
			return True
		

		if self.proceso==None:
			return True

		if self.proceso.poll()==None:
			return True

		the_error=self.proceso.wait()

		if the_error==0: # no error
			if self.slides_done==False:
				self.slides_done=True
				self.proceso=None
				return True
			self.ventana.response(1) # no error
		else:
			if self.slides_done==False:
				self.ventana.response(3) # pdf2swf failed
			else:
				self.ventana.response(2) # a kind of error
		return False


	def get_param(self,text):
		
		pos1_old=0;
		while True:
			pos1=text.find("{",pos1_old)
			if pos1==-1: # no more sequences to replace
				return (-1,0,"","")
			
			pos2=text.find("}",pos1)
			if pos2==-1: # sequence not ended: no more sequences to replace
				return (-1,0,"","")
			
			t1=text.find(":",pos1,pos2) # check that there are ':' in the middle
			if t1==-1: # if there isn't it, it's not a sequence
				pos1_old=pos2
				continue
			
			t2=text.find("\n",pos1,pos2) # check that there aren't newlines in the middle
			if t2!=-1: # if there are it, it's not a sequence
				pos1_old=pos2
				continue
			
			t2=text.find(";",pos1,pos2) # check that there aren't semicolons in the middle
			if t2!=-1: # if there are it, it's not a sequence
				pos1_old=pos2
				continue
			
			t2=text.find(" ",pos1,pos2) # check that there aren't blank spaces in the middle
			if t2!=-1: # if there are it, it's not a sequence
				pos1_old=pos2
				continue
			
			return (pos1,pos2,text[pos1+1:t1],text[t1+1:pos2])
			

	def gen_script(self,quality=85,pdf2swf=False):

		global globaldir

		print "Generating the script"

		counter=len(self.tiempos)				
		self.tiempos.append(1000+self.tiempos[-1])
		
		filescript=open(globaldir+"script.base","r")
		contenido=filescript.read()
		filescript.close()
		
		contenido+="\n"
		
		while True:

			(start,end,param,var)=self.get_param(contenido)
			if start==-1:
				break
			
			if param=="filename":
				if var=="out":
					contenido=contenido[:start]+self.output+".swf"+contenido[end+1:]
					continue
				if var=="slides":
					contenido=contenido[:start]+self.output+".tmp/slides.swf"+contenido[end+1:]
					continue
				if var=="audio":
					contenido=contenido[:start]+self.output+".tmp/salida.wav"+contenido[end+1:]
					continue
				if var=="basepath":
					contenido=contenido[:start]+self.output+contenido[end+1:]
					continue
				if var=="installpath":
					contenido=contenido[:start]+globaldir+contenido[end+1:]
					continue
				
			if param=="maxtime":
				contenido=contenido[:start]+var+"="+str(counter)+";"+contenido[end+1:]
				continue
			
			if param=="timelist":
				list_tmp=var+"[0]=0;\n"
				num = 1
				for element in self.tiempos:
					t=int(element)
					list_tmp+=var+'['+str(num)+']='+str(t)+';\n'
					num+=1
				contenido=contenido[:start]+list_tmp+contenido[end+1:]
				continue
			
			if param=="var":
				if var=="addbuttons":
					contenido=contenido[:start]+str(self.add_buttons)+contenido[end+1:]
					continue
				if var=="playagain":
					contenido=contenido[:start]+str(self.play_again)+contenido[end+1:]
					continue
				if var=="autohidebuttons":
					contenido=contenido[:start]+str(self.autohide_buttons)+contenido[end+1:]
					continue

				contenido=contenido[:start]+"0"+contenido[end+1:]
				continue
			
			# if not recognized, remove it
			contenido=contenido[:start]+contenido[end+1:]

		print "Saving the script at "+self.output+".tmp/script.sc"
		fichero=open(self.output+".tmp/script.sc","w")
		fichero.write(contenido)
		fichero.close()
		
		if pdf2swf==False:
			
			# If we are not using PDF2SWF, we must generate a second script
			# to create the slides from JPEG files
			
			contenido=["# Presentation script, generated by SuperShow"]
			contenido.append('.flash filename="'+self.output+'.tmp/slides.swf" version=6 fps=1')
			contenido.append('')
			listfiles=glob.glob(self.output+".tmp/[0-9][0-9][0-9]_slide.jpg")
			counter=0
			
			for afile in listfiles:
				contenido.append('.jpeg s'+str(counter)+' "'+afile+'" quality="'+str(quality)+'%"')
				counter+=1
				
			contenido.append('')
			for contad in range(counter):
				contenido.append('.frame '+str(contad+1))
				contenido.append('\t.put s'+str(contad))
				contenido.append('')
			contenido.append('.end')
			
			print "Saving the script at "+self.output+".tmp/script_slides.sc"
			fichero=open(self.output+".tmp/script_slides.sc","w")
			fichero.write("\n".join(contenido))
			fichero.close()


	def gen_sound(self,audio):
		
		self.player = gst.element_factory_make("playbin", "player")
		
		# creamos la salida completa a WAV
		myaudiosink = gst.element_factory_make('wavenc', "my-sink")
		salidaudio=gst.element_factory_make("filesink","salida")

		# creamos el divisor
		mytee = gst.element_factory_make("tee","divisor")
		queue = gst.element_factory_make("queue","queue2")		
		queue.set_property("max-size-time",5000000000) # up to five seconds in the WAV queue

		# creamos el fakesink para el video
		nulsink=gst.element_factory_make("fakesink")
		nulsink.set_property("can-activate-push",True)
		nulsink.set_property("can-activate-pull",True)
		nulsink.set_property("signal-handoffs",True)

		bin = gst.element_factory_make("bin")
		bin.add(myaudiosink)
		bin.add(salidaudio)
		
		bin.add(mytee)
		bin.add(queue)
		mytee.link(queue)
		queue.link(myaudiosink)
		myaudiosink.link(salidaudio)
		
		ghost_pad = gst.GhostPad("sink",mytee.get_pad("sink"))
		bin.add_pad(ghost_pad)
		salidaudio.set_property("location",self.output+".tmp/salida.wav")
		self.player.set_property("audio-sink", bin)
		self.player.set_property("video-sink",nulsink)
		self.player.set_property('uri', "file://" + audio)
		self.player.set_state(gst.STATE_PLAYING)
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()
		bus.connect('message', self.on_message)
		#bus.connect('sync-message::element', self.on_sync_message)


	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
		elif t == gst.MESSAGE_ERROR:
			self.player.set_state(gst.STATE_NULL)


	def on_sync_message(self, bus, message):
		if message.structure is None:
			return
		message_name = message.structure.get_name()
		if message_name == 'prepare-xwindow-id':
			imagesink = message.src
			imagesink.set_property('force-aspect-ratio', True)
			imagesink.set_xwindow_id(self.ventana_film.window.xid)
		

class prepare:

	""" Generates the JPG files from the PDF """

	def prepare_slides(self,fichero_pdf,output,resolution=60,deletedir=True):
		
		global globaldir
		
		self.arbol=gtk.glade.XML(globaldir+"supershow.glade","progress_dialog",domain="supershow")
		self.ventana=self.arbol.get_widget("progress_dialog")
		self.ventana.show()
		self.fichero_pdf=fichero_pdf
		self.output=output
		self.proces=self.arbol.get_widget("proceso")
		self.status=self.arbol.get_widget("estado")

		if self.convert_pdf(resolution,deletedir):
			return False
		
		retv=self.ventana.run()
		if retv<0:
			os.kill(self.proceso.pid,signal.SIGKILL)
			self.proceso.wait()
		self.ventana.hide()
		self.ventana.destroy()
		if retv==1: # no error
			return True

		if deletedir:
			try:
				shutil.rmtree(self.output+".tmp")
			except OSError:
				print "No original directory"	
		
		if retv==2: # there was an error
			tempo=show_error(_("Failed to create slides from PDF with GS"))
		else:
			tempo=show_error(_("Aborted"))

		return False


	def convert_pdf(self,resolution,erase):
		if erase:
			try:
				shutil.rmtree(self.output+".tmp")
			except OSError:
				print "No original directory"

		try:
			os.mkdir(self.output+".tmp")
		except OSError:
			if erase:
				show_error(_("Failed to create the output directory."))
				return True

		self.proces.set_text(_("Extracting slides from PDF"))
		command="gs -dNOPAUSE -dBATCH -sDEVICE=jpeg -sOutputFile=\""+self.output+".tmp/%03d_slide.jpg\" -r"+str(resolution)+" \""+self.fichero_pdf+"\""
		print "Running: "+command
		self.proceso=subprocess.Popen(command,shell=True,bufsize=32,stdout=subprocess.PIPE)
		self.watcher=gobject.io_add_watch(self.proceso.stdout,gobject.IO_IN+gobject.IO_HUP+gobject.IO_ERR,self.waiting_chars)
		return False


	def waiting_chars(self,source,condition):
		linea=self.proceso.stdout.readline()
		if linea=="":
			msgerror=self.proceso.wait()
			if msgerror==0:
				self.ventana.response(1) # ended fine
			else:
				self.ventana.response(2) # error
			return False
		self.status.set_text(linea[:-1])
		return True



class config_dialog:
	
	def __init__(self):
		
		global globaldir
		
		self.arbol=gtk.glade.XML(globaldir+"supershow.glade","config_dialog",domain="supershow")
		self.arbol.signal_autoconnect(self)
		
		file_filter=gtk.FileFilter()
		file_filter.set_name(_("PDF files"))
		file_filter.add_mime_type("application/pdf")
		file_filter2=gtk.FileFilter()
		file_filter2.set_name(_("All files"))
		file_filter2.add_pattern("*")
		w=self.arbol.get_widget("presentfile")
		w.add_filter(file_filter)
		w.add_filter(file_filter2)

		
		file_filter3=gtk.FileFilter()
		file_filter3.set_name(_("Audio/video files"))
		file_filter3.add_mime_type("video/*")
		file_filter3.add_mime_type("audio/*")
		file_filter4=gtk.FileFilter()
		file_filter4.set_name(_("All files"))
		file_filter4.add_pattern("*")
		w=self.arbol.get_widget("audiofile")
		w.add_filter(file_filter3)
		w.add_filter(file_filter4)

		
		self.w=self.arbol.get_widget("config_dialog")
		self.w.show()
		self.check_params()
		retv=self.w.run()
		self.w.hide()
		self.w.destroy()
		self.w=None
		self.arbol=None
		self.estado=False
		if retv==-6:
			while (self.outfile[-1]==os.sep):
				self.outfile=self.outfile[:-1]
			if self.outfile=="":
				return
			if self.outdir[-1]!=os.sep:
				self.outdir+=os.sep
			output=self.outdir+self.outfile
			while True:
				position=output.find(os.sep+os.sep)
				if (position!=-1):
					output=output[:position]+output[position+1:]
				else:
					break
			prepara=prepare()
			self.estado=prepara.prepare_slides(self.pdf,output)


	def salida_changed(self,widget):
		self.check_params()

	def salida_activated(self,widget):
		if self.estado:
			self.w.response(-6)

	def outputdir_changed(self,widget):
		self.check_params()

		
	def pdf_changed(self,widget):
		self.check_params()

		
	def audio_changed(self,widget):
		self.check_params()


	def check_params(self):
	
		audio=self.arbol.get_widget("audiofile")
		pdf=self.arbol.get_widget("presentfile")
		output=self.arbol.get_widget("fichero_salida")
		outdir=self.arbol.get_widget("outputdir")
		conversor=self.arbol.get_widget("config_accept")
		
		self.audio=audio.get_filename()
		self.pdf=pdf.get_filename()
		self.outfile=output.get_text()
		self.outdir=outdir.get_filename()
		
		self.estado=True
		if (self.audio==None):
			self.estado=False
		if (self.pdf==None):
			self.estado=False
		if (self.outfile==""):
			self.estado=False
		if (self.outdir==None):
			self.estado=False
		conversor.set_sensitive(self.estado)


class main_window:
	
	def __init__(self):
		
		global globaldir
		
		self.arbol=gtk.glade.XML(globaldir+"supershow.glade","main_window",domain="supershow")
		self.arbol.signal_autoconnect(self)
		self.mainwindow=self.arbol.get_widget("main_window")
		
		self.configuration={} # no files yet
		self.tiempos=[] # no timings
		
		self.current_slide_w=self.arbol.get_widget("current_slide")
		
		self.time_format = gst.Format(gst.FORMAT_TIME)
		self.tiempo = self.arbol.get_widget("sound_position")
		self.slide_pic = self.arbol.get_widget("slide_pic")
		self.slide_pic.set_from_pixbuf(None)
		self.ventana_film = self.arbol.get_widget("video")
		
		self.file_filter=gtk.FileFilter()
		self.file_filter.add_pattern("*.supershow")
		
		self.pic_width = 320
		self.pic_height = 240
		self.curr_pic = None
		
		self.sound_aborted = False
		
		self.old_width = -1
		self.old_height = -1
		
		self.reproduciendo=False
		self.set_buttons()
		self.mainwindow.show()
		

	def main_window_delete_event(self,arg1,arg2):
		
		global globaldir
		
		arbol=gtk.glade.XML(globaldir+"supershow.glade","ask_exit",domain="supershow")
		w=arbol.get_widget("ask_exit")
		w.show()
		retv=w.run()
		w.hide()
		w.destroy()
		w=None
		arbol=None
		if retv==-6:
			gtk.main_quit()
		else:
			return True


	def new_presentation_clicked(self,arg1):
		
		if len(self.configuration)!=0: # there's already files selected
			arbol=gtk.glade.XML(globaldir+"supershow.glade","new_files_dialog",domain="supershow")
			w=arbol.get_widget("new_files_dialog")
			w.show()
			retv=w.run()
			w.hide()
			w.destroy()
			w=None
			arbol=None
			if retv!=-6:
				return
		
		self.tiempos=[]
		self.configuration={}
		self.sound_aborted = False
		dialogo=config_dialog()
		if dialogo.estado:
			self.configuration["pdf"]=dialogo.pdf
			self.configuration["output"]=dialogo.outdir+dialogo.outfile
			self.configuration["audio"]=dialogo.audio
		else:
			self.configuration={}
		self.set_buttons()


	def about_clicked(self,arg1):
		
		arbol=gtk.glade.XML(globaldir+"supershow.glade","about1",domain="supershow")
		w=arbol.get_widget("about1")
		w.show()
		w.run()
		w.hide()
		w.destroy()
		w=None
		arbol=None

	
	def set_buttons(self):
		
		""" sets the status of the buttons in the main window """
		
		global globaldir
		
		w=self.arbol.get_widget("slide_pic")
		
		new_b=True
		
		if len(self.configuration)==0:
			w=self.arbol.get_widget("audio_label")
			w.set_text(_("No file"))
			w=self.arbol.get_widget("pdf_label")
			w.set_text(_("No file"))
			open_b=False
			add_b=False
		else:
			w=self.arbol.get_widget("audio_label")
			w.set_text(self.configuration["audio"].split(os.sep)[-1])
			w=self.arbol.get_widget("pdf_label")
			w.set_text(self.configuration["pdf"].split(os.sep)[-1])
			open_b=True
			add_b=True			
			
		if (len(self.tiempos)==0):
			save_b=False
			gen_b=False
		else:
			save_b=True
			gen_b=True
			add_b=False

		if self.reproduciendo:
			new_b=False
			add_b=False
			open_b=False
			save_b=False
			gen_b=False
			add_b=True
		
		w=self.arbol.get_widget("new_presentation")
		w.set_sensitive(new_b)
		w=self.arbol.get_widget("add_slide")
		w.set_sensitive(add_b)
		w=self.arbol.get_widget("open_presentation")
		w.set_sensitive(open_b)
		w=self.arbol.get_widget("save_presentation")
		w.set_sensitive(save_b)
		w=self.arbol.get_widget("generate_slideshow")
		w.set_sensitive(gen_b)


	def generate_slideshow_clicked(self,arg1):

		ventana=use_dialog()

		if ventana.usar=="":
			return
		
		converter=generate(self.configuration["output"],self.configuration["pdf"],self.configuration["audio"],self.tiempos,ventana.usar,ventana.dpi,ventana.quality,ventana.retardo,ventana.showbuttons,ventana.playagain,ventana.autohidebuttons)		
		


	def convert_ns(self, time_int):
		time_int = time_int / 10000000
		if time_int >= 360000:
			_hours = time_int / 360000
			time_int %= 360000
		else:
			_hours = 0
		time_str = str(_hours) + ":"
			
		if time_int >= 60000:
			_mins = time_int / 6000
			time_int %= 6000
			time_str = time_str + str(_mins) + ":"
		elif time_int >= 6000:
			_mins = time_int / 6000
			time_int %=  6000
			time_str += "0" + str(_mins) + ":"
		else:
			time_str += "00:"
		if time_int >= 1000:
			time_str += str(time_int/100)
		else:
			time_str += "0" + str(time_int/100)
		time_str += "."
		time_int %=100
		if time_int<10:
			time_str += "0"
		time_str += str(time_int%100)
		return time_str


	def temporizador_func(self):
		if self.reproduciendo==False:
			# TODO: borrar el directorio y mostrar mensaje de error
			print "Error al reproducir"
			merror=show_error(_("There was a problem when playing the audio/video.\nCheck that the file is playable with GStreamer."))
			self.tiempos=[]
			self.set_buttons()
			return False

		stop_detected=False
		v1,v2,v3=self.player.get_state()
		if v2==gst.STATE_NULL: # ended the play
			print "Se ha terminado la reproduccion"
			if self.sound_aborted:
				os.remove(self.configuration["output"]+".tmp/salida.wav")
			else:
				print "Añadiendo tiempo extra"
				tiempo = self.duracion / 1000000
				if tiempo>200:
					self.tiempos.append(tiempo-100)
					print str(tiempo-100)
			self.reproduciendo=False
			self.set_buttons()
			return False
		self.tiempo.set_text(str(self.convert_ns(self.player.query_position(self.time_format, None)[0])))
		if self.duracion==-1:
			try:
				self.duracion=self.player.query_duration(self.time_format, None)[0]
			except gst.QueryError:
				print "Error al coger la duracion"
				merror=show_error(_("There was a problem when playing the audio/video.\nCheck that the file is playable with GStreamer."))
				self.tiempos=[]
				self.reproduciendo=False
				self.set_buttons()
				return False
			print "Duracion: "+str(self.duracion)
		return True
		

	def pic_size_changed(self,par1,par2=""):
		
		width = par2.width
		height = par2.height
		
		if (width == self.old_width) and (height == self.old_height):
			return
		
		self.old_width = width
		self.old_height = height
		
		if (width*3/4)<height:
			self.pic_width=width
			self.pic_height=width*3/4
		else:
			self.pic_width=height*4/3
			self.pic_height=height
			
		if self.curr_pic == None:
			return

		try:
			picture=gtk.gdk.pixbuf_new_from_file(self.curr_pic)
		except:
			return
		
		picture=picture.scale_simple(self.pic_width,self.pic_height,gtk.gdk.INTERP_NEAREST)
		self.slide_pic.set_from_pixbuf(picture)


	def add_slide(self,widg):
		print "Entro en Add_slide"
		if self.reproduciendo:
			print "Estoy reproduciendo"
			instante=(self.player.query_position(self.time_format, None)[0])/1000000
			self.tiempos.append(instante)
			print str(instante)
		else:
			print "No estoy reproduciendo"
			self.slide_actual=1
			self.create_gstreamer()
			listfiles=glob.glob(self.configuration["output"]+".tmp/[0-9][0-9][0-9]_slide.jpg")
			self.nslides=str(len(listfiles))
			listfiles=None

		cadena=str(self.slide_actual)
		while len(cadena)<3:
			cadena="0"+cadena
		fichero=self.configuration["output"]+".tmp/"+cadena+"_slide.jpg"
		print "Cargo "+fichero
		
		self.current_slide_w.set_text(str(self.slide_actual)+"/"+self.nslides)
		
		try:
			picture=gtk.gdk.pixbuf_new_from_file(fichero)
			self.curr_pic=fichero
		except gobject.GError:
			print "Excepcion de PICTURE"
			self.curr_pic = None
			self.slide_pic.set_from_pixbuf(None)
			label=self.arbol.get_widget("curr_slide")
			label.set_label(_("<b>No more slides</b>"))
			self.current_slide_w.set_text("No more slides")
			self.arbol.get_widget("add_slide").set_sensitive(False)
			self.player.set_state(gst.STATE_NULL)
			self.sound_aborted = True
			return
		
		picture=picture.scale_simple(self.pic_width,self.pic_height,gtk.gdk.INTERP_NEAREST)
		self.slide_pic.set_from_pixbuf(picture)
		self.slide_actual+=1

		if self.reproduciendo==False:
			print "Entro en la reproduccion"
			self.reproduciendo=True
			self.set_buttons()
			self.temporizador=gobject.timeout_add(200,self.temporizador_func)
			self.player.set_property('uri', "file://" + self.configuration["audio"])
			self.player.set_state(gst.STATE_PLAYING)
			self.duracion=-1


	def create_gstreamer(self):
		
		print "Creo Gstreamer"
		
		self.player = gst.element_factory_make("playbin", "player")
		
		# creamos la salida completa a WAV
		self.myaudiosink = gst.element_factory_make('wavenc', "my-sink")
		self.salidaudio=gst.element_factory_make("filesink","salida")

		# creamos la salida a ALSA
		self.myalsasink = gst.element_factory_make('alsasink', "sound_sink")
		
		# creamos el divisor
		self.mytee = gst.element_factory_make("tee","divisor")
		self.queue1 = gst.element_factory_make("queue","queue1")
		self.queue2 = gst.element_factory_make("queue","queue2")		
		self.queue1.set_property("max-size-time",10000000) # only 10 ms in the audio queue
		self.queue2.set_property("max-size-time",5000000000) # up to ten seconds in the WAV queue

		self.bin = gst.element_factory_make("bin")
		self.bin.add(self.myaudiosink)
		self.bin.add(self.salidaudio)
		self.bin.add(self.myalsasink)
		self.bin.add(self.mytee)
		self.bin.add(self.queue1)
		self.bin.add(self.queue2)
		self.mytee.link(self.queue1)
		self.queue1.link(self.myalsasink)
		self.mytee.link(self.queue2)
		self.queue2.link(self.myaudiosink)
		self.myaudiosink.link(self.salidaudio)

		self.ghost_pad = gst.GhostPad("sink",self.mytee.get_pad("sink"))
		self.bin.add_pad(self.ghost_pad)
		self.salidaudio.set_property("location",self.configuration["output"]+".tmp/salida.wav")
		self.player.set_property("audio-sink", self.bin)
		self.bus = self.player.get_bus()
		self.bus.add_signal_watch()
		self.bus.enable_sync_message_emission()
		self.bus.connect('message', self.on_message)
		self.bus.connect('sync-message::element', self.on_sync_message)
		print "Gstreamer creado"


	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
		elif t == gst.MESSAGE_ERROR:
			self.player.set_state(gst.STATE_NULL)


	def on_sync_message(self, bus, message):
		if message.structure is None:
			return
		message_name = message.structure.get_name()
		if message_name == 'prepare-xwindow-id':
			self.arbol.get_widget("video_label").set_label(_("<b>Video</b>"))
			imagesink = message.src
			imagesink.set_property('force-aspect-ratio', True)
			imagesink.set_xwindow_id(self.ventana_film.window.xid)


	def save_presentation_clicked(self,arg1):

		global globaldir
		
		arbol=gtk.glade.XML(globaldir+"supershow.glade","save_timings",domain="supershow")
		ventana=arbol.get_widget("save_timings")
		ventana.show()
		retv=ventana.run()
		filename=ventana.get_filename()
		ventana.hide()
		ventana.destroy()
		ventana=None
		arbol=None
		if retv!=-6:
			return

		if (filename=="") or (filename==None):
			return
		
		if (len(filename)<10) or (filename[-10:]!=".supershow"):
			filename+=".supershow"
		
		try:
			filesave=open(filename,"w")
		except:
			merror=show_error(_("Error saving the file. Aborted."))
			return
		
		filesave.write("supershow\n")
		for element in self.tiempos:
			filesave.write("time:"+str(element)+"\n")
		filesave.close()


	def open_presentation_clicked(self,arg1):
		
		global globaldir
		
		if len(self.tiempos)!=0:
			arbol=gtk.glade.XML(globaldir+"supershow.glade","ask_timings",domain="supershow")
			ventana=arbol.get_widget("ask_timings")
			ventana.show()
			retv=ventana.run()
			ventana.hide()
			ventana.destroy()
			ventana=None
			arbol=None
			if retv!=-6:
				return
		
		arbol=gtk.glade.XML(globaldir+"supershow.glade","load_timings",domain="supershow")
		ventana=arbol.get_widget("load_timings")
		ventana.set_filter(self.file_filter)
		ventana.show()
		retv=ventana.run()
		filename=ventana.get_filename()
		ventana.hide()
		ventana.destroy()
		ventana=None
		arbol=None
		if retv!=-5:
			return
		
		print "Filename: "+str(filename)
		
		if (filename=="") or (filename==None):
			merror=show_error(_("No filename given. Aborted."))
			return
		
		try:
			fileopen=open(filename,"r")
		except:
			merror=show_error(_("Error opening the file. Aborted."))
			return
		
		self.tiempos=[]
		
		linea=fileopen.readline()
		if linea!="supershow\n":
			merror=show_error(_("The file isn't a valid SuperShow timing file. Aborted."))
			fileopen.close()
			self.set_buttons()
			return
		
		offset=0
		nlinea=1
		haserror=False
		while(True):
			linea=fileopen.readline()
			nlinea+=1
			print linea
			if linea=="":
				break
			if linea[:5]=="time:":
				try:
					self.tiempos.append(offset+int(linea[5:]))
				except:
					haserror=True
					
			if linea[:7]=="offset:":
				try:
					offset=int(linea[7:])
				except:
					haserror=True
			
			if haserror:
				merror=show_error(_("Error in line %(linea)d.\nThe file is corrupt. Aborted.")% {'linea':nlinea})
				self.tiempos=[]
				break
			
		fileopen.close()
		self.set_buttons()
	
	
class use_dialog:

	def use_changed(self,w):
		
		if self.programa_w.get_active():
			activa=False
		else:
			activa=True
		
		self.arbol.get_widget("proplabel1").set_sensitive(activa)
		self.arbol.get_widget("proplabel2").set_sensitive(activa)
		self.dpi_w.set_sensitive(activa)


	def on_show_buttons_toggled(self,widget):
		
		w=self.arbol.get_widget("autohide_buttons")
		if(widget.get_active()):
			w.set_sensitive(True)
		else:
			w.set_sensitive(False)


	def __init__(self):
	
		global globaldir
	
		self.arbol=gtk.glade.XML(globaldir+"supershow.glade","properties_dialog",domain="supershow")
		self.dpi_w=self.arbol.get_widget("dpi")
		self.quality_w=self.arbol.get_widget("jpeg_quality")
		self.programa_w=self.arbol.get_widget("use_pdf2swf")
		self.retardo_w=self.arbol.get_widget("audio_delay")
		self.showbuttons_w=self.arbol.get_widget("show_buttons")
		self.playagain_w=self.arbol.get_widget("play_again")
		self.autohidebuttons_w=self.arbol.get_widget("autohide_buttons")
		self.arbol.signal_autoconnect(self)
		
		self.use_changed(None)
		
		ventana=self.arbol.get_widget("properties_dialog")
		ventana.show()
		retv=ventana.run()
		self.dpi=self.dpi_w.get_value_as_int()
		self.quality=int(self.quality_w.get_value())
		self.programa=self.programa_w.get_active()
		self.retardo=self.retardo_w.get_value_as_int()
		self.showbuttons=self.showbuttons_w.get_active()
		self.playagain=self.playagain_w.get_active()
		self.autohidebuttons=self.autohidebuttons_w.get_active()
		ventana.hide()
		ventana.destroy()
		ventana=None
		self.arbol=None
		
		if retv!=-6:
			self.usar=""
		elif self.programa:
			self.usar="pdf2swf"
		else:
			self.usar="gs"
			

class check_programs:
	
	def __init__(self):
		self.texto=""
		if 0!=self.run_program("gs -v"):
			self.texto+="GhostScript\n"
		if 0!=self.run_program("pdf2swf -V"):
			self.texto+="PDF2SWF\n"
		if 0!=self.run_program("swfc -V"):
			self.texto+="SWFC"

	def run_program(self,command):
		print "Running "+command
		proceso=subprocess.Popen(command,shell=True,bufsize=8129)
		return proceso.wait()


textos=""
globaldir=""
try:
	fichero=open("/usr/share/supershow/supershow.glade","r")
	fichero.close()
	globaldir="/usr/share/supershow/"
	textos="/usr/share/locale"
	print "/usr"
except:
	pass

if globaldir=="":
	try:
		fichero=open("/usr/local/share/supershow/supershow.glade","r")
		fichero.close()
		globaldir="/usr/local/share/supershow/"
		textos="/usr/share/locale"
		print "/usr/local"
	except:
		pass
if globaldir=="":
	globaldir="./"
	textos="po/"
	print "./"

gettext.bindtextdomain('supershow', textos)
locale.setlocale(locale.LC_ALL,"")
gettext.textdomain('supershow')
_ = gettext.gettext
print "SuperShow 2.3b"

gtk.gdk.threads_init()

check_prog=check_programs()

if check_prog.texto!="":
	msgerror=show_error((_("Can't locate the following programs, needed to run SuperShow:\n\n"))+check_prog.texto,False)
else:
	main=main_window()
	gtk.main()
		
