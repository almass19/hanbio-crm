import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // this app lives in a subfolder of a larger repo — pin the trace root
  outputFileTracingRoot: import.meta.dirname,
  experimental: {
    // server actions form the write path of the CRM
    serverActions: { bodySizeLimit: "1mb" },
  },
  // lint is a separate `npm run lint` step; don't block deploys on it
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
