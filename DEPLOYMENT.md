# Deployment

This repository is prepared for Vercel.

## 1. Create a dedicated PostgreSQL database

Use a dedicated PostgreSQL database for this development deployment. Supabase, Neon, Prisma Postgres, or another PostgreSQL provider will work.

Set both:

- `DATABASE_URL`: pooled/runtime PostgreSQL URL
- `DIRECT_URL`: direct PostgreSQL URL used by Prisma schema operations

The Vercel build command currently runs `prisma db push` automatically. This is convenient for the development repository, but should be replaced with versioned migrations before a production launch.

## 2. Configure environment variables in Vercel

Required:

```text
DATABASE_URL=
DIRECT_URL=
NEXTAUTH_URL=https://YOUR-PROJECT.vercel.app
NEXTAUTH_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
AICLIPS_API_KEY=
WEBHOOK_URL=https://YOUR-PROJECT.vercel.app
STRIPE_SECRET_KEY=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_THEME=emerald
```

`WEBHOOK_URL` must contain only the base URL. The application automatically appends `/api/webhook/muapi`.

## 3. Google OAuth callback

Configure this callback URL in Google Cloud:

```text
https://YOUR-PROJECT.vercel.app/api/auth/callback/google
```

## 4. Stripe webhook

Configure a Stripe webhook for:

```text
https://YOUR-PROJECT.vercel.app/api/webhook/stripe
```

Subscribe at least to:

```text
checkout.session.completed
```

Copy its signing secret into `STRIPE_WEBHOOK_SECRET`.

## 5. Deploy

Import `xturn2u/clipping-dev` into Vercel and deploy the `main` branch.

Vercel uses:

```text
npm ci
npm run vercel-build
```

The build performs Prisma Client generation, applies the current Prisma schema to the dedicated database, and builds the Next.js application.

## 6. Post-deployment smoke test

Verify:

1. Landing page loads.
2. Google login succeeds.
3. A user row is created in PostgreSQL.
4. MuAPI key flow works.
5. YouTube download request returns a request ID.
6. AI clipping request creates a `Creation` row.
7. MuAPI webhook changes the creation status.
8. Stripe checkout opens.
9. Stripe webhook adds credits.
