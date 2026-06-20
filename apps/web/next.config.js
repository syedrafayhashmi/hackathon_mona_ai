/** @type {import('next').NextConfig} */
const apiUrl = process.env.API_INTERNAL_URL || "http://localhost:8000";

const nextConfig = {
  output: "standalone",
  async rewrites() {
    return {
      beforeFiles: [
        { source: "/api/:path*", destination: `${apiUrl}/api/:path*` },
        { source: "/health", destination: `${apiUrl}/health` },
      ],
      afterFiles: [],
      fallback: [],
    };
  },
};

module.exports = nextConfig;
