# Filename: theme_etl.py

import re
import json
import logging
from pathlib import Path
import shutil

# --- Configuration ---
OLD_THEMES_ROOT = Path("old")  # Root directory containing old theme folders
NEW_THEMES_ROOT = Path("new_themes")  # Output directory for new themes
UTILITIES_DIR = Path(
    "utilities"
)  # Path to the shared utilities folder (relative to where the script runs or adjust)
OUTPUT_JSON_FILE = NEW_THEMES_ROOT / "generated_themes.json"
LOG_FILE = Path("theme_etl.log")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),  # Overwrite log each run
        logging.StreamHandler(),
    ],
)

# --- Mappings & Defaults (CRUCIAL - Needs careful definition based on old themes) ---

# Map old variable names to new names in initial-variables.scss
# Add more mappings based on your analysis of 'old' themes
VARIABLE_MAP = {
    # General & Colors
    "$brand-primary": "$primary",
    "$brand-success": "$success",
    "$brand-info": "$info",
    "$brand-warning": "$warning",
    "$brand-danger": "$danger",
    "$gray-dark": "$grey-dark",  # Example mapping
    "$gray": "$grey",
    "$gray-light": "$grey-light",
    "$gray-lighter": "$grey-lighter",
    # Typography
    "$font-family-sans-serif": "$family-sans-serif",
    "$font-family-monospace": "$family-code",  # Map to code family
    "$font-size-base": "$size-normal",  # Map base size
    "$font-size-lg": "$size-medium",  # Approximate mapping
    "$font-size-sm": "$size-small",  # Approximate mapping
    "$font-weight-light": "$weight-light",
    "$font-weight-normal": "$weight-normal",
    "$font-weight-bold": "$weight-bold",
    # Components
    "$border-radius": "$radius",
    "$border-radius-lg": "$radius-large",
    "$border-radius-sm": "$radius-small",
    "$input-height-base": "$control-height",  # Example component mapping
    "$navbar-default-bg": None,  # Example: Ignore old specific component BGs if using new system
    "$link-color": "$link",  # Map link color if defined separately
    "$link-hover-color": None,  # Often handled by CSS vars now
    # Add many more mappings here...
}

# Map old variable names to new CSS custom property names (registered in themename.scss)
# These often relate to layout, spacing, or base theme settings
CSS_VAR_MAP = {
    "$border-radius": "radius",
    "$border-radius-lg": "radius-large",
    "$border-radius-sm": "radius-small",
    "$headings-font-weight": "$weight-bold",  # Map to a weight var if needed by CSS var
    "$body-bg": None,  # Usually handled by scheme-main-l etc. now
    # Add more mappings...
}

# Default values for initial-variables.scss if not found/mapped
# Based on utilities/light-initial-variables.scss & cerulean/initial-variables.scss
DEFAULT_INITIAL_VARS = {
    "$scheme-h": 221,
    "$scheme-s": "14%",
    "$dark-l": "20%",
    "$light-l": "90%",
    "$black": "hsl(221, 14%, 4%)",
    "$black-bis": "hsl(221, 14%, 9%)",
    "$black-ter": "hsl(221, 14%, 14%)",
    "$grey-darker": "hsl(221, 14%, 21%)",
    "$grey-dark": "hsl(221, 14%, 29%)",
    "$grey": "hsl(221, 14%, 48%)",
    "$grey-light": "hsl(221, 14%, 71%)",
    "$grey-lighter": "hsl(221, 14%, 86%)",
    "$grey-lightest": "hsl(221, 14%, 93%)",
    "$white-ter": "hsl(221, 14%, 96%)",
    "$white-bis": "hsl(221, 14%, 98%)",
    "$white": "hsl(221, 14%, 100%)",
    "$orange": "hsl(14, 100%, 53%)",
    "$yellow": "hsl(42, 100%, 53%)",
    "$green": "hsl(153, 53%, 53%)",
    "$turquoise": "hsl(171, 100%, 41%)",
    "$cyan": "hsl(198, 100%, 70%)",
    "$blue": "hsl(233, 100%, 63%)",
    "$purple": "hsl(271, 100%, 71%)",
    "$red": "hsl(348, 100%, 70%)",
    "$family-sans-serif": '"Inter", "SF Pro", "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Helvetica Neue", "Helvetica", "Arial", sans-serif',
    "$family-monospace": '"Inconsolata", "Hack", "SF Mono", "Roboto Mono", "Source Code Pro", "Ubuntu Mono", monospace',
    "$weight-light": 300,
    "$weight-normal": 400,
    "$weight-medium": 500,
    "$weight-semibold": 600,
    "$weight-bold": 700,
    "$weight-extrabold": 800,
    "$block-spacing": "1.5rem",
    "$radius-small": "0.25rem",
    "$radius": "0.375rem",
    "$radius-medium": "0.5em",
    "$radius-large": "0.75rem",
    "$custom-colors": {},  # Placeholder for theme-specific additions to $my-colors
    # Add defaults for $primary, $link etc. if they might be missing
    "$primary": "$blue",
    "$success": "$green",
    "$info": "$cyan",
    "$warning": "$yellow",
    "$danger": "$red",
    "$light": "$white-ter",
    "$dark": "$grey-darker",
    "$link": "$blue",
}

# Default values for CSS custom properties registered in themename.scss
# Based on cerulean/cerulean.scss
DEFAULT_CSS_VARS = {
    # Deltas
    "hover-background-l-delta": "-5%",
    "active-background-l-delta": "-10%",
    "hover-border-l-delta": "-10%",
    "active-border-l-delta": "-20%",
    "hover-color-l-delta": "-5%",
    "active-color-l-delta": "-10%",
    "hover-shadow-a-delta": -0.05,
    "active-shadow-a-delta": -0.1,
    # Light only (adjust if making dark themes)
    "scheme-brightness": "light",
    "scheme-main-l": "100%",  # Default, might be overridden by theme
    "scheme-main-bis-l": "98%",
    "scheme-main-ter-l": "96%",
    "background-l": "96%",
    "border-weak-l": "93%",
    "border-l": "86%",
    "text-weak-l": "48%",
    "text-l": "29%",
    "text-strong-l": "21%",
    "text-title-l": "14%",
    "scheme-invert-ter-l": "14%",
    "scheme-invert-bis-l": "7%",
    "scheme-invert-l": "4%",
    # Other
    "duration": "294ms",
    "easing": "ease-out",
    "radius-rounded": "9999px",
    "speed": "86ms",
    # Burger specific
    "burger-border-radius": "0.5em",
    "burger-gap": "5px",
    "burger-item-height": "2px",
    "burger-item-width": "20px",
    # Values referencing other CSS Vars (keep as strings)
    "arrow-color": '#{cv.getVar("link")}',
    "loading-color": '#{cv.getVar("border")}',
    "burger-h": '#{cv.getVar("link-h")}',
    "burger-s": '#{cv.getVar("link-s")}',
    "burger-l": '#{cv.getVar("link-l")}',
}

# --- Helper Functions ---


def parse_scss_variable(line: str):
    """Extracts variable name and value from a simple SCSS line."""
    # Ignores lines starting with // or /*
    if line.strip().startswith("//") or line.strip().startswith("/*"):
        return None, None
    # Basic regex for $variable: value; possibly with !default
    match = re.match(r"^\s*\$([\w-]+)\s*:\s*(.+?)(?: !default)?;$", line)
    if match:
        name = f"${match.group(1)}"
        value = match.group(2).strip()
        # Basic cleanup (remove trailing comments)
        value = value.split("//")[0].strip()
        value = value.split("/*")[0].strip()
        # Remove trailing comma if value ends with one (from maps)
        if value.endswith(","):
            value = value[:-1].strip()
        return name, value
    return None, None


def extract_variables_from_file(filepath: Path):
    """Reads an SCSS file and extracts variable definitions."""
    variables = {}
    if not filepath.is_file():
        logging.warning(f"Variable file not found: {filepath}")
        return variables
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                name, value = parse_scss_variable(line)
                if name and value:
                    # Don't overwrite if already found (e.g., _variables takes precedence over _bootswatch)
                    if name not in variables:
                        variables[name] = value
                        logging.debug(
                            f"Extracted: {name} = {value} from {filepath.name}"
                        )
                    else:
                        logging.debug(f"Skipped duplicate: {name} in {filepath.name}")
    except Exception as e:
        logging.error(f"Error reading {filepath}: {e}")
    return variables


def find_invert_color(
    color_name: str, old_vars: dict[str, str], initial_vars: dict[str, str]
) -> str:
    """Tries to find the corresponding invert color variable."""
    # Try specific invert var names first
    possible_invert_names = [
        f"${color_name}-invert",
        f"$brand-{color_name}-invert",  # Old convention?
        f"${color_name}_invert",
    ]
    for name in possible_invert_names:
        if name in old_vars:
            return old_vars[name]
        if name in initial_vars:  # Check defaults too
            return initial_vars[name]

    # Fallback logic based on color type (very basic)
    if color_name in ["white", "light"]:
        return initial_vars.get(
            "$dark", "$black"
        )  # Default dark/black for light colors
    elif color_name in ["black", "dark"]:
        return initial_vars.get(
            "$light", "$white"
        )  # Default light/white for dark colors
    else:
        # Default for semantic colors (primary, info etc.) - often light/white
        return initial_vars.get("$light", "$white")


def transform_theme_data(theme_name: str, old_vars: dict[str, str]):
    """Transforms extracted variables into the new structure."""
    logging.info(f"Transforming theme: {theme_name}")
    # Start with defaults, then override with mapped/extracted values
    initial_vars = DEFAULT_INITIAL_VARS.copy()
    css_vars = DEFAULT_CSS_VARS.copy()
    my_colors_map = {}  # To build the $my-colors map

    # 1. Populate initial_vars: Apply mappings and direct values
    for old_name, old_value in old_vars.items():
        if old_name in VARIABLE_MAP:
            new_name = VARIABLE_MAP[old_name]
            if new_name:
                initial_vars[new_name] = old_value
                logging.debug(f"Mapped initial: {old_name} -> {new_name} = {old_value}")
        # Keep relevant old vars even if not explicitly mapped? (Optional)
        # elif old_name.startswith('$') and old_name not in initial_vars:
        #     initial_vars[old_name] = old_value # Keep potentially useful unmapped vars

    # 2. Populate css_vars: Apply mappings
    for old_name, old_value in old_vars.items():
        if old_name in CSS_VAR_MAP:
            new_css_var_name = CSS_VAR_MAP[old_name]
            if new_css_var_name:
                # Check if the map points to an initial_var name
                if new_css_var_name.startswith("$"):
                    # Reference the initial_var using 'iv.' prefix
                    css_vars[new_css_var_name.lstrip("$")] = f"iv.{new_css_var_name}"
                else:
                    # Directly set the CSS var value
                    css_vars[new_css_var_name] = old_value
                logging.debug(
                    f"Mapped CSS var: {old_name} -> {new_css_var_name} = {css_vars[new_css_var_name]}"
                )

    # 3. Build $my-colors map
    color_keys = [
        "white",
        "black",
        "light",
        "dark",
        "primary",
        "link",
        "info",
        "success",
        "warning",
        "danger",
    ]
    # Add any other potential color keys found in old_vars (e.g., secondary)
    for old_name in old_vars:
        if "color" in old_name or any(
            c in old_name
            for c in [
                "primary",
                "secondary",
                "success",
                "info",
                "warning",
                "danger",
                "link",
            ]
        ):
            potential_key = (
                old_name.replace("$", "")
                .replace("brand-", "")
                .replace("-color", "")
                .lower()
            )
            if potential_key not in color_keys:
                color_keys.append(potential_key)  # Add discovered color keys

    for key in color_keys:
        base_var_name = f"${key}"
        # Find the base color value (check mapped initial_vars first, then defaults)
        base_value = initial_vars.get(base_var_name)
        if not base_value:
            # Try finding in original old_vars if not mapped
            base_value = old_vars.get(base_var_name)
        if not base_value:
            # Try old naming convention
            base_value = old_vars.get(f"$brand-{key}")

        if base_value:
            # Find the invert color
            invert_value = find_invert_color(key, old_vars, initial_vars)
            my_colors_map[key] = (base_value, invert_value)
            logging.debug(
                f"Added to my_colors: '{key}': ({base_value}, {invert_value})"
            )
        else:
            logging.debug(f"Could not find base value for color key: '{key}'")

    # Ensure 'text' color map entry exists (special case)
    if "text" not in my_colors_map:
        text_invert = initial_vars.get("$dark", "$black")
        my_colors_map["text"] = ("transparent", text_invert)
        logging.debug(
            f"Added default 'text' to my_colors: ('transparent', {text_invert})"
        )

    # 4. Populate CSS vars that reference initial vars (using iv. prefix)
    #    These mirror the structure in cerulean.scss's register-vars call
    css_vars["primary"] = f"iv.{VARIABLE_MAP.get('$brand-primary', '$primary')}"
    css_vars["scheme-h"] = "iv.$scheme-h"
    css_vars["scheme-s"] = "iv.$scheme-s"
    css_vars["light-l"] = "iv.$light-l"
    css_vars["dark-l"] = "iv.$dark-l"
    css_vars["light-invert-l"] = "iv.$dark-l"  # Note the inversion mapping
    css_vars["dark-invert-l"] = "iv.$light-l"  # Note the inversion mapping
    css_vars["soft-l"] = "iv.$light-l"
    css_vars["bold-l"] = "iv.$dark-l"
    css_vars["soft-invert-l"] = "iv.$dark-l"
    css_vars["bold-invert-l"] = "iv.$light-l"

    # Typography CSS Vars (reference initial vars via iv.)
    css_vars["family-primary"] = (
        f"iv.{VARIABLE_MAP.get('$font-family-sans-serif', '$family-sans-serif')}"
    )
    css_vars["family-secondary"] = (
        f"iv.{VARIABLE_MAP.get('$font-family-sans-serif', '$family-sans-serif')}"  # Often same as primary
    )
    css_vars["family-code"] = (
        f"iv.{VARIABLE_MAP.get('$font-family-monospace', '$family-code')}"
    )
    css_vars["size-small"] = f"iv.{VARIABLE_MAP.get('$font-size-sm', '$size-small')}"
    css_vars["size-normal"] = (
        f"iv.{VARIABLE_MAP.get('$font-size-base', '$size-normal')}"
    )
    css_vars["size-medium"] = f"iv.{VARIABLE_MAP.get('$font-size-lg', '$size-medium')}"
    css_vars["size-large"] = (
        f"iv.{VARIABLE_MAP.get('$font-size-xl', '$size-large')}"  # Need a
        # default if $font-size-xl not common
    )
    css_vars["weight-light"] = (
        f"iv.{VARIABLE_MAP.get('$font-weight-light', '$weight-light')}"
    )
    css_vars["weight-normal"] = (
        f"iv.{VARIABLE_MAP.get('$font-weight-normal', '$weight-normal')}"
    )
    css_vars["weight-medium"] = (
        f"iv.{VARIABLE_MAP.get('$font-weight-medium', '$weight-medium')}"
    )
    css_vars["weight-semibold"] = (
        f"iv.{VARIABLE_MAP.get('$font-weight-semibold', '$weight-semibold')}"
    )
    css_vars["weight-bold"] = (
        f"iv.{VARIABLE_MAP.get('$font-weight-bold', '$weight-bold')}"
    )
    css_vars["weight-extrabold"] = (
        f"iv.{VARIABLE_MAP.get('$font-weight-extrabold', '$weight-extrabold')}"
    )

    # Other CSS Vars (reference initial vars via iv.)
    css_vars["block-spacing"] = (
        f"iv.{VARIABLE_MAP.get('$block-spacing', '$block-spacing')}"
    )
    css_vars["radius-small"] = (
        f"iv.{VARIABLE_MAP.get('$border-radius-sm', '$radius-small')}"
    )
    css_vars["radius"] = f"iv.{VARIABLE_MAP.get('$border-radius', '$radius')}"
    css_vars["radius-medium"] = (
        f"iv.{VARIABLE_MAP.get('$border-radius-md', '$radius-medium')}"  # Guessing name
    )
    css_vars["radius-large"] = (
        f"iv.{VARIABLE_MAP.get('$border-radius-lg', '$radius-large')}"
    )

    # --- Return structured data ---
    return {
        "initial_vars": initial_vars,
        "css_vars": css_vars,
        "my_colors": my_colors_map,
    }


# Filename: theme_etl.py
# ... (keep imports and other parts of the script the same) ...


def generate_file_content(theme_name: str, transformed_data: dict[str, str]):
    """Generates the content for the four SCSS files."""
    files = {}
    initial_vars = transformed_data["initial_vars"]
    css_vars = transformed_data["css_vars"]
    my_colors = transformed_data["my_colors"]
    theme_name_lower = theme_name.lower()

    # --- 1. initial-variables.scss ---
    # MODIFICATION START: Place @use rules first
    initial_content = f"""@use "../utilities/functions.scss" as fn;
@use "sass:color";
// --- End of @use rules ---

////////////////////////////////////////////////
// {theme_name.upper()}
////////////////////////////////////////////////

// These imports provide defaults and functions.
// Ensure the paths are correct relative to the new theme directory.
@import "../utilities/light-initial-variables.scss";
@import "../utilities/derived-variables.scss";

// --- Theme Specific Overrides ---
// These values override the defaults from the imported files.
"""
    # MODIFICATION END

    # Add mapped/extracted initial vars, prioritizing over defaults
    added_vars = set()
    for name, value in initial_vars.items():
        # Only add if it's different from the default or explicitly mapped
        if (
            name in DEFAULT_INITIAL_VARS
            and DEFAULT_INITIAL_VARS[name] == value
            and name not in VARIABLE_MAP.values()
        ):
            continue  # Skip if it's just the default and wasn't explicitly mapped
        if name.startswith("$"):  # Ensure it's a variable
            initial_content += f"{name}: {value};\n"
            added_vars.add(name)

    # Ensure critical variables (like $primary) are defined, even if using default
    critical_vars = [
        "$primary",
        "$link",
        "$info",
        "$success",
        "$warning",
        "$danger",
        "$light",
        "$dark",
        "$family-sans-serif",
        "$family-code",
    ]
    for cv in critical_vars:
        if cv not in added_vars and cv in initial_vars:
            initial_content += f"{cv}: {initial_vars[cv]};\n"

    # Construct $my-colors map string
    my_colors_map_str = "fn.mergeColorMaps(\n  (\n"
    for name, values in my_colors.items():
        base, invert = values
        # Ensure invert is a valid SCSS value (might need quoting if it's a var name)
        invert_str = str(invert)
        my_colors_map_str += (
            f'    "{name}": (\n      {base},\n      {invert_str},\n    ),\n'
        )
    my_colors_map_str += (
        "  ),\n  $custom-colors // Allows adding more colors via $custom-colors\n);"
    )

    initial_content += f"\n$my-colors: {my_colors_map_str}\n"

    files[f"{theme_name_lower}/initial-variables.scss"] = initial_content.strip()

    # --- 2. {theme_name}.scss (e.g., cerulean.scss) ---
    # NOTE: Ensure @use rules are also first here if any were added later
    theme_scss_content = f"""@use "sass:list";
@use "sass:meta"; // For meta.type-of
@use "../utilities/css-variables" as cv;
@use "../utilities/functions.scss" as fn;
@use "../utilities/setup";
@use "../utilities/derived-variables" as dv;
@use "initial-variables" as iv;
// --- End of @use rules ---

// Ensure the paths are correct relative to the new theme directory.

// --- Theme Configuration ---
// The main lightness of this theme (adjust if needed, e.g., for dark themes)
$scheme-main-l: {css_vars.get('scheme-main-l', '100%')};

// The main scheme color, used for calculations
$scheme-main: hsl(iv.$scheme-h, iv.$scheme-s, $scheme-main-l);

// --- Theme Mixin ---
@mixin light-theme {{ // Assuming light theme for now
  @include cv.register-vars(
    (
"""
    # ... (rest of the theme_scss_content generation remains the same) ...
    # Add CSS vars
    for name, value in css_vars.items():
        # Ensure values that are meant to be strings are quoted if necessary
        val_str = str(value)
        # Basic check: if value doesn't start with number, $, #, hsl, rgb, calc, var, iv., dv., #{
        # and isn't just a percentage
        if (
            not re.match(r"^[0-9#$hrcv]|iv\.|dv\.|#{", val_str.lower())
            and not val_str.endswith("%")
            and not val_str.startswith('"')
            and not val_str.startswith("'")
        ):
            # Quote strings that aren't SCSS variables/functions/keywords
            if val_str.lower() not in [
                "inherit",
                "transparent",
                "initial",
                "unset",
                "none",
                "auto",
                "ease-out",
                "ease-in",
                "ease-in-out",
                "linear",
                "light",
                "dark",
            ]:  # Add known keywords
                val_str = f'"{val_str}"'  # Basic quoting heuristic

        theme_scss_content += f'      "{name}": {val_str},\n'

    # Remove trailing comma from the last item
    if theme_scss_content.endswith(",\n"):
        theme_scss_content = theme_scss_content[:-2] + "\n"

    theme_scss_content += """
    )
  );

  // --- Color Palette Generation ---
  $no-palette: ("white", "black", "light", "dark"); // Colors without full palette

  @each $name, $color-data in iv.$my-colors {
    $base: $color-data;
    $invert: null;
    $light: null; // Placeholder for potential future use
    $dark: null;  // Placeholder for potential future use

    // Handle if $color-data is a list (base, invert, [light], [dark])
    @if meta.type-of($color-data) == "list" {
      $base: list.nth($color-data, 1);
      @if list.length($color-data) > 1 {
        $invert: list.nth($color-data, 2);
      }
      // Add logic here if light/dark variants are provided in the list
      // @if list.length($color-data) > 3 {
      //   $light: list.nth($color-data, 3);
      //   $dark: list.nth($color-data, 4);
      // }
    }

    // Generate the appropriate palette based on the color name
    @if list.index($no-palette, $name) {
      // Basic palette for white, black, light, dark
      @include cv.generate-basic-palette($name, $base, $invert);
    } @else {
      // Full color palette for semantic colors (primary, info, etc.)
      @include cv.generate-color-palette(
        $name,
        $base,
        $scheme-main-l, // Pass the theme's main lightness
        $invert,
        $light, // Pass light/dark if available
        $dark
      );
    }

    // Generate text contrast colors (-on-scheme)
    @include cv.generate-on-scheme-colors($name, $base, $scheme-main);
  }

  // --- Shades, Shadow, Sizes (from derived-variables) ---
  // These assume dv.$shades, dv.$shadow-color, dv.$sizes are defined correctly.
  @each $name, $shade in dv.$shades {
    @include cv.register-var($name, $shade);
  }

  @include cv.register-hsl("shadow", dv.$shadow-color);

  @each $size in dv.$sizes {
    $i: list.index(dv.$sizes, $size);
    $name: "size-#{$i}";
    @include cv.register-var($name, $size);
  }
}
"""
    files[f"{theme_name_lower}/{theme_name_lower}.scss"] = theme_scss_content.strip()

    # --- 3. bulmaswatch.scss ---
    # NOTE: Ensure @use rules are also first here
    bulmaswatch_content = f"""@use "../utilities/setup";
@use "{theme_name_lower}"; // Import the theme mixin file
@use "overrides"; // Import theme-specific CSS overrides
@use "bulma/sass" as bulma; // Import Bulma 1.0 core (.sass extension)
// --- End of @use rules ---

// Main entry point for the {theme_name.upper()} theme.

// Ensure the paths are correct relative to the new theme directory.

/*! bulmaswatch v1.0.0 | MIT License */ // TODO: Update version as needed

// Apply the theme variables and setup to the :root element
:root {{
  @include {theme_name_lower}.light-theme; // Apply the light theme mixin
  @include setup.setup-theme; // Apply general Bulma CSS variable setup
}}

// Optional: Add dark theme application logic if a dark-theme mixin exists
/*
@media (prefers-color-scheme: dark) {{
  :root {{
    // @include {theme_name_lower}.dark-theme;
  }}
}}
[data-theme="dark"],
.theme-dark {{
  // @include {theme_name_lower}.dark-theme;
}}
*/
"""
    files[f"{theme_name_lower}/bulmaswatch.scss"] = bulmaswatch_content.strip()

    # --- 4. overrides.scss (Placeholder) ---
    # NOTE: This file uses @import, which is fine as long as it doesn't also use @use
    overrides_content = f"""// SCSS Overrides for {theme_name.upper()} Theme
// This file contains theme-specific CSS rules that go beyond simple variable changes.

// Ensure the paths are correct relative to the new theme directory.
@import "../utilities/mixins.scss"; // Import shared mixins if needed
@import "initial-variables"; // Import theme variables for use in overrides

// -----------------------------------------------------------------------------
// TODO: Add theme-specific overrides below.
//
// Analyze the original theme's _bootswatch.scss (or equivalent) file
// and adapt the custom CSS rules here. This often requires manual adjustments
// to work correctly with Bulma 1.0's structure and CSS variables.
//
// Example structure (adapt from Cerulean or original theme):
/*
@mixin btn-gradient($color) {{
  background-image: linear-gradient(
    180deg,
    lighten($color, 8%) 0%,
    $color 60%,
    darken($color, 4%) 100%
  );
}}

.button {{
  font-weight: 400 !important; // Example override

  @each $name, $pair in $my-colors {{
    $color: list.nth($pair, 1);
    &.is-#{{$name}} {{
      &:not(.is-outlined):not(.is-inverted) {{
        // @include btn-gradient($color); // Apply custom mixin
      }}
    }}
  }}
}}

.navbar:not(.is-transparent) {{
  // ... navbar overrides using $primary, $white, etc. ...
}}

.hero.is-primary {{
  // ... hero overrides ...
}}
*/
// -----------------------------------------------------------------------------

"""
    files[f"{theme_name_lower}/overrides.scss"] = overrides_content.strip()

    return files


# ... (rest of the script remains the same) ...


def write_json_output(data: dict[str, str], filepath: Path):
    """Writes the generated file data to a JSON file."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)  # Sort keys for consistency
        logging.info(f"Successfully wrote JSON output to {filepath}")
    except Exception as e:
        logging.error(f"Error writing JSON to {filepath}: {e}")


def create_files_from_json(json_filepath: Path, output_base_dir: Path):
    """Reads the JSON file and creates the directory structure and files."""
    if not json_filepath.is_file():
        logging.error(f"JSON file not found: {json_filepath}")
        return
    try:
        with open(json_filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"Read {len(data)} file entries from {json_filepath}")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {json_filepath}: {e}")
        return
    except Exception as e:
        logging.error(f"Error reading JSON file {json_filepath}: {e}")
        return

    output_base_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured output base directory exists: {output_base_dir}")

    # Copy shared utilities to the output directory
    new_utilities_path = output_base_dir / "utilities"
    if UTILITIES_DIR.is_dir():
        try:
            if new_utilities_path.exists():
                shutil.rmtree(new_utilities_path)  # Remove old copy if exists
            shutil.copytree(UTILITIES_DIR, new_utilities_path)
            logging.info(
                f"Copied utilities from {UTILITIES_DIR} to {new_utilities_path}"
            )
        except Exception as e:
            logging.error(f"Failed to copy utilities directory: {e}")
    else:
        logging.warning(
            f"Utilities directory not found at {UTILITIES_DIR}. Shared SCSS files will be missing."
        )

    # Create theme files
    for relative_path_str, content in data.items():
        try:
            # Use pathlib for robust path handling
            relative_path = Path(relative_path_str)
            full_path = output_base_dir / relative_path

            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file content
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            logging.info(f"Created file: {full_path}")

        except OSError as e:
            logging.error(f"Error creating directory/file for {relative_path_str}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error writing file {relative_path_str}: {e}")


# --- Main Execution Logic ---
def main():
    """
    Main function to orchestrate the theme ETL process.

    Steps:
    1. Scan directories in OLD_THEMES_ROOT
    2. Iterate over each theme directory
    3. Extract SCSS variables from _variables.scss and _bootswatch.scss
    4. Transform the extracted data into the new structure
    5. Generate the content for the four SCSS files
    6. Write the generated file contents to a JSON file
    7. Read the JSON file and create the directory structure and files

    """

    logging.info("Starting SCSS theme ETL process...")
    logging.info(f"Scanning old themes in: {OLD_THEMES_ROOT.resolve()}")
    logging.info(f"Outputting new themes to: {NEW_THEMES_ROOT.resolve()}")
    logging.info(f"Expecting utilities in: {UTILITIES_DIR.resolve()}")

    if not OLD_THEMES_ROOT.is_dir():
        logging.error(f"Old themes directory not found: {OLD_THEMES_ROOT.resolve()}")
        return

    all_themes_data = {}

    # 1. Scan directories & 2. Iterate over themes
    theme_dirs = [item for item in OLD_THEMES_ROOT.iterdir() if item.is_dir()]
    logging.info(f"Found {len(theme_dirs)} potential theme directories.")

    for theme_dir in theme_dirs:
        theme_name = theme_dir.name
        logging.info(f"--- Processing theme directory: {theme_name} ---")

        # 3. Extract SCSS variables (Adjust filenames if needed)
        vars_filepath = theme_dir / "_variables.scss"
        bootswatch_filepath = theme_dir / "_bootswatch.scss"

        theme_vars = {}
        # _variables typically has precedence
        theme_vars.update(extract_variables_from_file(vars_filepath))
        # Update with _bootswatch, but don't overwrite existing keys from _variables
        bootswatch_vars = extract_variables_from_file(bootswatch_filepath)
        for name, value in bootswatch_vars.items():
            if name not in theme_vars:
                theme_vars[name] = value

        if not theme_vars:
            logging.warning(
                f"No variables extracted for theme: {theme_name}. Skipping."
            )
            continue
        logging.info(f"Extracted {len(theme_vars)} variables for {theme_name}.")

        # 4. Transform data
        try:
            transformed_data = transform_theme_data(theme_name, theme_vars)
        except Exception as e:
            logging.error(
                f"Failed to transform data for theme {theme_name}: {e}", exc_info=True
            )
            continue  # Skip this theme on transformation error

        # 5. Generate file content
        try:
            generated_files = generate_file_content(theme_name, transformed_data)
            all_themes_data.update(generated_files)
            logging.info(
                f"Generated file content for {len(generated_files)} files for theme {theme_name}."
            )
        except Exception as e:
            logging.error(
                f"Failed to generate file content for theme {theme_name}: {e}",
                exc_info=True,
            )
            continue  # Skip this theme on generation error

    # 6. Write contents to JSON
    if all_themes_data:
        write_json_output(all_themes_data, OUTPUT_JSON_FILE)

        # 7. Iterate JSON and create files/dirs
        create_files_from_json(OUTPUT_JSON_FILE, NEW_THEMES_ROOT)
    else:
        logging.warning(
            "No theme data was generated. JSON file not created, no files written."
        )

    logging.info("--- SCSS theme ETL process finished. ---")


if __name__ == "__main__":
    # Ensure the output directory exists or create it
    NEW_THEMES_ROOT.mkdir(parents=True, exist_ok=True)
    main()
