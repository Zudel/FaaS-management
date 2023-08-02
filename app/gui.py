import tkinter as tk
from tkinter import StringVar
import docker
import time
import yaml
import os
import threading
import redis



# Funzione per aggiornare il testo della finestra di output
def update_output_text(text):
    output_text.set(text)


# Creazione dell'applicazione GUI
app = tk.Tk()
app.title("FaaS Management GUI")
app.geometry("720x480")
# Creazione di una etichetta per visualizzare il risultato
label = tk.Label(app, text="welcome to my Faas management application!")
output_text = StringVar()
output_text.set("Output qui")


# Crea un'istanza del client Docker
client = docker.from_env()

dockerfile_path_foo1 = "C:\\Users\\Roberto\\Documents\\GitHub\\Faas management\\app\\functions\\func1"
dockerfile_path_foo2 = "C:\\Users\\Roberto\\Documents\\GitHub\\Faas management\\app\\functions\\func2"
redis_path = "C:\\Users\\Roberto\\Documents\\GitHub\\Faas management\\app\\redis"

#functions pool to create the containers 
image1 = client.images.build(path=dockerfile_path_foo1, tag="func1")
image2 = client.images.build(path=dockerfile_path_foo2 , tag="func2")
redis_image = client.images.build(path=redis_path, tag="redis:latest")

#run a redis container
options = {
        "command": "redis-server" ,  # Comando da eseguire all'interno del container
        "detach": True,  # Esegui il container in background
        "ports": {"6379": ("127.0.0.1", 6379)}  # Mappa la porta 6379 del container a 127.0.0.1:6379
    }
redis_container = client.containers.run("redis", **options)
# connect to redis
try:
    redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0) 
except Exception as e:
    print(e)
    redis_container.stop()
    redis_container.remove()

def verify_container_status(containers):
    f = False
    for container in containers:
        if container.status != "running":
            f = True
    return f

def get_unused_container(all_containers):
    for container in all_containers:
        # Verifica se il container non sta eseguendo
        if container.status != 'running':
            return container
    return None


    
def container_resource_metrics(containers):
    #remove the redis container from the list of containers
    containers.remove(redis_container)
    
    total_cpu_usage = 0
    total_memory_usage = 0
    
    print("numero di container in esecuzione: " + str(len(containers)))
    for container in containers:
        container_id = container.id
        container_name = container.name
        stats = container.stats(stream=False) #If stream set to false, only the current stats will be returned instead of a stream. True by default.
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


        # print the metrics
        print(f"Metriche per il container "+ container_name +" (ID: {container_id}):")
        print("cpu usage: " + str(percentage) + "%")
        print("memory usage: " + str(mem_perc) + "%")
        print("stato del container: " + container.status)
        print("------------------------")
    #wait 10 second before checking again the status of the container 
    time.sleep(10)

# thread to check the status of the container

thread = threading.Thread(target=container_resource_metrics, args=(client.containers.list(all=False),))
thread.start()

#first function to start the container
def on_button_click_function1():
    opzioni_creazione = {
        "command": "./main",  # Comando da eseguire all'interno del container
        "detach": True,  # Esegui il container in background
    }
    all_containers = client.containers.list(all=True)  # Ottieni tutti i container in running
    matching_containers_foo1 = [container for container in all_containers if "func1:latest" in container.image.tags]

    if get_unused_container(matching_containers_foo1) is None :
        container = client.containers.run("func1", **opzioni_creazione)
        matching_containers_foo1.append(container)
        update_output_text("Container func1 avviato")
    else: #if the container is not running restart the container
        container = get_unused_container(matching_containers_foo1)
        container.restart()
        update_output_text("Container func1 avviato")

#first function to start the container
def on_button_click_function2():
    opzioni_creazione = {
        "command": "./foo2",  # Comando da eseguire all'interno del container
        "detach": True,  # Esegui il container in background
    }
    all_containers = client.containers.list(all=True)  # Ottieni tutti i container in running
    matching_containers_foo2 = [container for container in all_containers if "func2:latest" in container.image.tags]
    
    if get_unused_container(matching_containers_foo2) is None:
        container = client.containers.run("func2", **opzioni_creazione)
        update_output_text("Container func2 avviato")
    else:
        container = get_unused_container(matching_containers_foo2)
        container.restart()
        update_output_text("Container func2 avviato")

label = tk.Label(app, text="Seleziona la funzione da avviare").grid(row=0, column=1)
button = tk.Button(app, text="foo1", command= on_button_click_function1, padx=10, pady=5).grid(row=4, column=2)
tk.Label(app, text="").grid(row=5, column=2)
tk.Label(app, text="").grid(row=6, column=2)
tk.Label(app, text="").grid(row=7, column=2)
button2 = tk.Button(app, text="foo2", command= on_button_click_function2, padx=10, pady=5).grid(row=8, column=2)
# Etichetta per la finestra di output
output_label = tk.Label(app, textvariable=output_text)
tk.Label(app, text="",padx=100, pady=5).grid(row=4, column=4)
output_label.grid(row=4, column=7)


   
# Esecuzione dell'applicazione
app.mainloop()
print('GUI closed')
#create a loop for for close the container when the GUI is closed
for container in client.containers.list(all=True):
    container.stop()
    print(container.name +" container stopped")
    container.remove()
    print(container.name + "container removed")
