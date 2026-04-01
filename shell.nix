{pkgs ? import <nixpkgs> {}}: let
  pipeline_runner = pkgs.callPackage ./package.nix {};

  pythonEnv = pkgs.python3.withPackages (
    ps:
      pipeline_runner.passthru.runtimeDeps ++ pipeline_runner.passthru.testDeps
  );
in
  pkgs.mkShell {
    inputsFrom = [pipeline_runner];

    packages = [
      pythonEnv
    ];

    shellHook = ''
      export PYTHONPATH="$PYTHONPATH:$(pwd)/src"

      echo "Pipeline Runner Shell Active"
      echo "Python version: $(python --version)"
    '';
  }
