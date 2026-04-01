/**
 * Simplified Auth Configuration for Demo
 * Doesn't require database connection
 */
import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions: NextAuthOptions = {
    providers: [
        CredentialsProvider({
            name: "credentials",
            credentials: {
                email: { label: "Email", type: "email" },
                password: { label: "Password", type: "password" },
            },
            async authorize(credentials) {
                try {
                    if (!credentials?.email || !credentials?.password) {
                        throw new Error("Email and password required");
                    }

                    // Simple demo authentication - accept any email/password
                    // In production, this would validate against a real user database
                    if (credentials.password === "demo") {
                        return { 
                            id: "1", 
                            name: "Demo User", 
                            email: credentials.email 
                        };
                    }

                    throw new Error("Invalid password - use 'demo' for demo mode");
                } catch (error) {
                    console.error("Auth error:", error);
                    return null;
                }
            },
        }),
    ],
    session: { strategy: "jwt" },
    pages: {
        signIn: "/login",
    },
    callbacks: {
        async jwt({ token, user }) {
            if (user) {
                token.id = user.id;
            }
            return token;
        },
        async session({ session, token }) {
            if (session.user) {
                (session.user as { id?: string }).id = token.id as string;
            }
            return session;
        },
    },
    secret: process.env.NEXTAUTH_SECRET || "demo-secret-key",
};
