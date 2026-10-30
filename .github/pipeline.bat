REM SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
REM SPDX-License-Identifier: AGPL-3.0-or-later
REM
REM AI-assisted code generation was used during development.

REM This batch file can be used to run some of the pipeline commands locally.
REM Run it as .github\pipeline.bat from the project root, or as pipeline.bat from
REM inside .github. The working directory does not matter: the script resolves the
REM project root from its own location and switches there, because every path
REM below is relative to the project root.
REM Also see GitHub workflows

REM %~dp0 is the folder holding this script, so %~dp0.. is the project root.
REM popd at the end restores the working directory the caller started from.
pushd "%~dp0.."


echo "Installing python requirements..."
pip install .[dev] | findstr /V /C:"Requirement already satisfied"

echo "Formatting code..."
isort .
black src -S -l 120
black test -S -l 120

echo "Checking code quality with... TODO..."


echo "Running unit tests and determining test coverage..."
pytest --cov

echo "Creating reuse annotations"
REM -t fraunhofer selects .reuse/templates/fraunhofer.jinja2, which is what adds the
REM AI-assisted note. The note is free text rather than an SPDX tag, so annotate's
REM default template cannot carry it. No copyright prefix is passed because the
REM default, spdx, already produces the required SPDX-FileCopyrightText form.
python -m reuse annotate --copyright="Fraunhofer-Gesellschaft e.V., München" --merge-copyrights --license=AGPL-3.0-or-later --skip-unrecognised -t fraunhofer --recursive src test THIRDPARTY.md

echo "Checking REUSE Compliance"
python -m reuse lint

REM Back to wherever the caller invoked this script from.
popd

if "%~1"=="skip_pause" (
 echo "Finished commands."
) else (
 echo "Finished commands."
 pause
)

