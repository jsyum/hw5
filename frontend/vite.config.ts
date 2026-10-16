import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend allows this exact origin (http://localhost:5173) via CORS.
export default defineConfig({
  plugins: [react()],
  server: { host: "localhost", port: 5173, strictPort: true },
});
