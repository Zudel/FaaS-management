package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/go-redis/redis/v7"
)

func knapsackRecursive(values []int, weights []int, capacity int, n int) int {
	if n == 0 || capacity == 0 {
		return 0
	}

	if weights[n-1] > capacity {
		return knapsackRecursive(values, weights, capacity, n-1)
	}

	return max(values[n-1]+knapsackRecursive(values, weights, capacity-weights[n-1], n-1),
		knapsackRecursive(values, weights, capacity, n-1))
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func handler(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	param1 := request.QueryStringParameters["param1"]
	param2 := request.QueryStringParameters["param2"]
	param3 := request.QueryStringParameters["param3"]

	set := convertToIntArray(param1)
	weights := convertToIntArray(param2)
	capacity, _ := strconv.Atoi(param3)
	fmt.Println("Running on AWS Lambda")
	// Controlla se il codice sta eseguendo su AWS Lambda o in locale

	maxValue := knapsackRecursive(set, weights, capacity, len(set))
	responseBody := fmt.Sprintf("Maximum value: %d\n", maxValue)

	return events.APIGatewayProxyResponse{Body: responseBody, StatusCode: 200}, nil
}

func convertToIntArray(numbersStr string) []int {
	// Dividi la stringa in una slice di stringhe utilizzando uno spazio come delimitatore
	numberStrSlice := strings.Split(numbersStr, " ")

	// Dichiarazione di un array di interi
	var intArray []int

	// Itera attraverso la slice di stringhe e converte ciascuna in un intero
	for _, str := range numberStrSlice {
		num, err := strconv.Atoi(str)
		if err != nil {
			fmt.Printf("Errore durante la conversione di %s in int: %v\n", str, err)
			os.Exit(1)
		}
		intArray = append(intArray, num)
	}

	// Stampare l'array di interi
	fmt.Println(intArray)
	return intArray
}

func main() {
	// Controlla se il codice sta eseguendo su AWS Lambda o in locale
	if os.Getenv("AWS_LAMBDA_FUNCTION_NAME") != "" {
		lambda.Start(handler)
	} else {
		fmt.Println("Running locally")
		client := redis.NewClient(&redis.Options{
			Addr: "172.17.0.2:6379",
			DB:   0, // use default DB
		})

		defer client.Close()
		val1, err := client.HGet("fastest_sorting_algorithm", "param1").Result()
		val2, err := client.HGet("fastest_sorting_algorithm", "param2").Result()
		val3, err := client.HGet("fastest_sorting_algorithm", "param3").Result()
		fmt.Println("valore passato: ", val1)
		fmt.Println("valore passato: ", val2)
		fmt.Println("valore passato: ", val3)
		set := convertToIntArray(val1) //controllare con la gui, so sballati
		weights := convertToIntArray(val2)
		capacity, _ := strconv.Atoi(val3)

		if err != nil {
			panic(err)
		}

		maxValue := knapsackRecursive(set, weights, capacity, len(set))
		fmt.Printf("Maximum value: %d\n", maxValue)
	}
}
