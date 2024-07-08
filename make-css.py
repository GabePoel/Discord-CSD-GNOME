import gi
import subprocess
import base64

gi.require_version('Gtk', '3.0')
from lxml import etree
from gi.repository import Gtk, Gio

icons = {
    '.winButton_a934d8[aria-label="Minimize"]': 'window-minimize-symbolic',
    '.winButton_a934d8[aria-label="Maximize"]': 'window-maximize-symbolic',
    '.winButton_a934d8[aria-label="Close"]': 'window-close-symbolic',
}
colors = {
    'light': '#2f2f2f',
    'dark': '#ffffff'
}
opacities = {
    ':before': 0.1,
    ':hover:before': 0.15,
    ':active:before': 0.3,
}


def svg_to_uri(svg_path):
    with open(svg_path, 'r', encoding='utf-8') as svg_file:
        svg_content = svg_file.read()

    # Encode the SVG content to base64
    encoded_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

    # Create the data URI
    svg_uri = f"data:image/svg+xml;base64,{encoded_svg}"

    return svg_uri


def apply_fill_recursively(element, color):
    """Recursively apply fill color to all elements."""
    if 'fill' in element.attrib:
        element.attrib['fill'] = color
    elif 'style' in element.attrib:
        element.attrib['style'] = f'fill:{color}'
    for child in element:
        apply_fill_recursively(child, color)


def generate_icon(icon_name, output_path, color, opacity):
    # Get the default icon theme
    icon_theme = Gtk.IconTheme.get_default()

    # Lookup the icon
    icon_info = icon_theme.lookup_icon(
        icon_name, 16, Gtk.IconLookupFlags.FORCE_SVG)
    if icon_info:
        icon_path = icon_info.get_filename()
        with open(icon_path, 'rb') as icon_file:
            svg_data = icon_file.read()

        # Parse the SVG data
        svg_root = etree.fromstring(svg_data)

        # Create a new SVG document with a 24x24 px canvas
        svg_ns = "http://www.w3.org/2000/svg"
        new_svg = etree.Element(f"{{{svg_ns}}}svg",
                                width="24",
                                height="24",
                                viewBox="0 0 24 24",
                                xmlns=svg_ns)

        # Create a background circle
        circle = etree.Element(f"{{{svg_ns}}}circle", cx="12", cy="12", r="12",
                               fill=color, attrib={'style': f'opacity:{opacity}'})

        # Apply fill color recursively to the existing SVG elements
        apply_fill_recursively(svg_root, color)

        # Create a group to apply transformations and center the icon
        group = etree.Element(f"{{{svg_ns}}}g",
                              transform="scale(1) translate(4, 4)")

        # Add the original SVG elements to the group
        for element in list(svg_root):
            group.append(element)

        # Append the circle and the group to the new SVG
        new_svg.append(circle)
        new_svg.append(group)

        # Write the modified SVG data to a temporary output file
        temp_output_path = output_path + ".temp.svg"
        with open(temp_output_path, 'wb') as output_file:
            output_file.write(etree.tostring(new_svg, pretty_print=True))

        # Use Inkscape to re-save the SVG file to ensure compatibility
        subprocess.run(['inkscape',
                        '--export-plain-svg',
                        temp_output_path,
                        '--export-filename',
                        output_path])

        # Remove the temporary file
        subprocess.run(['rm', temp_output_path])
        uri = svg_to_uri(output_path)
        subprocess.run(['rm', output_path])
        return uri
    else:
        print(f"Icon '{icon_name}' not found")


if __name__ == "__main__":
    css_pre_fp = './src/pre.css'
    css_post_fp = './src/post.css'
    css_out = open(css_pre_fp, 'r').read()
    for color in colors:
        css_out += f"@media (prefers-color-scheme: {color}) {{\n"
        for icon in icons:
            for opacity in opacities:
                icon_name = icons[icon]
                output_path = f"{icon_name}_{color}{opacity}.svg"
                uri = generate_icon(
                    icon_name,
                    output_path,
                    colors[color],
                    opacities[opacity])
                css_out += f"    {icon}{opacity} {{\n"
                css_out += f"        content: url(\"{uri}\");\n"
                css_out += "    }\n"
        css_out += "}\n"
    css_out += open(css_post_fp, 'r').read()
    css_out_fp = './csd.css'
    open(css_out_fp, 'w').write(css_out)
