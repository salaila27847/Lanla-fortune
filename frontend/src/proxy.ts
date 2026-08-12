export { auth as proxy } from "@/auth";

export const config = {
  matcher: ["/reading/:path*", "/history/:path*"],
};
