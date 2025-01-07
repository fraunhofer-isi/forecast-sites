// © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import licenseChecker from 'license-checker';

const allowedLicenses = [
  // Include the licenses that you would like to allow for the dependencies of your project.
  // Valid license IDs can be found at https://spdx.org/licenses/
  // In order to find out if a license is compatible, check for example
  // https://joinup.ec.europa.eu/collection/eupl/solution/joinup-licensing-assistant/jla-compatibility-checker
  // and ask your lawyer.

  // public domain
  'CC0-1.0',
  'Unlicense',

  // permissive
  '0BSD',
  'Apache-2.0',
  'BSD-2-Clause',
  'BSD-3-Clause',
  'CC-BY-4.0',
  'MIT',
  'ISC',
  'LGPL-2.1',
  'LGPL-3.0',

  // weakly protective

  // strongly protective
  'GPL-3.0',

  // network protective
  'AGPL-3.0'
];
const allowedLicensesString = allowedLicenses.join(';');
// console.log('Allowed licenes:')
// console.log(allowedLicensesString)

const excludedPackages = [
  'forecast-sites-web@0.0.1' // workaround; determination of the project license does not seem to work correctly
];
const excludePackageString = excludedPackages.join(';');

const options = {
  start: '.',
  production: true,
  onlyAllow: allowedLicensesString,
  excludePackages: excludePackageString
};

licenseChecker.init(
  options,
  function(error, packages) {
    if (error) {
      throw error;
    } else {
      console.log('All packages are fine:');
      console.log(packages);
    }
  }
);