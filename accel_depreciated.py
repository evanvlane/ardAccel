#!/usr/bin/python

import serial
import threading

import numpy
import math

import matplotlib.pyplot as plt
import drawnow
import time

class myThread (threading.Thread):
	"""
	myThread creates a thread which holds a function and locking ability
	"""
	threadNum = 0
	threadLock = threading.Lock()

	def __init__(self, name):
		threading.Thread.__init__(self)
		self.__class__.threadNum += 1
		self.threadID = self.__class__.threadNum
		self.name = name

	# def run(self,variable):
	# 	self.threadLock.acquire()
	# 	print "Starting " , self.name , self.threadID
	# 	print self.runfunc(variable)
	# 	self.threadLock.release()

class arduino (myThread):
	"""
	arduino instantiates a serial communication with an attached arduino
	"""
	arduinoNum = 0

	def __init__(self, comPort=0, baudrate=9600, timeout=1):
		self.__class__.arduinoNum += 1
		self.arduinoID = self.__class__.arduinoNum
		self.comPort = comPort
		self.baudrate = baudrate
		self.timeout = timeout
		self.data = []
		self.flag = 0

		super(arduino,self).__init__(str('Arduino %d' % self.arduinoID))
		
		try:
			self.ser = serial.Serial(port=comPort, baudrate=baudrate, timeout=timeout)
		except:
			print("The serial connection on COM{0} for {1} was unable to be opened.".format(comPort+1, self.name))
		
	def read(self):
		if (self.ser.inWaiting() > 0):
			self.threadLock.acquire()
			print "Lock acquired by serial."
			self.ser.write('A')
			self.ser.flushInput()
			self.buffer = self.ser.readline().strip().strip(";")

			self.flag = 1
			self.ser.flushOutput()			
			self.threadLock.release()

			

	def write(self):
		self.ser.write("H")

	def close(self):
		self.ser.close()

class plotty (myThread):
	"""
	multithreaded realtime plotting class
	"""
	
	plt.ion()
	plt.ylim(-1,1)
	plt.grid(True)

	def __init__(self,arduino):
		self.cnt = 0
		self.device = arduino

	def makeFig(self):
		"""
		refreshes the printing figure
		"""
		self.threadLock.acquire()	
		self.data = self.device.data

		plt.plot(self.data, 'ro-', label='Sine wave.')
		plt.legend(loc='upper left')

		self.threadLock.release()

		time.sleep(0.2)

	def pltFig(self):
		if self.device.flag != 0:
			drawnow.drawnow(self.makeFig)


def main():

	port = 2
	baudrate = 9600
	timeout = 1

	ard1 = arduino(comPort=port, baudrate=baudrate, timeout=1)
	plt1 = plotty(ard1)

	while True:
		ard1.read()
		plt1.pltFig()

if __name__ == "__main__":
	main()
