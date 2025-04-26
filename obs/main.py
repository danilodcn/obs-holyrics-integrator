from obs.gui import create_gui
from obs.message_bus import message_bus

root = create_gui(message_bus)
root.mainloop()
