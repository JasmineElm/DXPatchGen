{
  description = "DXPatchGen - Yamaha DX7 Patch Generator and Sound Design Tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;
      in
      {
        devShells.default = pkgs.mkShell {
          name = "dxpatchgen-dev";

          buildInputs = [
            python
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
        };
      }
    );
}
