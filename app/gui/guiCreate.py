import tkinter as tk

def gui_setup():
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
    tk.Label(app, text="inserire i pesi").grid(row=10, column=4)
    tk.Label(app, text="inserire i valori").grid(row=11, column=4)
    entryF2 = tk.Entry()
    entryF2.grid(row=9, column=5)
    entryF2Param2 = tk.Entry()
    entryF2Param2.grid(row=10, column=5)
    entryF2Param3 = tk.Entry()
    entryF2Param3.grid(row=11, column=5)
    tk.Button(app, text="fastest sorting algorithm", command= on_button_click_function1, padx=10, pady=5).grid(row=4, column=2)
    tk.Button(app, text="knapsack", command= on_button_click_function2, padx=10, pady=5).grid(row=10, column=2)
    tk.Button(app, text="Subset sum", command= on_button_click_function3, padx=10, pady=5).grid(row=17, column=2)

    # campi per la funzione 3
    tk.Label(app, text="").grid(row=15, column=4)
    tk.Label(app, text="").grid(row=16, column=4)
    tk.Label(app, text="Inserire gli elementi dell'insieme").grid(row=17, column=4)
    tk.Label(app, text="Inserire la soglia target").grid(row=18, column=4)
    entryF3Param2 = tk.Entry()
    entryF3Param2.grid(row=17, column=5)
    entryF3 = tk.Entry()
    entryF3.grid(row=18, column=5)

    # Creazione di una scrollbar
    scrollbar = tk.Scrollbar()
    scrollbar.grid(row=20, column=2, rowspan=20, sticky=tk.N + tk.S)

    # Creazione di un widget Text per visualizzare i risultati
    risultato_text = tk.Text(yscrollcommand=scrollbar.set)
    risultato_text.grid(row=20, column=2, rowspan=20, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W)
    scrollbar.config(command=risultato_text.yview)

    
    app.mainloop()