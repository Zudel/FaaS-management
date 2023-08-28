package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

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

func handler(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	set := []int{35, 34, 54, 11, 12, 13, 14, 20, 2, 91, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 55, 878, 54}
	target := 10000

	// Crea un contesto con timeout di 5 secondi
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	resultCh := make(chan bool)

	go func() {
		result := subsetSumNaive(set, len(set), target, 0)
		resultCh <- result
	}()

	select {
	case result := <-resultCh:
		if result {
			return events.APIGatewayProxyResponse{Body: "Subset with sum exists", StatusCode: 200}, nil
		} else {
			return events.APIGatewayProxyResponse{Body: "No subset with sum", StatusCode: 200}, nil
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

		// Esegui il codice localmente
		response, err := handler(events.APIGatewayProxyRequest{})
		if err != nil {
			fmt.Println("Error:", err)
			return
		}
		fmt.Println("Response:", response.Body)
	}
}
