package main

import (
	"fmt"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
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
	set := []int{60, 100, 120}
	weights := []int{10, 20, 30}
	capacity := 50
	fmt.Println("Running on AWS Lambda")
	// Controlla se il codice sta eseguendo su AWS Lambda o in locale

	maxValue := knapsackRecursive(set, weights, capacity, len(set))
	responseBody := fmt.Sprintf("Maximum value: %d\n", maxValue)

	return events.APIGatewayProxyResponse{Body: responseBody, StatusCode: 200}, nil
}

func main() {
	// Controlla se il codice sta eseguendo su AWS Lambda o in locale
	if os.Getenv("AWS_LAMBDA_FUNCTION_NAME") != "" {
		lambda.Start(handler)
	} else {
		fmt.Println("Running locally")

		set := []int{60, 100, 120}
		weights := []int{10, 20, 30}
		capacity := 50

		maxValue := knapsackRecursive(set, weights, capacity, len(set))
		fmt.Printf("Maximum value: %d\n", maxValue)
	}
}
