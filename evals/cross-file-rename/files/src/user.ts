export interface User { id: string; first: string; last: string; email: string }

export function formatUserName(u: User): string {
  return `${u.first} ${u.last}`.trim();
}
