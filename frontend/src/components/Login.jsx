import { useState } from "react";
import { api } from "../api";

export default function Login({ onLoginSuccess }) {
  const [name, setName] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const user = await api.login(name, pin);
      onLoginSuccess(user);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="card">
      <h2>Family Expense Tracker</h2>
      <form onSubmit={handleLogin}>
        <div>
          <label>Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="e.g. Sasirekha"
          />
        </div>
        <div>
          <label>4-Digit PIN</label>
          <input
            type="password"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            required
            maxLength="4"
            pattern="\d{4}"
          />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit">Login</button>
      </form>
    </div>
  );
}
