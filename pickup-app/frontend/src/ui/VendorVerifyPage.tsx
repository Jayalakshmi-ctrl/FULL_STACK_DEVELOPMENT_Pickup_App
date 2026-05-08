import React, { useState } from "react";
import { verifyPlastic } from "./api";

export function VendorVerifyPage() {
  const [customerEmail, setCustomerEmail] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const w = parseFloat(weightKg);
      if (Number.isNaN(w) || w <= 0) {
        throw new Error("Enter a valid weight in kg");
      }
      const out = await verifyPlastic(customerEmail.trim(), w, notes.trim() || undefined);
      setResult(
        `Credited ${out.eco_points_awarded} Eco-Points to ${out.customer_email} (${out.weight_kg} kg). Customer balance is now ${out.new_balance}.`
      );
      setWeightKg("");
      setNotes("");
    } catch (e: any) {
      setError(e?.message ?? "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <div style={{ fontWeight: 900, fontSize: 16, marginBottom: 6 }}>Vendor: verify plastic weigh-in</div>
      <div className="muted" style={{ marginBottom: 12 }}>
        Enter the customer&apos;s registered email and the weighed plastic in kilograms. Eco-Points are credited instantly.
      </div>

      {error ? <div className="notice error" style={{ marginBottom: 12 }}>{error}</div> : null}
      {result ? <div className="notice" style={{ marginBottom: 12 }}>{result}</div> : null}

      <form onSubmit={onSubmit} className="grid">
        <div>
          <div className="muted">Customer email</div>
          <input
            value={customerEmail}
            onChange={(e) => setCustomerEmail(e.target.value)}
            placeholder="customer@example.com"
            type="email"
            required
          />
        </div>
        <div>
          <div className="muted">Plastic weight (kg)</div>
          <input
            value={weightKg}
            onChange={(e) => setWeightKg(e.target.value)}
            placeholder="e.g. 2.5"
            inputMode="decimal"
            required
          />
        </div>
        <div>
          <div className="muted">Notes (optional)</div>
          <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Batch / location" />
        </div>
        <button type="submit" disabled={busy}>
          {busy ? "Saving…" : "Verify & credit Eco-Points"}
        </button>
      </form>
    </div>
  );
}
