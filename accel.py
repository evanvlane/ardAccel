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
  accel.py open [-x] <FILE>
  accel.py [-fdvx] [-p PORT] [-b BAUD] [-t TIMEOUT] [-r DATA] [-g GRANGE] (-l LENGTH) <FILE>

Arguments:
  ports  	Prints a list of available COM ports
  FILE  	File name to be loaded or saved 

Options:
  -b BAUD --baudrate=BAUD  	Baudrate for serial communcation [default: 115200]
  -d --date  			Prepend recording date to filename
  -f --force	  		Overwrite output file if it already exists
  -g GRANGE --grange=GRANGE  		Max +/- force in units of g [default: 4]
  -l LENGTH --length=LENGTH  	Seconds of data to be recorded [default: 5]
  -p PORT --port=PORT  		COM port for Arduino [default: 2]
  -r DATA --datarate=DATA  	Set data rate of ADXL345 in Hz[default: 3200]
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

Vec3 = namedtuple('Vector', ['x','y','z'])	#Named tuple for storing accel data points

class Arduino(object):
	"""Arduino Object"""

	ardCount = 0
	correctionFactor = {"2g": 3.9, "4g": 7.8, "8g": 1, "16g": 27.2553125} #Obtained by getting a stationary Z signal and dividing its average by 9.80665 m/s^2

	def __init__(self, port=2, grange=4, datarate=3200, baudrate=9600, timeout=1):
		self.__class__.ardCount += 1
		self.ID = self.__class__.ardCount

		super(Arduino, self).__init__()
		self.port = port
		self.baudrate = baudrate
		self.timeout = timeout
		self.name = "Arduino " + str(self.ID)
		self.buffer = ""
		self.data = [] 	#TODO implement better buffer system
		self.grange = grange
		self.datarate = datarate

		self.firstContact = True

		try:
			self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
		except:
			print("The serial connection on COM{0} for {1} was unable to be established.").format(port+1, self.name)
	
		#Wait until the Arduino is up and running its establishContact() routine

		self.ser.flushInput()
		while (self.ser.inWaiting() == 0):
			print "Waiting"

		#Set the g force range and the acquisition datarate
		self.setRegister(grange)
		self.setRegister(datarate)

	def __len__(self):
		return len(self.data)

	def readSer(self):
		"""Reads serial data from Arduino object"""

		if (self.ser.inWaiting() > 0):
			self.count = 0

			if self.firstContact:
				self.ser.write('a')
				self.firstContact = False
				print("Begining data read from {0}.").format(self.name)
				
				for __ in xrange(5):
					self.ser.flushInput()				
					time.sleep(0.05)

			self.buffer = self.buffer + str(self.ser.readline())
			self.buffer = ''.join(self.buffer.split())
			self.count = self.count + 1

			for point in filter(None, self.buffer.split(';')):
				self.data.append(Vec3(*[int(coord)/self.__class__.correctionFactor["16g"] for coord in point.split(',')]))

			self.buffer = ''

			#print len(self.data[-1])
			#lastData = len(self.data[-1])
			

	def writeSer(self,val):
		"""Writes serial data to the Arduino object"""

		self.ser.write(val)

	def close(self):
		self.ser.close()

	def setRegister(self,tuple):
		pass


		
# Functions
#------------------------------------------------------------------------------

def dataWriter(buffer=None, length=1, datarate=3200, filename=None, force=False, date=False):
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

	print('Data writing to: "{0}"').format(filename)
	with open(filename, 'wb') as csvfile:
		fieldnames = ['X Values', 'Y Values', 'Z Values']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

		writer.writerow({'X Values': datarate, 'Y Values': length, 'Z Values': 5})#str(datetime.date.today())})
		writer.writeheader()


		for i in buffer:
			writer.writerow({'X Values': i.x, 'Y Values': i.y, 'Z Values': i.z})

def dataReader(filename=None):
	filename = os.path.join("./data/",filename)

	with open(filename, 'rb') as csvfile:

		data = numpy.genfromtxt(csvfile, delimiter=',')
		return data[2:data.shape[0]]

def makeFig(data=None, scaleFactor=1, datarate=3200):
	"""
	prints the acquired data
	"""
	if docArgs['--xkcd']: plt.xkcd()

	time = len(data)/float(datarate)

	fig, ax1 = plt.subplots()
	ax1.axis('auto')
	plt.ylabel("Acceleration (g)")
	plt.xlabel("Time (s)")
	ax1.grid(True)

	try:
		timestep = numpy.linspace(0,time,len(data))
		ax1.plot(timestep, [dat.x for dat in data], 'r-', label='X Axis Values', lw=0.5)
		ax1.plot(timestep, [dat.y for dat in data], 'b-', label='Y Axis Values', lw=0.5)
		ax1.plot(timestep, [dat.z for dat in data], 'g-', label='Z Axis Values', lw=0.5)
	except:
		data = numpy.delete(data,0,0)
		timestep = numpy.linspace(0,time,len(data))
		#data2 = numpy.trapz(data[:,0])
		ax1.plot(timestep, [dat[0] for dat in data], 'r-', label='X Axis Values', lw=0.5)
		ax1.plot(timestep, [dat[1] for dat in data], 'b-', label='Y Axis Values', lw=0.5)
		ax1.plot(timestep, [dat[2] for dat in data], 'g-', label='Z Axis Values', lw=0.5)
		ax2 = ax1.twinx()
		#ax2.plot(timestep, velocity, 'k-', label='Velocity', lw=0.5)
		
	ax1.legend(loc='lower right')
	plt.show()

def getArgs():
	# Retreive the arguments passed in via the command line
	arguments = docopt(__doc__, version="Accel v0.1.1")

	# Typecast the ones that need it
	arguments['--length'] = float(arguments['--length'])
	arguments['--datarate'] = float(arguments['--datarate'])
	arguments['--baudrate'] = int(arguments['--baudrate'])
	arguments['--timeout'] = int(arguments['--timeout'])
	print arguments
	return arguments

if __name__ == '__main__':

	docArgs = getArgs()

	#Set the serial port
	if docArgs['--port'].startswith("COM"):
		docArgs['--port'] = int(docArgs['--port'][3])-1
	elif len(docArgs['--port']) < 3:
		docArgs['--port'] = int(docArgs['--port'])
	else:
		print "Unknown Port"

	#Enumerate the COM ports available to the program
	if docArgs['ports']:
		print "==============================="
		print "COM ports currently plugged in:"
		for i in enumPorts():
			print "  - " + i
		print "==============================="
	#Open a file
	elif docArgs['open']:
		makeFig(data=dataReader(docArgs['<FILE>']))
	else:
		ard1 = Arduino(port=docArgs['--port'], grange=docArgs['--grange'], datarate=docArgs['--datarate'], baudrate=docArgs['--baudrate'], timeout=docArgs['--timeout'])

		tic = timeit.default_timer()

		while True:
			ard1.readSer()

			if len(ard1) >= int(docArgs['--length']*docArgs['--datarate']):

				dataWriter(buffer=ard1.data, length=docArgs['--length'], datarate=docArgs['--datarate'], filename=docArgs['<FILE>'], force=docArgs['--force'],date=docArgs['--date'])
				toc = timeit.default_timer()
			
				
				print("{:.2f} seconds worth of acceleration data written in {:.2f} seconds.").format(len(ard1)/docArgs['--datarate'], toc-tic)
				print("Device Name: {0}\nCOM Port: COM{1}\nData Rate: {2} Hz\n").format(ard1.name, docArgs['--port']+1, docArgs['--datarate'])

				ard1.writeSer('s')

				if docArgs['--visualize']:
					makeFig(ard1.data,docArgs['--datarate'])
				break