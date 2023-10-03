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

var val int

func bubbleSort(arr []int) {
	n := len(arr)
	for i := 0; i < n-1; i++ {
		for j := 0; j < n-i-1; j++ {
			if arr[j] > arr[j+1] {
				arr[j], arr[j+1] = arr[j+1], arr[j]
			}
		}
	}
}

func selectionSort(arr []int) {
	n := len(arr)
	for i := 0; i < n-1; i++ {
		minIndex := i
		for j := i + 1; j < n; j++ {
			if arr[j] < arr[minIndex] {
				minIndex = j
			}
		}
		arr[i], arr[minIndex] = arr[minIndex], arr[i]
	}
}

func mergeSort(arr []int) []int {
	n := len(arr)
	if n <= 1 {
		return arr
	}

	mid := n / 2
	left := mergeSort(arr[:mid])
	right := mergeSort(arr[mid:])

	return merge(left, right)
}

func merge(left, right []int) []int {
	result := []int{}
	i, j := 0, 0

	for i < len(left) && j < len(right) {
		if left[i] < right[j] {
			result = append(result, left[i])
			i++
		} else {
			result = append(result, right[j])
			j++
		}
	}

	result = append(result, left[i:]...)
	result = append(result, right[j:]...)

	return result
}

func findFastestSortingAlgorithm(arr []int) (string, time.Duration) {

	bubbleSorted := make([]int, len(arr))
	selectionSorted := make([]int, len(arr))
	mergeSorted := make([]int, len(arr))

	copy(bubbleSorted, arr)
	copy(selectionSorted, arr)
	copy(mergeSorted, arr)

	bubbleStartTime := time.Now()
	bubbleSort(bubbleSorted)
	bubbleTime := time.Since(bubbleStartTime)

	selectionStartTime := time.Now()
	selectionSort(selectionSorted)
	selectionTime := time.Since(selectionStartTime)

	mergeStartTime := time.Now()
	mergeSort(mergeSorted)
	mergeTime := time.Since(mergeStartTime)

	if bubbleTime <= selectionTime && bubbleTime <= mergeTime {
		return "Bubble Sort", bubbleTime
	} else if selectionTime <= bubbleTime && selectionTime <= mergeTime {
		return "Selection Sort", selectionTime
	} else {
		return "Merge Sort", mergeTime
	}
}

func main() { //l'unico parametro che viene passato è la dimensione dell'array

	if os.Getenv("AWS_LAMBDA_FUNCTION_NAME") != "" { // Check if running on lambda or locally
		lambda.Start(handler)
	} else {
		fmt.Println("Running locally")
	}
	client := redis.NewClient(&redis.Options{
		Addr: "172.17.0.2:6379",
		DB:   0, // use default DB
	})

	defer client.Close()
	val2, err := client.HGet("fastestSortingAlgorithm", "param1").Result()
	fmt.Println("valore passato: ", val2)
	val, _ = strconv.Atoi(val2)
	if err != nil {
		panic(err)
	}

	rand.Seed(time.Now().UnixNano())
	arr := make([]int, val)
	for i := range arr {
		arr[i] = rand.Intn(100000)
	}

	fastestAlgorithm, duration := findFastestSortingAlgorithm(arr)
	fmt.Printf("The fastest sorting algorithm is %s with time: %v\n", fastestAlgorithm, duration)
	messaggio := "The fastest sorting algorithm with vector size " + strconv.Itoa(val) + " is " + fastestAlgorithm + " with time: " + duration.String()

	err2 := client.Publish("canale1", messaggio).Err()
	if err2 != nil {
		panic(err2)
	}
}

func handler(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	rand.Seed(time.Now().UnixNano())
	arr := make([]int, val)
	for i := range arr {
		arr[i] = rand.Intn(val)
	}

	fastestAlgorithm, duration := findFastestSortingAlgorithm(arr)
	responseBody := fmt.Sprintf("The fastest sorting algorithm is %s with time: %v\n", fastestAlgorithm, duration)

	return events.APIGatewayProxyResponse{Body: responseBody, StatusCode: 200}, nil
}
