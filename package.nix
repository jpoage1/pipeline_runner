{
  lib,
  python3Packages,
}: let
  runtimeDeps = with python3Packages; [
    packaging
  ];

  testDeps = with python3Packages; [
    pytest
    pytest-cov
    hypothesis
    coverage
    pip
  ];
in
  python3Packages.buildPythonApplication {
    pname = "pipeline_runner";
    version = "0.1.0";
    pyproject = true;

    src = ./.;

    nativeBuildInputs = with python3Packages; [
      setuptools
    ];

    # Add runtime dependencies here if you update pyproject.toml later
    propagatedBuildInputs = runtimeDeps;

    nativeCheckInputs = testDeps;
    passthru = {
      inherit runtimeDeps testDeps;
    };

    pythonImportsCheck = ["pipeline_runner"];

    meta = with lib; {
      description = "A pipeline runner script for running deployments or test suites";
      homepage = "https://github.com/jpoage1/pipeline_runner";
    };
  }
