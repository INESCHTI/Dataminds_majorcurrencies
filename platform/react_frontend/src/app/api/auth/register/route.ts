import { NextRequest, NextResponse } from "next/server";
import { hash } from "bcryptjs";
import { createLocalUser, findLocalUserByEmail } from "@/lib/local-users";

export async function POST(req: NextRequest) {
    try {
        const { name, email, password } = await req.json();

        const normalizedEmail = String(email || "").trim().toLowerCase();

        if (!normalizedEmail || !password) {
            return NextResponse.json({ error: "Email and password required" }, { status: 400 });
        }

        const exists = await findLocalUserByEmail(normalizedEmail);
        if (exists) {
            return NextResponse.json({ error: "Account already exists" }, { status: 409 });
        }

        const hashedPassword = await hash(password, 12);
        const user = await createLocalUser({
            name: name || normalizedEmail.split("@")[0],
            email: normalizedEmail,
            hashedPassword,
        });

        return NextResponse.json({ id: user.id, email: user.email }, { status: 201 });
    } catch (error) {
        console.error("Registration error:", error);
        return NextResponse.json({ error: "Registration failed" }, { status: 500 });
    }
}

