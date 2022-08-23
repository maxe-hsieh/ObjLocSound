#coding=utf-8

# Object Location Sound
# A global plugin for NVDA
# Copyright 2022 Maxe Hsieh

import addonHandler
addonHandler.initTranslation()

import globalPluginHandler
import tones
import config
import ui
import api
import globalVars
import gui
from scriptHandler import script, getLastScriptRepeatCount

configName = 'objLocSound'
scriptCategory = _(u'物件位置音效')
if configName not in config.conf:
	config.conf[configName] = {'switch': True}

conf = config.conf[configName]
if conf['switch'] == u'False':
	conf['switch'] = False


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super(GlobalPlugin, self).__init__()
		self.currentObject = None
		self.currentObjectLocation = None
		# 持續觀察物件位置，用於動態物件，例如跑馬燈，或是某些沒有事件的焦點移動，比如瀏覽模式。
		self.timer = gui.NonReEntrantTimer(self.playLocationSound)
		if self.switch:
			self.start()
		
	
	def terminate(self):
		if hasattr(self, 'timer'):
			self.stop()
		
	
	def _get_switch(self):
		return conf.get('switch')
	
	def _set_switch(self, value):
		conf['switch'] = value
	
	def start(self):
		self.timer.Start(10)
	
	def stop(self):
		self.timer.Stop()
	
	@script(_(u'提示開關'), scriptCategory, 'KB:NVDA+l')
	def script_toggleSwitch(self, gesture):
		switch = not self.switch
		self.switch = switch
		methods = (self.stop, self.start)
		methods[switch]()
		messages = (_(u'關閉物件位置提示音效'), _(u'開啟物件位置提示音效'))
		ui.message(messages[switch])
	
	def playLocationSound(self):
		# 播放當前瀏覽物件中心點所在位置音效
		try:
			obj = api.getNavigatorObject()
			location = obj.location
			if location is None or self.currentObject == obj and location == self.currentObjectLocation:
				return
			
			self.currentObject = obj
			self.currentObjectLocation = location
			x, y = self.getCenterCoordinate(obj)
			
			self.playCoordinateSound(x, y)
		except TypeError:
			pass
		
	
	def getCenterCoordinate(self, obj):
		l, t, w, h = obj.location
		x = l + (w // 2)
		y = t + (h // 2)
		return (x, y)
	
	def playCoordinateSound(self, x, y):
		screenWidth, screenHeight = api.getDesktopObject().location[2:]
		if 0 <= x <= screenWidth and 0 <= y <= screenHeight:
			minPitch = config.conf['mouse']['audioCoordinates_minPitch']
			maxPitch = config.conf['mouse']['audioCoordinates_maxPitch']
			curPitch = minPitch + ((maxPitch - minPitch) * ((screenHeight - y) / float(screenHeight)))
			brightness = config.conf['mouse']['audioCoordinates_maxVolume']
			leftVolume = int((85 * ((screenWidth - float(x)) / screenWidth)) * brightness)
			rightVolume = int((85 * (float(x) / screenWidth)) * brightness)
			tones.beep(curPitch, 40, left=leftVolume, right=rightVolume)
		
	
	@script(u'播放當前物件左上與右下角座標音效，連按兩次報讀詳細資訊', scriptCategory, 'KB:NVDA+a')
	def script_playAreaSound(self, gesture):
		obj = api.getNavigatorObject()
		l, t, w, h = obj.location
		if getLastScriptRepeatCount():
			message = _(u'左上角：') + u' X:' + str(l) + u', Y:' + str(t) + u'\n'
			message += _(u'寬：') + u' ' + str(w) + u', ' + _(u'高：') + u' ' + str(h)
			return ui.message(message)
		
		self.playCoordinateSound(l, t)
		gui.wx.CallLater(100, self.playCoordinateSound, l+w, t+h).Start()
	
