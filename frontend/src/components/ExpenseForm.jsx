import { useState, useEffect } from "react";
import { api } from "../api";

export default function ExpenseForm({ user, onExpenseAdded }) {
  const [categories, setCategories] = useState([]);
  const today = new Date().toISOString().split("T")[0];
  const [formData, setFormData] = useState({
    categoryId: "",
    amount: "",
    expenseDate: today,
    description: "",
  });
  const [error, setError] = useState("");

  useEffect(() => {
    api.getCategories().then(setCategories);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const amt = parseFloat(formData.amount);
    if (amt <= 0) {
      setError("Amount must be greater than 0");
      return;
    }
    try {
      await api.addExpense({
        user_id: user.id,
        category_id: parseInt(formData.categoryId),
        amount: amt,
        expense_date: formData.expenseDate,
        description: formData.description,
      });

      setFormData({ ...formData, amount: "", description: "", categoryId: "" });
      onExpenseAdded();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <p className="error">{error}</p>}
      <div>
        <label>Date</label>
        <input
          type="date"
          value={formData.expenseDate}
          onChange={(e) =>
            setFormData({ ...formData, expenseDate: e.target.value })
          }
          required
        />
      </div>
      <div>
        <label>Category</label>
        <select
          value={formData.categoryId}
          onChange={(e) =>
            setFormData({ ...formData, categoryId: e.target.value })
          }
          required>
          <option
            value=""
            disabled>
            Select Category
          </option>
          {categories.map((c) => (
            <option
              key={c.id}
              value={c.id}>
              {c.category_name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label>Amount (₹)</label>
        {/* Min 0.01 added here */}
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={formData.amount}
          onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
          required
        />
      </div>
      <div>
        <label>Description (Optional)</label>
        <input
          type="text"
          value={formData.description}
          onChange={(e) =>
            setFormData({ ...formData, description: e.target.value })
          }
        />
      </div>
      <button
        type="submit"
        className="btn-primary">
        Post Entry
      </button>
    </form>
  );
}
