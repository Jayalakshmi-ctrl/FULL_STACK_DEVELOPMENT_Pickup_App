import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AdminRedemption, listAdminRedemptions, scheduleRedemptionDelivery } from "./api";

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function AdminRedemptionsPage() {
  const [rows, setRows] = useState<AdminRedemption[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      setRows(await listAdminRedemptions());
    } catch (e: any) {
      setError(e?.message ?? "Failed to load redemptions");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onSentToCustomer(r: AdminRedemption) {
    const min = todayISO();
    const d = window.prompt("Delivery date (YYYY-MM-DD):", r.delivery_date ?? min);
    if (!d) return;
    if (d < min) {
      setError("Delivery date cannot be before today.");
      return;
    }
    setBusyId(r.id);
    setError(null);
    setMsg(null);
    try {
      const out = await scheduleRedemptionDelivery(r.id, d);
      setMsg(`Marked as “Sent to customer” for ${out.customer_email}. Delivery date: ${out.delivery_date}.`);
      await load();
    } catch (e: any) {
      setError(e?.message ?? "Schedule failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div style={{ fontWeight: 900, fontSize: 16 }}>Admin: redemptions</div>
        <Link className="ghostLink" to="/">
          Back
        </Link>
      </div>
      <div className="muted" style={{ marginBottom: 12 }}>
        See which customer redeemed what and mark items as sent with a delivery date (cannot be before today).
      </div>

      {error ? <div className="notice error" style={{ marginBottom: 12 }}>{error}</div> : null}
      {msg ? <div className="notice" style={{ marginBottom: 12 }}>{msg}</div> : null}

      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Customer</th>
            <th>Item</th>
            <th>Points</th>
            <th>Status</th>
            <th>Requested at</th>
            <th>Delivery date</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const isSent = r.status === "fulfilled" && !!r.delivery_date;
            return (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.customer_email}</td>
              <td>
                <div style={{ fontWeight: 800 }}>{r.reward_name}</div>
                <div className="muted" style={{ fontSize: 12 }}>Type: {r.reward_type.replace("_", " ")}</div>
              </td>
              <td style={{ fontWeight: 800 }}>{r.points_spent}</td>
              <td>
                <span className={`pill ${isSent ? "ok" : "pending"}`}>
                  {isSent ? "Sent to customer" : "Requested"}
                </span>
              </td>
              <td className="muted">{new Date(r.created_at).toLocaleString()}</td>
              <td style={{ fontWeight: 800 }}>{r.delivery_date ?? "—"}</td>
              <td style={{ width: 160 }}>
                {isSent ? (
                  <span className="muted" style={{ fontWeight: 700 }}>
                    Sent
                  </span>
                ) : (
                  <button className="secondary" disabled={busyId !== null} onClick={() => onSentToCustomer(r)}>
                    {busyId === r.id ? "Saving…" : "To send"}
                  </button>
                )}
              </td>
            </tr>
          );
          })}
          {rows.length === 0 ? (
            <tr>
              <td colSpan={8} className="muted">No redemptions yet.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}

