export function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export function passwordPolicyOk(value: string): boolean {
  return (
    value.length >= 8 &&
    /[a-zäöüß]/.test(value) &&
    /[A-ZÄÖÜ]/.test(value) &&
    /\d/.test(value)
  );
}