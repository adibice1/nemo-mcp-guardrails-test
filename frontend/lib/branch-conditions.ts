export type BranchTerm = {
  field: "source_branch" | "target_branch";
  operator: "=" | "!=";
  value: string;
};

export const MERGE_BRANCH_NOTICE = "Matching merges are blocked using trusted PR metadata. Other branch-restricted merges are refused because the connector cannot atomically pin the target branch. Selective merging is currently unavailable.";

// Match the backend's bounded, quoted branch grammar; never split inside JSON literals.
export function parseBranchConditions(text: string): BranchTerm[] | null {
  if (!text.trim()) return [];
  const pattern = /^(source_branch|target_branch)\s*(!=|=)\s*("(?:[^"\\]|\\.)*")/i;
  const terms: BranchTerm[] = [];
  let remaining = text.trim();
  while (remaining) {
    const match = pattern.exec(remaining);
    if (!match) return null;
    let value: unknown;
    try { value = JSON.parse(match[3]); } catch { return null; }
    if (typeof value !== "string") return null;
    terms.push({field: match[1].toLowerCase() as BranchTerm["field"], operator: match[2] as BranchTerm["operator"], value});
    remaining = remaining.slice(match[0].length);
    if (!remaining) break;
    const separator = /^\s+AND\s+/i.exec(remaining);
    if (!separator) return null;
    remaining = remaining.slice(separator[0].length);
    if (!remaining) return null;
  }
  if (terms.length > 2 || new Set(terms.map(term => term.field)).size !== terms.length) return null;
  return terms.sort((left, right) => left.field.localeCompare(right.field));
}

export function serializeBranchConditions(terms: BranchTerm[]): string {
  return [...terms].sort((left, right) => left.field.localeCompare(right.field))
    .map(term => `${term.field} ${term.operator} ${JSON.stringify(term.value)}`).join(" AND ");
}

export function formatBranchConditions(text: string): string | null {
  const terms = parseBranchConditions(text);
  if (!terms?.length) return null;
  return terms.map((term, index) => {
    const branch = term.field === "source_branch" ? "source" : "target";
    const comparison = term.operator === "!=" ? "is not" : "is";
    const name = term.value ? JSON.stringify(term.value) : "(choose a branch)";
    return `${index === 0 ? "The" : "the"} ${branch} branch ${comparison} ${name}`;
  }).join(" and ") + ".";
}
