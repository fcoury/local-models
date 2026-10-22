export function parseCents(text: string): number | null {
 const n = Number(text); return Number.isFinite(n) ? Math.round(n * 100) : null;
}
