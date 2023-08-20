import csv
import matplotlib.pyplot as plt

# Lista per memorizzare i dati
timestamps = []
total_cpu_usages = []
total_memory_usages = []

# Apri il file CSV e leggi i dati
with open('app/metrics.csv', 'r') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        timestamps.append(row['timestamp'])
        total_cpu_usages.append(float(row['total_cpu_usage']))
        total_memory_usages.append(float(row['total_memory_usage']))

# Crea un plot
plt.figure(figsize=(10, 6))
plt.plot(timestamps, total_cpu_usages, label='Total CPU Usage')
plt.plot(timestamps, total_memory_usages, label='Total Memory Usage')
plt.xlabel('Timestamp')
plt.ylabel('Usage')
plt.title('Metrics')
plt.legend()
plt.grid(True)
plt.show()