import {
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
} from "@fluentui/react-components";
import { t } from "../i18n/ru";

type Props = {
  open: boolean;
  title: string;
  body: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel,
  cancelLabel,
  destructive,
  busy,
  onConfirm,
  onCancel,
}: Props) {
  return (
    <Dialog open={open} onOpenChange={(_, d) => !d.open && onCancel()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{title}</DialogTitle>
          <DialogContent>{body}</DialogContent>
          <DialogActions>
            <Button onClick={onCancel} disabled={busy}>
              {cancelLabel || t.common.cancel}
            </Button>
            <Button
              appearance="primary"
              onClick={onConfirm}
              disabled={busy}
              style={
                destructive
                  ? { backgroundColor: "#b00020", borderColor: "#b00020" }
                  : undefined
              }
            >
              {busy ? t.common.loading : confirmLabel || t.common.confirm}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}