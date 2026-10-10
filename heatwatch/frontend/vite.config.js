import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Dev: proxy /api to FastAPI. Production: set VITE_API_URL to the API Gateway URL.
export default defineConfig({ plugins: [react()], server: { proxy: { "/api": "http://localhost:8000" } } });
