"use client";

import { useMemo, useState } from "react";
import { Check, ChevronDown, Plus, X } from "lucide-react";
import {
  actionOptions,
  connectorOptions,
  resourceOptions,
  type PolicyRow
} from "@/lib/mock-data";
import { cn } from "@/lib/utils";
import { FormField } from "@/components/shared/form-field";

type CreatePolicyModalProps = {
  open: boolean;
  appName: string | null;
  isAdmin?: boolean;
  onClose: () => void;
  onCreate: (policy: PolicyRow) => void;
};

export function CreatePolicyModal({
  open,
  appName,
  isAdmin = false,
  onClose,
  onCreate
}: CreatePolicyModalProps) {
  const [connector, setConnector] = useState("");
  const [action, setAction] = useState("");
  const [resourceType, setResourceType] = useState("");
  const [customResource, setCustomResource] = useState("");
  const [policyName, setPolicyName] = useState("");
  const [setGlobal, setSetGlobal] = useState(false);

  const actionLocked = !connector;
  const resourceLocked = !action;
  const customResourceLocked = !resourceType;
  const nameLocked = !resourceType;

  const canCreate = useMemo(
    () =>
      connector &&
      action &&
      resourceType &&
      policyName.trim(),
    [action, connector, policyName, resourceType]
  );

  if (!open) {
    return null;
  }

  function resetForm() {
    setConnector("");
    setAction("");
    setResourceType("");
    setCustomResource("");
    setPolicyName("");
    setSetGlobal(false);
  }

  function handleClose() {
    resetForm();
    onClose();
  }

  function handleCreate() {
    if (!canCreate) {
      return;
    }

    onCreate({
      id: Date.now(),
      connector,
      name: policyName.trim(),
      created: new Date().toISOString(),
      global: isAdmin && setGlobal,
      app: isAdmin && setGlobal ? null : appName
    });
    resetForm();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-transparent px-6">
      <section className="relative w-full max-w-[840px] rounded-[14px] bg-white px-5 pb-5 pt-16 shadow-modal">
        <button
          aria-label="Close create policy modal"
          className="absolute left-4 top-6 flex h-12 w-12 items-center justify-center rounded-xl bg-white text-gms-text shadow-[0_3px_12px_rgba(40,48,78,0.12)]"
          type="button"
          onClick={handleClose}
        >
          <X className="h-5 w-5" />
        </button>

        <div className="px-1">
          <h2 className="text-[22px] font-extrabold text-gms-text">
            Create Policy:
          </h2>

          <div className="mt-6 grid grid-cols-1 gap-7 md:grid-cols-3">
            <SelectField
              label="Choose Connector:"
              required
              placeholder="Connector"
              value={connector}
              options={connectorOptions}
              onChange={(value) => {
                setConnector(value);
                setAction("");
                setResourceType("");
                setCustomResource("");
                setPolicyName("");
              }}
            />
            <SelectField
              label="Choose Action:"
              required
              placeholder="Action"
              value={action}
              options={actionOptions}
              disabled={actionLocked}
              onChange={(value) => {
                setAction(value);
                setResourceType("");
                setCustomResource("");
                setPolicyName("");
              }}
            />
            <SelectField
              label="Choose Resource Type:"
              required
              placeholder="Resource Type"
              value={resourceType}
              options={resourceOptions}
              disabled={resourceLocked}
              onChange={(value) => {
                setResourceType(value);
                setCustomResource("");
                setPolicyName("");
              }}
            />
          </div>

          <FormField label="Customise Resource:" className="mt-6">
            <textarea
              className={cn(
                "h-[96px] w-full resize-none rounded border border-gms-blue px-3 py-3 text-sm outline-none",
                customResourceLocked
                  ? "bg-[#bdbdbd] text-white placeholder:text-white"
                  : "bg-white text-gms-text placeholder:text-[#a9bdff]"
              )}
              disabled={customResourceLocked}
              placeholder="Type your Resource"
              value={customResource}
              onChange={(event) => {
                setCustomResource(event.target.value);
              }}
            />
          </FormField>

          <div className="mt-6 grid grid-cols-1 gap-8 md:grid-cols-[240px_1fr]">
            <FormField label="Name Policy:" required>
              <input
                className="h-14 w-full rounded border border-gms-blue px-3 text-sm text-gms-text outline-none placeholder:text-[#a9bdff] disabled:bg-[#f2f2f2]"
                disabled={nameLocked}
                placeholder="Type your Policy Name"
                value={policyName}
                onChange={(event) => setPolicyName(event.target.value)}
              />
            </FormField>

            {isAdmin && (
              <FormField label="Set Permission:">
                <button
                  className="flex items-center gap-3 text-sm font-normal text-gms-text"
                  type="button"
                  onClick={() => setSetGlobal((current) => !current)}
                >
                  <span
                    className={cn(
                      "flex h-[18px] w-[18px] items-center justify-center rounded border border-gms-blue",
                      setGlobal && "bg-gms-blue text-white"
                    )}
                  >
                    {setGlobal && <Check className="h-3 w-3" />}
                  </span>
                  Set Policy as Global
                </button>
              </FormField>
            )}
          </div>

          <div className="mt-6 flex justify-end">
            <button
              className="inline-flex h-10 items-center gap-3 rounded-md bg-gms-blue px-5 text-sm font-medium text-white shadow-button disabled:opacity-50"
              disabled={!canCreate}
              type="button"
              onClick={handleCreate}
            >
              <Plus className="h-4 w-4" />
              Create
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

type SelectFieldProps = {
  label: string;
  placeholder: string;
  value: string;
  options: string[];
  required?: boolean;
  disabled?: boolean;
  onChange: (value: string) => void;
};

function SelectField({
  label,
  placeholder,
  value,
  options,
  required = false,
  disabled = false,
  onChange
}: SelectFieldProps) {
  const [open, setOpen] = useState(false);

  function handleSelect(nextValue: string) {
    onChange(nextValue);
    setOpen(false);
  }

  return (
    <FormField label={label} required={required}>
      <div className="relative">
        <button
          className={cn(
            "flex h-7 w-full items-center justify-between rounded border border-gms-blue px-3 text-left text-sm outline-none",
            disabled
              ? "bg-[#bdbdbd] text-white"
              : "bg-white text-gms-text",
            !value && !disabled && "text-[#a9bdff]"
          )}
          disabled={disabled}
          type="button"
          onClick={() => setOpen((current) => !current)}
        >
          <span>{value || placeholder}</span>
          <ChevronDown className="h-4 w-4 shrink-0 text-[#a9bdff]" />
        </button>

        {open && !disabled && (
          <div className="absolute left-0 top-8 z-30 max-h-44 w-full overflow-y-auto rounded border border-gms-blue bg-white py-1 shadow-[0_8px_20px_rgba(40,48,78,0.14)]">
            <button
              className="block w-full px-4 py-2 text-left text-sm text-[#a9bdff] hover:bg-gms-blue hover:text-white"
              type="button"
              onClick={() => handleSelect("")}
            >
              {placeholder}
            </button>
            {options.map((option) => (
              <button
                key={option}
                className={cn(
                  "block w-full px-4 py-2 text-left text-sm hover:bg-gms-blue hover:text-white",
                  value === option
                    ? "bg-gms-blue text-white"
                    : "bg-white text-gms-text"
                )}
                type="button"
                onClick={() => handleSelect(option)}
              >
                {option}
              </button>
            ))}
          </div>
        )}
      </div>
    </FormField>
  );
}
