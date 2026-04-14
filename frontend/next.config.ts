import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // Proxy all API routes except auth routes
      {
        source: '/api/llm/:path*',
        destination: 'http://localhost:8000/api/llm/:path*',
      },
      {
        source: '/api/patterns/:path*',
        destination: 'http://localhost:8000/api/patterns/:path*',
      },
      {
        source: '/api/rl/:path*',
        destination: 'http://localhost:8000/api/rl/:path*',
      },
      {
        source: '/api/timezone/:path*',
        destination: 'http://localhost:8000/api/timezone/:path*',
      },
      {
        source: '/api/monitoring/:path*',
        destination: 'http://localhost:8000/api/monitoring/:path*',
      },
      {
        source: '/api/signals/:path*',
        destination: 'http://localhost:8000/api/signals/:path*',
      },
      {
        source: '/api/v2/:path*',
        destination: 'http://localhost:8000/api/v2/:path*',
      },
      {
        source: '/api/mcp/:path*',
        destination: 'http://localhost:8000/api/mcp/:path*',
      },
    ]
  },
};

export default nextConfig;
