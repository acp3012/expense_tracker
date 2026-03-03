import { useState, useEffect } from "react";
import { api } from "../api";

export default function Report({ user }) {
  const [users, setUsers] = useState([]);
  const [reportData, setReportData] = useState([]);

  // Default to first day of current month to today
  const date = new Date();
  const firstDay = new Date(date.getFullYear(), date.getMonth(), 1)
    .toISOString()
    .split("T")[0];
  const today = date.toISOString().split("T")[0];

  const [filters, setFilters] = useState({
    startDate: firstDay,
    endDate: today,
    userId: user.is_admin ? 0 : user.id,
  });

  useEffect(() => {
    if (user.is_admin) api.getUsers().then(setUsers);
  }, [user.is_admin]);

  const generateReport = async (e) => {
    e?.preventDefault();
    const data = await api.getReport(
      filters.startDate,
      filters.endDate,
      filters.userId,
    );
    setReportData(data);
  };

  // Auto-load on mount
  useEffect(() => {
    generateReport();
  }, []);

  const totalSum = reportData.reduce((sum, row) => sum + row.total_amount, 0);

  return (
    <div className="card classic-border">
      <h3 className="section-title">Expense Summary Report</h3>
      <form
        onSubmit={generateReport}
        className="report-filters">
        <div>
          <label>Start Date</label>
          <input
            type="date"
            value={filters.startDate}
            onChange={(e) =>
              setFilters({ ...filters, startDate: e.target.value })
            }
            required
          />
        </div>
        <div>
          <label>End Date</label>
          <input
            type="date"
            value={filters.endDate}
            onChange={(e) =>
              setFilters({ ...filters, endDate: e.target.value })
            }
            required
          />
        </div>
        {user.is_admin && (
          <div>
            <label>User (Admin View)</label>
            <select
              value={filters.userId}
              onChange={(e) =>
                setFilters({ ...filters, userId: e.target.value })
              }>
              <option value={0}>-- All Users Combined --</option>
              {users.map((u) => (
                <option
                  key={u.id}
                  value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="filter-btn-container">
          <button
            type="submit"
            className="btn-primary">
            Generate
          </button>
        </div>
      </form>

      <table className="classic-table mt-20">
        <thead>
          <tr>
            <th>Category</th>
            <th className="text-right">Total Amount</th>
          </tr>
        </thead>
        <tbody>
          {reportData.length === 0 ? (
            <tr>
              <td colSpan="2">No data for this period.</td>
            </tr>
          ) : null}
          {reportData.map((row, idx) => (
            <tr key={idx}>
              <td>{row.category_name}</td>
              <td className="text-right">₹{row.total_amount.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="grand-total">
            <td>Grand Total</td>
            <td className="text-right">₹{totalSum.toFixed(2)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
