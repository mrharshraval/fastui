/** @type {import("next").NextConfig} */
const nextConfig = {
  devIndicators: {
    position: "bottom-right",
  },
  async rewrites() {
    return [
      {
        source: "/api/proxy/:path*",
        destination: "http://127.0.0.1:8000/:path*",
      },
    ];
  },
};
export default nextConfig;
