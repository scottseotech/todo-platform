package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	ServerPort string
	TodoAPIURL string
}

func Load() Config {
	// Load .env file for local development
	err := godotenv.Load()
	if err != nil {
		log.Printf("Continuing without .env file")
	}

	port := os.Getenv("SERVER_PORT")
	if port == "" {
		port = "8081"
	}

	todoAPIURL := os.Getenv("TODO_API_URL")
	if todoAPIURL == "" {
		todoAPIURL = "http://localhost:8081"
	}

	return Config{
		ServerPort: port,
		TodoAPIURL: todoAPIURL,
	}
}
