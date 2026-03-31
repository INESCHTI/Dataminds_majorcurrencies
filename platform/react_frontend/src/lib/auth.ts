import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { compare } from "bcryptjs";
import { findLocalUserByEmail } from "@/lib/local-users";

const DEMO_LOGIN_EMAIL = String(process.env.DEMO_LOGIN_EMAIL || "admin@fxalpha.local").trim().toLowerCase();
const DEMO_LOGIN_PASSWORD = String(process.env.DEMO_LOGIN_PASSWORD || "fxalpha123");
const DEMO_LOGIN_NAME = String(process.env.DEMO_LOGIN_NAME || "FX Alpha Admin");

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

                    const normalizedEmail = String(credentials.email).trim().toLowerCase();
                    const password = String(credentials.password);

                    const localUser = await findLocalUserByEmail(normalizedEmail);
                    if (localUser) {
                        const isValid = await compare(password, localUser.hashedPassword);
                        if (!isValid) {
                            throw new Error("Invalid password");
                        }
                        return {
                            id: localUser.id,
                            name: localUser.name,
                            email: localUser.email,
                        };
                    }

                    if (normalizedEmail === DEMO_LOGIN_EMAIL && password === DEMO_LOGIN_PASSWORD) {
                        return {
                            id: "demo-admin",
                            name: DEMO_LOGIN_NAME,
                            email: DEMO_LOGIN_EMAIL,
                        };
                    }

                    throw new Error("No account found with this email");
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
    secret: process.env.NEXTAUTH_SECRET,
};

