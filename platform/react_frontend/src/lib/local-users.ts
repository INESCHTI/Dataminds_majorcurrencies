import { promises as fs } from "fs";
import path from "path";
import { randomUUID } from "crypto";

export interface LocalUserRecord {
    id: string;
    name: string;
    email: string;
    hashedPassword: string;
    createdAt: string;
}

const DATA_DIR = path.join(process.cwd(), ".local-data");
const USERS_FILE = path.join(DATA_DIR, "users.json");

async function ensureDataDir(): Promise<void> {
    await fs.mkdir(DATA_DIR, { recursive: true });
}

async function readUsers(): Promise<LocalUserRecord[]> {
    await ensureDataDir();
    try {
        const raw = await fs.readFile(USERS_FILE, "utf-8");
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? (parsed as LocalUserRecord[]) : [];
    } catch {
        return [];
    }
}

async function writeUsers(users: LocalUserRecord[]): Promise<void> {
    await ensureDataDir();
    await fs.writeFile(USERS_FILE, JSON.stringify(users, null, 2), "utf-8");
}

export async function findLocalUserByEmail(email: string): Promise<LocalUserRecord | null> {
    const normalized = String(email || "").trim().toLowerCase();
    if (!normalized) {
        return null;
    }

    const users = await readUsers();
    const user = users.find((u) => String(u.email || "").trim().toLowerCase() === normalized);
    return user || null;
}

export async function createLocalUser(input: {
    name?: string;
    email: string;
    hashedPassword: string;
}): Promise<LocalUserRecord> {
    const email = String(input.email || "").trim().toLowerCase();
    if (!email) {
        throw new Error("Email is required");
    }

    const users = await readUsers();
    const exists = users.some((u) => String(u.email || "").trim().toLowerCase() === email);
    if (exists) {
        throw new Error("Account already exists");
    }

    const next: LocalUserRecord = {
        id: randomUUID(),
        name: String(input.name || email.split("@")[0] || "Trader").trim(),
        email,
        hashedPassword: input.hashedPassword,
        createdAt: new Date().toISOString(),
    };

    users.push(next);
    await writeUsers(users);
    return next;
}
