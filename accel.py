#!/usr/bin/python
"""
 
===============================================================================
Accel is an Arduino-based accelerometer data recording application written in
Python and C11 and designed for the ADXL345 accelerometer from Analog Devices

------------------------------------------
by: Evan Lane
license: MIT Open Source license
git: https://github.com/evanvlane/ardAccel
------------------------------------------

Usage: 
  accel.py ports
  accel.py [-fdvx] [-p PORT] [-b BAUD] [-t TIMEOUT] [-r DATA] [-g GRANGE] (-l LENGTH) <FILE>

Arguments:
  ports  	Prints a list of available COM ports
  FILE  	Output file name 

Options:
  -b BAUD --baudrate=BAUD  	Baudrate for serial communcation [default: 115200]
  -d --date  			Prepend recording date to filename
  -f --force	  		Overwrite output file if it already exists
  -g --grange=GRANGE  		Max +/- force in units of g [default: 4]
  -l LENGTH --length=LENGTH  	Seconds of data to be recorded [default: 5]
  -p PORT --port=PORT  		COM port for Arduino [default: 2]
  -r DATA --datarate=DATA  	Output data rate of ADXL345 in Hz[default: 3200]
  -t TIMEOUT --timeout=TIMEOUT  Timeout for serial communcation [default: 1]
  -v --visualize  		Visualize the results via matplotlib
  -x --xkcd  			Plots come out in XKCD style. Ya know... For kids!

"""

# Imports
#------------------------------------------------------------------------------

# Communication
import serial
from enumPorts import enumPorts

# File and Data Handling
from collections import namedtuple
import csv
import timeit
import os

# Math
import numpy
import math

# Plotting
import matplotlib.pyplot as plt
import drawnow

# Delay & Time
import time
import datetime

# Command Line Parsing
from docopt import docopt, DocoptExit

# Classes
#------------------------------------------------------------------------------

Vec3 = namedtuple('Vector', ['x','y','z'])	#Named tuple for storing accel data ponts

class Arduino(object):
	"""Arduino Object"""

	ardCount = 0

	def __init__(self, port=2, baudrate=9600, timeout=1):
		self.__class__.ardCount += 1
		self.ID = self.__class__.ardCount

		super(Arduino, self).__init__()
		self.port = port
		self.baudrate = baudrate
		self.timeout = timeout
		self.name = "Arduino " + str(self.ID)
		self.buffer = ""
		self.data = [] 	#TODO implement better buffer system

		self.firstContact = True

		try:
			self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
		except:
			print("The serial connection on COM{0} for {1} was unable to be established.").format(port+1, self.name)
	
	def __len__(self):
		return len(self.buffer)

	def readSer(self):
		"""Reads serial data from Arduino object"""

		if (self.ser.inWaiting() > 0):
			if self.firstContact:
				self.ser.write('Go')
				self.firstContact = False
				
				for __ in xrange(5):
					self.ser.flushInput()				
					time.sleep(0.05)

			self.buffer = self.buffer + str(self.ser.readline())
			#(Vec3(*[int(thing) for thing in self.ser.readline().strip().split(',')]))

			

	def writeSer(self,val):
		"""Writes serial data to the Arduino object"""

		self.ser.write(val)

	def close(self):
		self.ser.close()
		
# Functions
#------------------------------------------------------------------------------

def dataWriter(buffer=None, filename=None, force=False, date=False):
	"""dataWriter writes the inculded buffer to the listed file"""

	if not os.path.exists(os.path.join(os.getcwd(),"data")):
	    os.makedirs("./data")

	if date:
		filename = str(datetime.date.today()) + '-' + filename

	filename = os.path.join("./data/",filename) 
	firstFN = filename
	count = 1
	
	while os.path.isfile(filename) and not force:
		filename = firstFN[:-4] + str(count) + firstFN[-4:]
		count += 1

	with open(filename, 'wb') as csvfile:
		fieldnames = ['X Values', 'Y Values', 'Z Values']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

		writer.writeheader()

		for i in buffer:
			writer.writerow({'X Values': i.x, 'Y Values': i.y, 'Z Values': i.z})

def makeFig(data=None, datarate=3200):
	"""
	prints the acquired data
	"""
	time = len(data)/datarate

	timestep = numpy.linspace(0,time,len(data))

	plt.axis('auto')
	plt.grid(True)

	plt.plot(timestep, [dat.x for dat in data], 'r-', label='X Axis Values')
	plt.plot(timestep, [dat.y for dat in data], 'b-', label='Y Axis Values')
	plt.plot(timestep, [dat.z for dat in data], 'g-', label='Z Axis Values')
	plt.legend(loc='lower right')
	plt.show()

def getArgs():
	# Retreive the arguments passed in via the command line
	arguments = docopt(__doc__, version="Accel v0.1.1")

	# Typecast the ones that need it
	arguments['--length'] = float(arguments['--length'])
	arguments['--datarate'] = float(arguments['--datarate'])
	arguments['--baudrate'] = int(arguments['--baudrate'])
	arguments['--timeout'] = int(arguments['--timeout'])

	return arguments

if __name__ == '__main__':

	docArgs = getArgs()

	if docArgs['--xkcd']: plt.xkcd()

	if docArgs['--port'].startswith("COM"):
		docArgs['--port'] = int(docArgs['--port'][3])-1
	elif len(docArgs['--port']) < 3:
		docArgs['--port'] = int(docArgs['--port'])
	else:
		print "Unknown Port"

	if docArgs['ports']:
		print "==============================="
		print "COM ports currently plugged in:"
		for i in enumPorts():
			print "  - " + i
		print "==============================="
	else:
		ard1 = Arduino(port=docArgs['--port'], baudrate=docArgs['--baudrate'], timeout=docArgs['--timeout'])

		tic = timeit.default_timer()

		while True:
			ard1.readSer()

			if len(ard1) == int(docArgs['--length']*docArgs['--datarate']):

				dataWriter(buffer=ard1.buffer, filename=docArgs['<FILE>'], force=docArgs['--force'],date=docArgs['--date'])
				toc = timeit.default_timer()
			
				
				print("{:.2f} seconds worth of acceleration data written in {:.2f} seconds.").format(len(ard1)/docArgs['--datarate'], toc-tic)
				print("Device Name: {0}\nCOM Port: COM{1}\nData Rate: {2} Hz\n").format(ard1.name, docArgs['--port']+1, docArgs['--datarate'])

				ard1.writeSer('s')

				if docArgs['--visualize']:
					makeFig(ard1.buffer,docArgs['--datarate'])
				break