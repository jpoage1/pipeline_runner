{
  lib,
  python3Packages,
  black,
  ruff,
  pyright,
}: let
  runtimeDeps = with python3Packages; [
    packaging
    # lib/declarative.py imports yaml at module level (load_task_classes_from_yaml) -
    # a real, declared dependency of the package, not a deferred/optional import.
    pyyaml
  ];

  testDeps = with python3Packages; [
    pytest
    pytest-cov
    hypothesis
    coverage
    pip
  ];

  lintDeps = [
    black
    ruff
    pyright
  ];

  # pyright resolves third-party imports (pytest, yaml, ...) by inspecting
  # a real Python environment, not just nixpkgs metadata - point it at one
  # that has testDeps installed via --pythonpath, same idea as shell.nix's
  # pythonEnv for interactive dev.
  checkPythonEnv = python3Packages.python.withPackages (_: runtimeDeps ++ testDeps);
in
  python3Packages.buildPythonApplication {
    pname = "pipeline_runner";
    version = "0.1.0";
    pyproject = true;

    # Restrict src to what's actually git-tracked so local dev cruft
    # (.venv, .pytest_cache, .coverage, __pycache__) never enters the Nix
    # store or gets scanned by ruff/pyright below - src = ./.; alone pulls
    # in whatever happens to exist on disk at eval time, tracked or not.
    src = lib.fileset.toSource {
      root = ./.;
      fileset = lib.fileset.gitTracked ./.;
    };

    nativeBuildInputs = with python3Packages; [
      setuptools
    ];

    # Add runtime dependencies here if you update pyproject.toml later
    propagatedBuildInputs = runtimeDeps;

    nativeCheckInputs = testDeps ++ lintDeps;

    checkPhase = ''
      runHook preCheck

      ./scripts/enforce-strict-linting.sh

      echo "[check] ruff lint..."
      ruff check src tests

      echo "[check] pyright type-check..."
      pyright --pythonpath ${checkPythonEnv}/bin/python src tests

      echo "[check] pytest..."
      pytest --cov=pipeline_runner --cov-report=term-missing --cov-fail-under=100

      runHook postCheck
    '';

    passthru = {
      inherit runtimeDeps testDeps lintDeps checkPythonEnv;
    };

    pythonImportsCheck = ["pipeline_runner"];

    meta = with lib; {
      description = "A pipeline runner script for running deployments or test suites";
      homepage = "https://github.com/jpoage1/pipeline_runner";
    };
  }
