import { useState } from "react";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [user, setUser] = useState(null);

  return (
    <div className="app-container">
      {!user ? (
        <Login onLoginSuccess={setUser} />
      ) : (
        <Dashboard
          user={user}
          onLogout={() => setUser(null)}
        />
      )}
    </div>
  );
}
