package main

import (
	"fmt"
	"math/rand"
	"time"
)

func main() {
	// Inizializziamo il generatore di numeri casuali utilizzando un seme basato sull'ora corrente.
	rand.Seed(time.Now().UnixNano())

	for {
		// Generiamo un numero casuale intero tra 1 e 100.
		randomNumber := rand.Intn(100) + 1

		// Stampiamo il numero casuale.
		fmt.Println(randomNumber)

		// Pausa di 1 secondo per evitare un loop troppo veloce.
		time.Sleep(time.Second)
	}
}
