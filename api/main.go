package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv" // 1. Add this import!// 1. Add this import!
	_ "github.com/lib/pq"
)

type User struct {
	ID      int    `json:"id"`
	Name    string `json:"name"`
	Pin     string `json:"pin"`
	IsAdmin bool   `json:"is_admin"`
}

type Category struct {
	ID   int    `json:"id"`
	Name string `json:"category_name"`
}

type Expense struct {
	ID           int     `json:"id"`
	UserID       int     `json:"user_id"`
	CategoryID   int     `json:"category_id"`
	CategoryName string  `json:"category_name,omitempty"`
	Amount       float64 `json:"amount"`
	ExpenseDate  string  `json:"expense_date"`
	Description  string  `json:"description"`
}

type ReportSummary struct {
	CategoryName string  `json:"category_name"`
	TotalAmount  float64 `json:"total_amount"`
}

var db *sql.DB

func main() {
	var err error
	// This tells Go to look for a .env file in the current folder
	err = godotenv.Load()
	if err != nil {
		// We don't use log.Fatal here, because in production, systemd handles the variables!
		log.Println("INFO: No .env file found locally, relying on OS environment variables.")
	}
	// Load secrets from the operating system
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	// fmt.Printf("INFO: Loaded DB_USER=%s, DB_NAME=%s\n", dbUser, dbName)
	if dbPassword == "" {
		log.Fatal("FATAL: Database credentials not found in environment!")
	}

	connStr := fmt.Sprintf("user=%s password=%s dbname=%s sslmode=disable", dbUser, dbPassword, dbName)
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal("FATAL: Cannot connect to DB:", err)
	}
	defer db.Close()

	r := gin.Default()

	// 1. LOGIN
	r.POST("/api/login", func(c *gin.Context) {
		var req User
		if err := c.ShouldBindJSON(&req); err != nil {
			log.Printf("ERROR parsing login payload: %v\n", err)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
			return
		}

		var user User
		err := db.QueryRow("SELECT id, name, is_admin FROM users WHERE name = $1 AND pin = $2", req.Name, req.Pin).Scan(&user.ID, &user.Name, &user.IsAdmin)
		if err != nil {
			log.Printf("WARN: Failed login attempt for user '%s': %v\n", req.Name, err)
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid Name or PIN"})
			return
		}
		
		log.Printf("INFO: User '%s' logged in successfully.\n", user.Name)
		c.JSON(http.StatusOK, user)
	})

	// 2. GET USERS
	r.GET("/api/users", func(c *gin.Context) {
		rows, err := db.Query("SELECT id, name FROM users ORDER BY name")
		if err != nil {
			log.Printf("ERROR fetching users: %v\n", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
			return
		}
		defer rows.Close()

		var users []User
		for rows.Next() {
			var u User
			if err := rows.Scan(&u.ID, &u.Name); err != nil {
				log.Printf("ERROR scanning user row: %v\n", err)
				continue
			}
			users = append(users, u)
		}
		c.JSON(http.StatusOK, users)
	})

	// 3. GET CATEGORIES
	r.GET("/api/categories", func(c *gin.Context) {
		rows, err := db.Query("SELECT id, category_name FROM categories ORDER BY category_name")
		if err != nil {
			log.Printf("ERROR fetching categories: %v\n", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
			return
		}
		defer rows.Close()

		var categories []Category
		for rows.Next() {
			var cat Category
			if err := rows.Scan(&cat.ID, &cat.Name); err != nil {
				log.Printf("ERROR scanning category row: %v\n", err)
				continue
			}
			categories = append(categories, cat)
		}
		c.JSON(http.StatusOK, categories)
	})

	// 4. POST EXPENSE
	r.POST("/api/expenses", func(c *gin.Context) {
		var exp Expense
		if err := c.ShouldBindJSON(&exp); err != nil {
			log.Printf("ERROR: Invalid expense payload: %v\n", err)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid input format"})
			return
		}

		err := db.QueryRow("INSERT INTO expenses (user_id, category_id, amount, expense_date, description) VALUES ($1, $2, $3, $4, $5) RETURNING id",
			exp.UserID, exp.CategoryID, exp.Amount, exp.ExpenseDate, exp.Description).Scan(&exp.ID)

		if err != nil {
			log.Printf("ERROR saving expense for user %d: %v\n", exp.UserID, err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save to database"})
			return
		}

		log.Printf("SUCCESS: Expense %d (₹%.2f) added for user %d\n", exp.ID, exp.Amount, exp.UserID)
		c.JSON(http.StatusCreated, exp)
	})

	// 5. UPDATE EXPENSE
	r.PUT("/api/expenses/:id", func(c *gin.Context) {
		id := c.Param("id")
		var exp Expense
		if err := c.ShouldBindJSON(&exp); err != nil {
			log.Printf("ERROR parsing update payload for expense %s: %v\n", id, err)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid input format"})
			return
		}

		_, err := db.Exec("UPDATE expenses SET amount = $1, description = $2 WHERE id = $3", exp.Amount, exp.Description, id)
		if err != nil {
			log.Printf("ERROR updating expense %s: %v\n", id, err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update expense"})
			return
		}
		
		log.Printf("SUCCESS: Expense %s updated.\n", id)
		c.JSON(http.StatusOK, gin.H{"status": "updated"})
	})

	// 6. GET RECENT EXPENSES
	r.GET("/api/expenses/recent", func(c *gin.Context) {
		userID := c.Query("user_id")
		rows, err := db.Query(`SELECT e.id, c.category_name, e.amount, e.expense_date, e.description 
			FROM expenses e JOIN categories c ON e.category_id = c.id WHERE e.user_id = $1 ORDER BY e.expense_date DESC, e.id DESC LIMIT 10`, userID)

		if err != nil {
			log.Printf("ERROR fetching recent expenses for user %s: %v\n", userID, err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
			return
		}
		defer rows.Close()

		expenses := make([]Expense, 0)
		for rows.Next() {
			var exp Expense
			if err := rows.Scan(&exp.ID, &exp.CategoryName, &exp.Amount, &exp.ExpenseDate, &exp.Description); err != nil {
				log.Printf("ERROR scanning expense row: %v\n", err)
				continue
			}
			// Safe substring for date to prevent bounds out of range panic
			if len(exp.ExpenseDate) >= 10 {
				exp.ExpenseDate = exp.ExpenseDate[:10]
			}
			expenses = append(expenses, exp)
		}
		c.JSON(http.StatusOK, expenses)
	})

	// 7. GET REPORTS
	r.GET("/api/reports", func(c *gin.Context) {
		startDate, endDate, userID := c.Query("start_date"), c.Query("end_date"), c.Query("user_id")
		
		query := `SELECT c.category_name, SUM(e.amount) FROM expenses e JOIN categories c ON e.category_id = c.id WHERE e.expense_date >= $1 AND e.expense_date <= $2`
		args := []interface{}{startDate, endDate}

		if userID != "0" && userID != "" {
			query += " AND e.user_id = $3"
			args = append(args, userID)
		}
		query += " GROUP BY c.category_name ORDER BY SUM(e.amount) DESC"

		rows, err := db.Query(query, args...)

		if err != nil {
			log.Printf("ERROR generating report: %v\n", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
			return
		}
		defer rows.Close()

		summaries := make([]ReportSummary, 0)
		for rows.Next() {
			var s ReportSummary
			if err := rows.Scan(&s.CategoryName, &s.TotalAmount); err != nil {
				log.Printf("ERROR scanning report row: %v\n", err)
				continue
			}
			summaries = append(summaries, s)
		}
		c.JSON(http.StatusOK, summaries)
	})

	log.Println("Starting Expense API Server on 0.0.0.0:8090...")
	r.Run("0.0.0.0:8090")
}