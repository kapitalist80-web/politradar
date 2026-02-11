import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      'politradar.cranodyne.com',
      'localhost',
      '.cranodyne.com',  // erlaubt alle Subdomains von cranodyne.com
    ],
    host: '0.0.0.0',
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
