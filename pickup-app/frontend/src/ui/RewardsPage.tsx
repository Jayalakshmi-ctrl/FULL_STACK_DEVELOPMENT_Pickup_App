import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE, getToken } from "./api";

type PlasticRow = {
  id: number;
  weight_kg: number;
  eco_points_awarded: number;
  vendor_email: string;
  created_at: string;
  notes?: string | null;
};

type RedemptionRow = {
  id: number;
  reward_name: string;
  reward_type: string;
  points_spent: number;
  status: string;
  delivery_date?: string | null;
  sent_at?: string | null;
  created_at: string;
};

type PickupRow = {
  pickup_id: number;
  pickup_date: string;
  status: string;
  points_earned: number;
  created_at: string;
  updated_at?: string | null;
};

type RewardsOut = {
  eco_points_balance: number;
  eco_points_per_kg: number;
  plastic_history: PlasticRow[];
  redemptions: RedemptionRow[];
  pickup_history: PickupRow[];
};

async function fetchRewards(): Promise<RewardsOut> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/rewards/me`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") msg = data.detail;
    } catch {}
    throw new Error(msg);
  }
  return (await res.json()) as RewardsOut;
}

export function RewardsPage() {
  const [data, setData] = useState<RewardsOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    fetchRewards()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div style={{ fontWeight: 900, fontSize: 16 }}>Eco-Points &amp; history</div>
        <div className="row" style={{ alignItems: "center" }}>
          <Link className="ghostLink" to="/shop">
            Redeem for plants
          </Link>
          <span className="badge">Plastic → Plants</span>
        </div>
      </div>

      {error ? <div className="notice error">{error}</div> : null}

      <div className="grid two" style={{ marginTop: 12 }}>
        <div className="card glassCard">
          <div className="muted">Eco-Points balance</div>
          <div style={{ fontSize: 40, fontWeight: 950, letterSpacing: "-0.04em", marginTop: 6 }}>
            {data ? data.eco_points_balance : "—"}
          </div>
          <div className="muted" style={{ marginTop: 6 }}>
            Earn <b>{data?.eco_points_per_kg ?? "—"}</b> Eco-Points per <b>1 kg</b> of plastic when a vendor verifies your drop-off on-site.
          </div>
        </div>

        <div className="card glassCard">
          <div className="muted">Activity</div>
          <div className="muted" style={{ marginTop: 6 }}>
            {data
              ? `${data.plastic_history.length} verified weigh-ins · ${data.redemptions.length} redemptions · ${data.pickup_history.length} pickup requests`
              : "Loading..."}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={{ fontWeight: 800, marginBottom: 8 }}>Verified plastic (Eco-Points)</div>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>When</th>
              <th>Weight (kg)</th>
              <th>Points</th>
              <th>Vendor</th>
            </tr>
          </thead>
          <tbody>
            {(data?.plastic_history ?? []).map((h) => (
              <tr key={h.id}>
                <td>{h.id}</td>
                <td className="muted">{new Date(h.created_at).toLocaleString()}</td>
                <td>{h.weight_kg}</td>
                <td style={{ fontWeight: 800 }}>{h.eco_points_awarded}</td>
                <td className="muted">{h.vendor_email}</td>
              </tr>
            ))}
            {data && data.plastic_history.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  No verified plastic yet. Visit a collection point and ask the vendor to credit your account.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={{ fontWeight: 800, marginBottom: 8 }}>Redemptions (saplings, seeds, compost)</div>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Reward</th>
              <th>Points</th>
              <th>Status</th>
              <th>Delivery</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {(data?.redemptions ?? []).map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.reward_name}</td>
                <td style={{ fontWeight: 800 }}>{r.points_spent}</td>
                <td>
                  <span className={`pill ${r.status === "fulfilled" ? "ok" : "pending"}`}>
                    {r.status === "fulfilled" ? "Sent to customer" : "Requested"}
                  </span>
                </td>
                <td style={{ fontWeight: 800 }}>{r.delivery_date ?? "—"}</td>
                <td className="muted">
                  {new Date((r.sent_at ?? r.created_at) as string).toLocaleString()}
                </td>
              </tr>
            ))}
            {data && data.redemptions.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted">
                  No redemptions yet. Browse the garden rewards catalog.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={{ fontWeight: 800, marginBottom: 8 }}>Pickup requests (logistics)</div>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {(data?.pickup_history ?? []).map((h) => (
              <tr key={h.pickup_id}>
                <td>{h.pickup_id}</td>
                <td>{h.pickup_date}</td>
                <td>
                  <span className={`pill ${h.status === "Picked Up" ? "ok" : "pending"}`}>{h.status}</span>
                </td>
              </tr>
            ))}
            {data && data.pickup_history.length === 0 ? (
              <tr>
                <td colSpan={3} className="muted">
                  No pickup requests yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
