import tkinter as tk
from tkinter import StringVar
import docker
import boto3
import time
import yaml
import os
import threading
import redis
from datetime import datetime
import json
import sys


offloading = False #if the offloading is true the function will be executed on aws lambda
# Funzione per aggiornare il testo della finestra di output
def update_output_text(text):
    output_text.set(text)
opzioni_creazione = {
        "command": "./main",  # Comando da eseguire all'interno del container
        "detach": True,  # Esegui il container in background
    }

with open("config.json", "r") as config_file:
    config_data = json.load(config_file)

app = tk.Tk()
app.title("FaaS Management GUI")
app.geometry("720x480")
label = tk.Label(app, text="welcome to my Faas management application!")
output_text = StringVar()
output_text.set("Output qui")

client = docker.from_env()
lambda_client = boto3.client('lambda')
sqs_client = boto3.client('sqs', region_name='us-east-1')
queue_url = config_data["url"]["queue_url"]
dockerfile_path_foo1 = config_data["path"]["func1_path"]
dockerfile_path_foo2 = config_data["path"]["func2_path"]
dockerfile_path_foo3 = config_data["path"]["func3_path"]
redis_path = config_data["path"]["redis_path"]

with open('metrics.csv', 'a') as f:
            #header 
            f.write("total_cpu_usage,total_memory_usage,number_of_containers,number_of_active_containers,number_of_inactive_containers,timestamp\n")
f.close()

#functions pool to create the containers 
image1 = client.images.build(path=dockerfile_path_foo1, tag="func1")
image2 = client.images.build(path=dockerfile_path_foo2 , tag="func2")
image3 = client.images.build(path=dockerfile_path_foo3 , tag="func3")

redis_image = client.images.build(path=redis_path, tag="redis:latest")
all_containers = client.containers.list(all=True)  

#run a redis container
options = {
        "command": config_data["redis"]["command"] ,  
        "detach": True,  
        "ports": {config_data["redis"]["port"] : (config_data["redis"]["host"] , config_data["redis"]["portNumber"] )}  # Mappa la porta 6379 del container a 127.0.0.1:6379
    }
redis_container = client.containers.run("redis", **options)
nameRedisContainer = redis_container.name

# connect to redis
try:
    redis_client = redis.Redis(host=config_data["redis"]["host"] , port=config_data["redis"]["portNumber"] , db=0) 
    
except Exception as e:
    print(e)
    redis_container.stop()
    redis_container.remove()




   
def container_resource_metrics(lettera):
    global offloading
    #remove the redis container from the list of containers
    time.sleep(5)
    while True:
        
        active_containers = client.containers.list(all=False)
        containers = client.containers.list(all=True)
        containersOffline = utilityFunc.retrieve_containers_offline(containers)
        
        if (lettera == "a"):
            total_cpu_usage = 0
            total_memory_usage = 0
            if nameRedisContainer in active_containers:
                active_containers.remove(nameRedisContainer)
            for container in active_containers:
                if nameRedisContainer == container.name:
                    continue
                    
                #print("numero di container istanziati: " + str(len(containers)-1)) #remove the redis container from the list of containers
                #print("numero di container in esecuzione: " + str(len(active_containers)-1)) #remove the redis container from the list of containers
                #print("numero di container inattivi: " + str(len(containersOffline)))    
                try:
                    stats = container.stats(stream = False) #If stream set to false, only the current stats will be returned instead of a stream. True by default.
                        
                    UsageDelta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                    SystemDelta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                    len_cpu  = len( stats['cpu_stats']['cpu_usage']['percpu_usage'])
                    memory_usage = stats['memory_stats']['usage'] - stats['memory_stats']['stats']['cache']
                    memory_limit = stats['memory_stats']['limit']
                    percentage = (UsageDelta / SystemDelta) * len_cpu * 100
                    memory_percentage = (memory_usage / memory_limit) * 100
                    mem_perc = round(memory_percentage, 2)
                    #compute the total cpu usage and the total memory usage
                    total_cpu_usage = total_cpu_usage + percentage
                    total_memory_usage = total_memory_usage + mem_perc
                except KeyError:
                    break  
                    
            # after the for loop print the total cpu usage and the total memory usage 
            if(len(active_containers) > 1):
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
            datetime_obj = datetime.fromtimestamp(time.time())
            human_readable_time = datetime_obj.strftime('%H:%M:%S')     
            with open('metrics.csv', 'a') as f:
                f.write(str(total_cpu_usage) + "," + str(total_memory_usage) + "," + str(len(containers)-1) + "," + str(len(active_containers)-1) + "," + str(len(containersOffline)) + "," + str(human_readable_time) + "\n")
            f.close()

            
        if (lettera == "b"):
            #check if the container is inactive for more than 20 seconds       
            
            for container in containersOffline:
                if container.status == "exited" and redis_client.hget("cold_start", container.name) is None:
                    redis_client.hset("cold_start", container.name, time.time())
                if container.status == "running" and redis_client.hget("cold_start", container.name) is not None:
                    redis_client.hdel("cold_start", container.name)
                if container.status == "exited" and redis_client.hget("cold_start", container.name) is not None:
                    tempo = time.time() - float(redis_client.hget("cold_start", container.name))
                    if tempo > 20 and container.status != "running":                           #if the container is inactive for more than 20 seconds remove the container
                        container.remove()
                        redis_client.hdel("cold_start", container.name)
                        print("container " + container.name + " removed")
                        print("tempo di inattività: " + str(tempo) + " secondi")
                        print("------------------------")    
        if (lettera == "c"):
           
            try:
                total_cpu_usage2 = float(redis_client.hget("metrics", "total_cpu_usage"))
                total_memory_usage2 = float(redis_client.hget("metrics", "total_memory_usage"))
                number_of_active_containers = int(redis_client.hget("metrics", "number_of_active_containers"))
                timestamp = float(redis_client.hget("metrics", "timestamp"))
            
            
                #get the threshold from json file
                threshold_cpu = float(config_data["threshold"]["cpu"])
                threshold_memory = float(config_data["threshold"]["memory"])
                threshold_number_of_active_containers = int(config_data["threshold"]["number_of_active_containers"])

                #check if the metrics are greater than the threshold
                if total_cpu_usage2 > threshold_cpu or total_memory_usage2 > threshold_memory or number_of_active_containers > threshold_number_of_active_containers:
                    #do offloading
                        offloading = True
                else:
                        offloading = False # se almeno una delle condizioni non è soddisfatta, torno in locale
            
            except Exception as e:
                print(e)
                continue

        if killThread == True:
            break

def serveRequest(opzioni_creazione):
    all_containers = client.containers.list(all=True)  # Ottieni tutti i container in running
    matching_containers_foo1 = [container for container in all_containers if "func1:latest" in container.image.tags]
   
    if offloading == False:
        if utilityFunc.get_unused_container(matching_containers_foo1) is None :
            container = client.containers.run("func1", **opzioni_creazione)
            matching_containers_foo1.append(container)
            update_output_text("Container func1 avviato")
        else: #if the container is not running restart the container
            container = utilityFunc.get_unused_container(matching_containers_foo1)
            if redis_client.hget("cold_start", container.name) is not None:
                container.restart()
                redis_client.hdel("cold_start", container.name)
                update_output_text("Container func1 avviato")
    else: #if the offloading is true create a new container on aws lambda 
        print("offloading of function 1")
        try:
            response = lambda_client.invoke(            # Chiama la funzione Lambda in modo asincrono senza dati di input

                FunctionName="foo1",
                InvocationType='Event'  # Imposta 'Event' per una chiamata asincrona senza dati di input
            )
            
            # Estrai la risposta quando risulta disponibile
            
            
            response_payload = response['Payload'].read()
            print(f"Risposta dalla funzione Lambda: {response_payload.decode('utf-8')}")
        
        except Exception as e:
            print(f"Errore durante la chiamata della funzione Lambda: {str(e)}")

killThread = False
lock = threading.Lock()
thread1 = threading.Thread(target=container_resource_metrics, args=("a"))
thread1.start()    
thread2 = threading.Thread(target=container_resource_metrics, args=("b"))
thread2.start()  
thread3 = threading.Thread(target=container_resource_metrics, args=("c"))
thread3.start()

#first function 
def on_button_click_function1():
    global offloading
    serveRequest(opzioni_creazione)
        

#second function 
def on_button_click_function2():
    global offloading
    serveRequest(opzioni_creazione)

#third function 
def on_button_click_function3():
    global offloading
    serveRequest(opzioni_creazione)


label = tk.Label(app, text="Seleziona la funzione da avviare").grid(row=0, column=1)
button = tk.Button(app, text="foo1", command= on_button_click_function1, padx=10, pady=5).grid(row=4, column=2)
tk.Label(app, text="").grid(row=5, column=2)
tk.Label(app, text="").grid(row=6, column=2)
tk.Label(app, text="").grid(row=7, column=2)
button2 = tk.Button(app, text="foo2", command= on_button_click_function2, padx=10, pady=5).grid(row=8, column=2)
tk.Label(app, text="").grid(row=8, column=2)
tk.Label(app, text="").grid(row=9, column=2)
tk.Label(app, text="").grid(row=10, column=2)
button3 = tk.Button(app, text="foo3", command= on_button_click_function3, padx=10, pady=5).grid(row=12, column=2)
output_label = tk.Label(app, textvariable=output_text) # Etichetta per la finestra di output
tk.Label(app, text="",padx=100, pady=5).grid(row=4, column=4)
output_label.grid(row=4, column=7)


utilityFunc.removeDanglingImages(client) #remove all the dangling images 
app.mainloop()
killThread = True
print('GUI closed')
utilityFunc.clerAllContainers(client) #create a loop for for close the container when the GUI is closed
