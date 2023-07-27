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
func power(x int, y int) int {
	result := 1
	for i := 0; i < y; i++ {
		result *= x
	}
	return result
}

func main() {
	var x, y int
	var input string
	x = 2
	y = 3
	input = "Hello, World!"
	result := power(x, y)
	println(result)
	power(x, y)
	fmt.Println(countOccurrences(input))
	waitTenSeconds()

}
