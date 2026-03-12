# Next.js Setup

> **What is this?** Next.js is a React framework that adds server-side rendering, file-based routing, and a build system on top of React. The "App Router" (introduced in Next.js 13) uses a folder structure to define routes.

---

## Key Concepts

### React vs Next.js

- **React** = UI library (builds components/UI)
- **Next.js** = full framework built on React (adds routing, SSR, API routes, optimization)

### App Router

In Next.js 15 (what we use), every folder inside `app/` becomes a URL route, and every `page.tsx` inside that folder is the page content.

```
app/
├── page.tsx              → / (home page)
├── dashboard/
│   └── page.tsx          → /dashboard
└── agents/
    ├── page.tsx           → /agents
    └── [id]/
        └── page.tsx       → /agents/123 (dynamic route)
```

### Server vs Client Components

Next.js 15 defaults to **Server Components** — they run on the server and send HTML to the browser (faster initial load, can access databases directly).

Mark a component as **Client Component** (runs in the browser) when you need:
- `useState`, `useEffect`, event handlers
- Browser APIs

```tsx
"use client"   // ← add this line at the top for client components
```

---

## Code Examples

### Project was bootstrapped with

```bash
PATH="/opt/homebrew/bin:$PATH" npx -y create-next-app@latest frontend \
  --typescript \       # ← TypeScript (not JavaScript)
  --tailwind \         # ← Tailwind CSS for styling
  --app \              # ← App Router (not Pages Router)
  --no-src-dir \       # ← files at root level, not inside src/
  --eslint \           # ← code linting
  --import-alias "@/*" # ← @/components instead of ../../components
```

### Folder structure created

```
frontend/
├── app/
│   ├── layout.tsx     ← Root layout (wraps all pages)
│   ├── page.tsx       ← Home page (/)
│   └── globals.css    ← Global styles
├── public/            ← Static files (images, icons)
├── package.json       ← Node.js dependencies
├── next.config.ts     ← Next.js configuration
├── tsconfig.json      ← TypeScript configuration
└── tailwind.config.ts ← Tailwind CSS configuration
```

### Starting the dev server

```bash
cd frontend/
npm run dev            # http://localhost:3000
```

### A simple page (TypeScript + App Router)

```tsx
// app/dashboard/page.tsx

export default function DashboardPage() {
  return (
    <main>
      <h1 className="text-2xl font-bold">Dashboard</h1>
    </main>
  )
}
```

**What this does:**
- `export default function` — Next.js looks for a default export from `page.tsx`
- `className="text-2xl font-bold"` — Tailwind CSS utility classes (no separate CSS file needed!)
- No `import React` needed in modern React/Next.js

---

## Commands

```bash
# Install all dependencies (after cloning)
cd frontend/
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run ESLint (code style checker)
npm run lint
```

---

## Gotchas & Tips

- **`npx` needs Node.js on PATH** — on Mac with Homebrew, Node might not be in the shell's PATH. Use `PATH="/opt/homebrew/bin:$PATH" npx ...` if you get "command not found: npx".
- **App Router vs Pages Router** — if you Google old Next.js tutorials, they use `pages/`. The new way is `app/`. They work differently. Make sure to look for App Router docs.
- **`"use client"` directive** — without it, your component is a Server Component. Add it at the very top of the file (before imports) when you need interactivity.
- **Tailwind classes must be complete strings** — don't build class names dynamically with string interpolation (e.g., `text-${size}`) — Tailwind won't include those in the build.

---

## See Also

- [typescript-basics.md](typescript-basics.md) — TypeScript concepts used in Next.js
- [tailwind-css.md](tailwind-css.md) — how to use Tailwind in Next.js components
- `docs/folder-structure.md` — the planned full folder structure for the frontend
