// Help & FAQ search by MEANING (Moshe, 2026-11-01: "use gemma embedding so natural
// language can search"). The website and the app both call this.
//
//   GET /api/help-search?q=how do i get quotes from many factories
//   -> { model, hits: [{ id, score }] }   best first, up to 12, score = cosine 0..1
//
// Model: EmbeddingGemma 300M on Cloudflare Workers AI (binding AI in wrangler.toml).
// EmbeddingGemma wants its task prompts: "task: search result | query: ..." for the
// question and "title: ... | text: ..." for each answer. Without them it ranks worse.
//
// The answers are embedded ONCE per version of help.json, not per question: the vectors
// are kept in memory and in the Cache API under a hash of help.json + the model. A new
// help.json is a new hash, so the vectors rebuild by themselves after a deploy.
// Each question's result is cached a day, so a repeat question costs nothing.
//
// The callers ALSO run their own word search. This answer is an extra, never the only
// path: if it fails or is slow, the word results stay on screen.

const MODEL = "@cf/google/embeddinggemma-300m";
const MAX_Q = 300;
const TOP = 12;

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const json = (body, status = 200, extra = {}) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json", ...extra } });

async function sha(s) {
  const b = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)));
  return [...b].map((x) => x.toString(16).padStart(2, "0")).join("").slice(0, 24);
}
const normalize = (q) => q.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "")
  .replace(/[^\p{L}\p{N}]+/gu, " ").trim().replace(/\s+/g, " ");
function unit(v) {
  let n = 0;
  for (const x of v) n += x * x;
  n = Math.sqrt(n) || 1;
  return v.map((x) => Math.round((x / n) * 1e5) / 1e5);
}
// What each answer is embedded as. The hand-written "asks" are other ways people put
// the same question, so they belong to the answer's meaning.
const docText = (e) => `title: ${e.question} | text: ${e.answer}` +
  (e.asks?.length ? ` People also ask: ${e.asks.join("; ")}.` : "");

let mem = null;   // { key, docs } for this isolate

async function docVectors(env, ctx, helpText, key) {
  if (mem?.key === key) return mem.docs;
  const cacheKey = new Request(`https://help-search.internal/docs/${key}`);
  const hit = await caches.default.match(cacheKey);
  if (hit) { mem = { key, docs: await hit.json() }; return mem.docs; }
  const entries = JSON.parse(helpText).sections.flatMap((s) => s.entries);
  const vecs = [];
  for (let i = 0; i < entries.length; i += 50) {
    const r = await env.AI.run(MODEL, { text: entries.slice(i, i + 50).map(docText) });
    vecs.push(...r.data);
  }
  const docs = entries.map((e, i) => ({ id: e.id, v: unit(vecs[i]) }));
  ctx.waitUntil(caches.default.put(cacheKey, new Response(JSON.stringify(docs),
    { headers: { "Cache-Control": "public, max-age=2592000" } })));
  mem = { key, docs };
  return docs;
}

export async function onRequest(ctx) {
  const { request, env } = ctx;
  if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (request.method !== "GET") return json({ error: "GET only" }, 405);
  const q = (new URL(request.url).searchParams.get("q") || "").trim();
  if (q.length < 2 || q.length > MAX_Q) return json({ error: `2 to ${MAX_Q} characters` }, 400);
  if (!env.AI) return json({ error: "no AI binding" }, 503);

  try {
    const helpText = await (await env.ASSETS.fetch(new URL("/help/help.json", request.url))).text();
    const key = await sha(MODEL + "\n" + helpText);

    const qKey = new Request(`https://help-search.internal/q/${key}/${encodeURIComponent(normalize(q))}`);
    const cached = await caches.default.match(qKey);
    if (cached) return json(await cached.json(), 200, { "X-Cache": "hit" });

    const docs = await docVectors(env, ctx, helpText, key);
    const qv = unit((await env.AI.run(MODEL, { text: [`task: search result | query: ${q}`] })).data[0]);
    const hits = docs.map((d) => {
      let s = 0;
      for (let i = 0; i < qv.length; i++) s += qv[i] * d.v[i];
      return { id: d.id, score: Math.round(s * 1e4) / 1e4 };
    }).sort((a, b) => b.score - a.score).slice(0, TOP);

    const body = { model: "embeddinggemma-300m", hits };
    ctx.waitUntil(caches.default.put(qKey, new Response(JSON.stringify(body),
      { headers: { "Cache-Control": "public, max-age=86400" } })));
    return json(body);
  } catch (e) {
    return json({ error: String(e).slice(0, 200) }, 502);
  }
}
