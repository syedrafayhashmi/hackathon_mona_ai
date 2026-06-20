const apiInternalUrl = (process.env.API_INTERNAL_URL || "http://localhost:8000").replace(/\/$/, "");

export const dynamic = "force-dynamic";

export async function GET(): Promise<Response> {
  const upstream = await fetch(`${apiInternalUrl}/health`, { cache: "no-store" });
  const headers = new Headers(upstream.headers);
  headers.delete("content-length");

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers,
  });
}
