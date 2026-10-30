<!-- SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- AI-assisted code generation was used during development. -->

--- 
applyTo: "**"
---

# Copilot Instructions (Terminal/Shell)

**Environment:** Windows + PowerShell (pwsh.exe preferred).

**Command syntax:**

- Use PowerShell syntax.
- **Do NOT** use Bash operators like `&&` or `||` in Windows PowerShell 5.1.
- Prefer `;` for simple sequencing in both PS 5.1 and PS 7.
- If conditional chaining is needed, use `&&` / `||` only when the terminal is **PowerShell 7+**.

**Paths:** Use Windows-style paths and quote those with spaces.
