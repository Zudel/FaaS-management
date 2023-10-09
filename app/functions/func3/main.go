package main

import (
	"context"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/go-redis/redis/v7"
)

var val1Int int
var val2Int int
var messaggio string

func createVector(n int) []int {
	rand.Seed(time.Now().UnixNano())
	arr := make([]int, n)
	for i := range arr {
		arr[i] = rand.Intn(100000)
	}
	return arr
}

func subsetSumNaive(set []int, n, target, index int) bool {
	if target == 0 {
		return true
	}
	if index == n {
		return false
	}

	// Includi l'elemento corrente nel sottoinsieme e sottrai il suo valore dal target
	if set[index] <= target {
		if subsetSumNaive(set, n, target-set[index], index+1) {
			return true
		}
	}

	// Non includere l'elemento corrente nel sottoinsieme
	return subsetSumNaive(set, n, target, index+1)
}

type MyEvent struct {
	Name   string `json:""`
	Param1 string `json:"param1"`
	Param2 string `json:"param2"`
}

func handler(ctx context.Context, event MyEvent) (events.APIGatewayProxyResponse, error) {
	param1 := event.Param1
	param2 := event.Param2
	// Puoi ora utilizzare "param1" e "param2" nella tua logica di elaborazione
	fmt.Println("Param1:", param1)
	fmt.Println("Param2:", param2)
	val1Int, _ := strconv.Atoi(param1) // numero di elementi
	val2Int, _ := strconv.Atoi(param2) // target

	set := createVector(val1Int)
	target := val2Int

	resultCh := make(chan bool)

	go func() {
		result := subsetSumNaive(set, val1Int, target, 0)
		resultCh <- result
	}()

	select {
	case result := <-resultCh:
		if result {
			responseBody := fmt.Sprintf("Subset with target %d exists with vector size %d", target, val1Int)
			return events.APIGatewayProxyResponse{Body: responseBody, StatusCode: 200}, nil
		} else {
			responseBody := fmt.Sprintf("No subset with target %d exists with vector size %d", target, val1Int)
			return events.APIGatewayProxyResponse{Body: responseBody, StatusCode: 200}, nil
		}
	case <-ctx.Done():
		return events.APIGatewayProxyResponse{Body: "Timeout reached", StatusCode: 500}, nil
	}
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
		val1, err := client.HGet("subset_sum", "param1S").Result()
		val1Int, _ := strconv.Atoi(val1) //dimensione vettore
		vector := createVector(val1Int)  // numero di elementi
		val2, err2 := client.HGet("subset_sum", "param2S").Result()
		val2Int, _ := strconv.Atoi(val2) // target

		fmt.Println("valore passato: ", val1Int)
		fmt.Println("valore passato: ", val2Int)

		if err != nil || err2 != nil {
			panic(err)
		}

		result := subsetSumNaive(vector, val1Int, val2Int, 0)

		if result {
			fmt.Printf("Subset with sum exists")
			messaggio = " subset with sum  EXISTS with vector size " + strconv.Itoa(val1Int) + " and target " + strconv.Itoa(val2Int)
		} else {
			fmt.Printf("No subset with sum")
			messaggio = "No subset with sum with vector size " + strconv.Itoa(val1Int) + " and target " + strconv.Itoa(val2Int)
		}

		err3 := client.Publish("canale3", messaggio).Err()
		if err3 != nil {
			panic(err3)
		}
	}
}
