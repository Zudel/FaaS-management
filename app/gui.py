import tkinter as tk
import docker


# Creazione dell'applicazione GUI
app = tk.Tk()
app.title("FaaS Management GUI")
app.geometry("720x480")


# Creazione di una etichetta per visualizzare il risultato
label = tk.Label(app, text="Hello, world!")
label.grid(row=0, column=0)
tk.Label(app, text="Hello, world!").grid(row=2, column=0)
tk.Label(app, text="this is una cosa").grid(row=3, column=0)

#text input 
e1 = tk.Entry(app, width=50, borderwidth=5).grid(row=2, column=1)
e2 = tk.Entry(app, width=50, borderwidth=5).grid(row=3, column=1)

# Crea un'istanza del client Docker
client = docker.from_env()

# Specifica il percorso del Dockerfile (se non si trova nella directory corrente)
dockerfile_path = "C:\\Users\\Roberto\\Documents\\GitHub\\Faas management\\app\\functions"

# Imposta il nome dell'immagine da costruire
nome_immagine = "goimagine"  # Specifica il nome desiderato per l'immagine

# Costruisci l'immagine utilizzando il Dockerfile
image = client.images.build(path=dockerfile_path, tag=nome_immagine)
#prendi il nome dell'immagine

def on_button_click():
    opzioni_creazione = {
        "command": "./main",  # Comando da eseguire all'interno del container
        "detach": True  # Esegui il container in background
    }
    # Avvia il container
    container = client.containers.run(nome_immagine, **opzioni_creazione)


# Creazione di un pulsante
button = tk.Button(app, text="Click Me", command= on_button_click ).grid(row=4, column=5)

# Esecuzione dell'applicazione
app.mainloop()


