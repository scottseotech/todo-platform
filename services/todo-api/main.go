package main

import (
	"context"
	_ "embed"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/scottseo.tech/todo-platform/services/todo-api/config"
	"github.com/scottseo.tech/todo-platform/services/todo-api/database"
	"github.com/scottseo.tech/todo-platform/services/todo-api/handlers"
	"github.com/scottseo.tech/todo-platform/services/todo-api/telemetry"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
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

	// Initialize OpenTelemetry
	telemetryConfig := telemetry.LoadConfig("todo-api", "1.0.0")
	shutdown, err := telemetry.InitTracer(telemetryConfig)
	if err != nil {
		log.Fatalf("Failed to initialize telemetry: %v", err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := shutdown(ctx); err != nil {
			log.Printf("Error shutting down telemetry: %v", err)
		}
	}()

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

	// Add OpenTelemetry middleware
	router.Use(otelgin.Middleware("todo-api"))

	router.Use(cors.New(cors.Config{
		AllowOrigins: []string{"https://editor.swagger.io"},
		AllowMethods: []string{"GET"},
		AllowHeaders: []string{"Content-Type"},
	}))

	router.Use(cors.New(cors.Config{
		AllowOrigins: []string{"http://localhost:8000"},
		AllowMethods: []string{"GET"},
		AllowHeaders: []string{"Content-Type"},
	}))

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy"})
	})

	// Prometheus metrics endpoint
	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

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

	// Start server with graceful shutdown
	serverAddr := ":" + cfg.Server.Port
	log.Printf("Starting server on %s", serverAddr)

	// Setup signal handling for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		if err := router.Run(serverAddr); err != nil {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	<-quit
	log.Println("Shutting down server...")
}
