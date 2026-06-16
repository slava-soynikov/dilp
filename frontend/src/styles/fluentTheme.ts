import { webLightTheme, webDarkTheme, type Theme } from "@fluentui/react-components";

/**
 * Override a handful of Fluent design tokens so the built-in Button/Input/Dialog
 * components blend with the warm EDU4UA-inspired palette in theme.css.
 * Only the most visible tokens are remapped — the rest fall back to Fluent defaults.
 */

const TEAL = "#01696f";
const TEAL_HOVER = "#0c4e54";
const TEAL_PRESSED = "#063e44";
const TEAL_TINT = "#d8e9eb";

const PAPER_BG = "#f7f6f2";
const PAPER_SURFACE = "#f9f8f5";
const PAPER_SURFACE_2 = "#fbfbf9";
const PAPER_BORDER = "#d4d1ca";
const PAPER_TEXT = "#28251d";
const PAPER_TEXT_MUTED = "#7a7974";

export const warmLightTheme: Theme = {
  ...webLightTheme,

  // brand button + accent
  colorBrandBackground: TEAL,
  colorBrandBackgroundHover: TEAL_HOVER,
  colorBrandBackgroundPressed: TEAL_PRESSED,
  colorBrandBackground2: TEAL_TINT,
  colorBrandForeground1: TEAL,
  colorBrandForeground2: TEAL_HOVER,
  colorBrandForegroundLink: TEAL,
  colorBrandForegroundLinkHover: TEAL_HOVER,
  colorBrandStroke1: TEAL,
  colorBrandStroke2: TEAL_TINT,
  colorCompoundBrandBackground: TEAL,
  colorCompoundBrandStroke: TEAL,
  colorCompoundBrandStrokeHover: TEAL_HOVER,
  colorCompoundBrandForeground1: TEAL,
  colorCompoundBrandForeground1Hover: TEAL_HOVER,

  // neutrals — warm paper feel
  colorNeutralBackground1: PAPER_SURFACE,
  colorNeutralBackground2: PAPER_SURFACE_2,
  colorNeutralBackground3: PAPER_BG,
  colorNeutralBackground1Hover: PAPER_SURFACE_2,
  colorNeutralBackground1Pressed: PAPER_BG,
  colorNeutralStroke1: PAPER_BORDER,
  colorNeutralStroke2: PAPER_BORDER,
  colorNeutralForeground1: PAPER_TEXT,
  colorNeutralForeground2: PAPER_TEXT_MUTED,
  colorNeutralForeground3: PAPER_TEXT_MUTED,
};

const TEAL_DARK = "#4f98a3";
const TEAL_DARK_HOVER = "#227f8b";

const DARK_BG = "#171614";
const DARK_SURFACE = "#1c1b19";
const DARK_SURFACE_2 = "#201f1d";
const DARK_BORDER = "#393836";
const DARK_TEXT = "#cdccca";
const DARK_TEXT_MUTED = "#9a9894";

export const warmDarkTheme: Theme = {
  ...webDarkTheme,
  colorBrandBackground: TEAL_DARK,
  colorBrandBackgroundHover: TEAL_DARK_HOVER,
  colorBrandBackgroundPressed: TEAL_DARK_HOVER,
  colorBrandBackground2: "rgba(79,152,163,0.2)",
  colorBrandForeground1: TEAL_DARK,
  colorBrandForeground2: TEAL_DARK_HOVER,
  colorBrandForegroundLink: TEAL_DARK,
  colorBrandForegroundLinkHover: TEAL_DARK_HOVER,
  colorBrandStroke1: TEAL_DARK,
  colorBrandStroke2: "rgba(79,152,163,0.4)",
  colorCompoundBrandBackground: TEAL_DARK,
  colorCompoundBrandStroke: TEAL_DARK,
  colorCompoundBrandStrokeHover: TEAL_DARK_HOVER,
  colorCompoundBrandForeground1: TEAL_DARK,
  colorCompoundBrandForeground1Hover: TEAL_DARK_HOVER,

  colorNeutralBackground1: DARK_SURFACE,
  colorNeutralBackground2: DARK_SURFACE_2,
  colorNeutralBackground3: DARK_BG,
  colorNeutralBackground1Hover: DARK_SURFACE_2,
  colorNeutralBackground1Pressed: DARK_BG,
  colorNeutralStroke1: DARK_BORDER,
  colorNeutralStroke2: DARK_BORDER,
  colorNeutralForeground1: DARK_TEXT,
  colorNeutralForeground2: DARK_TEXT_MUTED,
  colorNeutralForeground3: DARK_TEXT_MUTED,
};
