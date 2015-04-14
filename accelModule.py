import numpy as np
import matplotlib.pyplot as plt

figure, (ax1,ax2) = plt.subplots(2)

x = np.linspace(0,2*np.pi,1000)
y = np.sin(x)

ax1.plot(x,y,'r-')
ax2.plot(y,x,'bo')

plt.show()

def pltShow(plot):
	