package models

import (
	"time"
)

type Todo struct {
	ID        uint       `json:"id" gorm:"primaryKey;autoIncrement"`
	Title     string     `json:"title" gorm:"not null" binding:"required"`
	DueDate   *time.Time `json:"due_date,omitempty" gorm:"default:null"`
	CreatedAt time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

type CreateTodoRequest struct {
	Title   string     `json:"title" binding:"required"`
	DueDate *time.Time `json:"due_date,omitempty"`
}

type UpdateTodoRequest struct {
	Title   *string    `json:"title,omitempty"`
	DueDate *time.Time `json:"due_date,omitempty"`
}
