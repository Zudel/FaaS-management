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

offloading = True #if the offloading is true the function will be executed on aws lambda
opzioni_creazione = {
        "command": "./main",  
        "detach": True,  
    }

with open("config.json", "r") as config_file:
    config_data = json.load(config_file)
client = docker.from_env()
lambda_client = boto3.client('lambda')
sqs_client = boto3.client('sqs', region_name='us-east-1')
queue_url = config_data["url"]["queue_url"]
dockerfile_path_foo1 = config_data["path"]["func1_path"]
dockerfile_path_foo2 = config_data["path"]["func2_path"]
dockerfile_path_foo3 = config_data["path"]["func3_path"]
redis_path = config_data["path"]["redis_path"]
# channels for the broker message Redis
knapsack_channel = config_data["channel"]["knapsack_channel"] 
subsetSum_channel = config_data["channel"]["subsetSum_channel"]
sortAlg_Channel = config_data["channel"]["sortAlg_Channel"]

#functions pool to create the containers 

image1 = client.images.build(path=dockerfile_path_foo1, tag="fastest_sorting_algorithm")
image2 = client.images.build(path=dockerfile_path_foo2 , tag="knapsack")
image3 = client.images.build(path=dockerfile_path_foo3 , tag="subset_sum")
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
    exit(-1)

pubsub = redis_client.pubsub()
pubsub.subscribe(knapsack_channel)
pubsub.subscribe(subsetSum_channel)
pubsub.subscribe(sortAlg_Channel)

def controller(lettera):
    global offloading
    #remove the redis container from the list of containers
    time.sleep(0.5)
    while True:
        try:
            active_containers = client.containers.list(all=False)
            containers = client.containers.list(all=True)
            containersOffline = retrieve_containers_offline(containers)
        except Exception as e:
            continue
        
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

        if (lettera == "b"):
            try:
                coldStart(containersOffline, redis_client)#check if the container is inactive for more than 20 seconds 
            except Exception as e:
                print("errore in fase di cold start: "+str(e))
                continue

        if (lettera == "c"):
                try:
                    time.sleep(1)
                    res = computeThreshold(redis_client, config_data)
                    offloading = res
                except Exception as e:
                    print("errore nell'attuare la politica di offloading: "+str(e))
        if (lettera == "d"):
            while killThread == False:
                # check if there are messages in redis broker
                for messaggio in pubsub.listen():
                        canale = messaggio['channel'].decode('utf-8')
                        dati = messaggio['data']
                        if dati == 1 or dati == 2 or dati == 3:
                            continue
                        print(f"Ricevuto messaggio da {canale}: {dati}")
                        risultato_text.insert(tk.END, str(dati) + "\n")        

        if killThread == True:
            break

def offloadingFunction(input_data, fooName):
    try:
            print("invio della richiesta alla funzione lambda")
            print("input data: " + str(input_data) + "destination function: " + fooName)
            response = lambda_client.invoke(            
                FunctionName=fooName,
                InvocationType='RequestResponse',  
                Payload = json.dumps(input_data)
            )
            response_payload = response['Payload'].read()
            response_payload_str = response_payload.decode('utf-8')
            print("Risposta dalla funzione Lambda: " + str(response_payload_str))
            try:
                response_data = json.loads(response_payload_str)
                print("Risposta dalla funzione Lambda: " + str(response_data))
                result = response_data.get("body")
                if result is not None:
                    print("Risultato dalla funzione Lambda: " + str(result))
                    
                else:
                    result = response_data.get("errorMessage")
                    print("Errore dalla funzione Lambda: " + str(result))

                risultato_text.insert(tk.END,"Risultato dalla funzione Lambda: " +  str(result) + "\n")
                
            except json.JSONDecodeError:
                print("Impossibile analizzare la risposta di Lambda come JSON.")
            
    except Exception as e:
            print(f"Errore durante la chiamata della funzione Lambda: {str(e)}")
            return     

def serveRequest(opzioni_creazione, fooName):
    global offloading
    try:
        all_containers = client.containers.list(all=True)  # obtain all the containers 
    except Exception as e:
        print(e)
        return
                
    matching_containers_foo = [container for container in all_containers if str(fooName)+":latest" in container.image.tags]
   
    if offloading == False:
        if get_unused_container(matching_containers_foo) is None :
            container = client.containers.run(fooName, **opzioni_creazione)
            matching_containers_foo.append(container)

        else: #if the container is not running restart the container
            container = get_unused_container(matching_containers_foo)
            if redis_client.hget("cold_start", container.name) is not None:
                container.restart()
                redis_client.hdel("cold_start", container.name)
                
    else: #if the offloading is true create a new container on aws lambda 
        print("offloading of function " + fooName + " on aws lambda"  )
        
        
        if fooName == "fastest_sorting_algorithm":
            input_data = { #input data for the lambda function like a dictionary
                "param1": redis_client.hget("fastest_sorting_algorithm", "param1").decode('utf-8')
        }
        elif fooName == "knapsack":

            input_data = { #input data for the lambda function like a dictionary
                "param1": redis_client.hget("knapsack", "param1K").decode('utf-8') ,       
                "param2": redis_client.hget("knapsack", "param2K").decode('utf-8')
                
        }
        else:
            # devo assegnar eil dizionario di redis a input data
            input_data ={
                "param1": redis_client.hget("subset_sum", "param1S").decode('utf-8') ,
                "param2": redis_client.hget("subset_sum", "param2S").decode('utf-8')
            }
        thread5 = threading.Thread(target=offloadingFunction, args=(input_data, fooName)) #thread check the messages in the queue of aws sqs
        thread5.start()
        
        

killThread = False
lock = threading.Lock()
thread1 = threading.Thread(target=controller, args=("a")) #thread for the metrics
thread1.start()    
thread2 = threading.Thread(target=controller, args=("b")) #thread for the cold start
thread2.start()  
thread3 = threading.Thread(target=controller, args=("c")) #thread for the offloading
thread3.start()
thread4 = threading.Thread(target=controller, args=("d")) #thread check the messages from broker message Redis 
thread4.start()


def on_button_click_function1(): 
    global offloading
    param1 = entryF1.get()
    if param1 != "":
        print("parametro inserito: "+param1)
        redis_client.hmset("fastest_sorting_algorithm", {"param1": param1}) 
    else:
        print("parametro non inserito")
        return
    serveRequest(opzioni_creazione,"fastest_sorting_algorithm") #fastest sorting algorithm

def on_button_click_function2():
    global offloading
    param1K = entryF2.get() #capacity
    param2K = entryF2Param2.get() #size of the array of objects
    if param1K != "" and param2K != "" :
        print("parametri inseriti: "+param1K+" "+param2K)
        redis_client.hmset("knapsack", {"param1K": param1K, "param2K": param2K})
    else:
        print("manca un parametro")
        return
    serveRequest(opzioni_creazione, "knapsack") #knapsack NP problem
    
def on_button_click_function3(): #subsetSum NP problem
    global offloading
    param1S = entryF3Param2.get()
    param2S = entryF3.get()
    if param1S != "" and param2S != "":
        print("parametri inseriti: "+param1S+" "+param2S)
        redis_client.hmset("subset_sum", {"param1S": param1S, "param2S": param2S})
    else:
        print("manca un parametro")
        return
    serveRequest(opzioni_creazione, "subset_sum")

# GUI setup

app = tk.Tk()
app.title("FaaS Management GUI")
app.geometry("720x480")
label = tk.Label(app, text="welcome to my Faas management application!")

label = tk.Label(app, text="Seleziona la funzione da avviare").grid(row=0, column=1)

entryF1 = tk.Entry()
entryF1.grid(row=4, column=5)
tk.Label(app, text="").grid(row=5, column=2)
tk.Label(app, text="").grid(row=6, column=2)
tk.Label(app, text="").grid(row=7, column=2)
tk.Label(app, text="").grid(row=8, column=2)
tk.Label(app, text="").grid(row=9, column=2)
tk.Label(app, text="").grid(row=10, column=2)
tk.Label(app, text="").grid(row=11, column=2)
tk.Label(app, text="").grid(row=12, column=2)
tk.Label(app, text="inserire la dimensione dell'array",padx=100, pady=5).grid(row=4, column=4)


tk.Label(app, text="inserire la capacità  ").grid(row=9, column=4)
tk.Label(app, text="inserire la dimensione del vettore degli oggetti").grid(row=10, column=4)
entryF2 = tk.Entry()
entryF2.grid(row=9, column=5)
entryF2Param2 = tk.Entry()
entryF2Param2.grid(row=10, column=5)

# buttons
tk.Button(app, text="fastest sorting algorithm", command= on_button_click_function1, padx=10, pady=5).grid(row=4, column=2)
tk.Button(app, text="knapsack", command= on_button_click_function2, padx=10, pady=5).grid(row=10, column=2)
tk.Button(app, text="Subset sum", command= on_button_click_function3, padx=10, pady=5).grid(row=17, column=2)

tk.Label(app, text="").grid(row=15, column=4)
tk.Label(app, text="").grid(row=16, column=4)
tk.Label(app, text="Inserire la dimensione del vettore degli elementi del sottoinsieme").grid(row=17, column=4)
tk.Label(app, text="Inserire la soglia target").grid(row=18, column=4)
entryF3Param2 = tk.Entry()
entryF3Param2.grid(row=17, column=5)
entryF3 = tk.Entry()
entryF3.grid(row=18, column=5)

# scrollbar
scrollbar = tk.Scrollbar()
scrollbar.grid(row=20, column=2, rowspan=20, sticky=tk.N + tk.S)

#widget Text 
risultato_text = tk.Text(yscrollcommand=scrollbar.set)
risultato_text.grid(row=20, column=2, rowspan=20, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W)
scrollbar.config(command=risultato_text.yview)
removeDanglingImages(client) #remove all the dangling images
app.mainloop()

killThread = True
clerAllContainers(client) #close all the container when the GUI is closed
