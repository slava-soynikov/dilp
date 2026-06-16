import { Field, Input } from "@fluentui/react-components";
import type { InputProps } from "@fluentui/react-components";

type Props = {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: InputProps["type"];
  error?: string;
  autoComplete?: string;
  required?: boolean;
};

export function FormField({
  label,
  value,
  onChange,
  type = "text",
  error,
  autoComplete,
  required,
}: Props) {
  return (
    <Field
      label={label}
      required={required}
      validationState={error ? "error" : undefined}
      validationMessage={error}
    >
      <Input
        type={type}
        value={value}
        onChange={(_, d) => onChange(d.value)}
        autoComplete={autoComplete}
      />
    </Field>
  );
}