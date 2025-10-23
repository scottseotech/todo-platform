package main

import (
	_ "embed"
	"log"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/scottseo.tech/todo-platform/services/todo-api/config"
	"github.com/scottseo.tech/todo-platform/services/todo-api/database"
	"github.com/scottseo.tech/todo-platform/services/todo-api/handlers"
)

//go:embed openapi.json
var openapiSpec []byte

func main() {
	// during local development, load .env file
	err := godotenv.Load()
	if err != nil {
		log.Printf("Continuing without .env file")
	}

	// Load configuration from environment variables provided in k8s deployment
	cfg := config.Load()

	// Connect to database
	dbConfig := database.Config{
		Host:     cfg.Database.Host,
		Port:     cfg.Database.Port,
		User:     cfg.Database.User,
		Password: cfg.Database.Password,
		DBName:   cfg.Database.DBName,
		SSLMode:  cfg.Database.SSLMode,
	}

	if err := database.Connect(dbConfig); err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	// Run migrations
	if err := database.Migrate(); err != nil {
		log.Fatalf("Failed to migrate database: %v", err)
	}

	// Initialize Gin router
	router := gin.Default()

	router.Use(cors.New(cors.Config{
		AllowOrigins: []string{"https://editor.swagger.io"},
		AllowMethods: []string{"GET"},
		AllowHeaders: []string{"Content-Type"},
	}))

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy"})
	})

	// OpenAPI specification endpoint
	router.GET("/openapi.json", func(c *gin.Context) {
		c.Data(200, "application/json", openapiSpec)
	})

	// API v1 routes
	v1 := router.Group("/api/v1")

	todos := v1.Group("/todos")

	todos.GET("", handlers.GetTodos)
	todos.GET("/:id", handlers.GetTodo)
	todos.POST("", handlers.CreateTodo)
	todos.PUT("/:id", handlers.UpdateTodo)
	todos.DELETE("/:id", handlers.DeleteTodo)

	// Start server
	serverAddr := ":" + cfg.Server.Port
	log.Printf("Starting server on %s", serverAddr)
	if err := router.Run(serverAddr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
