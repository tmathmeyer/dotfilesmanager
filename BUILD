langs("Python")

py_library (
  name = "dotspec",
  srcs = [ "dotspec.py" ],
  deps = [
    "//impulse/core:debug",
  ],
)

py_library (
  name = "converter",
  srcs = [ "converter.py" ],
  deps = [
    "//impulse/core:debug",
    ":dotspec",
  ],
)

py_binary (
  name = "dotfiles",
  srcs = [ "dotfiles.py" ],
  deps = [
    ":dotspec",
    ":converter",
    "//impulse/args:args",
    "//impulse/core:debug",
  ],
)