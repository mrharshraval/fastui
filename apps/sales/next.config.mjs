/** @type {import("next").NextConfig} */
const backendUrl = (process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const nextConfig = {
  devIndicators: {
    position: "bottom-right",
  },
  async rewrites() {
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};
export default nextConfig;

