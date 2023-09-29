import tkinter as tk
from tkinter import StringVar
import docker
import boto3
import time
import threading
import redis
from datetime import datetime
import json
from utility.utilityFunc import *

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

with open('metrics.csv', 'a') as f: #header 
            f.write("total_cpu_usage,total_memory_usage,number_of_containers,number_of_active_containers,number_of_inactive_containers,timestamp\n")
f.close()

#functions pool to create the containers 
image1 = client.images.build(path=dockerfile_path_foo1, tag="func1")
image2 = client.images.build(path=dockerfile_path_foo2 , tag="func2")
image3 = client.images.build(path=dockerfile_path_foo3 , tag="func3")
redis_image = client.images.build(path=redis_path, tag="redis:latest")

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
    time.sleep(4)
    while True:
        active_containers = client.containers.list(all=False)
        containers = client.containers.list(all=True)
        containersOffline = retrieve_containers_offline(containers)
        
        if (lettera == "a"):
            total_cpu_usage = 0
            total_memory_usage = 0
            if nameRedisContainer in active_containers:
                active_containers.remove(nameRedisContainer)
            for container in active_containers:
                if nameRedisContainer == container.name:
                    continue    
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
            try:
                coldStart(containersOffline, redis_client)#check if the container is inactive for more than 20 seconds 
            except Exception as e:
                print("errore in fase di cold start: "+str(e))
                continue

        if (lettera == "c"):
            try:
                computeThreshold(redis_client, config_data)
            except Exception as e:
                print("errore in fase di offloading: "+str(e))
                continue

        if killThread == True:
            break

def serveRequest(opzioni_creazione, fooName):
    try:
        all_containers = client.containers.list(all=True)  # Ottieni tutti i container in running
    except Exception as e:
        print(e)
        return
                
    matching_containers_foo = [container for container in all_containers if str(fooName)+":latest" in container.image.tags]
   
    if offloading == False:
        if get_unused_container(matching_containers_foo) is None :
            container = client.containers.run(fooName, **opzioni_creazione)
            matching_containers_foo.append(container)
            update_output_text("Container "+fooName+" avviato")
        else: #if the container is not running restart the container
            container = get_unused_container(matching_containers_foo)
            if redis_client.hget("cold_start", container.name) is not None:
                container.restart()
                redis_client.hdel("cold_start", container.name)
                
    else: #if the offloading is true create a new container on aws lambda 
        print("offloading of function "  )
        try:
            response = lambda_client.invoke(            # Chiama la funzione Lambda in modo asincrono senza dati di input

                FunctionName=fooName,
                InvocationType='RequestResponse'  # Imposta 'Event' per una chiamata asincrona senza dati di input
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

def on_button_click_function1(): #first function 
    global offloading
    param1 = entryF1.get()
    if param1 != "":
        print("parametro inserito: "+param1)
        redis_client.hset("fastestSortingAlgorithm", "param1", param1)
    else:
        print("parametro non inserito")
        return
    serveRequest(opzioni_creazione,"func1")

def on_button_click_function2(): #second function 
    global offloading
    serveRequest(opzioni_creazione, "func2")

def on_button_click_function3(): #third function 
    global offloading
    serveRequest(opzioni_creazione, "func3")

label = tk.Label(app, text="Seleziona la funzione da avviare").grid(row=0, column=1)
button = tk.Button(app, text="fastest sorting algorithm", command= on_button_click_function1, padx=10, pady=5).grid(row=4, column=2)
entryF1 = tk.Entry()
entryF1.grid(row=4, column=4)

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

removeDanglingImages(client) #remove all the dangling images
app.mainloop() 
killThread = True
clerAllContainers(client) #close all the container when the GUI is closed
