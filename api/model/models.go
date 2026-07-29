package model

import "time"

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

// Represents the data sent TO React
type PendingNotification struct {
	ID          int64     `json:"id"`
	TxnDate     time.Time `json:"txnDate"`
	Amount      float64   `json:"amount"`
	Description *string    `json:"description"` // use pointer to handle NULL values
	UPIRef      *string    `json:"upiRef"`
	Merchant    *string   `json:"merchant"` // Added Merchant
}

// Represents the payload coming FROM React
type ProcessRequest struct {
	ID          int64  `json:"id"`
	CategoryID  int    `json:"categoryId"`
	Description *string `json:"description"`  // Optional description provided by the user
	UserID      int    `json:"userId"`
}
