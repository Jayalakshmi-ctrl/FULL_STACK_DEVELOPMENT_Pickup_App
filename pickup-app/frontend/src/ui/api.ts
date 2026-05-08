// Prefer same-origin /api (Vite proxy → gateway) to avoid CORS and "Failed to fetch".
// Override with VITE_API_BASE_URL only if you need a direct URL (e.g. production).
export const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || "/api";

export type Role = "Customer" | "Admin" | "Vendor";

export function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export function setToken(token: string, role: Role) {
  localStorage.setItem("access_token", token);
  localStorage.setItem("role", role);
}

export function clearToken() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("role");
}

export function getRole(): Role | null {
  const r = localStorage.getItem("role");
  if (r === "Customer" || r === "Admin" || r === "Vendor") return r;
  return null;
}

function formatErrorDetail(data: unknown): string {
  if (data && typeof data === "object" && "detail" in data) {
    const d = (data as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d
        .map((e) => {
          if (e && typeof e === "object" && "msg" in e) return String((e as { msg: string }).msg);
          return JSON.stringify(e);
        })
        .join("; ");
    }
  }
  return "";
}

async function http<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      const d = formatErrorDetail(data);
      if (d) msg = d;
    } catch {}
    throw new Error(msg);
  }
  return (await res.json()) as T;
}

export async function registerCustomer(email: string, password: string) {
  return http<{ email: string; role: Role }>(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
}

export async function login(email: string, password: string) {
  return http<{ access_token: string; token_type: string; role: Role }>(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
}

export type Pickup = {
  id: number;
  customer_email: string;
  address: string;
  pickup_date: string;
  status: string;
  created_at: string;
  updated_at?: string | null;
};

export async function listPickups() {
  const token = getToken();
  return http<Pickup[]>(`${API_BASE}/pickups`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export async function createPickup(address: string, pickup_date: string) {
  const token = getToken();
  return http<Pickup>(`${API_BASE}/pickups`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ address, pickup_date })
  });
}

export async function setPickupStatus(
  id: number,
  status: "Picked Up" | "Requested",
  weight_kg?: number,
  notes?: string
) {
  const token = getToken();
  return http<Pickup>(`${API_BASE}/pickups/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      status,
      weight_kg: typeof weight_kg === "number" ? weight_kg : null,
      notes: notes ? notes : null
    })
  });
}

export async function verifyPlastic(customer_email: string, weight_kg: number, notes?: string) {
  const token = getToken();
  return http<{
    id: number;
    customer_email: string;
    weight_kg: number;
    eco_points_awarded: number;
    vendor_email: string;
    new_balance: number;
    created_at: string;
  }>(`${API_BASE}/eco/verify-plastic`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ customer_email, weight_kg, notes: notes || null })
  });
}

export type CatalogReward = {
  id: number;
  slug: string;
  name: string;
  reward_type: string;
  description: string;
  points_cost: number;
};

export type AdminRedemption = {
  id: number;
  customer_email: string;
  reward_name: string;
  reward_type: string;
  points_spent: number;
  status: string;
  delivery_date?: string | null;
  sent_at?: string | null;
  created_at: string;
};

export async function listAdminRedemptions() {
  const token = getToken();
  return http<AdminRedemption[]>(`${API_BASE}/admin/redemptions`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export async function scheduleRedemptionDelivery(id: number, delivery_date: string) {
  const token = getToken();
  return http<AdminRedemption>(`${API_BASE}/admin/redemptions/${id}/schedule`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ delivery_date })
  });
}

export async function listCatalogRewards() {
  const token = getToken();
  return http<CatalogReward[]>(`${API_BASE}/catalog/rewards`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export async function redeemReward(reward_id: number) {
  const token = getToken();
  return http<{
    id: number;
    reward_name: string;
    points_spent: number;
    remaining_balance: number;
    status: string;
    created_at: string;
  }>(`${API_BASE}/catalog/redeem`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ reward_id })
  });
}
