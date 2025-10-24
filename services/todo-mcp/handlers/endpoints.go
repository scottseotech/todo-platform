package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func Tools(c *gin.Context) {
	tools := []gin.H{
		{
			"id":          "hello",
			"name":        "hello",
			"description": "A simple hello world tool that greets you and says hello back",
			"inputSchema": gin.H{
				"type": "object",
				"properties": gin.H{
					"name": gin.H{
						"type":        "string",
						"description": "The name to greet",
					},
				},
				"required": []string{"name"},
			},
		},
	}

	c.JSON(http.StatusOK, gin.H{
		"tools": tools,
	})
}
