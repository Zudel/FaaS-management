package main

import (
	"fmt"
	"time"
)

func waitTenSeconds() {
	fmt.Println("Inizio attesa di 10 secondi...")
	time.Sleep(15 * time.Second)
	fmt.Println("Attesa completata!")
}

func countOccurrences(input string) []int {
	occurrences := make([]int, 26) // Creazione di un array di interi per le 26 lettere dell'alfabeto inglese

	for _, char := range input {
		if char >= 'a' && char <= 'z' {
			occurrences[char-'a']++ // Incremento l'occorrenza corrispondente all'indice della lettera nell'array
		} else if char >= 'A' && char <= 'Z' {
			occurrences[char-'A']++ // Incremento l'occorrenza corrispondente all'indice della lettera nell'array
		}
	}

	return occurrences
}

func main() {
	var input string
	//the input was inserted by the user in the terminal
	fmt.Println("Insert a string:")
	fmt.Scanln(&input)
	input = "Hello, World!"
	fmt.Println(countOccurrences(input))
	waitTenSeconds()

}
