import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <span className="inline-block rounded-full bg-slate-200 px-3 py-1 text-xs font-medium uppercase tracking-wide text-slate-700">
        Beta privada
      </span>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900">
        law-saas
      </h1>
      <p className="mt-3 max-w-2xl text-lg text-slate-600">
        Gestión de clientes, expedientes y actuaciones para estudios jurídicos
        — multi-tenant, encriptado por estudio, en el navegador.
      </p>

      <div className="mt-8 flex gap-3">
        <Link
          href="/signup"
          className="inline-flex h-11 items-center justify-center rounded-md bg-slate-900 px-5 text-sm font-medium text-white hover:bg-slate-800"
        >
          Crear estudio
        </Link>
        <Link
          href="/login"
          className="inline-flex h-11 items-center justify-center rounded-md border border-slate-300 px-5 text-sm font-medium text-slate-900 hover:bg-slate-100"
        >
          Ya tengo cuenta
        </Link>
      </div>

      <p className="mt-12 text-sm text-slate-500">
        ¿Tu estudio ya existe? Ingresá en{" "}
        <span className="font-mono text-slate-700">tu-estudio.lawsaas.app</span>.
      </p>
    </main>
  );
}
