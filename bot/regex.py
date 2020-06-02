import re

hex_color_regex = re.compile(r'^#([A-Fa-f0-9]{6})$')
hex3_color_regex = re.compile(r'^#([A-Fa-f0-9]{3})$')
rgb_regex = re.compile(r'^(?:(?:^|,?\s*)([01]?\d\d?|2[0-4]\d|25[0-5])){3}$')
rgb_hex_regex = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^(?:(?:^|,?\s*)([01]?\d\d?|2[0-4]\d|25[0-5])){3}$')
