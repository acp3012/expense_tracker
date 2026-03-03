import { useState, useEffect } from "react";
import { api } from "../api";

export default function ExpenseList({ user, refreshTrigger }) {
  const [expenses, setExpenses] = useState([]);
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState({ amount: "", description: "" });

  const loadExpenses = () => api.getRecentExpenses(user.id).then(setExpenses);

  useEffect(() => {
    loadExpenses();
  }, [user.id, refreshTrigger]);

  const handleEdit = (exp) => {
    setEditId(exp.id);
    setEditForm({ amount: exp.amount, description: exp.description });
  };

  const handleSave = async (id) => {
    const amt = parseFloat(editForm.amount);
    if (amt <= 0) return alert("Amount must be greater than 0");
    await api.updateExpense(id, amt, editForm.description);
    setEditId(null);
    loadExpenses();
  };

  if (expenses.length === 0)
    return <p className="empty-state">No recent entries.</p>;

  return (
    <div className="table-responsive">
      <table className="classic-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Category</th>
            <th>Amount</th>
            <th>Note</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {expenses.map((exp) => (
            <tr key={exp.id}>
              <td>{exp.expense_date}</td>
              <td>{exp.category_name}</td>
              <td>
                {editId === exp.id ? (
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    className="edit-input"
                    value={editForm.amount}
                    onChange={(e) =>
                      setEditForm({ ...editForm, amount: e.target.value })
                    }
                  />
                ) : (
                  `₹${exp.amount.toFixed(2)}`
                )}
              </td>
              <td>
                {editId === exp.id ? (
                  <input
                    type="text"
                    className="edit-input"
                    value={editForm.description}
                    onChange={(e) =>
                      setEditForm({ ...editForm, description: e.target.value })
                    }
                  />
                ) : (
                  exp.description
                )}
              </td>
              <td>
                {editId === exp.id ? (
                  <button
                    className="btn-text save"
                    onClick={() => handleSave(exp.id)}>
                    Save
                  </button>
                ) : (
                  <button
                    className="btn-text"
                    onClick={() => handleEdit(exp)}>
                    Edit
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
