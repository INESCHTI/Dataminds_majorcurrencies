import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["localhost", "127.0.0.1"],
  async rewrites() {
    return [
      {
        source: "/trader_guide.html",
        destination: "/trader-guide",
      },
      {
        source: "/trader-guide.html",
        destination: "/trader-guide",
      },
    ];
  },
};

export default nextConfig;
