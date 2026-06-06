# chotic-ui

A small raw-terminal TUI toolkit, no heavy dependencies. Pulled out of the
`-chotic` apps (synchotic, stemchotic) so they share one framework.

## What's in it

- **primitives** - terminal control, raw keyboard input (arrows/esc/backspace),
  themed colors with gradients.
- **components** - box drawing, a configurable gradient ASCII header, formatting
  helpers.
- **widgets**
  - `Menu` - arrow-key menu with toggles, hotkeys, scrolling, pinned items.
  - `FilterList` - real-time filterable, scrollable picker (type to filter).
  - `ConfirmDialog` - yes/no prompt.

## Use

```python
from chotic_ui import configure_header, FilterList, Menu, MenuItem

configure_header(MY_ASCII_BANNER, version="1.0.0")

choice = FilterList(
    [("Vocals  bs_roformer", "vocals"), ("Drums  htdemucs", "drums")],
    title="Pick one", prompt="Filter",
).run()
```

## Install

Editable, typically as a git submodule of the host app:

```sh
pip install -e ./libs/chotic-ui
```

MIT licensed.
