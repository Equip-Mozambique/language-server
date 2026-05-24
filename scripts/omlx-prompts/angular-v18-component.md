Write an Angular 18 component file `<<component-name>>.component.ts`. Output TypeScript code only. No markdown fences. No commentary.

CRITICAL syntax rules (do NOT use older Angular patterns):
- Standalone component (`standalone: true`). NO NgModule.
- Signals API for state: `signal()`, `computed()`, `effect()` from `@angular/core`.
- Inject dependencies with `inject()`, not constructor parameters.
- Use `templateUrl` + `styleUrl` (singular), not `styleUrls`.
- Imports array must list each Material module + every Angular standalone
  dependency used in the template.

Top-level template (in `<<component-name>>.component.html`) MUST use new
control-flow syntax — `@if`, `@for (... ; track ...)`, `@else if` — NOT
`*ngIf` or `*ngFor`.

Component spec:

  selector: `app-<<component-name>>`
  templateUrl: `./<<component-name>>.component.html`
  styleUrl: `./<<component-name>>.component.scss`

State signals:
  <<name>> = signal<<<Type>>>(<<initial>>)
  <<...>>

Computed signals:
  <<name>> = computed(() => <<expression>>)

Injected services:
  private <<name>> = inject(<<ServiceClass>>)

Methods:
  <<name>>(<<args>>): <<return>> {
    <<body>>
  }

Material modules to import:
  <<list each, e.g. MatButtonModule, MatCardModule>>

Template content goes in a separate file — DO NOT inline `template:` in the
`.ts` file unless explicitly told otherwise.

No `OnInit` hooks unless required — prefer `effect()` for reactive setup.
No `subscribe(...)` in component body — use `toSignal()` from
`@angular/core/rxjs-interop` for observables.
