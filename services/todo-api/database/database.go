package database

import (
	"fmt"
	"log"

	"github.com/scottseo.tech/todo-platform/services/todo-api/models"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"gorm.io/plugin/opentelemetry/tracing"
)

type Config struct {
	Host     string
	Port     string
	User     string
	Password string
	DBName   string
	SSLMode  string
}

var DB *gorm.DB

func Connect(config Config) error {
	dsn := fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		config.Host,
		config.Port,
		config.User,
		config.Password,
		config.DBName,
		config.SSLMode,
	)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	// Register OpenTelemetry plugin for database tracing
	if err := db.Use(tracing.NewPlugin()); err != nil {
		return fmt.Errorf("failed to register tracing plugin: %w", err)
	}

	DB = db
	log.Println("Database connection established with OpenTelemetry tracing")

	return nil
}

func Migrate() error {
	if DB == nil {
		return fmt.Errorf("database connection not established")
	}

	err := DB.AutoMigrate(&models.Todo{})
	if err != nil {
		return fmt.Errorf("failed to migrate database: %w", err)
	}

	log.Println("Database migration completed")
	return nil
}
