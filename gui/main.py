#crea una gui per la gestione dei file
#crea una gui per la gestione dei file

import boto3
import tkinter as tk

#devo creare una gui per le funzioi 

def on_button_click():
    label.config(text="Button clicked!")

# Creazione dell'applicazione GUI
app = tk.Tk()
app.title("FaaS Management GUI")
app.geometry("800x600")


# Creazione di un pulsante
button = tk.Button(app, text="Click Me", command=on_button_click)
button.pack()

# Creazione di una etichetta per visualizzare il risultato
label = tk.Label(app, text="Hello, world!")
label.pack()

# Esecuzione dell'applicazione
app.mainloop()


