import { NextResponse } from "next/server";
import { Pool } from "pg";

export const dynamic = "force-dynamic";

export async function GET() {
  const vercelHost =
    process.env.VERCEL_PROJECT_PRODUCTION_URL ||
    process.env.VERCEL_URL ||
    null;

  const nextAuthUrl =
    process.env.NEXTAUTH_URL ||
    (vercelHost ? "https://" + vercelHost : null);

  let databaseReachable = false;
  let databaseError = null;

  if (process.env.DATABASE_URL) {
    const pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      connectionTimeoutMillis: 3000,
      max: 1,
    });
    try {
      await pool.query("SELECT 1");
      databaseReachable = true;
    } catch (error) {
      databaseError = error?.code || error?.message || "Database connection failed";
    } finally {
      await pool.end().catch(() => {});
    }
  }

  const checks = {
    googleClientId: Boolean(process.env.GOOGLE_CLIENT_ID),
    googleClientSecret: Boolean(process.env.GOOGLE_CLIENT_SECRET),
    nextAuthSecret: Boolean(process.env.NEXTAUTH_SECRET),
    nextAuthUrl: Boolean(nextAuthUrl),
    databaseUrl: Boolean(process.env.DATABASE_URL),
    databaseReachable,
  };

  return NextResponse.json({
    ok: Object.values(checks).every(Boolean),
    checks,
    optional: {
      directUrl: Boolean(process.env.DIRECT_URL),
    },
    databaseError,
    resolvedNextAuthUrl: nextAuthUrl,
    expectedGoogleCallback: nextAuthUrl
      ? nextAuthUrl + "/api/auth/callback/google"
      : null,
  });
}
