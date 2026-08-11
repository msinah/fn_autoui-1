from pathlib import Path

from playwright.sync_api import Page

from unit_tools.log_util.recordlog import logs


def install_interaction_recorder(page: Page) -> None:
    page.evaluate(
        """
        () => {
          if (window.__fnAutoRecorderInstalled) {
            return;
          }

          window.__fnAutoRecorderInstalled = true;
          window.__fnAutoRecorderEvents = [];

          const normalize = (value) => String(value || '').replace(/\\s+/g, ' ').trim();
          const escapePyString = (value) =>
            String(value || '').replace(/\\\\/g, '\\\\\\\\').replace(/"/g, '\\"');

          const toPythonCall = (name, value, extra = '') => {
            const suffix = extra ? `, ${extra}` : '';
            return `${name}("${escapePyString(value)}"${suffix})`;
          };

          const buildXPath = (element) => {
            if (!(element instanceof Element)) {
              return '';
            }

            if (element.id) {
              const escapedId = String(element.id).replace(/"/g, '\\"');
              return `//*[@id="${escapedId}"]`;
            }

            const segments = [];
            let node = element;
            while (node && node.nodeType === Node.ELEMENT_NODE) {
              const tagName = node.tagName.toLowerCase();
              let index = 1;
              let sibling = node.previousElementSibling;
              while (sibling) {
                if (sibling.tagName.toLowerCase() === tagName) {
                  index += 1;
                }
                sibling = sibling.previousElementSibling;
              }
              segments.unshift(`${tagName}[${index}]`);
              node = node.parentElement;
            }
            return '/' + segments.join('/');
          };

          const candidateText = (element) => {
            if (!(element instanceof Element)) {
              return '';
            }
            const source =
              element.getAttribute('data-title') ||
              element.getAttribute('title') ||
              element.getAttribute('aria-label') ||
              element.innerText ||
              element.textContent ||
              '';
            return normalize(source).slice(0, 60);
          };

          const buildLocator = (element) => {
            if (!(element instanceof Element)) {
              return '';
            }

            const field =
              element.closest('input,textarea,select,[role="textbox"]') || element;
            const placeholder = normalize(field.getAttribute?.('placeholder') || '');
            if (placeholder) {
              return toPythonCall('get_by_placeholder', placeholder);
            }

            const label = normalize(field.getAttribute?.('aria-label') || '');
            if (label) {
              return toPythonCall('get_by_label', label);
            }

            const textElement =
              element.closest(
                'button,a,label,[role="button"],[role="option"],[role="tab"],li,.el-select-dropdown__item,.el-button,span,div'
              ) || element;
            const text = candidateText(textElement);
            if (text && text.length <= 30) {
              return toPythonCall('get_by_text', text, 'exact=True');
            }

            return buildXPath(element);
          };

          const buildName = (action, element) => {
            const primary =
              candidateText(element) ||
              normalize(element.getAttribute?.('placeholder') || '') ||
              normalize(element.getAttribute?.('aria-label') || '') ||
              normalize(element.getAttribute?.('name') || '') ||
              element.tagName.toLowerCase();
            const shortName = primary.slice(0, 30) || 'element';
            return action === 'fill' ? `input-${shortName}` : `click-${shortName}`;
          };

          const pushEvent = (payload) => {
            if (!payload || !payload.locator) {
              return;
            }
            const events = window.__fnAutoRecorderEvents;
            const last = events[events.length - 1];
            if (
              last &&
              last.method === payload.method &&
              last.locator === payload.locator &&
              (last.value || '') === (payload.value || '')
            ) {
              return;
            }
            events.push(payload);
          };

          document.addEventListener(
            'click',
            (event) => {
              const target = event.target instanceof Element ? event.target : null;
              if (!target) {
                return;
              }
              const element =
                target.closest(
                  'button,a,input,textarea,select,label,[role="button"],[role="option"],[role="tab"],li,.el-select-dropdown__item,.el-radio,.el-checkbox,.el-button'
                ) || target;
              pushEvent({
                name: buildName('click', element),
                switch_to_page: false,
                method: 'click',
                locator: buildLocator(element),
              });
            },
            true
          );

          document.addEventListener(
            'change',
            (event) => {
              const element = event.target;
              if (
                !(element instanceof HTMLInputElement) &&
                !(element instanceof HTMLTextAreaElement) &&
                !(element instanceof HTMLSelectElement)
              ) {
                return;
              }
              const value = normalize(element.value);
              if (!value) {
                return;
              }
              pushEvent({
                name: buildName('fill', element),
                switch_to_page: false,
                method: 'fill',
                locator: buildLocator(element),
                value,
              });
            },
            true
          );
        }
        """
    )


def collect_recorded_steps(page: Page) -> list[dict]:
    steps = page.evaluate("() => window.__fnAutoRecorderEvents || []")
    if not isinstance(steps, list):
        return []
    return [
        step
        for step in steps
        if isinstance(step, dict) and step.get("method") in {"click", "fill"}
    ]


def append_recorded_steps_to_yaml(yaml_path: str, steps: list[dict]) -> int:
    if not steps:
        return 0

    path = Path(yaml_path)
    original_text = path.read_text(encoding="utf-8")
    lines = original_text.splitlines(keepends=True)

    rendered_steps = []
    for step in steps:
        rendered = _render_step(step)
        if rendered and rendered not in original_text and rendered not in rendered_steps:
            rendered_steps.append(rendered)

    if not rendered_steps:
        return 0

    insert_at = _find_insert_index(lines)
    block = []
    if insert_at > 0 and lines[insert_at - 1].strip():
        block.append("\n")
    for rendered in rendered_steps:
        block.append(rendered)
        if not rendered.endswith("\n\n"):
            block.append("\n")

    updated_lines = lines[:insert_at] + block + lines[insert_at:]
    path.write_text("".join(updated_lines), encoding="utf-8")
    logs.info("Recorded %s new steps into %s", len(rendered_steps), yaml_path)
    return len(rendered_steps)


def _find_insert_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#      - name:"):
            return index
        if stripped.startswith("assertion:") or stripped.startswith("#    assertion:"):
            return index
    return len(lines)


def _render_step(step: dict) -> str:
    method = str(step.get("method") or "").strip()
    locator = str(step.get("locator") or "").strip()
    if method not in {"click", "fill"} or not locator:
        return ""

    name = str(step.get("name") or f"{method}-step").strip()
    rows = [
        f"      - name: {_yaml_quote(name)}\n",
        "        switch_to_page: False\n",
        f"        method: {method}\n",
        f"        locator: {_yaml_quote(locator)}\n",
    ]
    value = step.get("value")
    if method == "fill" and value not in (None, ""):
        rows.append(f"        value: {_yaml_quote(str(value))}\n")
    return "".join(rows)


def _yaml_quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"
