import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const vercelHost =
    process.env.VERCEL_PROJECT_PRODUCTION_URL ||
    process.env.VERCEL_URL ||
    null;

  const nextAuthUrl =
    process.env.NEXTAUTH_URL ||
    (vercelHost ? "https://" + vercelHost : null);

  const checks = {
    googleClientId: Boolean(process.env.GOOGLE_CLIENT_ID),
    googleClientSecret: Boolean(process.env.GOOGLE_CLIENT_SECRET),
    nextAuthSecret: Boolean(process.env.NEXTAUTH_SECRET),
    nextAuthUrl: Boolean(nextAuthUrl),
    databaseUrl: Boolean(process.env.DATABASE_URL),
    directUrl: Boolean(process.env.DIRECT_URL),
  };

  return NextResponse.json({
    ok: Object.values(checks).every(Boolean),
    checks,
    resolvedNextAuthUrl: nextAuthUrl,
    expectedGoogleCallback: nextAuthUrl
      ? nextAuthUrl + "/api/auth/callback/google"
      : null,
  });
}
