import { useState } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  MessageBar,
  MessageBarBody,
} from "@fluentui/react-components";
import { t } from "../i18n/ru";

type Props = {
  open: boolean;
  username: string;
  pin: string;
  onClose: () => void;
};

export function PinDisplayDialog({ open, username, pin, onClose }: Props) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(pin);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // ignore
    }
  }

  return (
    <Dialog open={open} modalType="alert">
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{t.children.pin.title}</DialogTitle>
          <DialogContent>
            <MessageBar intent="warning" style={{ marginBottom: 12 }}>
              <MessageBarBody>{t.children.pin.intro}</MessageBarBody>
            </MessageBar>
            <div style={{ marginBottom: 8 }}>
              <strong>{t.children.create.username}:</strong> {username}
            </div>
            <div
              style={{
                fontFamily: "monospace",
                fontSize: 28,
                letterSpacing: 4,
                textAlign: "center",
                padding: "12px 0",
                backgroundColor: "#f3f3f3",
                borderRadius: 8,
              }}
            >
              {pin}
            </div>
          </DialogContent>
          <DialogActions>
            <Button onClick={copy}>
              {copied ? t.children.pin.copied : t.children.pin.copy}
            </Button>
            <Button appearance="primary" onClick={onClose}>
              {t.children.pin.gotIt}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}