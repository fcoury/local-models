export interface Summary { account: string; totalCents: number; count: number }
export function summarizeJsonLines(text: string): Summary[] {
 const groups = new Map<string,Summary>();
 for (const line of text.split(/\r?\n/)) {
  if (!line.trim()) continue;
  const row: unknown = JSON.parse(line);
  if (!row || typeof row !== 'object' || Array.isArray(row)) throw new Error('invalid record');
  const {account,cents}=row as Record<string,unknown>;
  if (typeof account !== 'string' || !account.trim() || typeof cents !== 'number' || !Number.isSafeInteger(cents)) throw new Error('invalid fields');
  const key=account.trim(); const old=groups.get(key) ?? {account:key,totalCents:0,count:0};
  const total=old.totalCents+cents; if (!Number.isSafeInteger(total)) throw new Error('unsafe total');
  groups.set(key,{account:key,totalCents:total,count:old.count+1});
 }
 return [...groups.values()].sort((a,b)=>a.account<b.account?-1:a.account>b.account?1:0);
}
