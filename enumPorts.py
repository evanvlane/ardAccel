import _winreg as winreg
import itertools

def enumPorts():

	path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'

	try:
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
	except WindowsError:
		raise IterationError

	for i in itertools.count():
		try:
			val = winreg.EnumValue(key, i)
			yield str(val[1])
		except EnvironmentError:
			break
