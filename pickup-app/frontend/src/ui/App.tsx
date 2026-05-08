import React, { useEffect, useMemo, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import {
  clearToken,
  createPickup,
  getRole,
  getToken,
  listPickups,
  login,
  Pickup,
  registerCustomer,
  Role,
  setPickupStatus,
  setToken
} from "./api";
import plasticsImg from "../assets/plastics.svg";
import greeneryImg from "../assets/greenery.svg";
import { RewardsPage } from "./RewardsPage";
import { ShopPage } from "./ShopPage";
import { VendorVerifyPage } from "./VendorVerifyPage";
import { AdminRedemptionsPage } from "./AdminRedemptionsPage";

function formatDt(iso: string) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [role, setRole] = useState<Role | null>(getRole());
  const [token, setTokenState] = useState<string | null>(getToken());

  const [pickups, setPickups] = useState<Pickup[]>([]);
  const [address, setAddress] = useState("");
  const [pickupDate, setPickupDate] = useState(() => new Date().toISOString().slice(0, 10));

  const isAuthed = useMemo(() => !!token && !!role, [token, role]);
  const location = useLocation();

  async function refreshPickups() {
    const data = await listPickups();
    setPickups(data);
  }

  useEffect(() => {
    if (!isAuthed) return;
    setError(null);
    refreshPickups().catch((e) => setError(e.message));
  }, [isAuthed]);

  async function onSubmitAuth(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") {
        await registerCustomer(email, password);
      }
      const t = await login(email, password);
      setToken(t.access_token, t.role);
      setTokenState(t.access_token);
      setRole(t.role);
    } catch (e: any) {
      setError(e?.message ?? "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function onLogout() {
    clearToken();
    setRole(null);
    setTokenState(null);
    setPickups([]);
  }

  async function onCreatePickup(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createPickup(address, pickupDate);
      setAddress("");
      await refreshPickups();
    } catch (e: any) {
      setError(e?.message ?? "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function onMarkPickedUp(p: Pickup) {
    setBusy(true);
    setError(null);
    try {
      const raw = window.prompt("Enter plastic weight (kg) to credit Eco-Points:", "1");
      const w = raw === null ? null : parseFloat(raw);
      if (w === null || !Number.isFinite(w) || w <= 0) {
        throw new Error("Please enter a valid weight in kg.");
      }
      await setPickupStatus(p.id, "Picked Up", w);
      await refreshPickups();
    } catch (e: any) {
      setError(e?.message ?? "Request failed");
    } finally {
      setBusy(false);
    }
  }

  const rolePillClass =
    role === "Admin" ? "badge" : "badge";

  return (
    <div className="shell">
      <div className="container">
        <div className="topbar">
          <div className="brand">
            <div className="logo" />
            <div>
              <div className="title">Plan for Green Earth</div>
              <div className="muted">Eco-Points for verified plastic · redeem saplings, seeds &amp; compost.</div>
            </div>
          </div>
        {isAuthed ? (
          <div className="row" style={{ alignItems: "center" }}>
            <Link className="ghostLink" to="/" aria-current={location.pathname === "/" ? "page" : undefined}>
              Home
            </Link>
            {role === "Vendor" ? (
              <Link className="ghostLink" to="/verify" aria-current={location.pathname === "/verify" ? "page" : undefined}>
                Verify plastic
              </Link>
            ) : null}
            {role === "Customer" ? (
              <>
                <Link className="ghostLink" to="/rewards" aria-current={location.pathname === "/rewards" ? "page" : undefined}>
                  Eco-Points
                </Link>
                <Link className="ghostLink" to="/shop" aria-current={location.pathname === "/shop" ? "page" : undefined}>
                  Garden shop
                </Link>
              </>
            ) : null}
            {role === "Admin" ? (
              <Link className="ghostLink" to="/admin/redemptions" aria-current={location.pathname === "/admin/redemptions" ? "page" : undefined}>
                Redemptions
              </Link>
            ) : null}
            <span className={rolePillClass}>{role}</span>
            <button className="ghost" onClick={onLogout}>
              Log out
            </button>
          </div>
        ) : null}
      </div>

      {error ? (
        <div className="notice error" style={{ marginBottom: 12 }}>
          {error}
        </div>
      ) : null}

      {!isAuthed ? (
        <div className="authHero">
          <div className="authArt">
            <div className="authArtInner">
              <div>
                <div className="authArtTitle">Plastic in. Plants out.</div>
                <div className="authArtSubtitle">
                  Customers earn Eco-Points from vendor-verified plastic weight. Redeem for saplings, seeds, and compost.
                </div>
              </div>

              <div className="authImages" aria-hidden="true">
                <img className="heroImg plastics" src={plasticsImg} alt="" />
                <img className="heroImg greenery" src={greeneryImg} alt="" />
              </div>
            </div>
          </div>

          <div className="card glassCard authCard">
            <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
              <div className="mainArrived">Arrived on Main screen</div>
              <div className="segmented">
                <button
                  type="button"
                  className={mode === "login" ? "active" : ""}
                  onClick={() => setMode("login")}
                  disabled={busy}
                >
                  Login
                </button>
                <button
                  type="button"
                  className={mode === "register" ? "active" : ""}
                  onClick={() => setMode("register")}
                  disabled={busy}
                >
                  Register
                </button>
              </div>
            </div>

            <form onSubmit={onSubmitAuth} className="grid" style={{ marginTop: 12 }}>
              <div>
                <div className="muted">Email</div>
                <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
              </div>
              <div>
                <div className="muted">Password</div>
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="min 8 chars"
                  type="password"
                />
              </div>
              <div className="btnRow">
                <button disabled={busy}>
                  {busy ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
                </button>
                <span className="muted adminHint">
                  Admin / vendor accounts: see <code>.env</code> (<code>ADMIN_*</code>, <code>VENDOR_*</code>).
                </span>
              </div>
            </form>
          </div>
        </div>
      ) : (
        <Routes>
          <Route
            path="/"
            element={
              role === "Vendor" ? (
                <div className="grid">
                  <div className="card glassCard">
                    <div style={{ fontWeight: 800, marginBottom: 8 }}>Vendor workspace</div>
                    <div className="muted">
                      Use <b>Verify plastic</b> in the nav to weigh a customer&apos;s material and credit Eco-Points instantly.
                    </div>
                  </div>
                </div>
              ) : (
                <div className="grid two">
                  <div className="card">
                    <div style={{ fontWeight: 700, marginBottom: 8 }}>
                      {role === "Customer" ? "Request a pickup" : "Admin actions"}
                    </div>

                    {role === "Customer" ? (
                      <form onSubmit={onCreatePickup} className="grid">
                        <div>
                          <div className="muted">Address</div>
                          <input
                            value={address}
                            onChange={(e) => setAddress(e.target.value)}
                            placeholder="Enter pickup address"
                          />
                        </div>
                        <div>
                          <div className="muted">Pickup date</div>
                          <input
                            value={pickupDate}
                            onChange={(e) => setPickupDate(e.target.value)}
                            type="date"
                            min={new Date().toISOString().slice(0, 10)}
                          />
                        </div>
                        <button disabled={busy || !address.trim()}>Submit request</button>
                      </form>
                    ) : (
                      <div className="muted">Select a pickup on the right and mark it as Picked Up.</div>
                    )}
                  </div>

                  <div className="card">
                    <div className="row" style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <div style={{ fontWeight: 700 }}>{role === "Admin" ? "All pickups" : "My pickups"}</div>
                      <button className="secondary" onClick={() => refreshPickups()} disabled={busy}>
                        Refresh
                      </button>
                    </div>

                    <table className="table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Date</th>
                          <th>Status</th>
                          <th>Customer</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {pickups.map((p) => (
                          <tr key={p.id}>
                            <td>{p.id}</td>
                            <td>{p.pickup_date}</td>
                            <td>
                              <span className={`pill ${p.status === "Picked Up" ? "ok" : "pending"}`}>{p.status}</span>
                            </td>
                            <td>{role === "Admin" ? p.customer_email : "me"}</td>
                            <td style={{ width: 140 }}>
                              {role === "Admin" && p.status !== "Picked Up" ? (
                                <button onClick={() => onMarkPickedUp(p)} disabled={busy}>
                                  Picked Up
                                </button>
                              ) : (
                                <span className="muted">{formatDt(p.created_at)}</span>
                              )}
                            </td>
                          </tr>
                        ))}
                        {pickups.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="muted">
                              No pickups yet.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </div>
              )
            }
          />
          <Route path="/verify" element={role === "Vendor" ? <VendorVerifyPage /> : <Navigate to="/" replace />} />
          <Route path="/rewards" element={role === "Customer" ? <RewardsPage /> : <Navigate to="/" replace />} />
          <Route path="/shop" element={role === "Customer" ? <ShopPage /> : <Navigate to="/" replace />} />
          <Route path="/admin/redemptions" element={role === "Admin" ? <AdminRedemptionsPage /> : <Navigate to="/" replace />} />
        </Routes>
      )}
      </div>
    </div>
  );
}

