import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    server: {
        host: "0.0.0.0", // Allows access from outside the container
        port: 5173, // Default Vite port
        strictPort: true, // Ensures it fails if the port is unavailable
        watch: {
            usePolling: true, // Ensures live reload works inside Docker
        },
        proxy: {
            "/api": {
                target: "http://backend:5000",
                changeOrigin: true,
                secure: false,
            },
        },
    },
});
