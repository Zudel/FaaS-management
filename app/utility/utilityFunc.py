import os
import time

def removeDanglingImages(client):
    images = client.images.list() #remove all the dangling images 
    for image in images:
        if not image.tags:
            client.images.remove(image.id, force=True)
    for container in client.containers.list(all=True):
        if not container.image.tags:
            container.remove()

def clerAllContainers(client):
    for container in client.containers.list(all=True): #create a loop for for close the container when the GUI is closed

        container.stop()
        print(container.name +" container stopped")
        container.remove()
        print(container.name + "container removed")
    try:
        os.remove('metrics.csv')
        print(f"Il file metrics è stato eliminato con successo.")
    except OSError as e:
        print(f"Si è verificato un errore durante l'eliminazione del file: {e}")

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

def coldStart(containersOffline, redis_client):
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

def computeThreshold(redis_client, config_data):
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
                        res = True
                else:
                        res = False # se almeno una delle condizioni non è soddisfatta, torno in locale
                return res