import { headers } from "next/headers";

export default async function Home() {
  const host = (await headers()).get("host") ?? "";
  const subdomain = host.split(".")[0];

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-3xl font-semibold">law-saas</h1>
      <p className="mt-4 text-slate-600">
        Phase 0 placeholder. Detected subdomain: <code className="font-mono">{subdomain || "(none)"}</code>
      </p>
      <p className="mt-2 text-slate-500 text-sm">
        Replace this in Phase 3 with the real signup / dashboard / clients UI.
      </p>
    </main>
  );
}
