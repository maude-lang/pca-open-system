#
# Form window external object for Maude
# by R. Rubio
# Python code implementing the basic interface for GUI external objects
#

import signal
import subprocess
import sys
import tkinter as tk
import tkinter.ttk as ttk
import threading
import traceback

import maude


class FormWindow(tk.Toplevel):
	"""Form window"""

	def __init__(self, master, manager, window_id, title='Form window'):
		super().__init__(master)
		self.title(title)
		self.nr_fields = 0

		# GUI Manager and ID on it
		self.manager = manager
		self.window_id = window_id

		# Widgets by name
		self.widgets = {}

	def add_field(self, name: str, editable: bool):
		"""Add a field to the form"""

		label = ttk.Label(self, text=name)
		string_var = tk.StringVar()
		entry = ttk.Entry(self, state='enabled' if editable else 'disabled', textvariable=string_var)
		entry.string_var = string_var
		entry.label = name
		entry.bind('<FocusOut>', self._on_change)
		entry.bind('<Return>', self._on_change)

		entry.grid(row=self.nr_fields, column=0)
		label.grid(row=self.nr_fields, column=1, sticky='W')
		self.nr_fields += 1

		self.widgets[name] = entry

	def add_button(self, name: str, clickable: bool):
		"""Add a button to the form"""

		button = ttk.Button(self, text=name)
		button.bind('<Button>', self._on_click)

		button.grid(row=self.nr_fields, columnspan=2)
		self.nr_fields += 1

		self.widgets[name] = button

	def set_field(self, name: str, value: str) -> bool:
		"""Set the value of a field"""

		if entry := self.widgets.get(name):
			entry.string_var.set(value)

		return entry is not None

	def _on_click(self, event):
		"""Event handler for a button click"""

		# Button click event with its label
		self.manager.push((self.window_id, 'button', event.widget['text']))

	def _on_change(self, event):
		"""Event handler for a entry change"""

		# Entry change event with its label and content
		self.manager.push((self.window_id, 'entry', event.widget.label, event.widget.get()))


class WindowManager:
	"""Manager of windows"""

	def __init__(self, gui_manager):
		# Application window (invisible)
		self.root = tk.Tk()
		self.root.withdraw()
		# Map from identifiers to windows
		self.windows = {}
		# GUI manager
		self.gui_manager = gui_manager

	def get(self, wid):
		"""Get window by identifier"""

		return self.windows.get(wid)

	def new_window(self, wid, title='Window'):
		"""Create a new window"""

		window = FormWindow(self.root, self.gui_manager, wid, title=title)
		self.windows[wid] = window

		return window

	def destroy_window(self, wid) -> bool:
		"""Destroy an existing window"""

		if window := self.windows.get(wid):
			window.destroy()
			self.windows.pop(wid)

		return window is not None

	def mainloop(self):
		"""Run the application main loop"""

		return tk.mainloop()

	def destroy(self):
		"""Destroy the GUI"""

		return self.root.destroy()


class GuiManager(maude.Hook):
	"""Manager for the Maude external object"""

	def __init__(self, winmanager_class=FormWindow):
		super().__init__()
		# Queue of events for the caller
		self.event_queue = []
		# Next index to assign
		self.next_index = 0

		# Window manager
		self.window_manager = WindowManager(self)
		# Window owners
		self.owners = {}

	def mainloop(self):
		"""Run the application main loop"""

		return self.window_manager.mainloop()

	def destroy(self):
		"""Destroy the GUI"""

		return self.window_manager.destroy()

	def push(self, event: tuple):
		"""Push an event to the Queue"""

		self.event_queue.append(event)

	def _make_string(self, term, text):
		"""Make a Maude string"""

		m = term.symbol().getModule()
		text = text.replace('"', r'\"')

		return m.parseTerm(f'"{text}"')

	def _make_window_id(self, term, data, index):
		"""Make a Maude string"""

		m = term.symbol().getModule()
		index = m.parseTerm(str(index))
		window_id = data.getSymbol('window')(index)
		window_id.reduce()

		return window_id

	def _get_string(self, term):
		"""Obtain a Python string from a Maude one"""

		return str(term)[1:-1].replace('\"', '"')

	def _iter_sbmap(self, term, true_term):
		"""Iterate over a Maude dictionary from String to Bool"""

		term.reduce()
		top_symbol = term.symbol()

		# Identify symbols by properties that are not subject to renaming
		# (we could have received the symbols instead)
		if top_symbol.arity() > 0:
			# The _,_ operator for building maps
			if top_symbol.hasAttr(maude.OP_ASSOC):
				for arg in term.arguments():
					key, value = arg.arguments()

					yield self._get_string(key), value == true_term

			# The map symbol
			else:
				key, value = term.arguments()

				yield self._get_string(key), value == true_term


	def run(self, term, data):
		"""Receive a message or an update request"""

		try:
			symbol = str(term.symbol())
			reply = None

			if symbol == '<G>':
				msgs = []

				# Create messages for each event in the queue
				for event in self.event_queue:
					window, etype, *args = event

					# Reply symbol and message
					symbol = data.getSymbol('buttonPressed' if etype == 'button' else 'valueChanged')
					msgs.append(symbol(self.owners[window], window, *(self._make_string(term, arg) for arg in args)))

				self.event_queue.clear()

				if msgs:
					reply = data.getSymbol('configJoin')(term, *msgs)
				else:
					reply = term

			elif symbol == 'createWindow':
				dest, sender, title, fields, buttons = term.arguments()

				true_term = data.getTerm('trueTerm')
				title = self._get_string(title)

				# Make an identifier and create the new window
				window_id = self._make_window_id(term, data, self.next_index)
				self.next_index += 1
				window = self.window_manager.new_window(window_id, title)

				# Register sender as owner of the window
				# (maybe allowing objects to subscribe is better)
				self.owners[window_id] = sender

				# Insert the fields and buttons
				for name, editable in self._iter_sbmap(fields, true_term):
					window.add_field(name, editable)

				for name, clickable in self._iter_sbmap(buttons, true_term):
					window.add_button(name, clickable)

				# Reply with the window identifier
				reply = data.getSymbol('createdWindow')(sender, dest, window_id)

			elif symbol == 'destroyWindow':
				window_id, sender = term.arguments()

				if self.window_manager.destroy_window(window_id):
					self.owners.pop(window_id)
					reply = data.getSymbol('destroyedWindow')(sender, window_id)
				else:
					reply = data.getSymbol('guiError')(sender, window_id, self._make_string(term, 'Unknown window'))

			elif symbol == 'setValue':
				window_id, sender, field, value = term.arguments()

				if window := self.window_manager.get(window_id):
					if window.set_field(self._get_string(field), self._get_string(value)):
						reply = data.getSymbol('valueSet')(sender, window_id)
					else:
						reply = data.getSymbol('guiError')(sender, window_id, self._make_string(term, 'Unknown field'))
				else:
					reply = data.getSymbol('guiError')(sender, window_id, self._make_string(term, 'Unknown window'))

			else:
				print('Unknown message received:', term)

		except Exception as e:
			traceback.print_exception(e)

		return reply


def read_constant(module, name, ctype=int):
	"""Read constant from a Maude module"""

	term = module.parseTerm(name)
	term.reduce()

	return str(ctype(term))


def main():
	"""Entry point"""

	import argparse

	parser = argparse.ArgumentParser(description='PCA open system')
	parser.add_argument('--two', '-2', help='Second variation of the model', action='store_true')

	args = parser.parse_args()

	maude.init()

	# Allow files for the actuator (controlled by a pipe)
	maude.setAllowFiles(True)
	maude.setAllowProcesses(True)

	guiManager = GuiManager()
	maude.connectRlHook('guiHook', guiManager)

	maude.load('pca2.maude' if args.two else 'pca.maude')

	if (m := maude.getCurrentModule()) is None:
		print('Bad module.')
		return 1

	init = m.parseTerm('init')

	def maude_task():
		print(init.erewrite())
		guiManager.destroy()

	# Start the sensor servers
	temp_proc = subprocess.Popen(('./sensor-bin', 'data/s1_sit.txt', read_constant(m, 'PORT-TEMP-SENSOR')))
	pulse_proc = subprocess.Popen(('./sensor-bin', 'data/p1.txt', read_constant(m, 'PORT-PULSE-SENSOR')))
	actuator_proc = subprocess.Popen(('./actuator-bin'))

	# Run erewrite in a different thread
	thread = threading.Thread(target=maude_task)
	thread.daemon = True
	thread.start()

	# Use themes for a better look and feel
	# s = ttk.Style()
	# s.theme_use('alt')

	guiManager.mainloop()

	# Terminate the sensor servers
	temp_proc.terminate()
	pulse_proc.terminate()
	actuator_proc.send_signal(signal.SIGINT)
	actuator_proc.terminate()

	return 0


if __name__ == '__main__':
	main()
