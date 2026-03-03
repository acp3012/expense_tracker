// const API_BASE_URL = `http://${window.location.hostname}:8090/api`;
const API_BASE_URL = `/api`;

export const api = {
  login: async (name, pin) => {
    const res = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, pin }),
    });

    // If the server returns an error, grab the message and throw it!
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || "Server failed to save the expense.");
    }
    return res.json();
  },
  getUsers: async () => {
    const res = await fetch(`${API_BASE_URL}/users`);
    return res.json();
  },
  getCategories: async () => {
    const res = await fetch(`${API_BASE_URL}/categories`);
    return res.json();
  },
  addExpense: async (expense) => {
    const res = await fetch(`${API_BASE_URL}/expenses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(expense),
    });
    if (!res.ok) throw new Error("Validation failed");
    return res.json();
  },
  updateExpense: async (id, amount, description) => {
    const res = await fetch(`${API_BASE_URL}/expenses/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, description }),
    });
    if (!res.ok) throw new Error("Validation failed");
    return res.json();
  },
  getRecentExpenses: async (userId) => {
    const res = await fetch(
      `${API_BASE_URL}/expenses/recent?user_id=${userId}`,
    );
    return res.json();
  },
  getReport: async (startDate, endDate, userId = 0) => {
    const res = await fetch(
      `${API_BASE_URL}/reports?start_date=${startDate}&end_date=${endDate}&user_id=${userId}`,
    );
    return res.json();
  },
};
