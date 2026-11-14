# FinTrack Design System

## Design direction

FinTrack uses a calm, trustworthy financial dashboard style: deep navy structure, teal actions, green positive states, red negative states, and restrained glass surfaces. Glassmorphism is used for emphasis, not as the default for every element; data tables and forms must remain high-contrast and easy to scan.

## Color palette

```css
:root {
  --navy: #14395f;
  --navy-deep: #0b1c2b;
  --teal: #159d91;
  --teal-dark: #087e76;
  --blue: #3d84c6;
  --green: #2ba25c;
  --orange: #f5a623;
  --red: #d9434d;
  --ink: #17395f;
  --muted: #687d91;
  --surface: #f3f7fa;
  --white: #ffffff;
  --line: #d4e0e8;
  --glass: rgb(255 255 255 / 72%);
  --glass-border: rgb(255 255 255 / 42%);
  --shadow: 0 8px 30px rgb(20 57 95 / 10%);
}
```

### Meaning

- Teal: primary actions, links, focus states
- Green: income, positive savings, completed goals
- Red: expenses, overdue items, destructive actions
- Orange: warnings and near-limit budgets
- Navy: navigation and headings
- Muted: secondary labels and supporting information

Never use color alone to communicate meaning. Pair it with text, an icon, or a status label.

## Typography

- Font stack: `Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif`
- Page title: 24–30px, weight 700
- Section heading: 16–18px, weight 700
- Card heading: 14–16px, weight 700
- Body: 14px, line-height 1.5
- Metadata: 12px, color `--muted`
- Financial amounts: 20–28px, weight 700; use tabular numbers where available

## Layout and spacing

Use a 4px spacing scale:

```text
4  8  12  16  20  24  32  40  48
```

- Page max width: 1100px
- Page padding: 24px desktop, 16px mobile
- Grid gap: 16px
- Card padding: 20px
- Card radius: 12px
- Input/button radius: 8px
- Do not use more than three visual hierarchy levels in one card.

## Glass surfaces

Use glass effects only for navigation, summary cards, and modal overlays:

```css
.glass {
  background: var(--glass);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}
```

Do not use translucent glass behind transaction tables, dense forms, or small text. Those areas need solid surfaces for readability.

## Components

### Buttons

- Primary: teal background, white text
- Secondary: transparent or white background with navy border
- Danger: red background, white text
- Disabled: reduced contrast and `cursor: not-allowed`
- Every destructive button needs a confirmation step.

### Forms

- Label every input
- Put validation text beside the field
- Keep the submit button visible without scrolling where possible
- Show a loading state after submit
- Preserve entered values when validation fails
- Use native date, email, number, and required validation as a first layer

### Cards

Cards should answer one question: balance, spending, budget status, goal progress, or upcoming bills. Avoid mixing unrelated actions and metrics inside one card.

### Financial values

- Income uses a `+` prefix and green styling
- Expenses use a `-` prefix and red styling
- Zero and empty values use neutral styling
- Always show currency and two decimal places for transaction amounts
- Use an explicit empty state instead of showing fake zeros or placeholder charts

### Status labels

Use text labels such as `On track`, `Near limit`, `Over budget`, `Upcoming`, `Paid`, and `Overdue`. Add color and an icon, but never remove the text.

## Charts

- Use real API data only
- Green for income, red for expenses, teal for savings
- Include a legend and accessible text summary
- Keep chart labels readable on mobile
- Show an empty state when the selected range has no data

## Navigation

- Desktop: persistent navy sidebar
- Mobile: collapsible sidebar with visible menu button
- Active page: teal background plus `aria-current="page"`
- Profile and notification menus must be keyboard reachable
- Escape closes open modals and menus

## Accessibility

- Minimum text contrast: WCAG AA
- Visible `:focus-visible` outline in teal
- Every icon-only button needs an accessible label
- Use semantic headings in order
- Use `aria-live="polite"` for save/error notifications
- Do not depend on hover for essential information
- Respect `prefers-reduced-motion`

## Responsive breakpoints

- Mobile: below 560px, one-column layout
- Tablet: 560–800px, two-column cards where readable
- Desktop: above 800px, sidebar and multi-column dashboard
- Tables should scroll horizontally rather than compress financial columns until unreadable

## Implementation rule

Prefer existing vanilla CSS variables and components over one-off inline styles. Add a reusable class when a visual pattern appears twice. Bootstrap may provide behavior or responsive utilities, but the FinTrack palette and component classes remain the source of truth.

### Bootstrap usage

- Load Bootstrap before `static/css/style.css` so FinTrack theme rules win when selectors overlap.
- Use Bootstrap utilities such as `d-flex`, `flex-wrap`, `gap-*`, `row`, `col-*`, and `table-responsive` for layout and responsive behavior.
- Keep FinTrack classes (`card`, `btn`, `field`, `progress`, navigation, and status colors) for visual styling.
- Do not replace the application shell with Bootstrap components or add Bootstrap JavaScript unless a feature specifically needs it.
