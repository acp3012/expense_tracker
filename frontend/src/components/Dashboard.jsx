import { useState } from "react";
import ExpenseForm from "./ExpenseForm";
import ExpenseList from "./ExpenseList";
import Report from "./Report";

export default function Dashboard({ user, onLogout }) {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [activeTab, setActiveTab] = useState("tracker"); // 'tracker' or 'report'

  return (
    <div>
      <header className="dashboard-header classic-border">
        <h2>Ledger: {user.name}</h2>
        <nav className="nav-menu">
          <button
            className={activeTab === "tracker" ? "active" : ""}
            onClick={() => setActiveTab("tracker")}>
            Entry
          </button>
          <button
            className={activeTab === "report" ? "active" : ""}
            onClick={() => setActiveTab("report")}>
            Reports
          </button>
          <button
            onClick={onLogout}
            className="btn-secondary">
            Logout
          </button>
        </nav>
      </header>

      {activeTab === "tracker" ? (
        <div className="dashboard-grid">
          <div className="card classic-border">
            <h3 className="section-title">Record Expense</h3>
            <ExpenseForm
              user={user}
              onExpenseAdded={() => setRefreshTrigger((prev) => prev + 1)}
            />
          </div>
          <div className="card classic-border">
            <h3 className="section-title">Recent Entries</h3>
            <ExpenseList
              user={user}
              refreshTrigger={refreshTrigger}
            />
          </div>
        </div>
      ) : (
        <Report user={user} />
      )}
    </div>
  );
}
