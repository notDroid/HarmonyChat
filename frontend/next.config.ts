import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'standalone',
  allowedDevOrigins: ["macbook-pro", "walis-macbook-pro"],
};

export default nextConfig;
