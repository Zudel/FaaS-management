
import tkinter as tk
import subprocess


# Creazione dell'applicazione GUI
app = tk.Tk()
app.title("FaaS Management GUI")
app.geometry("720x480")

def on_button_click():
    #invocare una funzione scritta in Go
    process = subprocess.run(["./functions"],capture_output=True, text=True)
    output = process.stdout.read()
    print(output)
    


# Creazione di una etichetta per visualizzare il risultato
label = tk.Label(app, text="Hello, world!")
label.grid(row=0, column=0)
tk.Label(app, text="Hello, world!").grid(row=2, column=0)
tk.Label(app, text="this is una cosa").grid(row=3, column=0)

#text input 
e1 = tk.Entry(app, width=50, borderwidth=5).grid(row=2, column=1)
e2 = tk.Entry(app, width=50, borderwidth=5).grid(row=3, column=1)
# Creazione di un pulsante
button = tk.Button(app, text="Click Me", command=on_button_click).grid(row=4, column=5)
def on_button_click():
   button.config(text="Button clicked!")
# Esecuzione dell'applicazione
app.mainloop()


