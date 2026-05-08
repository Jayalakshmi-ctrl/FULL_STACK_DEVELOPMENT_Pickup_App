import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CatalogReward, listCatalogRewards, redeemReward } from "./api";
import tulsiImg from "../assets/medicinal-tulsi.svg";
import aloeImg from "../assets/medicinal-aloe-vera.svg";
import neemImg from "../assets/medicinal-neem.svg";
import mintImg from "../assets/medicinal-mint.svg";
import lemongrassImg from "../assets/medicinal-lemongrass.svg";
import ashwagandhaImg from "../assets/medicinal-ashwagandha.svg";

const rewardImagesBySlug: Record<string, string> = {
  "medicinal-tulsi": tulsiImg,
  "medicinal-aloe-vera": aloeImg,
  "medicinal-neem": neemImg,
  "medicinal-mint": mintImg,
  "medicinal-lemongrass": lemongrassImg,
  "medicinal-ashwagandha": ashwagandhaImg
};

export function ShopPage() {
  const [items, setItems] = useState<CatalogReward[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      setItems(await listCatalogRewards());
    } catch (e: any) {
      setError(e?.message ?? "Failed to load catalog");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onRedeem(id: number) {
    setBusyId(id);
    setError(null);
    setMsg(null);
    try {
      const out = await redeemReward(id);
      setMsg(`Redeemed “${out.reward_name}” for ${out.points_spent} points. Balance: ${out.remaining_balance}.`);
      await load();
    } catch (e: any) {
      setError(e?.message ?? "Redeem failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div style={{ fontWeight: 900, fontSize: 16 }}>Garden rewards</div>
        <Link className="ghostLink" to="/rewards">
          Eco-Points history
        </Link>
      </div>
      <div className="muted" style={{ marginBottom: 12 }}>
        Trade Eco-Points for saplings, organic seeds, or compost — pick up at your partner location (fulfillment tracked as <b>requested</b> until staff confirms).
      </div>

      {error ? <div className="notice error" style={{ marginBottom: 12 }}>{error}</div> : null}
      {msg ? <div className="notice" style={{ marginBottom: 12 }}>{msg}</div> : null}

      <div className="grid two">
        {items.map((r) => (
          <div key={r.id} className="card glassCard">
            <div className="row" style={{ gap: 12, alignItems: "center", marginBottom: 10 }}>
              {rewardImagesBySlug[r.slug] ? (
                <img
                  src={rewardImagesBySlug[r.slug]}
                  alt=""
                  width={54}
                  height={54}
                  style={{ borderRadius: 14, background: "rgba(255,255,255,0.75)", boxShadow: "0 10px 24px rgba(15,23,42,0.10)" }}
                  aria-hidden="true"
                />
              ) : (
                <div style={{ width: 54, height: 54 }} />
              )}
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 800 }}>{r.name}</div>
                <div className="muted" style={{ marginTop: 4 }}>{r.description}</div>
              </div>
              <span className="pill pending" style={{ whiteSpace: "nowrap" }}>{r.points_cost} pts</span>
            </div>
            <div className="muted" style={{ marginTop: 8, fontSize: 12 }}>
              Type: {r.reward_type.replace("_", " ")}
            </div>
            <button
              style={{ marginTop: 12, width: "100%" }}
              type="button"
              disabled={busyId !== null}
              onClick={() => onRedeem(r.id)}
            >
              {busyId === r.id ? "Redeeming…" : "Redeem"}
            </button>
          </div>
        ))}
      </div>
      {items.length === 0 && !error ? <div className="muted">Loading catalog…</div> : null}
    </div>
  );
}
