import { withAuth } from "next-auth/middleware";

export default withAuth({
    pages: { signIn: "/login" },
});

export const config = {
    matcher: [
        "/dashboard/:path*",
        "/agents/:path*",
        "/analytics/:path*",
        "/reports/:path*",
        "/trading/:path*",
        "/trader-guide/:path*",
        "/monitoring/:path*",
        "/settings/:path*",
    ],
};

