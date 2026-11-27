import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dashboard calls /api/...; during development Vite forwards those
// requests to the backend on port 8000 (so the browser sees one address).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.API_URL || "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
