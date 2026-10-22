export function parseCents(text: string): number | null {
 const m = /^(-?)([0-9]+)(?:\.([0-9]{1,2}))?$/.exec(text);
 if (!m || m[0] !== text) return null;
 const n = BigInt(m[2]) * 100n + BigInt((m[3] ?? '').padEnd(2,'0'));
 const signed = m[1] ? -n : n;
 const bound = BigInt(Number.MAX_SAFE_INTEGER);
 return signed < -bound || signed > bound ? null : Number(signed);
}
