import os
import numpy as np
import matplotlib.pyplot as plt
import FileDialog

def dataReader(filename=None, axis=0):
	'Reads CSV files into numpy array and returns a single axis of data.'

	#Input file name within subfolder 'data'
	filename = os.path.join("./data/",filename)

	with open(filename, 'rb') as csvfile:
		data = np.genfromtxt(csvfile, delimiter=',', unpack=False)

		#My .csv files have a header line. Comment this line out if your data starts
		# at row 0 and just return data
		datarate, length= data[0][0], data[0][1]
		
		return [data[2:data.shape[0],axis], datarate, length]

if __name__ == "__main__":

	#Establish a figure
	figure, (ax0,ax1) = plt.subplots(nrows=2)
	linewidth = 0.5
	color = 'k-'

	#Gets all the data from my csv. Axis is 0-indexed and in x,y,z order.
	y, datarate, time = dataReader(filename="Toothbrush.csv",axis=0)
	sampling = 1.0/datarate
	#These two lines should be identical. It's a good indicator that
	#something is wrong if they're not.
	points = time/sampling
	n = len(y)
	#y = np.sin(260*np.pi*np.linspace(0,time,n))

	yf = np.fft.rfft(y*np.hanning(n))*2/n
	yfreq = np.fft.fftfreq(n,d=sampling)

	#Just deal with positive frequencies.
	yfreq = yfreq[:n/2+1]

	#Puts the limits as 0 to 5% above the max amplitude
	ax0.set_ylim(0,np.max(abs(yf[10:len(yf)]))+0.05*np.max(abs(yf[10:len(yf)])))
	
	#Uncomment this if you want to focus on a specific frequency range.
	ax0.set_xlim(-1,1600) 
	ax0.plot(yfreq,abs(yf[:n/2+1]), color,linewidth=linewidth)
	ax0.set_title('FFT of Acceleration Signal')
	ax0.set_xlabel('Frequencies (Hz)')
	ax0.set_ylabel('Amplitude (g)')


	ax1.plot(np.linspace(0,3,len(y)),y, color, linewidth=linewidth)
	ax1.set_title('Time Domain of Acceleration Signal')
	ax1.set_xlabel('Time (s)')
	ax1.set_ylabel('Amplitude (g)')

	# Tweak spacing between subplots to prevent labels from overlapping
	plt.subplots_adjust(hspace=0.5)


	plt.show()
