import type {NextConfig} from "next";

const staticQa=process.env.STATIC_QA==="1";
const securityHeaders=[
  {key:"X-Content-Type-Options",value:"nosniff"},
  {key:"X-Frame-Options",value:"DENY"},
  {key:"Referrer-Policy",value:"no-referrer"},
  {key:"Permissions-Policy",value:"camera=(), microphone=(), geolocation=()"},
  {key:"Content-Security-Policy",value:"default-src 'self'; connect-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'"},
];
const nextConfig:NextConfig={
  reactStrictMode:true,
  poweredByHeader:false,
  output:staticQa?"export":undefined,
  turbopack:{root:process.cwd()},
  rewrites:staticQa?undefined:async()=>[{source:"/api/v1/:path*",destination:"http://127.0.0.1:8000/api/v1/:path*"}],
  headers:staticQa?undefined:async()=>[{source:"/(.*)",headers:securityHeaders}],
};
export default nextConfig;
