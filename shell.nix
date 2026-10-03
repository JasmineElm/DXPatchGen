{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "dxpatchgen-dev";

  buildInputs = [
    pkgs.python312
    pkgs.uv
    pkgs.git
  ];

  shellHook = ''
    export UV_VENV_CLEAR=1
    if [ -d .venv ]; then
      source .venv/bin/activate
      echo "🎹 DXPatchGen Dev Shell (Python 3.12 + uv) — Virtual environment (.venv) activated"
    else
      echo "🎹 DXPatchGen Dev Shell (Python 3.12 + uv)"
      echo "Run 'uv venv && source .venv/bin/activate && uv pip install -e \".[dev]\"' to set up your environment."
    fi
  '';
}
