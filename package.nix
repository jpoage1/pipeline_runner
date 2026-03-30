{
  lib,
  buildPythonPackage,
  setuptools,
}:
buildPythonPackage {
  pname = "pipeline_runner";
  version = "0.1.0";
  pyproject = true;

  # Reference the local directory containing pyproject.toml
  src = ./.;

  nativeBuildInputs = [
    setuptools
  ];

  # Add runtime dependencies here if you update pyproject.toml later
  propagatedBuildInputs = [];

  pythonImportsCheck = ["pipeline_runner"];

  meta = with lib; {
    description = "A pipeline runner script for running deployments or test suites";
    homepage = "https://github.com/jpoage1/pipeline_runner";
  };
}
