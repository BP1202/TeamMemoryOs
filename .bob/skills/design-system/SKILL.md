# Design System Skill

## Purpose

This skill defines the visual language of TeamMemoryOS.

## Principles

* Premium desktop-first AI workspace.
* Minimal visual noise.
* High information density with generous spacing.
* Dark-first interface.
* Accessibility-first.

## Component Rules

* Never create duplicate Button/Card/Input components.
* Always reuse components from `components/ui`.
* Every component supports loading, disabled, and error states.
* Icons use Lucide React only.
* Motion uses Framer Motion with reduced-motion support.

## AI Components

AI-specific UI belongs in `features/explainability`.

## Styling Rules

* Use Tailwind utility classes.
* Colors come from CSS variables only.
* Never hardcode hex colors inside components.
* Spacing follows the design token scale.

## Accessibility

Every interactive component supports keyboard navigation and visible focus states.