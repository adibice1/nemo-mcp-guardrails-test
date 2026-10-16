"use client";

import {MERGE_BRANCH_NOTICE, parseBranchConditions, serializeBranchConditions, type BranchTerm} from "@/lib/branch-conditions";

type Props = {value: string; onChange: (value: string) => void; merge: boolean};

export function BranchConditionEditor({value, onChange, merge}: Props) {
  const terms = parseBranchConditions(value);
  const controlClass = "rounded border border-gms-blue bg-white px-2 py-2 text-sm text-gms-text dark:bg-[#252932]";

  function update(field: BranchTerm["field"], changes: Partial<BranchTerm>) {
    if (terms === null) return;
    const existing = terms.find(term => term.field === field);
    const next = terms.filter(term => term.field !== field);
    const term = {...(existing ?? {field, operator: "=" as const, value: ""}), ...changes};
    next.push(term);
    onChange(serializeBranchConditions(next));
  }

  return <fieldset className="mt-6 space-y-3 rounded border border-gms-blue p-3">
    <legend className="px-1 text-sm font-semibold">Block when all selected branch conditions match</legend>
    {terms === null ? <p className="text-sm text-gms-muted">Existing condition retained below. Use branch controls only after explicitly replacing it.</p> :
      (["source_branch", "target_branch"] as const).map(field => {
        const term = terms.find(item => item.field === field);
        return <div className="flex flex-wrap items-center gap-2" key={field}>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={!!term} onChange={event => onChange(serializeBranchConditions(event.target.checked
              ? [...terms, {field, operator: "=", value: ""}] : terms.filter(item => item.field !== field)))} />
            {field === "source_branch" ? "Source branch" : "Target branch"}
          </label>
          {term && <>
            <select aria-label={`${field} comparison`} className={controlClass} value={term.operator}
              onChange={event => update(field, {operator: event.target.value as BranchTerm["operator"]})}>
              <option value="=">equals</option><option value="!=">does not equal</option>
            </select>
            <input aria-label={`${field} name`} className={controlClass} value={term.value} maxLength={255}
              placeholder="Exact branch name" onChange={event => update(field, {value: event.target.value})} />
          </>}
        </div>;
      })}
    <p className="text-xs text-gms-muted">Branch names are case-sensitive. Leaving both conditions unselected blocks all resources.</p>
    {merge && <p className="text-xs text-amber-700 dark:text-amber-300">{MERGE_BRANCH_NOTICE}</p>}
    {terms === null && <button type="button" className="text-sm text-gms-blue underline"
      onClick={() => onChange('source_branch = ""')}>Replace with a branch condition</button>}
  </fieldset>;
}
