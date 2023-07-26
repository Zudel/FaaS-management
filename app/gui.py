import tkinter as tk
import docker
import psutil
import time
import threading


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

def resource_metrics(container):
    container_id = container.id
    container_name = container.name
    container_status = container.status
    container_cpu = container.stats(stream=False)['cpu_stats']['cpu_usage']['total_usage']
    container_memory = container.stats(stream=False)['memory_stats']

    print("container status: " + container_status)
    print("amount cpu usage : " + str(container_cpu)+ " by " + str(container_name) +" with id: "+ str(container_id) +"\n")


    
def monitor_consumo_risorse(container):
     ferma_thread = False
     while ferma_thread == False:
        # Ottieni l'ID del container
        container_id = container.id

        # Ottieni le informazioni del container
        info_container = container.attrs

        # Ottieni le metriche di utilizzo della CPU
        cpu_percent = psutil.cpu_percent()
        cpu_stats = container.stats(stream=False)['cpu_stats']['cpu_usage']['total_usage']
    
        if cpu_stats == 0:
            ferma_thread = True

        # Stampa le metriche ottenute
        print(f"Metriche per il container (ID: {container_id}):")
        print(f"Utilizzo CPU : {cpu_percent:.2f}%")
        print("stato del container: " + container.status)
        print("------------------------")
       

        # Aspetta 10 secondi prima di ottenere nuovamente le metriche
        time.sleep(5)


def on_button_click():
    opzioni_creazione = {
        "command": "./main",  # Comando da eseguire all'interno del container
        "detach": True,  # Esegui il container in background
    }
    # Avvia il container
    container = client.containers.run(nome_immagine, **opzioni_creazione)
    all_containers = client.containers.list()
    # Crea un thread per monitorare le risorse di ogni container
    for container in all_containers:
        thread = threading.Thread(target=monitor_consumo_risorse, args=(container,))
        thread.start()
   

# Creazione di un pulsante
button = tk.Button(app, text="Click Me", command= on_button_click ).grid(row=4, column=5)

# Esecuzione dell'applicazione
app.mainloop()


