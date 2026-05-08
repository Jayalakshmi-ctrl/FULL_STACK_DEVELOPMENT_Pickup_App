import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In Docker, set VITE_PROXY_TARGET=http://gateway-service:8000
// Locally (no Docker), defaults to your machine's gateway.
const proxyTarget = process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: proxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "")
      }
    }
  }
});
