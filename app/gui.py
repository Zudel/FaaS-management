import tkinter as tk
import docker
import time
import threading


# Creazione dell'applicazione GUI
app = tk.Tk()
app.title("FaaS Management GUI")
app.geometry("720x480")


# Creazione di una etichetta per visualizzare il risultato
label = tk.Label(app, text="welcome to my Faas management application!")
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
all_containers = client.containers.list(all=True)  # Ottieni tutti i container in running
unused_containers = []


def get_unused_containers():
 
    for container in all_containers:
        # Verifica se il container non sta eseguendo
        if container.status != 'running':
            unused_containers.append(container)

    return unused_containers



    
def container_resource_metrics(container):
     ferma_thread = False
     while container.status == "running"  :
        # Ottieni l'ID del container
        container_id = container.id

        # Ottieni le informazioni del container
        info_container = container.attrs
        stats = container.stats(stream=False)
        #compute cpu usage
        UsageDelta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        try:
            SystemDelta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        except KeyError:
            return #return if the system_cpu_usage is not available
        len_cpu = len( stats['cpu_stats']['cpu_usage']['percpu_usage'])
        
        percentage = (UsageDelta / SystemDelta) * len_cpu * 100
        #compute memory usage
        memory_usage = stats['memory_stats']['usage'] - stats['memory_stats']['stats']['cache']
        memory_limit = stats['memory_stats']['limit']
        memory_percentage = (memory_usage / memory_limit) * 100
        mem_perc = round(memory_percentage, 2)


        # Stampa le metriche ottenute
        print(f"Metriche per il container (ID: {container_id}):")
        print("cpu usage: " + str(percentage) + "%")
        print("memory usage: " + str(mem_perc) + "%")
        #print("container stats: " + str(container.stats(stream=False)) )
        print("stato del container: " + container.status)
        print("------------------------")
       
        time.sleep(1)

# Crea un thread per monitorare le risorse di ogni container
for container in client.containers.list(all=False):
    thread = threading.Thread(target=container_resource_metrics, args=(container,))
    thread.start()

def on_button_click():
    opzioni_creazione = {
        "command": "./main",  # Comando da eseguire all'interno del container
        "detach": True,  # Esegui il container in background
    }
    if all_containers.__len__() == 0:
        container = client.containers.run(nome_immagine, **opzioni_creazione)
    else:
        container = get_unused_containers()[len(unused_containers)-1]
        print("container trovato")
        print(container)
        #delete the container in unused_containers
        unused_containers.remove(container)
        container.restart()

    
button = tk.Button(app, text="Click Me", command= on_button_click ).grid(row=4, column=5)

   
# Esecuzione dell'applicazione
app.mainloop()


