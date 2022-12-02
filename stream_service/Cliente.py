import sys
from tkinter import Tk
from .ClienteGUI import ClienteGUI

class Cliente:
        def main(self, addr, port):
	
                root = Tk()
                
                # Create a new client
                app = ClienteGUI(root, addr, port)
                app.master.title("Cliente Exemplo")	
                root.mainloop()
	
