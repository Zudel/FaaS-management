import tkinter as tk
from tkinter import StringVar
import docker
import time
import yaml
import os
import threading
import redis
from datetime import datetime


# Funzione per aggiornare il testo della finestra di output
def update_output_text(text):
    output_text.set(text)


# Creazione dell'applicazione GUI
app = tk.Tk()
app.title("FaaS Management GUI")
app.geometry("720x480")
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
all_containers = client.containers.list(all=True)  # Ottieni tutti i container in running

#run a redis container
options = {
        "command": "redis-server" ,  # Comando da eseguire all'interno del container
        "detach": True,  # Esegui il container in background
        "ports": {"6379": ("127.0.0.1", 6379)}  # Mappa la porta 6379 del container a 127.0.0.1:6379
    }
redis_container = client.containers.run("redis", **options)
nameRedisContainer = redis_container.name

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

def retrieve_containers_offline(containers):
    offline_containers = []
    for container in containers:
        if container.status == "exited":
            offline_containers.append(container)
    return offline_containers

    
def container_resource_metrics():
    #remove the redis container from the list of containers
    time.sleep(6)
    while True:
        active_containers = client.containers.list(all=False)
        containers = client.containers.list(all=True)
        containersOffline = retrieve_containers_offline(containers)
        total_cpu_usage = 0
        total_memory_usage = 0
        if nameRedisContainer in active_containers:
            active_containers.remove(nameRedisContainer)
        for container in active_containers:
            print("numero di container istanziati: " + str(len(containers)-1)) #remove the redis container from the list of containers
            print("numero di container in esecuzione: " + str(len(active_containers)-1)) #remove the redis container from the list of containers
            print("numero di container inattivi: " + str(len(containersOffline))) 
            
            container_id = container.id
            container_name = container.name
            print("nome del container: " + container_name)
            print("stato del container: " + container.status)
                
            try:
                print("stato del container: " + container.status)
                stats = container.stats(stream = False) #If stream set to false, only the current stats will be returned instead of a stream. True by default.
                    
                UsageDelta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                SystemDelta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                len_cpu  = len( stats['cpu_stats']['cpu_usage']['percpu_usage'])
                #compute memory usage
                memory_usage = stats['memory_stats']['usage'] - stats['memory_stats']['stats']['cache']
                memory_limit = stats['memory_stats']['limit']
                percentage = (UsageDelta / SystemDelta) * len_cpu * 100
                memory_percentage = (memory_usage / memory_limit) * 100
                mem_perc = round(memory_percentage, 2)
            except KeyError:
                continue   
                
                
                # print the metrics for each container
                print(f"Metriche per il container "+ container_name +" (ID: {container_id}):")
                print("cpu usage: " + str(percentage) + "%")
                print("memory usage: " + str(mem_perc) + "%")
                print("stato del container: " + container.status)
                print("------------------------")

            #compute the total cpu usage and the total memory usage
                total_cpu_usage = total_cpu_usage + percentage
                total_memory_usage = total_memory_usage + mem_perc
            time.sleep(1)
         # after the for loop print the total cpu usage and the total memory usage 
        print("total cpu usage: " + str(total_cpu_usage) + "%")
        print("total memory usage: " + str(total_memory_usage) + "%")
        print("------------------------")
        #insert the metrics in redis 
        redis_client.hset("metrics", "total_cpu_usage", total_cpu_usage)
        redis_client.hset("metrics", "total_memory_usage", total_memory_usage)
        redis_client.hset("metrics", "number_of_containers", len(containers)-1)
        redis_client.hset("metrics", "number_of_active_containers", len(active_containers)-1)
        redis_client.hset("metrics", "number_of_inactive_containers", len(containersOffline))
        redis_client.hset("metrics", "timestamp", time.time())
        # Crea un oggetto datetime dal timestamp
        datetime_obj = datetime.fromtimestamp(time.time())
        # Formatta l'oggetto datetime in una stringa leggibile
        human_readable_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')     

        # write the metrics in a file csv 
        with open('metrics.csv', 'a') as f:
            #header 
            f.write("total_cpu_usage,total_memory_usage,number_of_containers,number_of_active_containers,number_of_inactive_containers,timestamp\n")
            f.write(str(total_cpu_usage) + "," + str(total_memory_usage) + "," + str(len(containers)-1) + "," + str(len(active_containers)-1) + "," + str(len(containersOffline)) + "," + str(human_readable_time) + "\n")
        f.close()

        #check if the container is inactive for more than 20 seconds       
        
        for container in containersOffline:
            if containersOffline is None:
                continue
            if container.status == "exited" and redis_client.hget("cold_start", container.name) is None:
                redis_client.hset("cold_start", container.name, time.time())
            if container.status == "running" and redis_client.hget("cold_start", container.name) is not None:
                redis_client.hdel("cold_start", container.name)
            if container.status == "exited" and redis_client.hget("cold_start", container.name) is not None:
                tempo = time.time() - float(redis_client.hget("cold_start", container.name))
                if tempo > 20:                           #if the container is inactive for more than 20 seconds remove the container
                    container.remove()
                    redis_client.hdel("cold_start", container.name)
                    print("container " + container.name + " removed")
                    print("tempo di inattività: " + str(tempo) + " secondi")
                    print("------------------------")    
        #crea un if che se viene chiusa l'aplicazione termina il thread
        if killThread == True:
            break

killThread = False
thread1 = threading.Thread(target=container_resource_metrics, args=())
thread1.start()    
    

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
images = client.images.list()

#remove all the dangling images 
for image in images:
    if not image.tags:
        client.images.remove(image.id, force=True)
for container in client.containers.list(all=True):
    if not container.image.tags:
        container.remove()

 
app.mainloop()
print('GUI closed')
killThread = True
#create a loop for for close the container when the GUI is closed
for container in client.containers.list(all=True):
    container.stop()
    print(container.name +" container stopped")
    container.remove()
    print(container.name + "container removed")
# Elimina il file
try:
    os.remove('metrics.csv')
    print(f"Il file metrics è stato eliminato con successo.")
except OSError as e:
    print(f"Si è verificato un errore durante l'eliminazione del file: {e}")
