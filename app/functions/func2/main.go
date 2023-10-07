package main

import (
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/go-redis/redis/v7"
)

func createVector(n int) []int {
	rand.Seed(time.Now().UnixNano())
	arr := make([]int, n)
	for i := range arr {
		arr[i] = rand.Intn(100000)
	}
	return arr
}

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
		val1, _ := client.HGet("knapsack", "param1K").Result()       //cap
		numObjects, _ := client.HGet("knapsack", "param2K").Result() //objects of knapsack
		fmt.Println("valore passato: ", val1)
		fmt.Println("valore passato: ", numObjects)
		val1Int, _ := strconv.Atoi(val1)
		numObjectsInt, _ := strconv.Atoi(numObjects)
		set := createVector(numObjectsInt)
		weights := createVector(numObjectsInt)
		capacity := val1Int

		maxValue := knapsackRecursive(set, weights, capacity, numObjectsInt)
		fmt.Sprintf("Maximum value: %d\n with capacity: %d and number of objects %d", maxValue, capacity, numObjectsInt)
		messaggio := "Maximum value: " + strconv.Itoa(maxValue) + " with capacity: " + strconv.Itoa(capacity) + " and number of objects " + strconv.Itoa(numObjectsInt)

		err2 := client.Publish("canale2", messaggio).Err()
		if err2 != nil {
			panic(err2)
		}
	}
}

func handler(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	param1 := request.QueryStringParameters["param1"] //cap
	param2 := request.QueryStringParameters["param2"] //objects of knapsack
	fmt.Println("valore passato: ", param1)
	fmt.Println("valore passato: ", param2)
	param1Int, _ := strconv.Atoi(param1)
	numObjects, _ := strconv.Atoi(param2)
	set := createVector(numObjects)
	weights := createVector(numObjects)
	capacity := param1Int
	fmt.Println("Running on AWS Lambda")
	// Controlla se il codice sta eseguendo su AWS Lambda o in locale

	maxValue := knapsackRecursive(set, weights, capacity, numObjects)
	responseBody := fmt.Sprintf("Maximum value: %d\n with capacity: %s and number of objects %s", maxValue, param1, param2)

	return events.APIGatewayProxyResponse{Body: responseBody, StatusCode: 200}, nil
}
